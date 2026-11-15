"""FastAPI OpenAPI gateway integrating bilingual translation, Stage 3/5 RAG, and Qwen3-8B physics reasoning."""

from collections import OrderedDict
from functools import lru_cache
import gc
import re
import sqlite3
import sys
import threading
from pathlib import Path
from typing import Any, Final

import faiss
import numpy as np
import pandas as pd
import requests
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

SOURCE_DIR: Final[Path] = Path(__file__).resolve().parent
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import config
from llm_client import LlamaServerManager
from stage3_index import LocalBGEEmbedder, search_weighted
from stage5_export import build_summary_tables
from translator_layer import translate_to_english_query

MAX_QUERY_EMBED_CHARS: Final[int] = 256
MAX_CACHE_ENTRIES: Final[int] = 32
_QUERY_LOCK: Final[threading.Lock] = threading.Lock()
_QUERY_CACHE: OrderedDict[tuple[Any, ...], "QueryResponse"] = OrderedDict()


def _memory_guarded_embed_texts(self: LocalBGEEmbedder, texts: list[str]) -> np.ndarray:
    """Compute L2-normalized embeddings in small ONNX batches with bounded query length."""
    if not texts:
        return np.zeros((0, config.EMBED_DIM), dtype=np.float32)
    if len(texts) == 1:
        bounded_texts = [str(texts[0])[:MAX_QUERY_EMBED_CHARS]]
    else:
        bounded_texts = [str(t)[:1024] for t in texts]
    vectors = np.array(
        list(self.embedder.embed(bounded_texts, batch_size=8)),
        dtype=np.float32,
    )
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, 1.0, norms)
    normalized = (vectors / norms).astype(np.float32)
    return normalized


LocalBGEEmbedder.embed_texts = _memory_guarded_embed_texts  # type: ignore[method-assign]

PHYSICS_SYSTEM_PROMPT: Final[str] = (
    "Bạn là Chuyên gia Vật lý Sự cháy Vi trọng lực NASA. "
    "Hãy phân tích dữ liệu thực nghiệm được truy xuất và trả lời hoàn toàn bằng tiếng Việt trong đúng 3 đến 4 gạch đầu dòng ngắn gọn. "
    "Yêu cầu bắt buộc:\n"
    "1. Nhấn mạnh đầy đủ các thông số chuẩn SI gồm áp suất (`kPa`), nồng độ oxy (`% O2`), và tốc độ cháy/luồng khí (`mm/s`).\n"
    "2. Giải thích rõ cơ chế vật lý: sự triệt tiêu đối lưu tự nhiên (buoyancy-driven convection) trong vi trọng lực (0g) hoặc trọng lực một phần (Partial-g), khuếch tán phân tử, ngọn lửa cầu và tổn thất nhiệt bức xạ (radiative quenching).\n"
    "3. Trích dẫn chính xác mã định danh thí nghiệm theo định dạng `[PSI-ID]` ở mỗi luận điểm."
)

_ACTIVE_LLM_SERVER: LlamaServerManager | None = None


class QueryRequest(BaseModel):
    """Input payload for POST /api/query supporting dynamic Stage 3 weights."""

    query: str = Field(
        default="Áp suất và tốc độ gió của các thí nghiệm cháy vật liệu rắn trên Mặt Trăng",
        description="User query in Vietnamese or English.",
    )
    target_env: str = Field(
        default="Lunar_Base",
        description="Target NASA environment ('Lunar_Base', 'ISS_Earth', 'Spacesuit', 'All').",
    )
    w_semantic: float = Field(default=0.50, ge=0.0, le=1.0, description="FAISS semantic similarity weight.")
    w_env_target: str | float = Field(
        default="Lunar_Base",
        description="Target NASA environment ('Lunar_Base', 'ISS_Earth', 'Spacesuit', 'All') or numeric weight.",
    )
    w_env_weight: float = Field(default=0.35, ge=0.0, le=1.0, description="Environment compatibility weight.")
    w_quantitative: float = Field(default=0.30, ge=0.0, le=1.0, description="Quantitative SI data density weight.")
    w_pillar: str | float = Field(
        default="All",
        description="Safety pillar ('All', 'Prevention', 'Detection', 'Suppression', 'Partial-G') or numeric weight.",
    )
    top_k: int = Field(default=8, ge=1, le=30, description="Number of top reranked evidence chunks to return.")
    enable_ai_explanation: bool = Field(
        default=True,
        description="Whether to synthesize Vietnamese combustion physics explanation via Qwen3-8B.",
    )


