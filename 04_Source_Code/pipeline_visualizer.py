"""Pipeline Architecture Introspection & Visualizer for Flame in Freefall."""

from dataclasses import dataclass
from pathlib import Path

import psutil
from tabulate import tabulate

import config


@dataclass(frozen=True)
class StageSpec:
    """Architectural specification for a single pipeline stage."""

    stage_id: str
    module_name: str
    input_contract: str
    output_contract: str
    ai_model: str
    hardware_target: str
    ram_budget: str
    checkpoint_paths: tuple[Path, ...]


def get_pipeline_stages() -> tuple[StageSpec, ...]:
    """Return immutable definitions of all 5 pipeline stages."""
    return (
        StageSpec(
            stage_id="Stage 1",
            module_name="stage1_ingest.py",
            input_contract="03_Datasets_NASA (PDFs & Videos)",
            output_contract="stage1_ingest.json + PNGs (<=1024px)",
            ai_model="PyMuPDF (>=200x200px) + OpenCV Hist-Diff",
            hardware_target="CPU Multi-Core",
            ram_budget="~0.5 GB RAM",
            checkpoint_paths=(config.STAGE1_CHECKPOINT,),
        ),
        StageSpec(
            stage_id="Stage 2",
            module_name="stage2_vision.py",
            input_contract="stage1_ingest.json (VisualAssets)",
            output_contract="stage2_vision.json (VisualDescriptions)",
            ai_model="Qwen2.5-VL-3B-Q4_K_M + mmproj-F16 (-c 4096)",
            hardware_target="AMD Radeon 860M iGPU (Vulkan -ngl 99)",
            ram_budget="~3.4 GB Shared VRAM (Freed on Exit)",
            checkpoint_paths=(config.STAGE2_CHECKPOINT,),
        ),
        StageSpec(
            stage_id="Stage 3",
            module_name="stage3_index.py",
            input_contract="stage1_ingest.json + stage2_vision.json",
            output_contract="nasa_flame.index + chunks_metadata.json",
            ai_model="BAAI/bge-small-en-v1.5 ONNX (384-dim, <=512 tok)",
            hardware_target="CPU ONNX Runtime + FAISS IndexFlatIP",
            ram_budget="~0.4 GB RAM",
            checkpoint_paths=(config.STAGE3_FAISS_INDEX, config.STAGE3_METADATA_JSON),
        ),
        StageSpec(
            stage_id="Stage 4",
            module_name="stage4_rank.py",
            input_contract="FAISS Top-K (K=6) per experiment_id",
            output_contract="stage4_rank.json (Normalized SI Units)",
            ai_model="Qwen3-8B-Q4_K_M (-c 8192, /no_think, JSON Schema)",
            hardware_target="AMD Radeon 860M iGPU (Vulkan -ngl 99)",
            ram_budget="~5.6 GB Shared VRAM (Freed on Exit)",
            checkpoint_paths=(config.STAGE4_CHECKPOINT,),
        ),
        StageSpec(
            stage_id="Stage 5",
            module_name="scoring_engine.py + stage5_export.py",
            input_contract="stage4_rank.json",
            output_contract="NASA_Flame_Ranking.xlsx + NASA_Flame_Report.md",
            ai_model="Min-Max Normalization + WEIGHTS - Penalty",
            hardware_target="CPU Deterministic Math Engine",
            ram_budget="~0.2 GB RAM",
            checkpoint_paths=(
                config.STAGE5_SCORED_JSON,
                config.STAGE5_EXCEL_PATH,
                config.STAGE5_REPORT_PATH,
            ),
        ),
    )


def check_Checkpoint_status(paths: tuple[Path, ...]) -> str:
    """Return READY if all stage checkpoints exist, otherwise PENDING."""
    if all(p.exists() for p in paths):
        return "READY"
    if any(p.exists() for p in paths):
        return "PARTIAL"
    return "PENDING"


def check_weights_and_runtime() -> list[tuple[str, str, str, str]]:
    """Inspect presence and file sizes of models and runtime binaries."""
    items = [
        ("VLM Backbone (3B Q4_K_M)", config.VLM_MODEL_PATH, "iGPU Vulkan (-ngl 99)"),
        ("VLM Projector (FP16 ViT)", config.VLM_MMPROJ_PATH, "iGPU Vulkan (--mmproj)"),
        ("Embedding Bi-Encoder (ONNX)", config.EMBED_ONNX_PATH, "CPU ONNX Runtime"),
        ("Embedding Tokenizer", config.EMBED_TOKENIZER_PATH, "CPU Fast Tokenizer"),
        ("Reasoning LLM (8B Q4_K_M)", config.LLM_MODEL_PATH, "iGPU Vulkan (-ngl 99)"),
        ("Llama Server Runtime", config.LLAMA_SERVER_EXE, "Vulkan Backend Process"),
    ]
    rows: list[tuple[str, str, str, str]] = []
    for label, path, hw in items:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            status = f"READY ({size_mb:,.1f} MB)"
        else:
            status = "MISSING"
        rows.append((label, path.name, hw, status))
    return rows


