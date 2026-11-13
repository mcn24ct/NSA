"""Main Sequential Orchestrator for the 5-Stage NASA Microgravity Combustion Pipeline."""

import argparse
import time
from typing import Callable, TypeVar

import psutil

import config
from pipeline_visualizer import run_visualizer
from stage1_ingest import run_stage1_ingest
from stage2_vision import run_stage2_vision
from stage3_index import run_stage3_index
from stage4_rank import run_stage4_rank
from stage5_export import run_stage5_export

T = TypeVar("T")


def get_process_ram_mb() -> float:
    """Return current process tree resident memory usage in MB."""
    proc = psutil.Process()
    total_rss = proc.memory_info().rss
    for child in proc.children(recursive=True):
        try:
            total_rss += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return total_rss / (1024 * 1024)


def run_timed_stage(stage_label: str, func: Callable[[], T]) -> T:
    """Execute a single stage while logging elapsed time and RAM delta."""
    ram_before = get_process_ram_mb()
    t0 = time.perf_counter()
    print(f"[START] {stage_label} | Process RAM: {ram_before:.1f} MB")
    result = func()
    elapsed = time.perf_counter() - t0
    ram_after = get_process_ram_mb()
    print(
        f"[DONE]  {stage_label} | Elapsed: {elapsed:.2f}s | Process RAM: {ram_after:.1f} MB"
    )
    return result


def execute_pipeline(force: bool = False) -> None:
    """Run all 5 pipeline stages sequentially with checkpoint resume support."""
    config.ensure_artifact_dirs()
    t_total = time.perf_counter()

    bundles = run_timed_stage(
        "Stage 1: Ingest & Noise Filter",
        lambda: run_stage1_ingest(force=force),
    )
    descriptions = run_timed_stage(
        "Stage 2: VLM Vision-to-Text",
        lambda: run_stage2_vision(bundles=bundles, force=force),
    )
    index, chunks = run_timed_stage(
        "Stage 3: Multimodal Fusion & FAISS Indexing",
        lambda: run_stage3_index(
            bundles=bundles, descriptions=descriptions, force=force
        ),
    )
    extractions = run_timed_stage(
        "Stage 4: Multi-Query RAG & Qwen3-8B Extraction",
        lambda: run_stage4_rank(index=index, chunks=chunks, force=force),
    )
    scored = run_timed_stage(
        "Stage 5: Mathematical Scoring & Export",
        lambda: run_stage5_export(extractions=extractions),
    )

    total_sec = time.perf_counter() - t_total
    print(
        f"\n[PIPELINE COMPLETE] Ranked {len(scored)} experiments in {total_sec:.2f}s. "
        f"Outputs saved in: {config.ARTIFACTS_DIR}"
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the pipeline orchestrator."""
    parser = argparse.ArgumentParser(
        description="Flame in Freefall - 5-Stage Multimodal AI Pipeline"
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Run pipeline_visualizer.py to display architecture & generate PIPELINE_FLOW.md",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore existing checkpoints and recompute all stages from scratch",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for CLI execution."""
    args = parse_args()
    if args.describe:
        run_visualizer()
        return
    execute_pipeline(force=args.force)


if __name__ == "__main__":
    main()
