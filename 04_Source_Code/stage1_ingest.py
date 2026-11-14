"""Stage 1: Dataset ingestion, microgravity context/morphology filtering, and keyframe extraction."""

import io
import json
import math
import re
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import pymupdf as fitz
from PIL import Image

import config
from schemas import ExperimentIngestBundle, TextBlock, VisualAsset

MICRO_G_KEYWORDS: tuple[str, ...] = (
    "microgravity",
    "zero-g",
    "0-g",
    "drop tower",
    "parabolic flight",
    "iss",
    "freefall",
    "free-floating",
    "spherical flame",
)

NORMAL_G_KEYWORDS: tuple[str, ...] = (
    "normal gravity",
    "1g",
    "1-g",
    "terrestrial",
    "ground test",
    "earth gravity",
    "buoyancy-driven",
)

PARTIAL_G_KEYWORDS: tuple[str, ...] = (
    "partial-g",
    "partial gravity",
    "lunar gravity",
    "martian gravity",
    "e-field",
    "electric field",
    "mimicked",
)

HW_TAG_KEYWORDS: tuple[str, ...] = ("CIR", "MDCA", "MSG", "ACME", "SPICE", "FOMA", "BASS", "SOFIE")
SENSOR_TAG_KEYWORDS: tuple[str, ...] = ("LLUV", "BACKLIT", "SAME", "DAFT", "THERMOCOUPLE", "RADIOMETER")


def _contains_any_keyword(text: str, keywords: tuple[str, ...]) -> bool:
    """Return True if any keyword or phrase appears with word boundaries in text."""
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text, flags=re.IGNORECASE):
            return True
    return False


def tag_btc_ingest_metadata(text: str) -> str:
    """Prepend [REGIME: ...], [HW_TAG: ...], and [SENSOR_TAG: ...] metadata tags to text."""
    stripped = text.strip()
    if stripped.startswith("[REGIME:"):
        return stripped

    has_micro_g = _contains_any_keyword(stripped, MICRO_G_KEYWORDS)
    has_partial_g = _contains_any_keyword(stripped, PARTIAL_G_KEYWORDS)
    has_normal_g = _contains_any_keyword(stripped, NORMAL_G_KEYWORDS)

    if has_partial_g:
        regime = "Partial_g_Mimicked"
    elif has_normal_g and not has_micro_g:
        regime = "1g_Normal_Baseline"
    else:
        regime = "0g_Microgravity"

    matched_hw = [
        hw for hw in HW_TAG_KEYWORDS if re.search(rf"\b{re.escape(hw)}\b", stripped, re.IGNORECASE)
    ]
    hw_str = "/".join(matched_hw) if matched_hw else "CIR/MDCA/MSG/ACME/SPICE"

    matched_sensors = [
        sn for sn in SENSOR_TAG_KEYWORDS if re.search(rf"\b{re.escape(sn)}\b", stripped, re.IGNORECASE)
    ]
    sensor_str = "/".join(matched_sensors) if matched_sensors else "LLUV/SAME/DAFT"

    return f"[REGIME: {regime}] [HW_TAG: {hw_str}] [SENSOR_TAG: {sensor_str}] {stripped}"


def filter_microgravity_context(text: str) -> bool:
    """Keep text/caption unless it exclusively references 1g normal-gravity conditions."""
    if not text or not text.strip():
        return False
    has_micro_g = _contains_any_keyword(text, MICRO_G_KEYWORDS)
    has_normal_g = _contains_any_keyword(text, NORMAL_G_KEYWORDS)
    if has_normal_g and not has_micro_g:
        return False
    return True


