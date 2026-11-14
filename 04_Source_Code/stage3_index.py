"""Stage 3: Multimodal fusion, prefix-tagged chunking (<=380 words / <=512 tokens), and FAISS indexing."""

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from fastembed import TextEmbedding
from tokenizers import Tokenizer

import config
from schemas import ExperimentIngestBundle, IndexedChunk, VisualDescription


class LocalBGEEmbedder:
    """Offline wrapper around BAAI/bge-small-en-v1.5 ONNX Runtime and Tokenizer."""

    def __init__(
        self,
        model_dir: Path = config.EMBED_MODEL_DIR,
        tokenizer_path: Path = config.EMBED_TOKENIZER_PATH,
    ) -> None:
        """Load local BGE tokenizer and FastEmbed ONNX session."""
        self.model_dir = model_dir
        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.embedder = TextEmbedding(
            model_name=config.EMBED_MODEL_NAME,
            specific_model_path=str(model_dir),
        )

    def count_tokens(self, text: str) -> int:
        """Return exact token count produced by the BGE WordPiece tokenizer."""
        return len(self.tokenizer.encode(text).ids)

    def truncate_to_max_tokens(
        self, prefix: str, body: str, max_tokens: int = config.MAX_SEQ_LEN
    ) -> tuple[str, int]:
        """Ensure '[EXP | SOURCE | LOC] body' never exceeds 512 tokens."""
        combined = f"{prefix} {body}".strip()
        encoded = self.tokenizer.encode(combined)
        if len(encoded.ids) <= max_tokens:
            return combined, len(encoded.ids)

        words = body.split()
        while words:
            words.pop()
            candidate = f"{prefix} {' '.join(words)}".strip()
            cand_ids = self.tokenizer.encode(candidate).ids
            if len(cand_ids) <= max_tokens:
                return candidate, len(cand_ids)

        return prefix, self.count_tokens(prefix)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Compute L2-normalized float32 embeddings of shape (N, 384)."""
        if not texts:
            return np.zeros((0, config.EMBED_DIM), dtype=np.float32)
        vectors = np.array(list(self.embedder.embed(texts)), dtype=np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        normalized = (vectors / norms).astype(np.float32)
        return normalized


def format_citation_prefix(experiment_id: str, source_file: str, loc: str) -> str:
    """Build mandatory source attribution prefix for every chunk."""
    return f"[EXP: {experiment_id} | SOURCE: {source_file} | LOC: {loc}]"


def split_words_with_overlap(
    text: str,
    max_words: int = config.CHUNK_MAX_WORDS,
    overlap_words: int = config.CHUNK_OVERLAP_WORDS,
) -> list[str]:
    """Split text into word windows of <=380 words with 50-word overlap."""
    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: list[str] = []
    step = max(1, max_words - overlap_words)
    for start in range(0, len(words), step):
        window = words[start : start + max_words]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + max_words >= len(words):
            break
    return chunks


def _extract_leading_btc_tags(text: str) -> tuple[str, str]:
    """Separate leading [REGIME: ...], [HW_TAG: ...], [SENSOR_TAG: ...] tags from body text."""
    m = re.match(
        r"^((?:\[(?:REGIME|HW_TAG|SENSOR_TAG|SOURCE):[^\]]+\]\s*)+)(.*)$",
        text.strip(),
        flags=re.DOTALL,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "", text.strip()


def build_multimodal_chunks(
    bundles: list[ExperimentIngestBundle],
    descriptions: list[VisualDescription],
    embedder: LocalBGEEmbedder,
    include_external_rag: bool = False,
    rag_json_path: Path = config.DATASETS_DIR / "rag_chunks_complete.json",
) -> list[IndexedChunk]:
    """Merge PDF text, VLM descriptions, and optional PSI RAG chunks into token-safe prefixed chunks."""
    chunks: list[IndexedChunk] = []
    chunk_id = 0

    for bundle in bundles:
        for block in bundle.text_blocks:
            base_prefix = format_citation_prefix(
                block.experiment_id, block.source_file, block.page_or_sec
            )
            btc_tags, clean_body = _extract_leading_btc_tags(block.text)
            full_prefix = f"{base_prefix} {btc_tags}".strip() if btc_tags else base_prefix
            body_for_split = clean_body if clean_body else block.text
            for window in split_words_with_overlap(body_for_split):
                safe_text, tok_count = embedder.truncate_to_max_tokens(full_prefix, window)
                chunks.append(
                    IndexedChunk(
                        chunk_id=chunk_id,
                        experiment_id=block.experiment_id,
                        source_file=block.source_file,
                        page_or_sec=block.page_or_sec,
                        modality="pdf_text",
                        token_count=tok_count,
                        prefixed_text=safe_text,
                    )
                )
                chunk_id += 1

    for desc in descriptions:
        prefix = format_citation_prefix(
            desc.experiment_id, desc.source_file, desc.page_or_sec
        )
        vlm_body = f"[VISUAL_{desc.asset_type.upper()}] {desc.technical_description}"
        for window in split_words_with_overlap(vlm_body):
            safe_text, tok_count = embedder.truncate_to_max_tokens(prefix, window)
            chunks.append(
                IndexedChunk(
                    chunk_id=chunk_id,
                    experiment_id=desc.experiment_id,
                    source_file=desc.source_file,
                    page_or_sec=desc.page_or_sec,
                    modality="vlm_vision",
                    token_count=tok_count,
                    prefixed_text=safe_text,
                )
            )
            chunk_id += 1

    if include_external_rag and rag_json_path.exists():
        raw_rag = json.loads(rag_json_path.read_text(encoding="utf-8"))
        for item in raw_rag:
            inv_id = str(item.get("investigation_id") or item.get("psi_id") or "PSI_EXP")
            psi_id = str(item.get("psi_id") or "")
            topic = str(item.get("topic_folder") or "")
            c_type = str(item.get("chunk_type") or "psi_chunk")
            src = str(item.get("source_pdf") or "psi.nasa.gov")
            loc = f"page_{item.get('page', 1)}"
            text_body = str(item.get("text") or "").strip()
            if not text_body:
                continue
            prefix = (
                f"{format_citation_prefix(inv_id, src, loc)} "
                f"[REGIME: 0g_Microgravity] [PSI_ID: {psi_id}] [PILLAR: {topic}] [TYPE: {c_type}]"
            )
            for window in split_words_with_overlap(text_body):
                safe_text, tok_count = embedder.truncate_to_max_tokens(prefix, window)
                chunks.append(
                    IndexedChunk(
                        chunk_id=chunk_id,
                        experiment_id=inv_id,
                        source_file=src,
                        page_or_sec=loc,
                        modality="pdf_text",
                        token_count=tok_count,
                        prefixed_text=safe_text,
                    )
                )
                chunk_id += 1

    return chunks


def run_stage3_index(
    bundles: list[ExperimentIngestBundle] | None = None,
    descriptions: list[VisualDescription] | None = None,
    stage1_checkpoint: Path = config.STAGE1_CHECKPOINT,
    stage2_checkpoint: Path = config.STAGE2_CHECKPOINT,
    faiss_index_path: Path = config.STAGE3_FAISS_INDEX,
    metadata_path: Path = config.STAGE3_METADATA_JSON,
    force: bool = False,
) -> tuple[faiss.IndexFlatIP, list[IndexedChunk]]:
    """Create L2-normalized 384-dim FAISS IndexFlatIP and save chunks_metadata.json."""
    config.ensure_artifact_dirs()
    if faiss_index_path.exists() and metadata_path.exists() and not force:
        raw_meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunks = [IndexedChunk.model_validate(item) for item in raw_meta]
        has_regime_tags = any("[REGIME:" in c.prefixed_text for c in chunks)
        if has_regime_tags:
            index = faiss.read_index(str(faiss_index_path))
            return index, chunks

    if bundles is None:
        raw_s1 = (
            json.loads(stage1_checkpoint.read_text(encoding="utf-8"))
            if stage1_checkpoint.exists()
            else []
        )
        bundles = [ExperimentIngestBundle.model_validate(item) for item in raw_s1]

    if descriptions is None:
        raw_s2 = (
            json.loads(stage2_checkpoint.read_text(encoding="utf-8"))
            if stage2_checkpoint.exists()
            else []
        )
        descriptions = [VisualDescription.model_validate(item) for item in raw_s2]

    embedder = LocalBGEEmbedder()
    chunks = build_multimodal_chunks(bundles, descriptions, embedder)
    index = faiss.IndexFlatIP(config.EMBED_DIM)

    if chunks:
        matrix = embedder.embed_texts([c.prefixed_text for c in chunks])
        index.add(matrix)

    try:
        faiss.write_index(index, str(faiss_index_path))
        metadata_path.write_text(
            json.dumps([c.model_dump() for c in chunks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except (RuntimeError, PermissionError, OSError):
        pass
    return index, chunks


_CACHED_SEARCH_STATE: dict[str, Any] = {}


def load_psi_catalog(
    db_path: Path = config.DATASETS_DIR / "psi_structured.db",
) -> dict[str, dict[str, Any]]:
    """Load NASA PSI structured catalog keyed by code and psi_id."""
    catalog: dict[str, dict[str, Any]] = {}
    if not db_path.exists():
        return catalog
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute("SELECT * FROM investigations_catalog").fetchall()
        for r in rows:
            rec = dict(r)
            code = str(rec.get("code") or "").strip().upper()
            psi_id = str(rec.get("psi_id") or "").strip().upper()
            if code:
                catalog[code] = rec
            if psi_id:
                catalog[psi_id] = rec
    finally:
        con.close()
    return catalog


def _get_combined_search_state() -> tuple[LocalBGEEmbedder, faiss.IndexFlatIP, list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return cached embedder, combined FAISS index (RAG JSON + Stage 3), chunk dicts, and PSI catalog."""
    if _CACHED_SEARCH_STATE.get("ready"):
        return (
            _CACHED_SEARCH_STATE["embedder"],
            _CACHED_SEARCH_STATE["index"],
            _CACHED_SEARCH_STATE["records"],
            _CACHED_SEARCH_STATE["catalog"],
        )

    embedder = LocalBGEEmbedder()
    catalog = load_psi_catalog()
    combined_index = faiss.IndexFlatIP(config.EMBED_DIM)
    records: list[dict[str, Any]] = []

    rag_path = config.DATASETS_DIR / "rag_chunks_complete.json"
    if rag_path.exists():
        raw_rag = json.loads(rag_path.read_text(encoding="utf-8"))
        rag_texts: list[str] = []
        for item in raw_rag:
            text_body = str(item.get("text") or "").strip()
            if not text_body:
                continue
            inv_id = str(item.get("investigation_id") or item.get("psi_id") or "PSI_EXP")
            psi_id = str(item.get("psi_id") or "")
            topic = str(item.get("topic_folder") or "")
            c_type = str(item.get("chunk_type") or "psi_chunk")
            src = str(item.get("source_pdf") or "psi.nasa.gov")
            loc = f"page_{item.get('page', 1)}"
            prefixed = (
                f"[EXP: {inv_id} | SOURCE: {src} | LOC: {loc}] "
                f"[PSI_ID: {psi_id}] [PILLAR: {topic}] [TYPE: {c_type}] {text_body}"
            )
            rag_texts.append(prefixed)
            records.append(
                {
                    "chunk_id": str(item.get("chunk_id") or f"RAG_{len(records)}"),
                    "experiment_id": inv_id,
                    "psi_id": psi_id,
                    "pillar": topic,
                    "chunk_type": c_type,
                    "source_file": src,
                    "page_or_sec": loc,
                    "prefixed_text": prefixed,
                    "raw_text": text_body,
                }
            )
        if rag_texts:
            rag_vecs = embedder.embed_texts(rag_texts)
            combined_index.add(rag_vecs)

    if config.STAGE3_FAISS_INDEX.exists() and config.STAGE3_METADATA_JSON.exists():
        disk_index = faiss.read_index(str(config.STAGE3_FAISS_INDEX))
        raw_meta = json.loads(config.STAGE3_METADATA_JSON.read_text(encoding="utf-8"))
        if disk_index.ntotal == len(raw_meta) and disk_index.ntotal > 0:
            reconstructed = np.vstack(
                [disk_index.reconstruct(i) for i in range(disk_index.ntotal)]
            ).astype(np.float32)
            combined_index.add(reconstructed)
            for m in raw_meta:
                records.append(
                    {
                        "chunk_id": str(m.get("chunk_id")),
                        "experiment_id": str(m.get("experiment_id") or "EXP_FLEX_01"),
                        "psi_id": "PSI-FLEX",
                        "pillar": "01_Prevention",
                        "chunk_type": str(m.get("modality") or "pdf_text"),
                        "source_file": str(m.get("source_file") or ""),
                        "page_or_sec": str(m.get("page_or_sec") or ""),
                        "prefixed_text": str(m.get("prefixed_text") or ""),
                        "raw_text": str(m.get("prefixed_text") or ""),
                    }
                )

    _CACHED_SEARCH_STATE["embedder"] = embedder
    _CACHED_SEARCH_STATE["index"] = combined_index
    _CACHED_SEARCH_STATE["records"] = records
    _CACHED_SEARCH_STATE["catalog"] = catalog
    _CACHED_SEARCH_STATE["ready"] = True
    return embedder, combined_index, records, catalog