def build_ascii_diagram() -> str:
    """Return a concise ASCII dataflow diagram for console display."""
    return (
        "+----------------------------------------------------------------------------+\n"
        "|                  FLAME IN FREEFALL - 5-STAGE AI PIPELINE                   |\n"
        "+----------------------------------------------------------------------------+\n"
        "  [03_Datasets_NASA: PDFs & Videos]\n"
        "          |\n"
        "          v\n"
        "  +------------------------------------------------------------------+       \n"
        "  | STAGE 1: stage1_ingest.py (CPU: PyMuPDF >=200px + OpenCV 5-10kf) |       \n"
        "  +------------------------------------------------------------------+       \n"
        "          |---> artifacts/stage1_ingest.json                                 \n"
        "          v                                                                  \n"
        "  +------------------------------------------------------------------+       \n"
        "  | STAGE 2: stage2_vision.py (Vulkan iGPU: Qwen2.5-VL-3B + mmproj)  |       \n"
        "  |          * Starts llama-server (-c 4096) -> Terminates via psutil|       \n"
        "  +------------------------------------------------------------------+       \n"
        "          |---> artifacts/stage2_vision.json (100% VRAM Freed)               \n"
        "          v                                                                  \n"
        "  +------------------------------------------------------------------+       \n"
        "  | STAGE 3: stage3_index.py (CPU ONNX: bge-small-en-v1.5, 384-dim)  |       \n"
        "  |          * Prefix: [EXP: <id> | SOURCE: <file> | LOC: <page/sec>]|       \n"
        "  |          * Chunks <=380 words (<=512 tokens) -> faiss.IndexFlatIP|       \n"
        "  +------------------------------------------------------------------+       \n"
        "          |---> artifacts/nasa_flame.index + chunks_metadata.json            \n"
        "          v                                                                  \n"
        "  +------------------------------------------------------------------+       \n"
        "  | STAGE 4: stage4_rank.py (Vulkan iGPU: Qwen3-8B-Q4_K_M, -c 8192)  |       \n"
        "  |          * Top-K (K=6) RAG + /no_think + Pydantic JSON Schema    |       \n"
        "  |          * Unit Normalization (kPa, %, mm/s, s) -> psutil Kill   |       \n"
        "  +------------------------------------------------------------------+       \n"
        "          |---> artifacts/stage4_rank.json (100% VRAM Freed)                 \n"
        "          v                                                                  \n"
        "  +------------------------------------------------------------------+       \n"
        "  | STAGE 5: scoring_engine.py & stage5_export.py (CPU Math Engine)  |       \n"
        "  |          * Min-Max Norm * WEIGHTS - Confidence Penalty           |       \n"
        "  +------------------------------------------------------------------+       \n"
        "          |---> NASA_Flame_Ranking.xlsx & NASA_Flame_Report.md               "
    )