class QueryResponse(BaseModel):
    """Output payload for POST /api/query consumed by Google AI Studio and Web UI."""

    original_query: str
    translated_query: str
    is_translated: bool
    metrics_summary: list[dict[str, Any]]
    evidence_chunks: list[dict[str, Any]]
    physics_explanation: str


app = FastAPI(
    title="NASA Flame in Freefall — OpenAPI Gateway",
    description="Bilingual Vietnamese-English RAG & Qwen3-8B Physics Explanation API for Google AI Studio.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_qwen_server_healthy(timeout_sec: float = 1.5) -> bool:
    """Return True if local llama-server.exe responds with HTTP 200 on /health."""
    try:
        resp = requests.get(f"{config.SERVER_BASE_URL}/health", timeout=timeout_sec)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def ensure_qwen_server_running(timeout_sec: float = 25.0) -> bool:
    """Verify Qwen3-8B llama-server is active or launch it automatically via LlamaServerManager."""
    global _ACTIVE_LLM_SERVER
    if _is_qwen_server_healthy():
        return True
    try:
        _ACTIVE_LLM_SERVER = LlamaServerManager(
            model_path=config.LLM_MODEL_PATH,
            mmproj_path=None,
            ctx_size=config.LLM_CTX,
            disable_thinking=True,
        )
        _ACTIVE_LLM_SERVER.start(timeout_sec=timeout_sec)
        return True
    except (FileNotFoundError, TimeoutError, RuntimeError, OSError):
        return False


def _build_fallback_physics_explanation(
    original_query: str, df_metrics: pd.DataFrame, df_evidence: pd.DataFrame
) -> str:
    """Generate a deterministic 3-4 bullet Vietnamese SI physics explanation when LLM is offline."""
    if df_metrics.empty:
        return (
            "- Không tìm thấy dữ liệu thực nghiệm khớp trực tiếp với truy vấn trong cơ sở dữ liệu NASA `[PSI-NONE]`.\n"
            "- Ở điều kiện tiêu chuẩn ISS (`101.35 kPa`, `21.0% O2`, `0.0 mm/s`), đối lưu tự nhiên bị triệt tiêu làm ngọn lửa có dạng cầu và truyền chất qua khuếch tán phân tử `[PSI-FLEX]`.\n"
            "- Trong môi trường Căn cứ Mặt Trăng (`70.33 kPa`, `30.0% - 34.0% O2`), áp suất thấp kết hợp nồng độ oxy cao làm giảm giới hạn oxy tối thiểu (LOI) và tăng tốc độ cháy lan `[PSI-BASS]`."
        )

    top_rows = df_metrics.head(3).to_dict(orient="records")
    row0 = top_rows[0]
    psi0 = str(row0.get("PSI_ID") or "PSI-FLEX")
    code0 = str(row0.get("Experiment_Code") or "EXP")
    p0 = row0.get("Pressure_kPa", 101.33)
    o2_0 = str(row0.get("O2_Range_%") or "21.0%")
    af0 = row0.get("Max_Airflow_mm_s", 0.0)
    fuel0 = str(row0.get("Fuels") or "PMMA / n-Heptane")

    bullets: list[str] = [
        (
            f"- **Thông số môi trường & Nhiên liệu chuẩn SI**: Thí nghiệm dẫn đầu `{code0}` (`[{psi0}]`) "
            f"khảo sát vật liệu `{fuel0}` ở áp suất buồng đốt `{p0} kPa`, dải nồng độ oxy `{o2_0} O2` "
            f"và tốc độ luồng khí cưỡng bức tối đa `{af0} mm/s` cho truy vấn *\"{original_query}\"*."
        ),
        (
            f"- **Cơ chế đối lưu & Khuếch tán vi trọng lực**: Khi thiếu lực đẩy nổi Archimedes (buoyancy) "
            f"trong vi trọng lực (`0g`) hoặc trọng lực một phần (`Partial-g`), ngọn lửa không bốc lên theo chiều dọc "
            f"mà phụ thuộc hoàn toàn vào khuếch tán phân tử và luồng gió cưỡng bức bậc thấp (`{af0} mm/s`), "
            f"giúp duy trì cấp oxy tới vùng phản ứng `[{psi0}]`."
        ),
    ]

    if len(top_rows) > 1:
        row1 = top_rows[1]
        psi1 = str(row1.get("PSI_ID") or psi0)
        code1 = str(row1.get("Experiment_Code") or "EXP_2")
        p1 = row1.get("Pressure_kPa", 70.33)
        o2_1 = str(row1.get("O2_Range_%") or "21.0%")
        af1 = row1.get("Max_Airflow_mm_s", 0.0)
        bullets.append(
            f"- **So sánh áp suất & Tốc độ cháy lan**: Đối chiếu với `{code1}` (`[{psi1}]`) tại `{p1} kPa`, "
            f"`{o2_1} O2` và tốc độ gió `{af1} mm/s`, sự gia tăng phần trăm phân tử oxy bù đắp cho mật độ khí "
            f"giảm ở áp suất thấp, làm tăng tốc độ lan truyền ngọn lửa (`flame spread rate`, `mm/s`)."
        )
    else:
        bullets.append(
            f"- **Tổn thất bức xạ & Dập tắt (Radiative Quenching)**: Ở tốc độ luồng khí cực thấp (`< 5.0 mm/s`), "
            f"lớp vỏ bồ hóng và thất thoát nhiệt bức xạ chiếm ưu thế khiến ngọn lửa dễ suy yếu thành ngọn lửa lạnh "
            f"(`cool flame`) hoặc tự tắt (`extinguishment`) `[{psi0}]`."
        )

    if not df_evidence.empty:
        ev0 = df_evidence.iloc[0]
        inv_str = str(ev0.get("Investigation") or code0)
        snippet = str(ev0.get("Extracted_Snippet") or "")[:140].strip()
        bullets.append(
            f"- **Bằng chứng thực nghiệm trích xuất**: Hồ sơ `{inv_str}` (`[{psi0}]`) ghi nhận trực tiếp: "
            f"*\"{snippet}...\"*, xác nhận ngưỡng an toàn cháy cho thiết kế trạm không gian và Căn cứ Mặt Trăng."
        )

    return "\n".join(bullets)


def explain_physics_with_qwen(
    original_query: str, df_metrics: pd.DataFrame, df_evidence: pd.DataFrame
) -> str:
    """Synthesize a 3-4 bullet Vietnamese physics explanation using Qwen3-8B (/no_think) with SI citations."""
    metrics_records = df_metrics.head(5).to_dict(orient="records")
    evidence_records = df_evidence.head(4).to_dict(orient="records")

    user_prompt = (
        f"Truy vấn người dùng: {original_query}\n\n"
        f"Bảng thông số chuẩn SI (Pressure_kPa, O2_Range_%, Max_Airflow_mm_s):\n{metrics_records}\n\n"
        f"Các đoạn bằng chứng thực nghiệm hàng đầu:\n{evidence_records}\n\n"
        "Hãy viết 3-4 gạch đầu dòng giải thích cơ chế vật lý sự cháy vi trọng lực bằng tiếng Việt, "
        "nêu rõ số liệu `kPa`, `% O2`, `mm/s` và trích dẫn `[PSI-ID]`.\n/no_think"
    )

    if ensure_qwen_server_running():
        payload: dict[str, Any] = {
            "messages": [
                {"role": "system", "content": PHYSICS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": config.TEMPERATURE,
            "max_tokens": 380,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        try:
            response = requests.post(
                f"{config.SERVER_BASE_URL}/v1/chat/completions",
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            raw_text = str(response.json()["choices"][0]["message"]["content"])
            cleaned = re.sub(
                r"<think>.*?</think>", "", raw_text, flags=re.DOTALL | re.IGNORECASE
            ).strip()
            if cleaned:
                return cleaned
        except (requests.RequestException, KeyError, IndexError, ValueError):
            pass

    return _build_fallback_physics_explanation(original_query, df_metrics, df_evidence)


@lru_cache(maxsize=MAX_CACHE_ENTRIES)
def _execute_cached_query(
    query: str,
    target_env: str,
    w_semantic: float,
    w_env_target: str | float,
    w_quantitative: float,
    w_pillar: str | float,
    top_k: int,
    enable_ai_explanation: bool,
    w_env_weight: float = 0.35,
) -> QueryResponse:
    """Execute bilingual translation, bounded BGE embedding search, and Qwen3-8B physics explanation."""
    bounded_raw_query = query.strip()[:MAX_QUERY_EMBED_CHARS]
    translation = translate_to_english_query(bounded_raw_query)
    english_query = str(translation["translated_query"]).strip()[:MAX_QUERY_EMBED_CHARS]

    effective_env_target: str | float = (
        w_env_target if isinstance(w_env_target, (int, float)) else target_env
    )
    weights: dict[str, Any] = {
        "w_semantic": w_semantic,
        "env_target": target_env,
        "w_env_target": effective_env_target,
        "w_env_weight": float(w_env_target) if isinstance(w_env_target, (int, float)) else w_env_weight,
        "w_quantitative": w_quantitative,
        "w_pillar": w_pillar,
    }
    search_results = search_weighted(
        query=english_query[:MAX_QUERY_EMBED_CHARS],
        weights=weights,
        top_k=top_k,
    )
    df_metrics, df_evidence = build_summary_tables(search_results)

    physics_explanation = (
        explain_physics_with_qwen(bounded_raw_query, df_metrics, df_evidence)
        if enable_ai_explanation
        else ""
    )

    return QueryResponse(
        original_query=query,
        translated_query=english_query,
        is_translated=bool(translation["is_translated"]),
        metrics_summary=df_metrics.to_dict(orient="records"),
        evidence_chunks=df_evidence.to_dict(orient="records"),
        physics_explanation=physics_explanation,
    )


@app.post("/api/query", response_model=QueryResponse)
def api_query_endpoint(request: QueryRequest) -> QueryResponse:
    """Serialize ONNX/Qwen3-8B access via lock, serve 32-entry LRU cache, cap query<=256 chars, and collect GC."""
    bounded_query = request.query.strip()[:MAX_QUERY_EMBED_CHARS]
    resolved_target_env = (
        request.w_env_target
        if isinstance(request.w_env_target, str) and request.target_env == "Lunar_Base"
        else request.target_env
    )
    cache_key = (
        bounded_query,
        resolved_target_env,
        float(request.w_semantic),
        request.w_env_target,
        float(request.w_quantitative),
        request.w_pillar,
        int(request.top_k),
        bool(request.enable_ai_explanation),
    )

    with _QUERY_LOCK:
        if cache_key in _QUERY_CACHE:
            _QUERY_CACHE.move_to_end(cache_key)
            return _QUERY_CACHE[cache_key]

        try:
            response_obj = _execute_cached_query(
                bounded_query,
                resolved_target_env,
                float(request.w_semantic),
                request.w_env_target,
                float(request.w_quantitative),
                request.w_pillar,
                int(request.top_k),
                bool(request.enable_ai_explanation),
                float(request.w_env_weight),
            )
            _QUERY_CACHE[cache_key] = response_obj
            while len(_QUERY_CACHE) > MAX_CACHE_ENTRIES:
                _QUERY_CACHE.popitem(last=False)
            return response_obj
        finally:
            gc.collect()


@app.get("/api/studio-tool-schema")
def get_studio_tool_schema() -> dict[str, Any]:
    """Return standard OpenAPI 3.0.3 and Google AI Studio Function Declaration schema."""
    parameter_properties: dict[str, Any] = {
        "query": {
            "type": "STRING",
            "description": "Vietnamese or English query about NASA microgravity combustion experiments.",
        },
        "w_semantic": {
            "type": "NUMBER",
            "description": "Weight for FAISS BGE semantic similarity (0.0 to 1.0, default 0.5).",
        },
        "w_env_target": {
            "type": "STRING",
            "description": "Target environment filter: 'Lunar_Base', 'ISS_Earth', 'Spacesuit', or 'All'.",
        },
        "w_quantitative": {
            "type": "NUMBER",
            "description": "Weight for quantitative SI telemetry density (0.0 to 1.0, default 0.3).",
        },
        "w_pillar": {
            "type": "STRING",
            "description": "NASA fire safety pillar: 'All', 'Prevention', 'Detection', 'Suppression', or 'Partial-G'.",
        },
        "top_k": {
            "type": "INTEGER",
            "description": "Number of top ranked evidence chunks to retrieve (default 8).",
        },
        "enable_ai_explanation": {
            "type": "BOOLEAN",
            "description": "Set True to generate Vietnamese combustion physics explanation via Qwen3-8B.",
        },
    }
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "NASA Flame in Freefall Tool API",
            "version": "1.0.0",
            "description": "Bilingual NASA Microgravity Combustion RAG and Qwen3-8B Physics Explanation API.",
        },
        "servers": [{"url": "http://localhost:8000"}],
        "function_declarations": [
            {
                "name": "query_nasa_microgravity_combustion",
                "description": (
                    "Search NASA Physical Sciences Informatics (PSI) microgravity combustion experiments "
                    "with bilingual Vietnamese-English translation, SI-normalized tables (kPa, % O2, mm/s), "
                    "and Qwen3-8B physics explanation."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": parameter_properties,
                    "required": ["query"],
                },
            }
        ],
        "paths": {
            "/api/query": {
                "post": {
                    "operationId": "query_nasa_microgravity_combustion",
                    "summary": "Execute bilingual weighted RAG search and Qwen3-8B physics synthesis.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": QueryRequest.model_json_schema(),
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Successful SI metrics, evidence chunks, and physics explanation.",
                            "content": {
                                "application/json": {
                                    "schema": QueryResponse.model_json_schema(),
                                }
                            },
                        }
                    },
                }
            }
        },
    }


@app.get("/health")
def health_check() -> dict[str, Any]:
    """Check readiness of FAISS index, SQLite PSI database, and local Qwen3-8B server."""
    faiss_exists = config.STAGE3_FAISS_INDEX.exists()
    faiss_vectors = 0
    if faiss_exists:
        try:
            idx = faiss.read_index(str(config.STAGE3_FAISS_INDEX))
            faiss_vectors = int(idx.ntotal)
        except (RuntimeError, OSError):
            faiss_vectors = 0

    db_path = config.DATASETS_DIR / "psi_structured.db"
    db_exists = db_path.exists()
    db_rows = 0
    if db_exists:
        try:
            con = sqlite3.connect(str(db_path))
            try:
                cur = con.execute("SELECT COUNT(*) FROM investigations_catalog")
                row = cur.fetchone()
                db_rows = int(row[0]) if row else 0
            finally:
                con.close()
        except sqlite3.Error:
            db_rows = 0

    qwen_running = _is_qwen_server_healthy(timeout_sec=1.0)
    qwen_weights_exist = config.LLM_MODEL_PATH.exists()

    overall_ok = faiss_exists and db_exists
    return {
        "status": "ok" if overall_ok else "degraded",
        "faiss_index": {
            "exists": faiss_exists,
            "path": str(config.STAGE3_FAISS_INDEX),
            "ntotal": faiss_vectors,
        },
        "sqlite_db": {
            "exists": db_exists,
            "path": str(db_path),
            "catalog_rows": db_rows,
        },
        "qwen3_8b_server": {
            "running": qwen_running,
            "model_weights_exist": qwen_weights_exist,
            "base_url": config.SERVER_BASE_URL,
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