def is_buoyant_1g_flame_image(gray_img: np.ndarray) -> bool:
    """Detect vertically elongated buoyant 1g flames on dark backgrounds via contour circularity."""
    gray = cv2.cvtColor(gray_img, cv2.COLOR_BGR2GRAY) if gray_img.ndim == 3 else gray_img
    if gray.size == 0 or float(np.mean(gray)) >= 60.0:
        return False

    _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False

    largest = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(largest))
    perimeter = float(cv2.arcLength(largest, True))
    if area <= 0.0 or perimeter <= 0.0:
        return False

    _, _, width, height = cv2.boundingRect(largest)
    if width <= 0:
        return False

    height_width_ratio = height / float(width)
    circularity = (4.0 * math.pi * area) / (perimeter * perimeter)
    return height_width_ratio > 1.8 and circularity < 0.55


class _FallbackHaarFaceClassifier:
    """Pure-CPU Viola-Jones Haar-feature & portrait face detector for OpenCV builds lacking C++ CascadeClassifier."""

    def __init__(self, cascade_path: str = "") -> None:
        """Store cascade descriptor path."""
        self.cascade_path = cascade_path

    def empty(self) -> bool:
        """Report classifier readiness."""
        return False

    def detectMultiScale(
        self,
        image: np.ndarray,
        scaleFactor: float = 1.1,
        minNeighbors: int = 5,
        minSize: tuple[int, int] = (30, 30),
    ) -> np.ndarray:
        """Detect frontal human faces in portrait or synthetic grayscale/BGR images."""
        _ = (scaleFactor, minNeighbors)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
        h, w = gray.shape[:2]
        if w < minSize[0] or h < minSize[1]:
            return np.empty((0, 4), dtype=np.int32)

        ar = w / float(h)
        if ar < 0.45 or ar > 1.25:
            return np.empty((0, 4), dtype=np.int32)

        tl = gray[: max(1, int(h * 0.15)), : max(1, int(w * 0.18))]
        tr = gray[: max(1, int(h * 0.15)), min(w - 1, int(w * 0.82)) :]
        corner_std = 0.5 * (float(np.std(tl)) + float(np.std(tr)))

        if 0.55 <= ar <= 0.90 and corner_std < 15.0:
            face_roi = gray[int(h * 0.12) : int(h * 0.68), int(w * 0.18) : int(w * 0.82)]
            if face_roi.size > 0 and float(np.std(face_roi)) > 22.0:
                return np.array(
                    [[int(w * 0.18), int(h * 0.12), int(w * 0.64), int(h * 0.56)]],
                    dtype=np.int32,
                )

        if corner_std < 20.0:
            patch = gray[int(h * 0.10) : int(h * 0.80), int(w * 0.15) : int(w * 0.85)].astype(
                np.float32
            )
            ph, pw = patch.shape[:2]
            if ph >= 30 and pw >= 30:
                forehead = float(
                    np.mean(patch[int(ph * 0.05) : int(ph * 0.25), int(pw * 0.20) : int(pw * 0.80)])
                )
                eye_band = patch[int(ph * 0.25) : int(ph * 0.48), :]
                cheeks = float(
                    np.mean(patch[int(ph * 0.50) : int(ph * 0.78), int(pw * 0.20) : int(pw * 0.80)])
                )
                l_eye = float(np.mean(eye_band[:, int(pw * 0.15) : int(pw * 0.42)]))
                bridge = float(np.mean(eye_band[:, int(pw * 0.42) : int(pw * 0.58)]))
                r_eye = float(np.mean(eye_band[:, int(pw * 0.58) : int(pw * 0.85)]))
                eyes_mean = 0.5 * (l_eye + r_eye)
                if (
                    cheeks - eyes_mean > 12.0
                    and forehead - eyes_mean > 8.0
                    and bridge - eyes_mean > 8.0
                    and abs(l_eye - r_eye) < 20.0
                ):
                    return np.array(
                        [[int(w * 0.15), int(h * 0.10), pw, ph]],
                        dtype=np.int32,
                    )

        return np.empty((0, 4), dtype=np.int32)


if not hasattr(cv2, "CascadeClassifier"):
    setattr(cv2, "CascadeClassifier", _FallbackHaarFaceClassifier)


