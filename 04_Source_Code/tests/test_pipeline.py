"""Unit and integration test suite for the Flame in Freefall 5-stage pipeline."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import faiss
import numpy as np
from pydantic import ValidationError

SOURCE_DIR = Path(r"D:\MCN\Hackathon_NASA_AI\04_Source_Code")
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

import config
from llm_client import LlamaServerManager
from pipeline_visualizer import run_visualizer
from schemas import (
    ExperimentExtraction,
    ExperimentIngestBundle,
    TextBlock,
    VisualDescription,
)
from scoring_engine import (
    WEIGHTS,
    compute_confidence_penalty,
    min_max_normalize,
    score_and_rank_experiments,
)
from stage1_ingest import (
    compute_dhash,
    deduplicate_same_page_burst,
    hamming_distance,
    has_human_face,
    is_banner_or_blank,
)
from stage3_index import (
    LocalBGEEmbedder,
    build_multimodal_chunks,
    format_citation_prefix,
    split_words_with_overlap,
)
from stage5_export import export_to_excel, export_to_markdown


class TestFlameInFreefallPipeline(unittest.TestCase):
    """Comprehensive verification of models, schemas, chunking, scoring, and visualizer."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize shared offline BGE embedder once for test speed."""
        cls.embedder = LocalBGEEmbedder()

    def test_01_embedding_dimension_and_faiss_index(self) -> None:
        """Verify 384-dim L2-normalized float32 embeddings and faiss.IndexFlatIP(384)."""
        sample_texts = [
            "[EXP: FLEX_01 | SOURCE: flex.pdf | LOC: page_1] Heptane droplet combustion at 101.3 kPa.",
            "[EXP: BASS_02 | SOURCE: bass.mp4 | LOC: 4.50s] Spherical blue flame under 21% O2.",
        ]
        vecs = self.embedder.embed_texts(sample_texts)
        self.assertEqual(vecs.shape, (2, config.EMBED_DIM))
        self.assertEqual(config.EMBED_DIM, 384)
        self.assertEqual(vecs.dtype, np.float32)

        norms = np.linalg.norm(vecs, axis=1)
        np.testing.assert_allclose(norms, np.ones(2, dtype=np.float32), atol=1e-4)

        index = faiss.IndexFlatIP(config.EMBED_DIM)
        index.add(vecs)
        self.assertEqual(index.ntotal, 2)
        scores, ids = index.search(vecs[:1], 1)
        self.assertEqual(int(ids[0, 0]), 0)
        self.assertAlmostEqual(float(scores[0, 0]), 1.0, places=4)

    def test_02_chunking_prefix_and_512_token_limit(self) -> None:
        """Verify chunk size <=380 words, mandatory prefix, and hard <=512 token ceiling."""
        long_text = " ".join([f"microgravity_combustion_parameter_{i}" for i in range(600)])
        windows = split_words_with_overlap(long_text, max_words=380, overlap_words=50)
        self.assertGreater(len(windows), 1)
        for win in windows:
            self.assertLessEqual(len(win.split()), 380)

        bundle = ExperimentIngestBundle(
            experiment_id="SOFIE_01",
            text_blocks=[
                TextBlock(
                    experiment_id="SOFIE_01",
                    source_file="sofie_report.pdf",
                    page_or_sec="page_12",
                    text=long_text,
                )
            ],
            visual_assets=[],
        )
        vlm_desc = VisualDescription(
            experiment_id="SOFIE_01",
            source_file="sofie_flame.mp4",
            page_or_sec="14.20s",
            asset_type="video_keyframe",
            image_path="dummy.png",
            technical_description="Spherical blue flame with radiative quenching at 8.5 mm/s.",
        )

        chunks = build_multimodal_chunks([bundle], [vlm_desc], self.embedder)
        self.assertGreaterEqual(len(chunks), 3)
        expected_prefix = format_citation_prefix("SOFIE_01", "sofie_report.pdf", "page_12")
        self.assertTrue(chunks[0].prefixed_text.startswith(expected_prefix))

        for chunk in chunks:
            actual_tokens = self.embedder.count_tokens(chunk.prefixed_text)
            self.assertLessEqual(actual_tokens, config.MAX_SEQ_LEN)
            self.assertEqual(chunk.token_count, actual_tokens)

    def test_03_pydantic_json_schema_validation(self) -> None:
        """Verify strict Pydantic schema validation and JSON schema generation."""
        schema_dict = ExperimentExtraction.model_json_schema()
        self.assertIn("properties", schema_dict)
        self.assertIn("pressure_kpa", schema_dict["properties"])

        valid_payload = {
            "experiment_id": "FLEX_01",
            "fuel_or_material": "n-Heptane",
            "pressure_kpa": 101.3,
            "oxygen_pct": 21.0,
            "burn_rate_mm_s": 1.45,
            "burn_duration_s": 18.2,
            "flame_stability_score": 88.0,
            "fire_safety_score": 82.0,
            "data_completeness_score": 95.0,
            "key_findings_summary": "Steady spherical burning followed by radiative extinction.",
            "citations": ["[SOURCE: flex.pdf | LOC: page_4]"],
        }
        model = ExperimentExtraction.model_validate(valid_payload)
        self.assertEqual(model.pressure_kpa, 101.3)

        invalid_payload = dict(valid_payload, flame_stability_score=150.0)
        with self.assertRaises(ValidationError):
            ExperimentExtraction.model_validate(invalid_payload)

    def test_04_scoring_engine_and_export(self) -> None:
        """Verify WEIGHTS sum, Min-Max normalization, confidence penalty, ranking, and exports."""
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0, places=5)
        normed = min_max_normalize([10.0, 20.0, 30.0, None], default_if_null=50.0)
        self.assertEqual(normed, [0.0, 50.0, 100.0, 50.0])

        exp_complete = ExperimentExtraction(
            experiment_id="EXP_HIGH",
            fuel_or_material="PMMA",
            pressure_kpa=101.3,
            oxygen_pct=25.0,
            burn_rate_mm_s=2.5,
            burn_duration_s=30.0,
            flame_stability_score=90.0,
            fire_safety_score=85.0,
            data_completeness_score=92.0,
            key_findings_summary="Complete high-quality microgravity burn dataset.",
            citations=["[SOURCE: exp_high.pdf | LOC: page_2]"],
        )
        exp_incomplete = ExperimentExtraction(
            experiment_id="EXP_LOW_PENALIZED",
            fuel_or_material=None,
            pressure_kpa=None,
            oxygen_pct=18.0,
            burn_rate_mm_s=1.0,
            burn_duration_s=10.0,
            flame_stability_score=70.0,
            fire_safety_score=65.0,
            data_completeness_score=50.0,
            key_findings_summary="Partial telemetry with missing pressure and citations.",
            citations=[],
        )

        pen_high, miss_high = compute_confidence_penalty(exp_complete)
        self.assertEqual(pen_high, 0.0)
        self.assertEqual(miss_high, [])

        pen_low, miss_low = compute_confidence_penalty(exp_incomplete)
        self.assertEqual(pen_low, 18.0)
        self.assertIn("pressure_kpa", miss_low)
        self.assertIn("citations", miss_low)

        ranked = score_and_rank_experiments([exp_incomplete, exp_complete])
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].rank, 1)
        self.assertEqual(ranked[0].experiment_id, "EXP_HIGH")
        self.assertEqual(ranked[1].rank, 2)
        self.assertGreater(ranked[0].final_weighted_score, ranked[1].final_weighted_score)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            xlsx_file = export_to_excel(ranked, excel_path=tmp_path / "test_rank.xlsx")
            md_file = export_to_markdown(ranked, report_path=tmp_path / "test_report.md")
            self.assertTrue(xlsx_file.exists() and xlsx_file.stat().st_size > 0)
            self.assertTrue(md_file.exists() and "EXP_HIGH" in md_file.read_text(encoding="utf-8"))

    def test_05_llm_client_command_and_psutil_cleanup(self) -> None:
        """Verify VLM/LLM CLI flags and psutil process termination guarantee."""
        vlm_mgr = LlamaServerManager(
            model_path=config.VLM_MODEL_PATH,
            mmproj_path=config.VLM_MMPROJ_PATH,
            ctx_size=config.VLM_CTX,
            disable_thinking=False,
        )
        vlm_cmd = vlm_mgr.build_command()
        self.assertIn("--mmproj", vlm_cmd)
        self.assertIn("4096", vlm_cmd)
        self.assertIn("99", vlm_cmd)

        llm_mgr = LlamaServerManager(
            model_path=config.LLM_MODEL_PATH,
            mmproj_path=None,
            ctx_size=config.LLM_CTX,
            disable_thinking=True,
        )
        llm_cmd = llm_mgr.build_command()
        self.assertNotIn("--mmproj", llm_cmd)
        self.assertIn("8192", llm_cmd)
        self.assertIn("--chat-template-kwargs", llm_cmd)

        dummy_proc = subprocess.Popen(
            [str(config.PYTHON_EXE), "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        llm_mgr.process = dummy_proc
        llm_mgr.stop()
        self.assertIsNotNone(dummy_proc.poll())
        self.assertIsNone(llm_mgr.process)

    def test_06_pipeline_visualizer_generates_flow_md(self) -> None:
        """Run pipeline_visualizer.py and verify PIPELINE_FLOW.md is generated completely."""
        out_path = run_visualizer()
        self.assertTrue(out_path.exists())
        text = out_path.read_text(encoding="utf-8")
        self.assertIn("```mermaid", text)
        self.assertIn("flowchart TD", text)
        self.assertIn("sequenceDiagram", text)
        self.assertIn("Qwen2.5-VL-3B", text)
        self.assertIn("Qwen3-8B", text)
        self.assertIn("bge-small-en-v1.5", text)

    def test_07_stage1_four_tier_image_filter(self) -> None:
        """Verify 4-tier CPU PDF image filter: dHash, Haar face, blank/chart guard, and burst dedup."""
        import cv2

        # Tier 1: Perceptual dHash Deduplication (Hamming distance <= 6)
        logo_a = np.zeros((240, 240), dtype=np.uint8)
        cv2.rectangle(logo_a, (40, 40), (200, 200), 220, -1)
        cv2.circle(logo_a, (120, 120), 50, 30, -1)
        logo_b = logo_a.copy()
        logo_b[10:15, 10:15] = 128
        self.assertLessEqual(hamming_distance(compute_dhash(logo_a), compute_dhash(logo_b)), 6)

        # Tier 2: Face Filter via CascadeClassifier
        portrait = np.full((300, 220), 235, dtype=np.uint8)
        cv2.ellipse(portrait, (110, 130), (65, 85), 0, 0, 360, 190, -1)
        cv2.rectangle(portrait, (65, 95), (98, 122), 35, -1)
        cv2.rectangle(portrait, (122, 95), (155, 122), 35, -1)
        cv2.rectangle(portrait, (85, 175), (135, 190), 60, -1)
        self.assertTrue(has_human_face(portrait))

        # Tier 3: Safe Aspect Ratio & Edge-Aware Blank Filter (protects thin line charts)
        banner = np.full((200, 900), 128, dtype=np.uint8)
        self.assertTrue(is_banner_or_blank(banner, 900, 200))
        solid_blank = np.full((300, 300), 250, dtype=np.uint8)
        self.assertTrue(is_banner_or_blank(solid_blank, 300, 300))
        thin_chart = np.full((400, 600), 255, dtype=np.uint8)
        cv2.line(thin_chart, (50, 350), (550, 350), 0, 1)
        cv2.line(thin_chart, (50, 50), (50, 350), 0, 1)
        cv2.line(thin_chart, (50, 320), (520, 80), 0, 1)
        self.assertFalse(is_banner_or_blank(thin_chart, 600, 400))

        # Tier 4: Same-Page Burst Deduplication (keeps <= 3: start, middle, end)
        burst_cands: list[dict[str, object]] = []
        for idx in range(6):
            frame = np.zeros((260, 260), dtype=np.uint8)
            cv2.circle(frame, (130, 130), 20 + idx * 15, 40 + idx * 35, -1)
            burst_cands.append({"img_idx": idx, "width": 260, "height": 260, "gray": frame})
        kept = deduplicate_same_page_burst(burst_cands, max_keep=3)
        self.assertEqual(len(kept), 3)
        kept_ids = [int(c["img_idx"]) for c in kept]
        self.assertEqual(kept_ids[0], 0)
        self.assertEqual(kept_ids[-1], 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
