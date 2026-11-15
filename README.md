# FreiFire — Spacecraft Fire Safety & NASA PSI Multimodal RAG Analytics

[![NASA PSI Dataset](https://img.shields.io/badge/Dataset-NASA%20PSI%20%26%20NTRS-0B3D91?style=for-the-badge&logo=nasa)](https://psi.nasa.gov/)
[![Architecture](https://img.shields.io/badge/Architecture-5--Stage%20Multimodal%20RAG-00A8E8?style=for-the-badge)](#architecture)
[![Models](https://img.shields.io/badge/Edge%20AI-Qwen2--VL%20%7C%20BGE--Small%20%7C%20Qwen3--8B-F59E0B?style=for-the-badge)](#core-ai-mechanics)
[![SI Standard](https://img.shields.io/badge/Physics-SI%20Unit%20Normalized-10B981?style=for-the-badge)](#si-unit-normalization)

> **FreiFire** is a local-first **Multimodal RAG (Retrieval-Augmented Generation)** engine with **Strict SI Unit Normalization** and **Dynamic Multi-Criteria Re-ranking**, paired with a cloud-ready FastAPI gateway[span_0](start_span)[span_0](end_span). It synthesizes and explains combustion physics in microgravity ($0g$) and partial-gravity ($0.16g$ Lunar, $0.38g$ Martian) habitats using **19 experimental datasets** from **NASA PSI** and **NASA NTRS**[span_1](start_span)[span_1](end_span).

---

## Overview & Motivation

Deep-space habitats (**Artemis**, **Lunar Gateway**, **Orion**) use low-pressure, oxygen-enriched **Exploration Atmospheres** ($10.2\text{ psi} / 70.33\text{ kPa}$, $30\%–34\%\text{ O}_2$) to reduce structural mass and EVA pre-breathe times[span_2](start_span)[span_2](end_span). In $0g$ and $0.16g$, buoyancy-driven natural convection vanishes or weakens, making combustion governed by low-speed forced ventilation ($20–400\text{ mm/s}$), lowering the **Limiting Oxygen Concentration (LOC)**, and enabling invisible **Cool Flames ($500–800\text{ K}$)** capable of two-stage reignition[span_3](start_span)[span_3](end_span).

**FreiFire** unifies fragmented NASA combustion reports, tables, and chamber imagery into an actionable physics assistant[span_4](start_span)[span_4](end_span):
* **Multimodal Data Fusion:** Ingests 19 experimental sources (13 NTRS PDFs, 56-page ISS Reference Guide, 36 CSV/XLSX tables, 299 VLM chamber images, 246 `.webp` plots, and 7 Apollo/Mir historical records) into **748+ knowledge chunks**[span_5](start_span)[span_5](end_span).
* **Strict SI Normalization:** Automatically converts legacy Imperial/CGS metrics (`psi`, `atm`, `cm/s`) into unified SI units (`kPa`, `% O2`, `mm/s`, `um`)[span_6](start_span)[span_6](end_span).
* **Dynamic Multi-Criteria Re-ranking:** Tunes retrieval weights across semantic similarity, target habitat (`Lunar_Base`, `ISS_Earth`, `Spacesuit`), quantitative density, and safety pillar (`Prevention`, `Detection`, `Suppression`, `Partial-G`)[span_7](start_span)[span_7](end_span).
* **Zero-Core-Modification API Wrapper:** Adds Vietnamese–English domain translation, `< 3s` real-time physics explanations (`Qwen3-8B`), and OpenAPI endpoints for **Google AI Studio**[span_8](start_span)[span_8](end_span).

---

## Architecture

```text
[NASA PSI & NTRS Data: 19 Sources | 36 CSV/XLSX | 13 PDFs | 545 Images]
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     5-STAGE CORE PIPELINE (LOCAL)                    │
│  1. stage1_ingest.py  ──► Parse PDF/CSV/XLSX/JSON + extract visuals  │
│  2. stage2_vision.py  ──► VLM plot/flame captioning (cached < 0.01s) │
│  3. stage3_index.py   ──► BGE-Small (384d) FAISS + 4-weight re-rank  │
│  4. stage4_rank.py    ──► Qwen3-8B structured JSON & SI conversion   │
│  5. stage5_export.py  ──► SQLite join -> Excel & Studio JSON payload │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   EXTERNAL WRAPPER & CLOUD GATEWAY                   │
│  • translator_layer.py ──► NASA Combustion Lexicon + Qwen3-8B (VI→EN)│
│  • api_gateway.py      ──► FastAPI (/api/query) + /no_think explainer│
│  • Frontend            ──► Google AI Studio (HTTPS Tunnel) / Streamlit│
└──────────────────────────────────────────────────────────────────────┘
```

### Repository Structure

```text
Hackathon_NASA_AI/
├── 01_Models_Weights/       # Local weights: bge-small-en-v1.5, vision_vlm, qwen3_8b (GGUF)
├── 02_Runtime_Engines/      # llama_cpp server & venv_hackathon
├── 03_Datasets_NASA/        # 19 NASA datasets, psi_structured.db, rag_chunks_complete.json
└── 04_Source_Code/          # stage1..5 scripts, main.py, translator_layer.py, api_gateway.py
    ├── artifacts/           # Stage checkpoints, FAISS index, studio_payload.json, .xlsx
    └── tests/               # Automated unit test suite (test_pipeline.py)
```

---

## Core AI Mechanics

1. **Incremental VLM Extraction (`Stage 2`):** Extracts axes, curve trends, and flame morphology from chamber/plot images while skipping already-processed frames in `stage2_vision.json` in $< 0.01\text{s}$[span_9](start_span)[span_9](end_span).
2. **Dynamic Weighted Re-ranking (`Stage 3`):** Retrieves Top-30 candidates via $L_2$-normalized `bge-small-en-v1.5` cosine similarity ($S_{\text{FAISS}}$) and re-ranks them[span_10](start_span)[span_10](end_span):
   $$\text{Score}_i = \frac{w_{\text{sem}} S_{\text{FAISS}, i} + w_{\text{env}} S_{\text{env}, i} + w_{\text{quant}} S_{\text{quant}, i} + w_{\text{pillar}} S_{\text{pillar}, i}}{w_{\text{sem}} + w_{\text{env}} + w_{\text{quant}} + w_{\text{pillar}}}$$
3. **Local LLM Synthesis (`Stage 4` & `Gateway`):** `Qwen3-8B` (`llama-server`) enforces structured JSON SI extraction offline and generates cited `[PSI-ID]` physics explanations in $< 3\text{s}$ using `/no_think` mode[span_11](start_span)[span_11](end_span).

### SI Unit Normalization

| Quantity | Source Unit | Conversion | Standardized SI | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Pressure** | $\text{psi}$ / $\text{atm}$ | $\times 6.894757$ / $\times 101.325$ | $\text{kPa}$ | `10.2 psi` $\rightarrow$ **$70.33\text{ kPa}$** (Lunar Base)[span_12](start_span)[span_12](end_span) |
| **Airflow Velocity** | $\text{cm/s}$ | $\times 10.0$ | $\text{mm/s}$ | `40 cm/s` $\rightarrow$ **$400.0\text{ mm/s}$** (`BASS-II`)[span_13](start_span)[span_13](end_span) |
| **Flame Spread / Particle** | $\text{mm/s}$ / $\mu\text{m}$ | $\times 1.0$ | $\text{mm/s}$ / $\mu\text{m}$ | Smoke `SAME`: **$0.42\text{ }\mu\text{m}$** vs Dust `DAFT`: **$> 3.80\text{ }\mu\text{m}$**[span_14](start_span)[span_14](end_span) |

---

## Integrated Dataset Coverage (19 Sources)

| Pillar | Experiments Included | Focus & Key Fuels |
| :--- | :--- | :--- |
| **Legacy Baseline** | `EXP_FLEX_01`[span_15](start_span)[span_15](end_span) | Droplet combustion (`n-Heptane`, `Methanol`) — 299 VLM images[span_16](start_span)[span_16](end_span) |
| **01. Prevention** | `BASS`, `BASS-II`, `SAFFIRE-I/II/III`, `ACME-CFI-G`, `FlameDesign`, `SPICE`, `ACME-BRE`, `SLICE`[span_17](start_span)[span_17](end_span) | Solid flammability (`Sibal`, `PMMA`, `Nomex`, `Silicone`) & gas diffusion/cool flames (`Propane`, `Ethylene`, `Methane`)[span_18](start_span)[span_18](end_span) |
| **02. Detection** | `SAME`, `SAME-R`, `MSG-DAFT`[span_19](start_span)[span_19](end_span) | Wire pyrolysis smoke (`Kapton`, `Teflon`) & Lunar regolith dust discrimination[span_20](start_span)[span_20](end_span) |
| **03. Suppression** | `FLEX`, `FLEX-2`, `PSI-142`[span_21](start_span)[span_21](end_span) | Droplet extinguishment ($\text{CO}_2$, $\text{He}$) & two-stage hot-to-cool flame transitions[span_22](start_span)[span_22](end_span) |
| **04. Partial-G** | `ACME-E-FIELD`, `FUTURE-LUCI-FM2`[span_23](start_span)[span_23](end_span) | Electric-field simulated $0.16g$/$0.38g$ buoyancy & Lunar habitat flammability gaps[span_24](start_span)[span_24](end_span) |
| **Historical** | `00_ISS_Reference_Guide` + 7 Mishap/Spinoff files[span_25](start_span)[span_25](end_span) | Apollo 1, Apollo 13, Mir oxygen generator fire, and NASA fire-safety spinoffs[span_26](start_span)[span_26](end_span) |

---

## Quick Start

### 1. Environment & Unit Tests
```bash
# Activate virtual environment (Linux/macOS; use Scripts\activate on Windows)
source ./02_Runtime_Engines/venv_hackathon/bin/activate
pip install -r requirements.txt

# Run automated unit tests
python -m unittest discover -s 04_Source_Code/tests -v
```

### 2. Run Core Pipeline & Local Verification UI
```bash
# Execute Stages 1 -> 5 (automatically reuses existing artifacts/ checkpoints)
python 04_Source_Code/main.py

# Launch Streamlit UI (http://localhost:8501) or fast CLI mode
python -m streamlit run 04_Source_Code/minimal_ui_test.py
python 04_Source_Code/minimal_ui_test.py --cli
```

### 3. Launch REST API & Connect to Google AI Studio
```bash
# Start FastAPI server (Swagger Docs: http://localhost:8000/docs)
python 04_Source_Code/api_gateway.py

# Expose HTTPS endpoint for Google AI Studio Tool Calling
cloudflared tunnel --url http://localhost:8000
```

---

## REST API Example (`POST /api/query`)

**Request:**
```json
{
  "query": "Áp suất và tốc độ gió của các thí nghiệm cháy vật liệu rắn trên Căn cứ Mặt Trăng",
  "target_env": "Lunar_Base",
  "target_pillar": "Prevention",
  "w_semantic": 0.50,
  "w_env_target": 0.35,
  "w_quantitative": 0.30,
  "w_pillar": 0.25,
  "top_k": 8,
  "enable_ai_explanation": true
}
```

**Response (Excerpt):**
```json
{
  "translated_query": "pressure and airflow speed of solid fuel flammability experiments in Lunar Base exploration atmosphere 70.33 kPa",
  "metrics_summary": [
    {
      "Experiment": "BASS-II (PSI-25)",
      "Pillar": "Prevention",
      "Pressure_kPa": 70.33,
      "O2_Range_%": "15.0 - 30.0%",
      "Max_Airflow_mm_s": 400.0,
      "Final_Weighted_Score": 0.9276
    }
  ],
  "physics_explanation": "- **Lunar Exploration Atmosphere (70.33 kPa, 30–34% O2):** Records [PSI-25] and [PSI-100] show elevated O2 at reduced pressure increases flame spread rates to 4.5–5.2 mm/s.\n- **Low-Speed Forced Flow (20–400 mm/s):** Replaces absent buoyant convection in 0g/0.16g, continuously feeding oxidizer to the flame base and lowering the LOC."
}
```

