"""Stage 4: Multi-query RAG retrieval and SI unit-normalized extraction via Qwen3-8B."""

import json
import re
from pathlib import Path
from typing import Any

import faiss

import config
from llm_client import LlamaServerManager
from schemas import ExperimentExtraction, IndexedChunk
from stage3_index import LocalBGEEmbedder

RAG_QUERIES: tuple[str, ...] = (
    "chamber pressure kPa atm psia ambient oxygen concentration percentage O2 fuel material",
    "burn rate flame spread rate droplet regression rate mm/s cm/s burn duration extinction time seconds",
    "spherical flame symmetry stability radiative quenching soot shell re-ignition spacecraft fire safety",
)

FEW_SHOT_EXAMPLE: str = (
    "FEW-SHOT EXTRACTION EXAMPLE:\n"
    "Context snippet: 'Free-floating n-heptane droplet burned in 0.20/0.75/0.05 O2/N2/CO2 "
    "at 1.0 atm and 25 °C with regression rate 0.12 cm/s for 0.30 min [SOURCE: flex.pdf | LOC: page_8].'\n"
    "Expected JSON output:\n"
    "{\n"
    '  "experiment_id": "EXP_EXAMPLE_01",\n'
    '  "fuel_or_material": "n-Heptane",\n'
    '  "pressure_kpa": 101.325,\n'
    '  "oxygen_pct": 20.0,\n'
    '  "burn_rate_mm_s": 1.2,\n'
    '  "burn_duration_s": 18.0,\n'
    '  "flame_stability_score": 90.0,\n'
    '  "fire_safety_score": 84.0,\n'
    '  "data_completeness_score": 92.0,\n'
    '  "key_findings_summary": "Free-floating n-Heptane droplet burned in 20.0% O2 at 101.325 kPa '
    'and 298.15 K with a burn rate of 1.2 mm/s for 18.0 s.",\n'
    '  "citations": ["[SOURCE: flex.pdf | LOC: page_8]"]\n'
    "}"
)