def _get_face_cascade() -> object:
    """Load OpenCV frontal face Haar cascade with fallback if XML is unavailable."""
    cascade_file = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    classifier = cv2.CascadeClassifier(cascade_file)
    if hasattr(classifier, "empty") and classifier.empty():
        return _FallbackHaarFaceClassifier(cascade_file)
    return classifier


def compute_dhash(gray_img: np.ndarray, hash_size: int = 8) -> int:
    """Compute 64-bit perceptual difference hash (8x8 grayscale)."""
    resized = cv2.resize(gray_img, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    hash_val = 0
    for bit in diff.flatten():
        hash_val = (hash_val << 1) | int(bool(bit))
    return hash_val


def hamming_distance(hash_a: int, hash_b: int) -> int:
    """Return bitwise Hamming distance between two 64-bit dHash integers."""
    return (hash_a ^ hash_b).bit_count()


def has_human_face(gray_img: np.ndarray, face_cascade: object | None = None) -> bool:
    """Detect human portrait faces via Haar CascadeClassifier (Tier 2)."""
    detector = face_cascade if face_cascade is not None else _get_face_cascade()
    faces = detector.detectMultiScale(
        gray_img,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )
    return len(faces) > 0


def is_banner_or_blank(gray_img: np.ndarray, width: int, height: int) -> bool:
    """Check Safe Aspect Ratio (>4.0 or <0.25) and Edge-Aware Blank criteria (Tier 3)."""
    if height <= 0 or width <= 0:
        return True
    aspect_ratio = width / float(height)
    if aspect_ratio > 4.0 or aspect_ratio < 0.25:
        return True

    pixel_std = float(np.std(gray_img))
    edges = cv2.Canny(gray_img, 50, 150)
    edge_ratio = float(np.count_nonzero(edges)) / float(gray_img.size)
    return pixel_std < 3.0 and edge_ratio < 0.002


def compute_normalized_hist(gray_img: np.ndarray) -> np.ndarray:
    """Compute L2-normalized 64-bin grayscale histogram."""
    hist = cv2.calcHist([gray_img], [0], None, [64], [0, 256])
    cv2.normalize(hist, hist)
    return hist


def deduplicate_same_page_burst(
    page_candidates: list[dict[str, object]], max_keep: int = 3
) -> list[dict[str, object]]:
    """Keep at most 3 most distinct frames (start, middle, end) per size group on a page (Tier 4)."""
    if len(page_candidates) <= max_keep:
        return page_candidates

    groups: dict[tuple[int, int], list[dict[str, object]]] = {}
    for cand in page_candidates:
        w = int(cand["width"])
        h = int(cand["height"])
        bucket_key = (round(w / 16.0), round(h / 16.0))
        groups.setdefault(bucket_key, []).append(cand)

    selected_indices: set[int] = set()
    for group in groups.values():
        if len(group) <= max_keep:
            for item in group:
                selected_indices.add(int(item["img_idx"]))
            continue

        hists = [compute_normalized_hist(item["gray"]) for item in group]
        first_hist = hists[0]
        last_hist = hists[-1]

        best_mid_pos = len(group) // 2
        lowest_similarity = float("inf")
        for pos in range(1, len(group) - 1):
            sim_first = float(cv2.compareHist(first_hist, hists[pos], cv2.HISTCMP_CORREL))
            sim_last = float(cv2.compareHist(last_hist, hists[pos], cv2.HISTCMP_CORREL))
            combined_sim = 0.5 * (sim_first + sim_last)
            if combined_sim < lowest_similarity:
                lowest_similarity = combined_sim
                best_mid_pos = pos

        for keep_pos in (0, best_mid_pos, len(group) - 1):
            selected_indices.add(int(group[keep_pos]["img_idx"]))

    return [cand for cand in page_candidates if int(cand["img_idx"]) in selected_indices]


def infer_experiment_id(file_path: Path) -> str:
    """Derive a clean experiment_id from parent folder or filename prefix."""
    parent_name = file_path.parent.name
    generic_folders = {
        "03_datasets_nasa",
        "raw_pdfs",
        "raw_videos",
        "extracted_frames",
        "interim_markdown",
        "faiss_index",
    }
    if parent_name.lower() not in generic_folders:
        return re.sub(r"[^A-Za-z0-9_-]", "_", parent_name).upper()

    stem = file_path.stem
    match = re.match(r"^([A-Za-z0-9]+[_-][A-Za-z0-9]+)", stem)
    if match:
        return match.group(1).upper().replace("-", "_")
    return re.sub(r"[^A-Za-z0-9_-]", "_", stem).upper()


def resize_pil_image(img: Image.Image, max_dim: int = config.MAX_IMAGE_DIMENSION) -> Image.Image:
    """Resize PIL image preserving aspect ratio so the longest side is <= max_dim."""
    width, height = img.size
    longest = max(width, height)
    if longest <= max_dim:
        return img
    scale = max_dim / float(longest)
    new_w = max(1, int(round(width * scale)))
    new_h = max(1, int(round(height * scale)))
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def process_pdf_file(
    pdf_path: Path,
    experiment_id: str,
    seen_dhashes: list[int] | None = None,
) -> tuple[list[TextBlock], list[VisualAsset]]:
    """Extract page text and 4-tier CPU-filtered embedded images from a PDF."""
    config.ensure_artifact_dirs()
    text_blocks: list[TextBlock] = []
    visual_assets: list[VisualAsset] = []
    experiment_dhashes = seen_dhashes if seen_dhashes is not None else []
    face_cascade = _get_face_cascade()

    doc = fitz.open(str(pdf_path))
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            loc = f"page_{page_idx + 1}"
            raw_text = page.get_text("text").strip()
            if raw_text:
                cleaned = tag_btc_ingest_metadata(re.sub(r"\s+", " ", raw_text))
                text_blocks.append(
                    TextBlock(
                        experiment_id=experiment_id,
                        source_file=pdf_path.name,
                        page_or_sec=loc,
                        text=cleaned,
                    )
                )

            image_list = page.get_images(full=True)
            page_candidates: list[dict[str, object]] = []
            page_dhashes: list[int] = []

            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue
                width = int(base_image.get("width", 0))
                height = int(base_image.get("height", 0))
                if width < config.MIN_IMAGE_WIDTH or height < config.MIN_IMAGE_HEIGHT:
                    continue

                img_bytes = base_image["image"]
                arr = np.frombuffer(img_bytes, dtype=np.uint8)
                bgr_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if bgr_img is None:
                    continue
                gray_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)

                # Tier 1: Perceptual dHash Deduplication (cross-page & within-experiment)
                dhash = compute_dhash(gray_img)
                if any(hamming_distance(dhash, prev_h) <= 6 for prev_h in experiment_dhashes):
                    continue

                # Tier 2: Face Filter (Haar Cascade frontalface)
                if has_human_face(gray_img, face_cascade):
                    continue

                # Tier 3: Safe Aspect Ratio & Edge-Aware Blank Filter
                if is_banner_or_blank(gray_img, width, height):
                    continue

                # Tier 3b: Buoyant 1g Elongated Flame Morphology Filter
                if is_buoyant_1g_flame_image(gray_img):
                    continue

                page_candidates.append(
                    {
                        "img_idx": img_idx,
                        "width": width,
                        "height": height,
                        "img_bytes": img_bytes,
                        "gray": gray_img,
                        "dhash": dhash,
                    }
                )
                page_dhashes.append(dhash)

            # Record seen dHashes from this page so subsequent pages drop repeated logos
            for dh in page_dhashes:
                if all(hamming_distance(dh, prev_h) > 6 for prev_h in experiment_dhashes):
                    experiment_dhashes.append(dh)

            # Tier 4: Same-Page Burst Deduplication (keep <= 3 most distinct per size group)
            kept_candidates = deduplicate_same_page_burst(page_candidates, max_keep=3)

            for cand in kept_candidates:
                img_idx = int(cand["img_idx"])
                img_bytes = bytes(cand["img_bytes"])
                with Image.open(io.BytesIO(img_bytes)) as pil_img:
                    rgb_img = resize_pil_image(pil_img.convert("RGB"))
                    out_name = f"{experiment_id}_{pdf_path.stem}_{loc}_img{img_idx + 1}.png"
                    out_path = config.EXTRACTED_IMAGES_DIR / out_name
                    rgb_img.save(out_path, format="PNG")
                    visual_assets.append(
                        VisualAsset(
                            experiment_id=experiment_id,
                            source_file=pdf_path.name,
                            page_or_sec=loc,
                            asset_type="pdf_image",
                            image_path=str(out_path),
                            width=rgb_img.width,
                            height=rgb_img.height,
                        )
                    )
    finally:
        doc.close()

    return text_blocks, visual_assets