def generate_pipeline_flow_markdown(
    output_path: Path = config.PIPELINE_FLOW_MD,
) -> Path:
    """Generate the comprehensive PIPELINE_FLOW.md presentation document."""
    stages = get_pipeline_stages()
    weights_rows = check_weights_and_runtime()
    vm = psutil.virtual_memory()

    stage_table_md = tabulate(
        [
            [
                s.stage_id,
                f"`{s.module_name}`",
                s.input_contract,
                s.output_contract,
                s.ai_model,
                s.hardware_target,
                s.ram_budget,
                check_Checkpoint_status(s.checkpoint_paths),
            ]
            for s in stages
        ],
        headers=[
            "Stage",
            "Module",
            "Input",
            "Output",
            "Model / Engine",
            "Hardware Target",
            "RAM Budget",
            "Checkpoint Status",
        ],
        tablefmt="github",
    )

    weights_table_md = tabulate(
        weights_rows,
        headers=["Component", "Artifact Filename", "Hardware Backend", "Readiness"],
        tablefmt="github",
    )

    content = f"""# FLAME IN FREEFALL — PIPELINE ARCHITECTURE & OPERATIONAL FLOW

## 1. Executive Hardware & Memory Status
- **Host RAM**: `{vm.total / (1024**3):.1f} GB Total` (`{vm.available / (1024**3):.1f} GB Available`)
- **Accelerator**: `AMD Radeon 860M iGPU (Vulkan Backend via llama-server.exe -ngl 99)`
- **Vector Engine**: `ONNX Runtime CPU + FAISS IndexFlatIP(384) (Cosine Similarity on L2 Vectors)`

### Model Weights & Runtime Readiness
{weights_table_md}

---

## 2. 5-Stage Pipeline Architecture Matrix

{stage_table_md}

---

## 3. End-to-End Multimodal Dataflow Diagram (Mermaid)

```mermaid
flowchart TD
    subgraph S1["Stage 1: Ingestion & Signal Filtering (stage1_ingest.py)"]
        D0["03_Datasets_NASA (PDFs & Videos)"] --> P1["PyMuPDF Page Text + Embedded Images (>=200x200px)"]
        D0 --> V1["OpenCV Histogram/Frame-Diff Keyframes (5-10 frames, <=1024px)"]
        P1 & V1 --> CK1[("artifacts/stage1_ingest.json")]
    end

    subgraph S2["Stage 2: Vision-to-Technical-Text (stage2_vision.py)"]
        CK1 --> VLM1["Spawn llama-server.exe: Qwen2.5-VL-3B-Q4_K_M + mmproj-F16 (-c 4096, temp=0.1)"]
        VLM1 --> VLM2["Extract Chart Axes/Units/Extrema & Microgravity Flame Morphology"]
        VLM2 --> VLM3["psutil Kill llama-server.exe (Reclaim 100% iGPU VRAM)"]
        VLM3 --> CK2[("artifacts/stage2_vision.json")]
    end

    subgraph S3["Stage 3: Multimodal Fusion & Vector Indexing (stage3_index.py)"]
        CK1 & CK2 --> CH1["Word Window Chunker (<=380 words, overlap=50, verified <=512 BGE tokens)"]
        CH1 --> CH2["Prepend Citation Tag: [EXP: <id> | SOURCE: <file> | LOC: <page/sec>]"]
        CH2 --> EMB["bge-small-en-v1.5 ONNX -> 384-dim L2-Normalized float32"]
        EMB --> CK3[("artifacts/nasa_flame.index + chunks_metadata.json")]
    end

    subgraph S4["Stage 4: Multi-Query RAG & Unit Standardization (stage4_rank.py)"]
        CK3 --> RAG["FAISS Multi-Query Search Filtered by experiment_id (Top-K = 6)"]
        RAG --> LLM1["Spawn llama-server.exe: Qwen3-8B-Q4_K_M (-c 8192, Thinking OFF)"]
        LLM1 --> LLM2["Pydantic JSON Schema Enforcement: kPa, %, mm/s, s + [SOURCE | LOC]"]
        LLM2 --> LLM3["psutil Kill llama-server.exe (Reclaim 100% iGPU VRAM)"]
        LLM3 --> CK4[("artifacts/stage4_rank.json")]
    end

    subgraph S5["Stage 5: Mathematical Scoring & Report Export (scoring_engine.py & stage5_export.py)"]
        CK4 --> SC1["Min-Max Normalization Across Experiments"]
        SC1 --> SC2["Weighted Sum (WEIGHTS) - Confidence Penalty (nulls / missing citations)"]
        SC2 --> OUT1[("NASA_Flame_Ranking.xlsx + NASA_Flame_Report.md")]
    end
```

---

## 4. Process Lifecycle & VRAM Guard Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Main as main.py (Orchestrator)
    participant Guard as llm_client.py (psutil Guard)
    participant Server as llama-server.exe (Radeon 860M Vulkan)
    participant ONNX as stage3_index.py (ONNX + FAISS)

    Main->>Main: Stage 1: Extract PDF text & >=200px images + 5-10 video keyframes (<=1024px)
    Main->>Guard: Enter Stage 2 Context (Qwen2.5-VL-3B + mmproj-F16, -c 4096)
    Guard->>Server: Spawn subprocess (-ngl 99 --port 8080) & poll /health
    Server-->>Guard: HTTP 200 OK
    Guard->>Server: POST /v1/chat/completions (Base64 PNG + Technical Vision Prompt)
    Server-->>Guard: Structured chart/flame technical description
    Guard->>Server: Exit Context (try...finally -> psutil terminate & kill tree)
    Note over Guard,Server: 100% RAM/VRAM Released Before Stage 3

    Main->>ONNX: Stage 3: Chunk <=380 words (<=512 tokens) with [EXP|SOURCE|LOC] prefix
    ONNX-->>Main: Save faiss.IndexFlatIP(384) + chunks_metadata.json

    Main->>Guard: Enter Stage 4 Context (Qwen3-8B-Q4_K_M, -c 8192, enable_thinking=false)
    Guard->>Server: Spawn subprocess (-ngl 99 --port 8080) & poll /health
    Server-->>Guard: HTTP 200 OK
    Guard->>Server: POST /v1/chat/completions (Top-6 RAG Chunks + Pydantic JSON Schema + /no_think)
    Server-->>Guard: Validated ExperimentExtraction JSON (kPa, %, mm/s, s)
    Guard->>Server: Exit Context (try...finally -> psutil terminate & kill tree)
    Note over Guard,Server: 100% RAM/VRAM Released Before Stage 5

    Main->>Main: Stage 5: Min-Max Normalization + WEIGHTS - Confidence Penalty -> Excel & Markdown
```

---

## 5. Detailed Algorithmic Explanation by Stage (Jury Presentation Guide)

1. **Stage 1 (`stage1_ingest.py`) — Noise Filtering & Keyframe Detection**:
   - Groups raw NASA documents in `03_Datasets_NASA` by `experiment_id`.
   - Uses `PyMuPDF` to extract page-indexed text and filters out logos/icons by enforcing `width >= 200px` and `height >= 200px`.
   - Uses `OpenCV` Bhattacharyya histogram distance combined with mean absolute pixel difference to isolate `5`–`10` peak combustion transition keyframes (ignition, steady spherical burn, radiative extinction) without frame-by-frame redundancy. All visuals are Lanczos-resized so the longest edge is `<= 1024px`.
2. **Stage 2 (`stage2_vision.py`) — High-Precision Multimodal Transcription**:
   - Launches `Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf` paired with `mmproj-F16.gguf` (`-ngl 99`, `-c 4096`, `temperature = 0.1`). Keeping the ViT projector in FP16 preserves fine chart tick marks and flame boundary gradients.
   - Transcribes plots (axes, units, min/max extrema) and flame photographs (color, spherical symmetry, soot shells) while preserving `experiment_id`, `source_file`, and `page_or_sec`, then terminates `llama-server.exe` via `psutil`.
3. **Stage 3 (`stage3_index.py`) — Traceable Chunking & 384-D Cosine Indexing**:
   - Fuses Stage 1 PDF text and Stage 2 VLM descriptions into a single corpus.
   - Splits text into windows of `<= 380` words (`50`-word overlap), prepends `[EXP: <id> | SOURCE: <file> | LOC: <page/sec>]` to every chunk, and verifies via `tokenizer.json` that no chunk exceeds `512` tokens.
   - Encodes chunks with `bge-small-en-v1.5` (`model_optimized.onnx`) into L2-normalized `384`-dimensional `float32` vectors and stores them in `faiss.IndexFlatIP(384)` (exact Inner Product = Cosine Similarity).
4. **Stage 4 (`stage4_rank.py`) — Multi-Query RAG & Unit Standardization**:
   - Queries FAISS across 3 domain-specific combustion probes filtered by `experiment_id` to retrieve Top-K (`K = 6`) chunks.
   - Runs `Qwen3-8B-Q4_K_M.gguf` (`-ngl 99`, `-c 8192`, `temperature = 0.1`) with thinking disabled (`--chat-template-kwargs "{{\\"enable_thinking\\": false}}"` and `/no_think`) and enforces `ExperimentExtraction` JSON Schema so all physical quantities are standardized (`kPa`, `%`, `mm/s`, `s`) with verifiable citations.
5. **Stage 5 (`scoring_engine.py` & `stage5_export.py`) — Mathematical Ranking & Export**:
   - Applies Min-Max normalization (`0..100`) across experiments for quantitative parameters, computes the weighted sum via `WEIGHTS`, and subtracts `confidence_penalty` (`-4.0` per missing physical field, `-10.0` if citations are missing).
   - Outputs `NASA_Flame_Ranking.xlsx` (2 formatted sheets) and `NASA_Flame_Report.md`.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def run_visualizer() -> Path:
    """Print pipeline introspection tables to console and write PIPELINE_FLOW.md."""
    stages = get_pipeline_stages()
    weights_rows = check_weights_and_runtime()

    print(build_ascii_diagram())
    print("\n=== MODEL WEIGHTS & RUNTIME READINESS ===")
    print(
        tabulate(
            weights_rows,
            headers=["Component", "Artifact", "Backend", "Status"],
            tablefmt="grid",
        )
    )

    print("\n=== 5-STAGE PIPELINE ARCHITECTURE MATRIX ===")
    print(
        tabulate(
            [
                [
                    s.stage_id,
                    s.module_name,
                    s.input_contract,
                    s.output_contract,
                    s.ai_model,
                    s.hardware_target,
                    s.ram_budget,
                    check_Checkpoint_status(s.checkpoint_paths),
                ]
                for s in stages
            ],
            headers=[
                "Stage",
                "Module",
                "Input",
                "Output",
                "Model",
                "Hardware Target",
                "RAM Budget",
                "Checkpoint",
            ],
            tablefmt="grid",
        )
    )

    out_md = generate_pipeline_flow_markdown()
    print(f"\n[OK] Generated visual architecture report: {out_md}")
    return out_md


if __name__ == "__main__":
    run_visualizer()
