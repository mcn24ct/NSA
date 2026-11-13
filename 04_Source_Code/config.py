"""Global configuration, file paths, and model hyperparameters for Flame in Freefall."""

from pathlib import Path
from typing import Final

BASE_DIR: Final[Path] = Path(r"D:\MCN\Hackathon_NASA_AI")
MODELS_DIR: Final[Path] = BASE_DIR / "01_Models_Weights"
RUNTIMES_DIR: Final[Path] = BASE_DIR / "02_Runtime_Engines"
DATASETS_DIR: Final[Path] = BASE_DIR / "03_Datasets_NASA"
SOURCE_DIR: Final[Path] = BASE_DIR / "04_Source_Code"
ARTIFACTS_DIR: Final[Path] = SOURCE_DIR / "artifacts"
EXTRACTED_IMAGES_DIR: Final[Path] = ARTIFACTS_DIR / "extracted_visuals"

VLM_DIR: Final[Path] = MODELS_DIR / "VLM_Vision"
VLM_MODEL_PATH: Final[Path] = VLM_DIR / "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
VLM_MMPROJ_PATH: Final[Path] = VLM_DIR / "mmproj-F16.gguf"

EMBED_MODEL_DIR: Final[Path] = MODELS_DIR / "Embedding_Retrieval"
EMBED_ONNX_PATH: Final[Path] = EMBED_MODEL_DIR / "model_optimized.onnx"
EMBED_TOKENIZER_PATH: Final[Path] = EMBED_MODEL_DIR / "tokenizer.json"
EMBED_MODEL_NAME: Final[str] = "BAAI/bge-small-en-v1.5"

LLM_DIR: Final[Path] = MODELS_DIR / "LLM_Reasoning"
LLM_MODEL_PATH: Final[Path] = LLM_DIR / "Qwen3-8B-Q4_K_M.gguf"

LLAMA_CPP_DIR: Final[Path] = RUNTIMES_DIR / "llama-cpp-vulkan"
LLAMA_SERVER_EXE: Final[Path] = LLAMA_CPP_DIR / "llama-server.exe"
PYTHON_EXE: Final[Path] = RUNTIMES_DIR / "venv_hackathon" / "Scripts" / "python.exe"

SERVER_HOST: Final[str] = "127.0.0.1"
SERVER_PORT: Final[int] = 8080
SERVER_BASE_URL: Final[str] = f"http://{SERVER_HOST}:{SERVER_PORT}"

NGL_LAYERS: Final[int] = 99
TEMPERATURE: Final[float] = 0.1
VLM_CTX: Final[int] = 4096
LLM_CTX: Final[int] = 8192

EMBED_DIM: Final[int] = 384
MAX_SEQ_LEN: Final[int] = 512
CHUNK_MAX_WORDS: Final[int] = 380
CHUNK_OVERLAP_WORDS: Final[int] = 50
TOP_K: Final[int] = 6

MIN_IMAGE_WIDTH: Final[int] = 200
MIN_IMAGE_HEIGHT: Final[int] = 200
MAX_IMAGE_DIMENSION: Final[int] = 1024
MIN_VIDEO_KEYFRAMES: Final[int] = 5
MAX_VIDEO_KEYFRAMES: Final[int] = 10

STAGE1_CHECKPOINT: Final[Path] = ARTIFACTS_DIR / "stage1_ingest.json"
STAGE2_CHECKPOINT: Final[Path] = ARTIFACTS_DIR / "stage2_vision.json"
STAGE3_FAISS_INDEX: Final[Path] = ARTIFACTS_DIR / "nasa_flame.index"
STAGE3_METADATA_JSON: Final[Path] = ARTIFACTS_DIR / "chunks_metadata.json"
STAGE4_CHECKPOINT: Final[Path] = ARTIFACTS_DIR / "stage4_rank.json"
STAGE5_SCORED_JSON: Final[Path] = ARTIFACTS_DIR / "stage5_scored.json"
STAGE5_EXCEL_PATH: Final[Path] = ARTIFACTS_DIR / "NASA_Flame_Ranking.xlsx"
STAGE5_REPORT_PATH: Final[Path] = ARTIFACTS_DIR / "NASA_Flame_Report.md"
PIPELINE_FLOW_MD: Final[Path] = SOURCE_DIR / "PIPELINE_FLOW.md"


def ensure_artifact_dirs() -> None:
    """Create artifact and visual cache directories if they do not exist."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