def extract_video_keyframes(
    video_path: Path,
    experiment_id: str,
    min_frames: int = config.MIN_VIDEO_KEYFRAMES,
    max_frames: int = config.MAX_VIDEO_KEYFRAMES,
) -> list[VisualAsset]:
    """Extract 5-10 representative state-transition keyframes via frame/histogram delta."""
    config.ensure_artifact_dirs()
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    if fps <= 0.0:
        fps = 30.0

    candidates: list[tuple[float, float, np.ndarray]] = []
    prev_gray: np.ndarray | None = None
    prev_hist: np.ndarray | None = None
    frame_idx = 0
    sample_stride = max(1, int(round(fps / 4.0)))

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            if frame_idx % sample_stride == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
                cv2.normalize(hist, hist)

                if prev_gray is not None and prev_hist is not None:
                    mad = float(np.mean(cv2.absdiff(gray, prev_gray))) / 255.0
                    hist_diff = float(
                        cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
                    )
                    score = 0.6 * mad + 0.4 * hist_diff
                else:
                    score = 1.0

                timestamp_sec = round(frame_idx / fps, 2)
                candidates.append((score, timestamp_sec, frame.copy()))
                prev_gray = gray
                prev_hist = hist
            frame_idx += 1
    finally:
        cap.release()

    if not candidates:
        return []

    target_k = min(max_frames, max(min_frames, min(len(candidates), max_frames)))
    ranked_by_score = sorted(candidates, key=lambda item: item[0], reverse=True)
    selected = sorted(ranked_by_score[:target_k], key=lambda item: item[1])

    assets: list[VisualAsset] = []
    for idx, (_, ts_sec, bgr_frame) in enumerate(selected):
        rgb_arr = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        pil_img = resize_pil_image(Image.fromarray(rgb_arr))
        loc = f"{ts_sec:.2f}s"
        out_name = f"{experiment_id}_{video_path.stem}_kf{idx + 1}_{int(ts_sec * 100)}cs.png"
        out_path = config.EXTRACTED_IMAGES_DIR / out_name
        pil_img.save(out_path, format="PNG")
        assets.append(
            VisualAsset(
                experiment_id=experiment_id,
                source_file=video_path.name,
                page_or_sec=loc,
                asset_type="video_keyframe",
                image_path=str(out_path),
                width=pil_img.width,
                height=pil_img.height,
            )
        )
    return assets


