"""Lifecycle and memory guard manager for llama-server.exe (VLM & LLM modes)."""

import base64
import json
import subprocess
import time
from pathlib import Path
from types import TracebackType
from typing import Any

import cv2
import psutil
import requests
from pydantic import BaseModel

import config


class LlamaServerManager:
    """Context-managed wrapper around llama-server.exe with psutil memory cleanup."""

    def __init__(
        self,
        model_path: Path,
        ctx_size: int = 2048,
        mmproj_path: Path | None = None,
        disable_thinking: bool = False,
        port: int = config.SERVER_PORT,
        ngl: int = config.NGL_LAYERS,
    ) -> None:
        """Initialize server configuration parameters."""
        self.model_path = model_path
        self.ctx_size = ctx_size
        self.mmproj_path = mmproj_path
        self.disable_thinking = disable_thinking
        self.port = port
        self.ngl = ngl
        self.base_url = f"http://{config.SERVER_HOST}:{self.port}"
        self.process: subprocess.Popen[bytes] | None = None

    def build_command(self) -> list[str]:
        """Construct the exact llama-server.exe CLI command array."""
        cmd: list[str] = [
            str(config.LLAMA_SERVER_EXE),
            "-m",
            str(self.model_path),
            "-ngl",
            str(self.ngl),
            "-c",
            str(self.ctx_size),
            "--host",
            config.SERVER_HOST,
            "--port",
            str(self.port),
        ]
        if self.mmproj_path is not None:
            cmd.extend(["--mmproj", str(self.mmproj_path)])
        if self.disable_thinking:
            cmd.extend(
                ["--chat-template-kwargs", json.dumps({"enable_thinking": False})]
            )
        return cmd

    def start(self, timeout_sec: float = 120.0) -> None:
        """Launch llama-server.exe and block until /health returns HTTP 200."""
        self.kill_stale_servers()
        if not config.LLAMA_SERVER_EXE.exists():
            raise FileNotFoundError(
                f"llama-server executable not found: {config.LLAMA_SERVER_EXE}"
            )
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weight not found: {self.model_path}")
        if self.mmproj_path is not None and not self.mmproj_path.exists():
            raise FileNotFoundError(f"MMProj weight not found: {self.mmproj_path}")

        cmd = self.build_command()
        self.process = subprocess.Popen(
            cmd,
            cwd=str(config.LLAMA_CPP_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.monotonic() + timeout_sec
        health_url = f"{self.base_url}/health"
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"llama-server terminated prematurely with code {self.process.returncode}"
                )
            try:
                resp = requests.get(health_url, timeout=2.0)
                if resp.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.5)

        self.stop()
        raise TimeoutError(
            f"llama-server failed to become healthy within {timeout_sec}s"
        )

    def stop(self) -> None:
        """Terminate llama-server.exe and any child processes via psutil."""
        try:
            if self.process is not None:
                try:
                    parent = psutil.Process(self.process.pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    parent.terminate()
                    _, alive = psutil.wait_procs([parent, *children], timeout=5.0)
                    for proc in alive:
                        try:
                            proc.kill()
                        except psutil.NoSuchProcess:
                            pass
                except psutil.NoSuchProcess:
                    pass
        finally:
            self.process = None
            self.kill_stale_servers()

    @staticmethod
    def kill_stale_servers() -> int:
        """Scan active OS processes via psutil and kill any residual llama-server.exe."""
        killed_count = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if "llama-server" in name:
                    proc.kill()
                    proc.wait(timeout=3.0)
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
        return killed_count

    def __enter__(self) -> "LlamaServerManager":
        """Enter context manager and start server."""
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Guarantee 100% RAM/VRAM release on context exit."""
        self.stop()

    @staticmethod
    def encode_image_base64(image_path: Path, max_dim: int = 640) -> str:
        """Downscale longest edge to <= max_dim via INTER_AREA and encode to Base64 URI."""
        img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img is not None:
            height, width = img.shape[:2]
            longest = max(height, width)
            if longest > max_dim:
                scale = max_dim / float(longest)
                new_w = max(1, int(round(width * scale)))
                new_h = max(1, int(round(height * scale)))
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            ok, encoded = cv2.imencode(".png", img)
            raw_bytes = encoded.tobytes() if ok else image_path.read_bytes()
        else:
            raw_bytes = image_path.read_bytes()
        b64_str = base64.b64encode(raw_bytes).decode("ascii")
        return f"data:image/png;base64,{b64_str}"

    def analyze_image(
        self,
        image_path: Path,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 200,
        temperature: float = 0.1,
        cache_prompt: bool = False,
        max_image_dim: int = 640,
    ) -> str:
        """Send a multimodal vision request to Qwen2.5-VL via OpenAI chat API."""
        image_uri = self.encode_image_base64(image_path, max_dim=max_image_dim)
        payload: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_uri}},
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            "cache_prompt": cache_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"]).strip()

    def generate_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema_model: type[BaseModel],
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        """Request strict JSON output conforming to a Pydantic schema from Qwen3-8B."""
        enforced_prompt = f"{user_prompt.rstrip()}\n/no_think"
        payload: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enforced_prompt},
            ],
            "temperature": config.TEMPERATURE,
            "max_tokens": max_tokens,
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {
                "type": "json_object",
                "schema": schema_model.model_json_schema(),
            },
        }
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=180.0,
        )
        response.raise_for_status()
        content = str(response.json()["choices"][0]["message"]["content"]).strip()
        validated = schema_model.model_validate_json(content)
        return validated.model_dump()
