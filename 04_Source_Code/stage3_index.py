"""Stage 3: Multimodal fusion, prefix-tagged chunking (<=380 words / <=512 tokens), and FAISS indexing."""

import json
from pathlib import Path

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


def build_multimodal_chunks(
    bundles: list[ExperimentIngestBundle],
    descriptions: list[VisualDescription],
    embedder: LocalBGEEmbedder,
) -> list[IndexedChunk]:
    """Merge PDF text and VLM descriptions into token-safe prefixed chunks."""
    chunks: list[IndexedChunk] = []
    chunk_id = 0

    for bundle in bundles:
        for block in bundle.text_blocks:
            prefix = format_citation_prefix(
                block.experiment_id, block.source_file, block.page_or_sec
            )
            for window in split_words_with_overlap(block.text):
                safe_text, tok_count = embedder.truncate_to_max_tokens(prefix, window)
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
        index = faiss.read_index(str(faiss_index_path))
        raw_meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        chunks = [IndexedChunk.model_validate(item) for item in raw_meta]
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

    faiss.write_index(index, str(faiss_index_path))
    metadata_path.write_text(
        json.dumps([c.model_dump() for c in chunks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return index, chunks