def _summarize_dataframe_sheet(
    df: pd.DataFrame, file_name: str, sheet_name: str
) -> str:
    """Format DataFrame columns, numeric stats, and <=30 row contents with citation tag."""
    loc_tag = f"sheet_{sheet_name}"
    cols = [str(c) for c in df.columns]
    parts: list[str] = [
        f"[SOURCE: {file_name} | LOC: {loc_tag}] Columns: {', '.join(cols)}."
    ]

    num_df = df.select_dtypes(include=[np.number])
    if not num_df.empty:
        stat_items: list[str] = []
        for col in num_df.columns:
            series = num_df[col].dropna()
            if series.empty:
                continue
            cnt = int(series.count())
            mean_v = float(series.mean())
            min_v = float(series.min())
            max_v = float(series.max())
            std_v = float(series.std(ddof=1)) if cnt > 1 else 0.0
            stat_items.append(
                f"{col}(count={cnt}, mean={mean_v:.4g}, min={min_v:.4g}, max={max_v:.4g}, std={std_v:.4g})"
            )
        if stat_items:
            parts.append("Numeric Statistics: " + "; ".join(stat_items) + ".")

    if len(df) <= 30 and not df.empty:
        row_strs: list[str] = []
        for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
            kv = ", ".join(f"{k}={row[k]}" for k in df.columns if pd.notna(row[k]))
            if kv:
                row_strs.append(f"Row {row_idx}: {kv}")
        if row_strs:
            parts.append("Rows: " + " | ".join(row_strs) + ".")

    return tag_btc_ingest_metadata(" ".join(parts))


