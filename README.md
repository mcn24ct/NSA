# FreiFire — Spacecraft Fire Safety & NASA PSI Multimodal RAG Analytics

[![NASA PSI Dataset](https://img.shields.io/badge/Dataset-NASA%20PSI%20%26%20NTRS-0B3D91?style=for-the-badge&logo=nasa)](https://psi.nasa.gov/)
[![Architecture](https://img.shields.io/badge/Architecture-5--Stage%20Multimodal%20RAG-00A8E8?style=for-the-badge)](#architecture)
[![Models](https://img.shields.io/badge/Edge%20AI-Qwen2--VL%20%7C%20BGE--Small%20%7C%20Qwen3--8B-F59E0B?style=for-the-badge)](#core-ai-mechanics)
[![SI Standard](https://img.shields.io/badge/Physics-SI%20Unit%20Normalized-10B981?style=for-the-badge)](#si-unit-normalization)

> **FreiFire** is a local-first **Multimodal RAG (Retrieval-Augmented Generation)** engine with **Strict SI Unit Normalization** and **Dynamic Multi-Criteria Re-ranking**, paired with a cloud-ready FastAPI gateway. It synthesizes and explains combustion physics in microgravity ($0g$) and partial-gravity ($0.16g$ Lunar, $0.38g$ Martian) habitats using **19 experimental datasets** from **NASA PSI** and **NASA NTRS**.

---

## Overview & Motivation

Deep-space habitats (**Artemis**, **Lunar Gateway**, **Orion**) operate with low-pressure, oxygen-enriched **Exploration Atmospheres** ($10.2\text{ psi} / 70.33\text{ kPa}$, $30\% - 34\%\text{ O}_2$) to reduce structural mass and Extravehicular Activity (EVA) pre-breathe times. In $0g$ and $0.16g$, buoyancy-driven natural convection vanishes or weakens, making combustion governed by low-speed forced ventilation ($20 - 400\text{ mm/s}$), lowering the **Limiting Oxygen Concentration (LOC)**, and enabling invisible **Cool Flames ($500 - 800\text{ K}$)** capable of two-stage reignition.

**FreiFire** unifies fragmented NASA combustion reports, experimental data tables, and chamber imagery into an actionable physics assistant:

- **Multimodal Data Fusion:** Ingests 19 experimental sources (13 NTRS PDFs, 56-page ISS Reference Guide, 36 CSV/XLSX tables, 299 VLM chamber images, 246 `.webp` plots, and 7 Apollo/Mir historical records) into **748+ knowledge chunks**.
- **Strict SI Normalization:** Automatically converts legacy Imperial and CGS metrics (`psi`, `atm`, `cm/s`) into unified SI units (`kPa`, `% O2`, `mm/s`, `um`).
- **Dynamic Multi-Criteria Re-ranking:** Tunes retrieval weights across semantic similarity, target habitat (`Lunar_Base`, `ISS_Earth`, `Spacesuit`), quantitative density, and safety pillar (`Prevention`, `Detection`, `Suppression`, `Partial-G`).
- **Zero-Core-Modification API Wrapper:** Adds bilingual domain query translation, $< 3\text{s}$ real-time physics explanations (`Qwen3-8B`), and OpenAPI endpoints for **Google AI Studio**.

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
│  • translator_layer.py ──► NASA Combustion Lexicon + Qwen3-8B        │
│  • api_gateway.py      ──► FastAPI (/api/query) + /no_think explainer│
│  • Frontend            ──► Google AI Studio (HTTPS Tunnel) / Streamlit│
└──────────────────────────────────────────────────────────────────────┘
```

### Repository & Data Storage Structure

```text
Hackathon_NASA_AI/
├── 01_Models_Weights/                 # Local AI model weights (Offline GGUF & SafeTensors)
│   ├── bge-small-en-v1.5/             # Dense semantic embedding model (384-dim)
│   ├── vision_vlm/                    # Vision-Language Model for plot & flame analysis
│   └── qwen3_8b/                      # Qwen3-8B Large Language Model (GGUF quantized)
│
├── 02_Runtime_Engines/                # C++ inference runtime & Python virtual environment
│   ├── llama_cpp/                     # Hardware-accelerated llama-server runtime
│   └── venv_hackathon/                # Isolated virtual environment with pinned dependencies
│
├── 03_Datasets_NASA/                  # Standardized repository of 19 NASA experimental sources
│   ├── EXP_FLEX_01/                   # Baseline droplet combustion dataset (299 VLM images)
│   ├── 00_ISS_Reference_Guide/        # ISS Combustion Research Reference Guide (56-page PDF)
│   ├── 01_Prevention/                 # 10 fire prevention & material/gas flammability experiments
│   ├── 02_Detection/                  # 3 smoke sensor & lunar dust discrimination experiments
│   ├── 03_Suppression/                # 3 flame extinguishment & cool-flame transition studies
│   ├── 04_Partial_Gravity/            # 2 partial-gravity simulation studies (0.16g - 0.38g)
│   ├── 05_Historical_And_Spinoffs/    # 7 historical mishaps (Apollo 1, Mir) & fire-safety spinoffs
│   ├── public/
│   │   └── psi_images/                # 246 scientific figure images (.webp) extracted from PDFs
│   ├── psi_structured.db              # SQLite database storing Catalog & Experimental Runs
│   └── rag_chunks_complete.json       # 748+ multimodal knowledge chunks
│
└── 04_Source_Code/                    # Core pipeline source code & automated test suite
    ├── artifacts/                     # Persistent checkpoints across all 5 pipeline stages
    │   ├── extracted_visuals/         # Figures extracted from PDFs for Stage 2 VLM inference
    │   ├── stage1_ingest.json         # Stage 1 parsed text & metadata checkpoint
    │   ├── stage2_vision.json         # Stage 2 VLM visual analysis checkpoint
    │   ├── stage3_index.faiss         # Stage 3 FAISS vector index
    │   ├── stage4_rank.json           # Stage 4 Qwen3-8B SI-normalized & ranked output
    │   ├── studio_payload.json        # Structured JSON payload formatted for Studio UI
    │   └── NASA_Flame_Ranking.xlsx    # Multi-sheet Excel summary exported from Stage 5
    ├── main.py                        # Orchestrator executing Stage 1 through Stage 5
    ├── stage1_ingest.py               # Multi-format document ingestion & parsing module
    ├── stage2_vision.py               # Cached Vision-Language analysis module
    ├── stage3_index.py                # FAISS indexing & dynamic weighted retrieval module
    ├── stage4_rank.py                 # Qwen3-8B physics reasoning & SI conversion module
    ├── stage5_export.py               # Pandas SI DataFrame aggregation & export module
    ├── data1.py                       # NASA NTRS automated PDF report scraper
    ├── data2.py                       # NASA PSI headless Playwright table & image extractor
    ├── data3.py                       # SQLite & multimodal JSON chunk packaging script
    ├── translator_layer.py            # Decoupled domain lexicon & query translation layer
    ├── api_gateway.py                 # FastAPI server exposing REST endpoints for AI Studio
    ├── minimal_ui_test.py             # Lightweight Streamlit & CLI verification interface
    └── tests/
        └── test_pipeline.py           # Automated unit test suite
```

---

## Core AI Mechanics

1. **Incremental VLM Extraction (`Stage 2`):** Extracts axes, curve trends, and flame morphology from chamber and plot images while skipping already-processed frames in `stage2_vision.json` in $< 0.01\text{s}$.
2. **Dynamic Weighted Re-ranking (`Stage 3`):** Retrieves Top-30 candidates via $L_2$-normalized `bge-small-en-v1.5` cosine similarity ($S_{\text{FAISS}}$) and re-ranks them using the multi-criteria weighted score ($\text{Score}_i$) defined below.
3. **Local LLM Synthesis (`Stage 4` & `Gateway`):** `Qwen3-8B` (`llama-server`) enforces structured JSON SI extraction offline and generates cited `[PSI-ID]` physics explanations in $< 3\text{s}$ using `/no_think` mode.

$$
\text{Score}_i = \frac{w_{\text{sem}} S_{\text{FAISS}, i} + w_{\text{env}} S_{\text{env}, i} + w_{\text{quant}} S_{\text{quant}, i} + w_{\text{pillar}} S_{\text{pillar}, i}}{w_{\text{sem}} + w_{\text{env}} + w_{\text{quant}} + w_{\text{pillar}}}
$$

### SI Unit Normalization

| Quantity | Source Unit | Conversion | Standardized SI | Example |
| :--- | :--- | :--- | :--- | :--- |
| **Pressure** | $\text{psi}$ / $\text{atm}$ | $\times 6.894757$ / $\times 101.325$ | $\text{kPa}$ | `10.2 psi` $\rightarrow$ $70.33\text{ kPa}$ (Lunar Base) |
| **Airflow Velocity** | $\text{cm/s}$ | $\times 10.0$ | $\text{mm/s}$ | `40 cm/s` $\rightarrow$ $400.0\text{ mm/s}$ (`BASS-II`) |
| **Flame Spread / Particle** | $\text{mm/s}$ / $\mu\text{m}$ | $\times 1.0$ | $\text{mm/s}$ / $\mu\text{m}$ | Smoke `SAME`: $0.42\text{ }\mu\text{m}$ vs Dust `DAFT`: $> 3.80\text{ }\mu\text{m}$ |

---

## Integrated Dataset Coverage (19 Sources)

| Pillar | Experiments Included | Focus & Key Fuels |
| :--- | :--- | :--- |
| **Legacy Baseline** | `EXP_FLEX_01` | Droplet combustion (`n-Heptane`, `Methanol`) — 299 VLM images |
| **01. Prevention** | `BASS`, `BASS-II`, `SAFFIRE-I`, `SAFFIRE-II`, `SAFFIRE-III`, `ACME-CFI-G`, `FlameDesign`, `SPICE`, `ACME-BRE`, `SLICE` | Solid flammability (`Sibal`, `PMMA`, `Nomex`, `Silicone`) & gas diffusion/cool flames (`Propane`, `Ethylene`, `Methane`) |
| **02. Detection** | `SAME`, `SAME-R`, `MSG-DAFT` | Wire pyrolysis smoke (`Kapton`, `Teflon`) & Lunar regolith dust discrimination |
| **03. Suppression** | `FLEX`, `FLEX-2`, `PSI-142` | Droplet extinguishment ($\text{CO}_2$, $\text{He}$) & two-stage hot-to-cool flame transitions |
| **04. Partial-G** | `ACME-E-FIELD`, `FUTURE-LUCI-FM2` | Electric-field simulated $0.16g$/$0.38g$ buoyancy & Lunar habitat flammability gaps |
| **Historical** | `00_ISS_Reference_Guide` + 7 Mishap/Spinoff files | Apollo 1, Apollo 13, Mir oxygen generator fire, and NASA fire-safety spinoffs |

---

## Quick Start

### 1. Environment & Unit Tests

```bash
# Activate virtual environment (Linux/macOS; use .\02_Runtime_Engines\venv_hackathon\Scripts\activate on Windows)
source ./02_Runtime_Engines/venv_hackathon/bin/activate
pip install -r requirements.txt

# Run automated unit tests
python -m unittest discover -s 04_Source_Code/tests -v
```

### 2. Run Core Pipeline & Local Verification UI

```bash
# Execute Stage 1 through Stage 5 (automatically reuses existing artifacts/ checkpoints)
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
  "query": "What are the pressure and forced airflow velocities for solid fuel flammability experiments in a Lunar Base habitat?",
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

**Response:**

```json
{
  "original_query": "What are the pressure and forced airflow velocities for solid fuel flammability experiments in a Lunar Base habitat?",
  "translated_query": "pressure and airflow speed of solid fuel flammability experiments in Lunar Base exploration atmosphere 70.33 kPa",
  "metrics_summary": [
    {
      "Experiment": "BASS-II (PSI-25)",
      "Pillar": "Prevention",
      "Fuels": "Sibal fabric (cotton-fiberglass), PMMA acrylic slabs/rods, Nomex",
      "Pressure_kPa": 70.33,
      "O2_Range_%": "15.0 - 30.0%",
      "Max_Airflow_mm_s": 400.0,
      "Final_Weighted_Score": 0.9276
    },
    {
      "Experiment": "SAFFIRE-III (PSI-100)",
      "Pillar": "Prevention",
      "Fuels": "Large Sibal cotton-fiberglass panel at exploration atmosphere",
      "Pressure_kPa": 70.33,
      "O2_Range_%": "21.0 - 34.0%",
      "Max_Airflow_mm_s": 300.0,
      "Final_Weighted_Score": 0.9198
    }
  ],
  "evidence_chunks": [
    {
      "Rank": 1,
      "Investigation": "BASS-II",
      "Source": "PSI-25_Experimental_Table.csv | row_4",
      "Chunk_Type": "experimental_table_row",
      "Final_Weighted_Score": 0.9276,
      "Snippet": "Run_ID: BASS2-04, Material: Thin PMMA Sheet, O2_Percent: 30.0, Pressure_psi: 10.2 (70.33 kPa), Airflow_cm_s: 8.0 (80.0 mm/s), Spread_Rate_mm_s: 4.5"
    }
  ],
  "physics_explanation": "- **Lunar Exploration Atmosphere (70.33 kPa, 30-34% O2):** Experimental records [PSI-25] (BASS-II) and [PSI-100] (SAFFIRE-III) demonstrate that elevated oxygen concentration at reduced ambient pressure accelerates surface flame spread rates to 4.5-5.2 mm/s.\n- **Low-Speed Forced Ventilation (20-400 mm/s):** Replaces absent or weakened buoyant convection in 0g and 0.16g, continuously supplying fresh oxidizer to the flame base and lowering the Limiting Oxygen Concentration (LOC) compared to terrestrial 1g conditions."
}
```