LLM_SYSTEM_PROMPT: str = (
    "You are a NASA Combustion Physics Data Extraction Engine. "
    "Extract experimental parameters strictly from the provided retrieved context chunks.\n\n"
    "1. MANDATORY SELF-CONSISTENCY RULE:\n"
    "Every parameter regarding fuel (`fuel_or_material`), pressure (`pressure_kpa`), "
    "oxygen concentration (`oxygen_pct`), burn rate (`burn_rate_mm_s`), and burn duration "
    "(`burn_duration_s`) mentioned in `key_findings_summary` or the retrieved context "
    "MUST be populated with its converted value in the corresponding JSON field and MUST NEVER be `null`.\n\n"
    "2. SI STANDARDIZATION & UNIT CONVERSION RULES:\n"
    "- Pressure (`pressure_kpa`) -> convert all to `kPa`: "
    "`1.0 atm = 101.325 kPa`, `1.0 bar = 100.0 kPa`, `1.0 psi = 6.89476 kPa`, "
    "`1.0 torr / mmHg = 0.133322 kPa`, `1000 Pa = 1.0 kPa`.\n"
    "- Oxygen concentration (`oxygen_pct`) -> convert to volume/mole percentage `%`: "
    "`0.20 O2 -> 20.0`, `0.21 O2 -> 21.0`.\n"
    "- Flame spread / regression / burn rate (`burn_rate_mm_s`) -> convert all to `mm/s`: "
    "`1.0 cm/s = 10.0 mm/s`, `1.0 m/s = 1000.0 mm/s`, `1.0 in/s = 25.4 mm/s`.\n"
    "- Burn duration (`burn_duration_s`) -> convert all to seconds `s`: "
    "`1.0 min = 60.0 s`, `1000 ms = 1.0 s`.\n"
    "- Temperature (when mentioned in descriptions) -> convert to Kelvin `K` (`°C + 273.15`).\n"
    "- Evaluation scores (`flame_stability_score`, `fire_safety_score`, `data_completeness_score`) "
    "must be rated on a 0.0 to 100.0 scale.\n"
    "Always include exact source citations formatted as [SOURCE: <file> | LOC: <page/sec>].\n\n"
    f"{FEW_SHOT_EXAMPLE}"
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
    """Format retrieved chunks and SI conversion instructions into a grounded prompt."""
    context_lines = [
        f"Chunk #{idx + 1}: {chunk.prefixed_text}"
        for idx, chunk in enumerate(top_chunks)
    ]
    joined_context = "\n\n".join(context_lines)
    return (
        f"Extract standardized parameters and evaluation scores (0-100 scale) for Experiment ID: {experiment_id}.\n\n"
        "Apply SI / Standardized Unit Conversions:\n"
        "- Pressure (`pressure_kpa`): 1.0 atm = 101.325 kPa, 1.0 bar = 100.0 kPa, "
        "1.0 psi = 6.89476 kPa, 1.0 torr/mmHg = 0.133322 kPa, 1000 Pa = 1.0 kPa.\n"
        "- Oxygen (`oxygen_pct`): mole/volume fraction to % (0.20 O2 -> 20.0, 0.21 O2 -> 21.0).\n"
        "- Burn Rate (`burn_rate_mm_s`): 1.0 cm/s = 10.0 mm/s, 1.0 m/s = 1000.0 mm/s, 1.0 in/s = 25.4 mm/s.\n"
        "- Burn Duration (`burn_duration_s`): 1.0 min = 60.0 s, 1000 ms = 1.0 s.\n"
        "- Temperature in summary: Kelvin K (°C + 273.15).\n"
        "SELF-CONSISTENCY RULE: Any value for `fuel_or_material`, `pressure_kpa`, `oxygen_pct`, "
        "`burn_rate_mm_s`, or `burn_duration_s` mentioned in `key_findings_summary` MUST be "
        "populated in its JSON field and MUST NOT be null.\n\n"
        f"{FEW_SHOT_EXAMPLE}\n\n"
        f"RETRIEVED MULTIMODAL CONTEXT:\n{joined_context}\n\n"
        "Return a valid JSON object matching the ExperimentExtraction schema."
    )


def enforce_self_consistency(
    raw_dict: dict[str, Any], top_chunks: list[IndexedChunk]
) -> dict[str, Any]:
    """Synchronize null structured fields from summary/context and normalize SI units."""
    summary = str(raw_dict.get("key_findings_summary") or "")
    combined_text = f"{summary}\n" + "\n".join(c.prefixed_text for c in top_chunks)

    if not raw_dict.get("fuel_or_material"):
        fuel_match = re.search(
            r"\b(n-heptane|heptane|methanol|ethanol|pmma|acrylic|cotton|nomex|dodecane|hexadecane|octane|butane|methane|hydrogen)\b",
            combined_text,
            re.IGNORECASE,
        )
        if fuel_match:
            token = fuel_match.group(1)
            raw_dict["fuel_or_material"] = (
                "n-Heptane" if token.lower() in {"heptane", "n-heptane"} else token.capitalize()
            )

    if raw_dict.get("pressure_kpa") is None:
        for pattern, factor in (
            (r"(\d+(?:\.\d+)?)\s*kpa\b", 1.0),
            (r"(\d+(?:\.\d+)?)\s*atm\b", 101.325),
            (r"(\d+(?:\.\d+)?)\s*bar\b", 100.0),
            (r"(\d+(?:\.\d+)?)\s*psi(?:a)?\b", 6.89476),
            (r"(\d+(?:\.\d+)?)\s*(?:torr|mmhg)\b", 0.133322),
            (r"(\d+(?:\.\d+)?)\s*pa\b", 0.001),
        ):
            m_press = re.search(pattern, combined_text, re.IGNORECASE)
            if m_press:
                raw_dict["pressure_kpa"] = round(float(m_press.group(1)) * factor, 3)
                break

    if raw_dict.get("oxygen_pct") is None:
        m_frac = re.search(
            r"\b(0\.\d+)(?:/0\.\d+)*\s*O2\b", combined_text, re.IGNORECASE
        )
        m_pct = re.search(
            r"\b(\d+(?:\.\d+)?)\s*%\s*(?:O2|oxygen)\b", combined_text, re.IGNORECASE
        )
        if m_frac:
            raw_dict["oxygen_pct"] = round(float(m_frac.group(1)) * 100.0, 2)
        elif m_pct:
            raw_dict["oxygen_pct"] = round(float(m_pct.group(1)), 2)
    elif isinstance(raw_dict.get("oxygen_pct"), (int, float)) and 0.0 < float(raw_dict["oxygen_pct"]) <= 1.0:
        raw_dict["oxygen_pct"] = round(float(raw_dict["oxygen_pct"]) * 100.0, 2)

    if raw_dict.get("burn_rate_mm_s") is None:
        for pattern, factor in (
            (r"(\d+(?:\.\d+)?)\s*mm\s*/\s*s\b", 1.0),
            (r"(\d+(?:\.\d+)?)\s*cm\s*/\s*s\b", 10.0),
            (r"(\d+(?:\.\d+)?)\s*m\s*/\s*s\b", 1000.0),
            (r"(\d+(?:\.\d+)?)\s*in\s*/\s*s\b", 25.4),
        ):
            m_rate = re.search(pattern, combined_text, re.IGNORECASE)
            if m_rate:
                raw_dict["burn_rate_mm_s"] = round(float(m_rate.group(1)) * factor, 3)
                break

    if raw_dict.get("burn_duration_s") is None:
        for pattern, factor in (
            (r"(?:to\s+)?(\d+(?:\.\d+)?)\s*(?:seconds|sec|s)\b", 1.0),
            (r"(\d+(?:\.\d+)?)\s*(?:minutes|min)\b", 60.0),
            (r"(\d+(?:\.\d+)?)\s*ms\b", 0.001),
        ):
            m_dur = re.search(pattern, combined_text, re.IGNORECASE)
            if m_dur:
                raw_dict["burn_duration_s"] = round(float(m_dur.group(1)) * factor, 3)
                break

    for score_key in ("flame_stability_score", "fire_safety_score", "data_completeness_score"):
        val = raw_dict.get(score_key)
        if isinstance(val, (int, float)) and 0.0 < float(val) <= 10.0:
            raw_dict[score_key] = round(float(val) * 10.0, 2)

    return raw_dict


def _is_checkpoint_consistent(items: list[ExperimentExtraction]) -> bool:
    """Return True only if all cached extractions have synchronized non-null core fields."""
    if not items:
        return False
    for item in items:
        if (
            item.fuel_or_material is None
            or item.pressure_kpa is None
            or item.oxygen_pct is None
            or item.burn_rate_mm_s is None
            or item.burn_duration_s is None
        ):
            return False
    return True


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
        cached = [ExperimentExtraction.model_validate(item) for item in raw_data]
        if _is_checkpoint_consistent(cached):
            return cached

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
                raw_dict = enforce_self_consistency(raw_dict, top_chunks)
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