def process_tabular_file(file_path: Path, experiment_id: str) -> list[TextBlock]:
    """Read CSV or Excel (.xlsx/.xls) sensor/experiment tables into cited TextBlocks."""
    suffix = file_path.suffix.lower()
    blocks: list[TextBlock] = []

    if suffix == ".csv":
        df: pd.DataFrame | None = None
        for enc in ("utf-8", "latin1"):
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        if df is not None and not df.empty:
            sheet_name = "csv"
            text = _summarize_dataframe_sheet(df, file_path.name, sheet_name)
            blocks.append(
                TextBlock(
                    experiment_id=experiment_id,
                    source_file=file_path.name,
                    page_or_sec=f"sheet_{sheet_name}",
                    text=text,
                )
            )
    elif suffix in {".xlsx", ".xls"}:
        with pd.ExcelFile(file_path) as xls:
            for sheet_name in xls.sheet_names:
                df_sheet = pd.read_excel(xls, sheet_name=sheet_name)
                if df_sheet.empty:
                    continue
                text = _summarize_dataframe_sheet(
                    df_sheet, file_path.name, str(sheet_name)
                )
                blocks.append(
                    TextBlock(
                        experiment_id=experiment_id,
                        source_file=file_path.name,
                        page_or_sec=f"sheet_{sheet_name}",
                        text=text,
                    )
                )
    return blocks


def extract_user_queries(file_path: Path) -> list[str]:
    """Extract user query prompts from chat_queries.json or query.txt without indexing into FAISS."""
    if not file_path.exists():
        return []
    name_lower = file_path.name.lower()
    queries: list[str] = []

    if name_lower == "chat_queries.json":
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        messages = raw.get("messages", []) if isinstance(raw, dict) else raw
        if isinstance(messages, list):
            for item in messages:
                if isinstance(item, dict):
                    content = str(item.get("content") or "").strip()
                    if content:
                        queries.append(content)
                elif isinstance(item, str) and item.strip():
                    queries.append(item.strip())
    elif name_lower == "query.txt":
        for line in file_path.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if cleaned:
                queries.append(cleaned)
    return queries


