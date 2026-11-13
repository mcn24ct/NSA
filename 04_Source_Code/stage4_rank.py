"""Stage 4: Multi-query RAG retrieval and unit-normalized extraction via Qwen3-8B."""

import json
from pathlib import Path

import faiss
import numpy as np

import config
from llm_client import LlamaServerManager
from schemas import ExperimentExtraction, IndexedChunk
from stage3_index import LocalBGEEmbedder

RAG_QUERIES: tuple[str, ...] = (
    "chamber pressure kPa atm psia ambient oxygen concentration percentage O2 fuel material",
    "burn rate flame spread rate droplet regression rate mm/s cm/s burn duration extinction time seconds",
    "spherical flame symmetry stability radiative quenching soot shell re-ignition spacecraft fire safety",
)

LLM_SYSTEM_PROMPT = (
    "You are a NASA Combustion Physics Data Extraction Engine. "
    "Extract experimental parameters strictly from the provided retrieved context chunks. "
    "Convert all physical measurements into standard units:\n"
    "- Pressure -> kPa (1 atm = 101.325 kPa, 1 bar = 100 kPa, 1 psia = 6.89476 kPa)\n"
    "- Oxygen concentration -> % (mole or volume percentage, e.g., 21.0)\n"
    "- Burn / regression / spread rate -> mm/s (1 cm/s = 10 mm/s)\n"
    "- Burn duration / extinction time -> s (seconds)\n"
    "If a parameter is not stated in the context, set it to null. "
    "Always include exact source citations formatted as [SOURCE: <file> | LOC: <page/sec>]."
)


def retrieve_top_k_for_experiment(
    experiment_id: str,
    index: faiss.IndexFlatIP,
    chunks: list[IndexedChunk],
    embedder: LocalBGEEmbedder,
    top_k: int = config.TOP_K,
) -> list[IndexedChunk]:
    """Perform multi-query FAISS search filtered by experiment_id to select Top-K chunks."""
    exp_chunk_ids = [c.chunk_id for c in chunks if c.experiment_id == experiment_id]
    if not exp_chunk_ids or index.ntotal == 0:
        return []

    query_vecs = embedder.embed_texts(list(RAG_QUERIES))
    search_k = min(index.ntotal, max(len(chunks), top_k * 4))
    scores_matrix, indices_matrix = index.search(query_vecs, search_k)

    best_scores: dict[int, float] = {}
    exp_id_set = set(exp_chunk_ids)

    for q_idx in range(scores_matrix.shape[0]):
        for rank_idx in range(scores_matrix.shape[1]):
            c_id = int(indices_matrix[q_idx, rank_idx])
            if c_id < 0 or c_id not in exp_id_set:
                continue
            sim = float(scores_matrix[q_idx, rank_idx])
            if c_id not in best_scores or sim > best_scores[c_id]:
                best_scores[c_id] = sim

    ranked_ids = sorted(best_scores.keys(), key=lambda cid: best_scores[cid], reverse=True)
    selected_ids = ranked_ids[:top_k]
    chunk_lookup = {c.chunk_id: c for c in chunks}
    return [chunk_lookup[cid] for cid in selected_ids if cid in chunk_lookup]


def build_extraction_prompt(experiment_id: str, top_chunks: list[IndexedChunk]) -> str:
    """Format retrieved chunks into a grounded prompt for Qwen3-8B."""
    context_lines = [
        f"Chunk #{idx + 1}: {chunk.prefixed_text}"
        for idx, chunk in enumerate(top_chunks)
    ]
    joined_context = "\n\n".join(context_lines)
    return (
        f"Extract standardized parameters and evaluation scores for Experiment ID: {experiment_id}.\n\n"
        f"RETRIEVED MULTIMODAL CONTEXT:\n{joined_context}\n\n"
        "Return a valid JSON object matching the ExperimentExtraction schema."
    )


def run_stage4_rank(
    index: faiss.IndexFlatIP | None = None,
    chunks: list[IndexedChunk] | None = None,
    faiss_index_path: Path = config.STAGE3_FAISS_INDEX,
    metadata_path: Path = config.STAGE3_METADATA_JSON,
    checkpoint_path: Path = config.STAGE4_CHECKPOINT,
    force: bool = False,
) -> list[ExperimentExtraction]:
    """Run multi-query RAG and Qwen3-8B structured JSON extraction for all experiments."""
    config.ensure_artifact_dirs()
    if checkpoint_path.exists() and not force:
        raw_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        return [ExperimentExtraction.model_validate(item) for item in raw_data]

    if index is None or chunks is None:
        if not faiss_index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("Stage 3 FAISS index or metadata not found.")
        index = faiss.read_index(str(faiss_index_path))
        raw_meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunks = [IndexedChunk.model_validate(item) for item in raw_meta]

    experiment_ids = sorted({c.experiment_id for c in chunks})
    extractions: list[ExperimentExtraction] = []

    if experiment_ids:
        embedder = LocalBGEEmbedder()
        contexts_by_exp: dict[str, list[IndexedChunk]] = {
            exp_id: retrieve_top_k_for_experiment(
                exp_id, index, chunks, embedder, top_k=config.TOP_K
            )
            for exp_id in experiment_ids
        }

        server = LlamaServerManager(
            model_path=config.LLM_MODEL_PATH,
            mmproj_path=None,
            ctx_size=config.LLM_CTX,
            disable_thinking=True,
        )
        try:
            server.start()
            for exp_id in experiment_ids:
                top_chunks = contexts_by_exp[exp_id]
                user_prompt = build_extraction_prompt(exp_id, top_chunks)
                raw_dict = server.generate_structured_json(
                    system_prompt=LLM_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    schema_model=ExperimentExtraction,
                )
                raw_dict["experiment_id"] = exp_id
                if not raw_dict.get("citations"):
                    raw_dict["citations"] = [
                        f"[SOURCE: {c.source_file} | LOC: {c.page_or_sec}]"
                        for c in top_chunks[:3]
                    ]
                extractions.append(ExperimentExtraction.model_validate(raw_dict))
        finally:
            server.stop()

    checkpoint_path.write_text(
        json.dumps(
            [e.model_dump() for e in extractions], indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    return extractions