def _score_env_match(
    env_target: str, rec: dict[str, Any], catalog: dict[str, dict[str, Any]]
) -> float:
    """Compute environment target compatibility in [0.0, 1.0] for a candidate chunk."""
    target = env_target.strip().lower().replace(" ", "_")
    if target in {"all", ""}:
        return 0.5

    inv_key = str(rec.get("experiment_id") or "").upper()
    psi_key = str(rec.get("psi_id") or "").upper()
    cat_row = catalog.get(inv_key) or catalog.get(psi_key) or {}

    p_psi = float(cat_row.get("pressure_psi") or 14.7)
    p_kpa = p_psi * 6.89476
    o2_min = float(cat_row.get("o2_min") or 20.0)
    o2_max = float(cat_row.get("o2_max") or 21.0)

    text_low = str(rec.get("prefixed_text") or "").lower()
    if "10.2 psi" in text_low or "70.3" in text_low:
        p_kpa = 70.33
    if "8.2 psi" in text_low or "4.3 psi" in text_low:
        p_kpa = 29.65

    if "lunar" in target:
        if p_kpa <= 71.0 and o2_max >= 30.0:
            return 1.0
        if p_kpa <= 71.0 or o2_max >= 30.0:
            return 0.7
        return 0.25
    if "iss" in target or "earth" in target:
        if abs(p_kpa - 101.35) <= 6.0 and o2_min <= 21.0 <= o2_max:
            return 1.0
        if abs(p_kpa - 101.35) <= 10.0:
            return 0.75
        return 0.3
    if "spacesuit" in target or "eva" in target:
        if p_kpa <= 40.0 or o2_max >= 50.0:
            return 1.0
        if o2_max >= 30.0:
            return 0.65
        return 0.2
    return 0.5