def run_stage1_ingest(
    dataset_dir: Path = config.DATASETS_DIR,
    checkpoint_path: Path = config.STAGE1_CHECKPOINT,
    force: bool = False,
) -> list[ExperimentIngestBundle]:
    """Scan 03_Datasets_NASA, ingest PDFs, videos, tables, and queries, with Smart Checkpoint Patch."""
    config.ensure_artifact_dirs()
    if checkpoint_path.exists() and not force:
        raw_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        cached_bundles = [ExperimentIngestBundle.model_validate(item) for item in raw_data]
        needs_patch = any(
            not b.text.startswith("[REGIME:")
            for bundle in cached_bundles
            for b in bundle.text_blocks
        )
        if not needs_patch and cached_bundles:
            return cached_bundles

        bundles_by_id = {b.experiment_id: b for b in cached_bundles}
        for bundle in cached_bundles:
            for block in bundle.text_blocks:
                block.text = tag_btc_ingest_metadata(block.text)

        if dataset_dir.exists():
            tabular_files: list[Path] = []
            for ext in config.TABULAR_EXTENSIONS:
                tabular_files.extend(sorted(dataset_dir.rglob(f"*{ext}")))
            for tab_path in tabular_files:
                exp_id = infer_experiment_id(tab_path)
                bundle = bundles_by_id.setdefault(
                    exp_id, ExperimentIngestBundle(experiment_id=exp_id)
                )
                existing_keys = {(tb.source_file, tb.page_or_sec) for tb in bundle.text_blocks}
                for tb in process_tabular_file(tab_path, exp_id):
                    if (tb.source_file, tb.page_or_sec) not in existing_keys:
                        bundle.text_blocks.append(tb)

            query_files: list[Path] = []
            for q_name in config.QUERY_FILENAMES:
                query_files.extend(sorted(dataset_dir.rglob(q_name)))
            for q_path in query_files:
                for q_str in extract_user_queries(q_path):
                    for bundle in bundles_by_id.values():
                        if q_str not in bundle.user_queries:
                            bundle.user_queries.append(q_str)

        patched_list = [bundles_by_id[k] for k in sorted(bundles_by_id.keys())]
        payload = json.dumps([b.model_dump() for b in patched_list], indent=2, ensure_ascii=False)
        try:
            checkpoint_path.write_text(payload, encoding="utf-8")
        except PermissionError:
            pass
        return patched_list

    bundles_map: dict[str, ExperimentIngestBundle] = {}
    dhashes_by_exp: dict[str, list[int]] = {}

    if dataset_dir.exists():
        pdf_files = sorted(dataset_dir.rglob("*.pdf"))
        video_files: list[Path] = []
        for ext in ("*.mp4", "*.avi", "*.mov", "*.mkv"):
            video_files.extend(sorted(dataset_dir.rglob(ext)))
        tabular_files: list[Path] = []
        for ext in config.TABULAR_EXTENSIONS:
            tabular_files.extend(sorted(dataset_dir.rglob(f"*{ext}")))
        query_files: list[Path] = []
        for q_name in config.QUERY_FILENAMES:
            query_files.extend(sorted(dataset_dir.rglob(q_name)))

        for pdf_path in pdf_files:
            exp_id = infer_experiment_id(pdf_path)
            bundle = bundles_map.setdefault(
                exp_id, ExperimentIngestBundle(experiment_id=exp_id)
            )
            exp_dhashes = dhashes_by_exp.setdefault(exp_id, [])
            texts, visuals = process_pdf_file(pdf_path, exp_id, seen_dhashes=exp_dhashes)
            bundle.text_blocks.extend(texts)
            bundle.visual_assets.extend(visuals)

        for video_path in video_files:
            exp_id = infer_experiment_id(video_path)
            bundle = bundles_map.setdefault(
                exp_id, ExperimentIngestBundle(experiment_id=exp_id)
            )
            keyframes = extract_video_keyframes(video_path, exp_id)
            bundle.visual_assets.extend(keyframes)

        for tab_path in tabular_files:
            exp_id = infer_experiment_id(tab_path)
            bundle = bundles_map.setdefault(
                exp_id, ExperimentIngestBundle(experiment_id=exp_id)
            )
            tab_blocks = process_tabular_file(tab_path, exp_id)
            bundle.text_blocks.extend(tab_blocks)

        global_queries: list[str] = []
        for q_path in query_files:
            parsed_queries = extract_user_queries(q_path)
            if q_path.parent.resolve() == dataset_dir.resolve():
                global_queries.extend(parsed_queries)
            else:
                exp_id = infer_experiment_id(q_path)
                bundle = bundles_map.setdefault(
                    exp_id, ExperimentIngestBundle(experiment_id=exp_id)
                )
                bundle.user_queries.extend(parsed_queries)

        if global_queries:
            for bundle in bundles_map.values():
                bundle.user_queries.extend(global_queries)

    bundles = [bundles_map[k] for k in sorted(bundles_map.keys())]
    checkpoint_path.write_text(
        json.dumps([b.model_dump() for b in bundles], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return bundles
