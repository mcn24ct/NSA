"""Minimalist Streamlit & CLI test harness for Stage 3 Dynamic Weighted Retrieval & SI Summary Tables."""

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SOURCE_DIR = Path(__file__).resolve().parent
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from api_gateway import explain_physics_with_qwen
from stage3_index import search_weighted
from stage5_export import build_summary_tables, export_studio_payload
from translator_layer import translate_to_english_query

DEFAULT_QUERY: str = (
    "Áp suất và tốc độ gió của các thí nghiệm cháy vật liệu rắn trên Mặt Trăng"
)


def run_weighted_query_pipeline(
    query: str = DEFAULT_QUERY,
    env_target: str = "Lunar_Base",
    pillar: str = "All",
    w_semantic: float = 0.50,
    w_env_weight: float = 0.35,
    w_quantitative: float = 0.30,
    top_k: int = 8,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Translate query, execute weighted Stage 3 FAISS search, and build SI-normalized DataFrames."""
    translation = translate_to_english_query(query)
    english_query = str(translation["translated_query"])
    weights: dict[str, Any] = {
        "w_semantic": w_semantic,
        "w_env_target": env_target,
        "w_env_weight": w_env_weight,
        "w_quantitative": w_quantitative,
        "w_pillar": pillar,
        "translated_query": english_query,
        "is_translated": bool(translation["is_translated"]),
    }
    results = search_weighted(query=english_query, weights=weights, top_k=top_k)
    df_metrics, df_evidence = build_summary_tables(results)
    return df_metrics, df_evidence, weights


def render_streamlit_ui() -> None:
    """Render minimalist Streamlit interface for testing Stage 3 dynamic weights, tables, and Qwen3-8B."""
    import streamlit as st

    st.set_page_config(page_title="Flame in Freefall - Minimal UI Test", layout="wide")
    st.title("Flame in Freefall — Stage 3 Dynamic Weighted Retrieval & SI Tables")

    with st.sidebar:
        st.header("Dynamic Retrieval Weights")
        env_target = st.selectbox(
            "Target Environment",
            options=["Lunar_Base", "ISS_Earth", "Spacesuit", "All"],
            index=0,
        )
        pillar = st.selectbox(
            "Safety Pillar",
            options=["All", "Prevention", "Detection", "Suppression", "Partial-G"],
            index=0,
        )
        w_semantic = st.slider("w_semantic (FAISS Similarity)", 0.0, 1.0, 0.50, 0.05)
        w_env_weight = st.slider("w_env_target (Environment Match)", 0.0, 1.0, 0.35, 0.05)
        w_quantitative = st.slider("w_quantitative (Data Density)", 0.0, 1.0, 0.30, 0.05)
        top_k = st.slider("Top-K Evidence Chunks", 3, 15, 8, 1)

    query = st.text_input("Query (Vietnamese or English):", value=DEFAULT_QUERY)
    df_metrics, df_evidence, weights = run_weighted_query_pipeline(
        query=query,
        env_target=env_target,
        pillar=pillar,
        w_semantic=w_semantic,
        w_env_weight=w_env_weight,
        w_quantitative=w_quantitative,
        top_k=top_k,
    )
    st.caption(f"Translated BGE Query: `{weights.get('translated_query', query)}`")

    st.subheader("1. SI-Normalized Experiment Metrics Summary (df_metrics_summary)")
    st.dataframe(df_metrics, use_container_width=True)

    st.subheader("2. Ranked Evidence Chunks (df_evidence_chunks)")
    st.dataframe(df_evidence, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Phân tích Vật lý với Qwen3-8B"):
            explanation = explain_physics_with_qwen(query, df_metrics, df_evidence)
            st.subheader("3. Giải thích Cơ chế Vật lý Vi trọng lực (physics_explanation)")
            st.info(explanation)
    with col2:
        if st.button("Export artifacts/studio_payload.json"):
            out_path = export_studio_payload(query, weights, df_metrics, df_evidence)
            st.success(f"Exported Google Studio payload to: {out_path}")


def main() -> None:
    """Entry point supporting both CLI verification and Streamlit execution."""
    parser = argparse.ArgumentParser(description="Minimal UI & CLI Test for Stage 3 Weighted RAG")
    parser.add_argument("--cli", action="store_true", help="Run in console mode and print DataFrames")
    args, _ = parser.parse_known_args()

    if args.cli or "streamlit" not in sys.modules:
        df_metrics, df_evidence, weights = run_weighted_query_pipeline()
        out_path = export_studio_payload(DEFAULT_QUERY, weights, df_metrics, df_evidence)
        print(f"=== TRANSLATED QUERY: {weights.get('translated_query')} ===")
        print("=== TABLE 1: df_metrics_summary (SI Units: kPa, %, mm/s) ===")
        print(df_metrics.to_string(index=False))
        print("\n=== TABLE 2: df_evidence_chunks (Top-K Reranked) ===")
        print(df_evidence.to_string(index=False))
        print(f"\n[OK] Exported Studio Payload: {out_path}")
    else:
        render_streamlit_ui()


if __name__ == "__main__":
    main()