def _score_quantitative_density(rec: dict[str, Any]) -> float:
    """Compute quantitative telemetry/table density score in [0.0, 1.0]."""
    text = str(rec.get("prefixed_text") or "")
    matches = re.findall(
        r"\b\d+(?:\.\d+)?\s*(?:psi|kpa|atm|bar|%|cm/s|mm/s|m/s|s|min|mm|cm|k)\b",
        text,
        flags=re.IGNORECASE,
    )
    c_type = str(rec.get("chunk_type") or "").lower()
    table_bonus = 0.35 if ("summary" in c_type or "sheet_" in text or "mean=" in text) else 0.0
    return min(1.0, 0.15 * len(matches) + table_bonus)


def _score_pillar_match(
    pillar_target: str, rec: dict[str, Any], catalog: dict[str, dict[str, Any]]
) -> float:
    """Return 1.0 if chunk matches requested NASA safety pillar or Partial-G proxy."""
    p_req = pillar_target.strip().lower()
    if p_req in {"all", ""}:
        return 0.5

    inv_key = str(rec.get("experiment_id") or "").upper()
    psi_key = str(rec.get("psi_id") or "").upper()
    cat_row = catalog.get(inv_key) or catalog.get(psi_key) or {}
    cat_pillar = str(cat_row.get("pillar") or rec.get("pillar") or "").lower()
    sim_pg = int(cat_row.get("simulates_partial_g") or 0)
    text_low = str(rec.get("prefixed_text") or "").lower()

    if "partial" in p_req:
        if sim_pg == 1 or "partial" in cat_pillar or "partial" in text_low or "mặt trăng" in text_low:
            return 1.0
        return 0.0
    if p_req in cat_pillar or p_req in text_low:
        return 1.0
    return 0.0


