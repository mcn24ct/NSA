"""Stage 1: Dataset ingestion, 4-tier CPU PDF image filtering, and video keyframe extraction."""

import io
import json
import re
from pathlib import Path

import cv2
import numpy as np
import pymupdf as fitz
from PIL import Image

import config
from schemas import ExperimentIngestBundle, TextBlock, VisualAsset


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
                cleaned = re.sub(r"\s+", " ", raw_text)
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


def run_stage1_ingest(
    dataset_dir: Path = config.DATASETS_DIR,
    checkpoint_path: Path = config.STAGE1_CHECKPOINT,
    force: bool = False,
) -> list[ExperimentIngestBundle]:
    """Scan 03_Datasets_NASA, ingest PDFs and videos by experiment_id, and save checkpoint."""
    config.ensure_artifact_dirs()
    if checkpoint_path.exists() and not force:
        raw_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        return [ExperimentIngestBundle.model_validate(item) for item in raw_data]

    bundles_map: dict[str, ExperimentIngestBundle] = {}
    dhashes_by_exp: dict[str, list[int]] = {}

    if dataset_dir.exists():
        pdf_files = sorted(dataset_dir.rglob("*.pdf"))
        video_files: list[Path] = []
        for ext in ("*.mp4", "*.avi", "*.mov", "*.mkv"):
            video_files.extend(sorted(dataset_dir.rglob(ext)))

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

    bundles = [bundles_map[k] for k in sorted(bundles_map.keys())]
    checkpoint_path.write_text(
        json.dumps([b.model_dump() for b in bundles], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return bundles
