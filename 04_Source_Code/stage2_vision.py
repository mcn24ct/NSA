"""Stage 2: Vision-to-technical-text transcription using Qwen2.5-VL-3B + mmproj-F16."""

import json
import os
import time
from pathlib import Path
from typing import Final

import config
from llm_client import LlamaServerManager
from schemas import ExperimentIngestBundle, VisualAsset, VisualDescription

VLM_CTX_SIZE: Final[int] = 2048
VLM_MAX_IMAGE_DIM: Final[int] = 640
VLM_MAX_TOKENS: Final[int] = 200
VLM_TEMPERATURE: Final[float] = 0.1
CHECKPOINT_FLUSH_INTERVAL: Final[int] = 5

VLM_SYSTEM_PROMPT = (
    "You are a NASA microgravity combustion diagnostics specialist. "
    "Analyze the provided scientific image with high technical precision."
)

VLM_USER_PROMPT = (
    "Identify whether this image is a scientific plot/chart or a flame photograph/keyframe:\n"
    "1. If it is a chart/plot: extract exact X-axis label and unit, Y-axis label and unit, "
    "maximum peak value, minimum value, and physical trend.\n"
    "2. If it is a flame photograph or video keyframe: describe flame color (blue, yellow, "
    "luminous soot), spherical symmetry in microgravity, soot shell formation, radiative "
    "quenching, or re-ignition phenomena.\n"
    "Provide a concise, dense paragraph of technical facts."
)


def flush_stage2_checkpoint(
    checkpoint_path: Path, descriptions: list[VisualDescription]
) -> None:
    """Serialize and immediately flush Stage 2 descriptions to disk."""
    payload = json.dumps(
        [d.model_dump() for d in descriptions], indent=2, ensure_ascii=False
    )
    with checkpoint_path.open("w", encoding="utf-8") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())


def load_stage2_checkpoint(checkpoint_path: Path) -> list[VisualDescription]:
    """Load existing Stage 2 checkpoint entries if valid."""
    if not checkpoint_path.exists():
        return []
    try:
        raw_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        return [VisualDescription.model_validate(item) for item in raw_data]
    except (json.JSONDecodeError, ValueError, OSError):
        return []


def describe_visual_asset(
    server: LlamaServerManager, asset: VisualAsset
) -> VisualDescription:
    """Query VLM for a single visual asset with iGPU-optimized token and KV limits."""
    img_path = Path(asset.image_path)
    description_text = server.analyze_image(
        image_path=img_path,
        system_prompt=VLM_SYSTEM_PROMPT,
        user_prompt=VLM_USER_PROMPT,
        max_tokens=VLM_MAX_TOKENS,
        temperature=VLM_TEMPERATURE,
        cache_prompt=False,
        max_image_dim=VLM_MAX_IMAGE_DIM,
    )
    return VisualDescription(
        experiment_id=asset.experiment_id,
        source_file=asset.source_file,
        page_or_sec=asset.page_or_sec,
        asset_type=asset.asset_type,
        image_path=asset.image_path,
        technical_description=description_text,
    )


def run_stage2_vision(
    bundles: list[ExperimentIngestBundle] | None = None,
    stage1_checkpoint: Path = config.STAGE1_CHECKPOINT,
    checkpoint_path: Path = config.STAGE2_CHECKPOINT,
    force: bool = False,
) -> list[VisualDescription]:
    """Run VLM over 100% of Stage 1 visual assets with rolling checkpoint and resume."""
    config.ensure_artifact_dirs()
    existing: list[VisualDescription] = (
        [] if force else load_stage2_checkpoint(checkpoint_path)
    )

    if bundles is None:
        if not stage1_checkpoint.exists():
            if existing:
                return existing
            raise FileNotFoundError(
                f"Stage 1 checkpoint not found: {stage1_checkpoint}"
            )
        raw_s1 = json.loads(stage1_checkpoint.read_text(encoding="utf-8"))
        bundles = [ExperimentIngestBundle.model_validate(item) for item in raw_s1]

    all_assets: list[VisualAsset] = [
        asset for bundle in bundles for asset in bundle.visual_assets
    ]
    descriptions: list[VisualDescription] = list(existing)
    processed_paths: set[str] = {d.image_path for d in descriptions}

    total = len(all_assets)
    pending_count = sum(1 for a in all_assets if a.image_path not in processed_paths)
    if pending_count == 0:
        if not checkpoint_path.exists() or force:
            flush_stage2_checkpoint(checkpoint_path, descriptions)
        return descriptions

    server = LlamaServerManager(
        model_path=config.VLM_MODEL_PATH,
        mmproj_path=config.VLM_MMPROJ_PATH,
        ctx_size=VLM_CTX_SIZE,
        disable_thinking=False,
    )
    newly_completed = 0
    try:
        server.start()
        for idx, asset in enumerate(all_assets, start=1):
            if asset.image_path in processed_paths:
                continue
            t0 = time.perf_counter()
            desc = describe_visual_asset(server, asset)
            elapsed = time.perf_counter() - t0
            descriptions.append(desc)
            processed_paths.add(asset.image_path)
            newly_completed += 1
            percent = (idx / total) * 100.0
            print(
                f"[Stage 2] {asset.experiment_id}: {idx}/{total} ({percent:.1f}%) - {elapsed:.1f}s",
                flush=True,
            )
            if newly_completed % CHECKPOINT_FLUSH_INTERVAL == 0:
                flush_stage2_checkpoint(checkpoint_path, descriptions)
    finally:
        if newly_completed > 0:
            flush_stage2_checkpoint(checkpoint_path, descriptions)
        server.stop()

    return descriptions