def search_weighted(
    query: str,
    weights: dict[str, Any] | None = None,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """Retrieve Top-30 FAISS candidates and rerank with dynamic user weights."""
    embedder, combined_index, records, catalog = _get_combined_search_state()
    if combined_index.ntotal == 0 or not records:
        return []

    w_cfg = weights or {}
    w_sem = float(w_cfg.get("w_semantic", 0.5))
    w_quant = float(w_cfg.get("w_quantitative", 0.3))

    raw_env = w_cfg.get("w_env_target", "All")
    if isinstance(raw_env, (int, float)):
        w_env_val = float(raw_env)
        env_target_str = str(w_cfg.get("env_target", "All"))
    else:
        env_target_str = str(raw_env)
        w_env_val = float(w_cfg.get("w_env_weight", 0.35))

    raw_pil = w_cfg.get("w_pillar", "All")
    if isinstance(raw_pil, (int, float)):
        w_pil_val = float(raw_pil)
        pillar_str = str(w_cfg.get("pillar", "All"))
    else:
        pillar_str = str(raw_pil)
        w_pil_val = 0.25 if pillar_str.lower() != "all" else 0.0

    q_vec = embedder.embed_texts([query])
    cand_k = min(combined_index.ntotal, max(30, top_k * 4))
    scores_mat, ids_mat = combined_index.search(q_vec, cand_k)

    reranked: list[dict[str, Any]] = []
    for rank_i in range(scores_mat.shape[1]):
        idx = int(ids_mat[0, rank_i])
        if idx < 0 or idx >= len(records):
            continue
        base_sim = max(0.0, float(scores_mat[0, rank_i]))
        rec = records[idx]
        env_s = _score_env_match(env_target_str, rec, catalog)
        quant_s = _score_quantitative_density(rec)
        pil_s = _score_pillar_match(pillar_str, rec, catalog)

        final_w_score = (
            w_sem * base_sim
            + w_env_val * env_s
            + w_quant * quant_s
            + w_pil_val * pil_s
        )
        inv_id = str(rec.get("experiment_id") or "")
        cat_entry = catalog.get(inv_id.upper()) or catalog.get(str(rec.get("psi_id") or "").upper()) or {}
        psi_id = str(cat_entry.get("psi_id") or rec.get("psi_id") or "PSI-FLEX")

        reranked.append(
            {
                "chunk_id": rec["chunk_id"],
                "psi_id": psi_id,
                "experiment_id": inv_id,
                "investigation": f"{inv_id} ({psi_id})" if psi_id and psi_id not in inv_id else inv_id,
                "source_file": rec["source_file"],
                "page_or_sec": rec["page_or_sec"],
                "base_faiss_score": round(base_sim, 4),
                "env_match_score": round(env_s, 4),
                "quant_score": round(quant_s, 4),
                "pillar_score": round(pil_s, 4),
                "weighted_score": round(final_w_score, 4),
                "prefixed_text": rec["prefixed_text"],
                "extracted_snippet": rec["raw_text"][:280],
            }
        )

    reranked.sort(key=lambda x: x["weighted_score"], reverse=True)
    results = reranked[:top_k]
    for r_idx, item in enumerate(results, start=1):
        item["rank"] = r_idx
    return results
