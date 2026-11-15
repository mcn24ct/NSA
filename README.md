# TECHNICAL REPORT & SYSTEM DEVELOPMENT PROGRESS SUMMARY
## Project: **Flame in Freefall — Spacecraft Fire Safety & NASA PSI Multimodal RAG Analytics**
**Project Root Directory:** `D:\MCN\Hackathon_NASA_AI`

---

## 1. PROJECT OVERVIEW & OBJECTIVES

The **Hackathon_NASA_AI (Flame in Freefall)** project implements a **Multimodal RAG (Retrieval-Augmented Generation) system integrated with SI Unit Normalization and Dynamic Weighted Ranking** that runs completely locally (Local Edge AI) alongside a cloud-connected REST API gateway, designed for analyzing spacecraft fire safety data from the **NASA Physical Sciences Informatics (PSI)** repository and the **NASA Technical Reports Server (NTRS)**.

### Core Problems Solved:
1. **Multimodal Data Fusion:** Combines academic PDF documents, experimental data tables (`.csv`, `.xlsx`), experiment metadata (`.json`), historical/spinoff application articles (`.txt`), and hundreds of charts/images of flames in microgravity (`0g`) and partial gravity (`0.16g` Lunar, `0.38g` Martian).
2. **International System of Units (SI) Normalization:** Automatically converts Imperial/mixed units found in historical NASA documents into standardized SI units (e.g., cabin pressure `14.7 psi` $\rightarrow$ $101.35\text{ kPa}$, lunar base pressure `10.2 psi` $\rightarrow$ $70.33\text{ kPa}$, ventilation fan airflow velocity `20 - 40 cm/s` $\rightarrow$ $200.0 - 400.0\text{ mm/s}$).
3. **Dynamic Multi-Criteria Weighted Retrieval:** Enables engineers to flexibly adjust weights across semantic similarity (`w_semantic`), target environment match (`w_env_target`: `Lunar_Base`, `ISS_Earth`, `Spacesuit`), quantitative data density (`w_quantitative`), and safety pillar (`w_pillar`: `Prevention`, `Detection`, `Suppression`, `Partial-G`).
4. **Absolute Compute Resource Preservation (Incremental Checkpointing):** Reuses 100% of the Vision-Language Model (VLM) analysis results from 299 images in the baseline experiment (`EXP_FLEX_01`) via an intelligent checkpointing mechanism, eliminating the need to re-run heavy inference tasks when expanding the dataset.
5. **External API Wrapper Architecture:** Adds a specialized Vietnamese–English technical translator (`translator_layer.py`), a physics mechanism explainer powered by a local Large Language Model (`Qwen3-8B`), and packages everything into an OpenAPI-compliant `FastAPI` gateway (`api_gateway.py`) to connect directly with the **Google AI Studio** interface via **Cloudflare Tunnel**.

---

## 2. STANDARD SYSTEM DIRECTORY ARCHITECTURE

The system is strictly partitioned into 4 independent zones to protect model weights, runtime environments, and raw data repositories:

```text
D:\MCN\Hackathon_NASA_AI\
│
├── 01_Models_Weights\               # Local AI model weights storage (Read-only)
│   ├── bge-small-en-v1.5\           # Vector Embedding model for FAISS Stage 3
│   ├── Qwen2-VL / Vision Models\    # Vision model for analyzing charts & flame images in Stage 2
│   └── Qwen3-8B-GGUF\               # Physics reasoning & SI-normalized JSON extraction model in Stage 4 & API
│
├── 02_Runtime_Engines\              # Execution engines & isolated virtual environment
│   ├── llama_cpp_ engine\           # Hardware-accelerated llama-server.exe runtime
│   └── venv_hackathon\              # Standard project Python environment (PyMuPDF, FAISS, Streamlit, FastAPI...)
│
├── 03_Datasets_NASA\                # NASA multimodal data repository (19 experiment sources)
│   ├── EXP_FLEX_01\                 # Baseline foundational experiment dataset (with 299 VLM-analyzed images)
│   ├── 00_ISS_Reference_Guide\      # ISS Combustion Researcher's Guide (56-page PDF)
│   ├── 01_Prevention\               # 10 fire prevention experiments (BASS, BASS-II, SAFFIRE I-III, ACME, SPICE, SLICE)
│   ├── 02_Detection\                # 3 smoke detection & lunar dust discrimination experiments (SAME, SAME-R, DAFT)
│   ├── 03_Suppression\              # 3 fire suppression & cool flame experiments (FLEX, FLEX-2, PSI-142)
│   ├── 04_Partial_Gravity\          # 2 partial-gravity simulation & data gap experiments (ACME-E-FIELD, LUCI & FM2)
│   ├── 05_Historical_And_Spinoffs\  # 7 historical records (Apollo 1, Apollo 13, Mir station) & firefighting Spinoff tech
│   ├── public\psi_images\           # 246+ scientific chart images (.webp) automatically extracted from PDF reports
│   ├── psi_structured.db            # Relational SQLite database storing Catalog & Experimental Tables
│   └── rag_chunks_complete.json     # 748+ normalized multimodal knowledge chunks
│
└── 04_Source_Code\                  # 5-stage pipeline source code & external API wrappers
    ├── artifacts\                   # Immutable checkpoint storage directory
    │   ├── extracted_visuals\       # Extracted images for Stage 2 processing
    │   ├── stage1_ingest.json       # Stage 1 Checkpoint (Text, tables, metadata)
    │   ├── stage2_vision.json       # Stage 2 Checkpoint (Preserves 299+ VLM results)
    │   ├── stage2_vision_BACKUP.json# Safety backup copy for Stage 2
    │   ├── stage3_index.faiss       # FAISS vector search index
    │   ├── stage4_rank.json         # SI-normalized & scored outputs from Qwen3-8B
    │   ├── studio_payload.json      # Standardized JSON export payload for Studio UI
    │   └── NASA_Flame_Ranking.xlsx  # Multi-sheet summary report exported from Stage 5
    │
    ├── main.py                      # Central orchestrator running Stage 1 -> Stage 5 sequentially
    ├── stage1_ingest.py             # Stage 1: Recursive scanning & multi-format extraction (PDF, CSV, XLSX, TXT, JSON)
    ├── stage2_vision.py             # Stage 2: Chart image analysis via VLM with skip-already-processed logic
    ├── stage3_index.py              # Stage 3: BGE-Small vector embedding, FAISS indexing & dynamic weighted search
    ├── stage4_rank.py               # Stage 4: Qwen3-8B inference, SI unit conversion & safety ranking
    ├── stage5_export.py             # Stage 5: SI-standardized DataFrame generation & Excel/JSON export
    ├── data1.py, data2.py, data3.py # Automated data ingestion toolkit for NASA PSI, NTRS & Spinoffs portals
    ├── minimal_ui_test.py           # Visual testing interface via Streamlit & CLI
    ├── translator_layer.py          # [External Wrapper] Standalone Vietnamese -> English physics terminology translator
    ├── api_gateway.py               # [External Wrapper] FastAPI gateway connecting Qwen3-8B & Google AI Studio
    └── tests\test_pipeline.py       # Automated unit testing suite (Unit Tests)
```

---

## 3. DETAILED CHRONOLOGICAL WORKFLOW

### Phase 1: Building the Core 5-Tier Pipeline & Processing the Baseline Experiment (`EXP_FLEX_01`)
* **5-Stage Sequential Architecture Setup:** Established an end-to-end workflow from raw document ingestion (`Stage 1`) $\rightarrow$ chart/image comprehension using VLM (`Stage 2`) $\rightarrow$ vector indexing with `bge-small-en-v1.5` and `FAISS` (`Stage 3`) $\rightarrow$ physical parameter reasoning and extraction with `Qwen3-8B` via `llama-server.exe` (`Stage 4`) $\rightarrow$ Excel ranking table export (`Stage 5`).
* **Completed Visual Analysis of 299 Experimental Images (`stage2_vision.json`):** The system ran the VLM model for ~1.5 hours to extract data from 299 images in `EXP_FLEX_01`. These results were persisted into `artifacts\stage2_vision.json` alongside an image ID verification mechanism so they **never need to be re-processed**.

### Phase 2: Expanding the Data Repository to All 18 NASA PSI Experiments & 6 Topic Folders (`data1.py` $\rightarrow$ `data3.py`)
* **Automated Collector Suite (`data1.py`, `data2.py`, `data3.py`):**
  * Automatically downloaded the 56-page *ISS Combustion Researcher's Guide* into `00_ISS_Reference_Guide`.
  * Scanned and profiled **18 key NASA experiments** categorized across 4 technical pillars:
    1. **`01_Prevention`:** `BASS-II (PSI-25)`, `BASS (PSI-26)`, `SAFFIRE-I (PSI-98)`, `SAFFIRE-II (PSI-99)`, `SAFFIRE-III (PSI-100)`, `ACME-CFI-G (PSI-159)`, `ACME-FlameDesign (PSI-10)`, `SPICE (PSI-107)`, `ACME-BRE`, `SLICE`.
    2. **`02_Detection`:** `SAME (PSI-102)`, `SAME-R (PSI-101)`, `DAFT & DAFT-2 (PSI-179)` — addressing the challenge of distinguishing true smoke particles ($< 0.7\text{ }\mu\text{m}$) from lunar dust particles ($> 3.8\text{ }\mu\text{m}$) to prevent false alarms.
    3. **`03_Suppression`:** `FLEX (PSI-69)`, `FLEX-2 (PSI-68)`, `Cool-Flames-Model (PSI-142)` — analyzing fire suppression mechanisms using $\text{CO}_2$ and $\text{He}$, as well as reignition phenomena from low-temperature *Cool Flames* ($500 - 1000\text{ K}$).
    4. **`04_Partial_Gravity`:** `ACME-E-FIELD` (utilizing high-voltage electric field ionic wind to simulate buoyant convection at $0.16g$ Lunar and $0.38g$ Martian gravity) and `FUTURE-LUCI-FM2` (quantifying data gaps on the lunar surface).
  * Automatically downloaded scientific PDF reports from the **NASA NTRS** API, scraped experimental tables (`Experimental_Table.csv/.xlsx`), and collected 7 historical/spinoff articles (`Apollo 1`, `Apollo 13`, `Mir Space Station`, breathing apparatus & smoke detector technologies) into `05_Historical_And_Spinoffs`.
  * Automatically extracted **246 scientific chart images (`.webp`)**, built the **`psi_structured.db`** relational database, and generated **`rag_chunks_complete.json`** containing **748 chunks**.

### Phase 3: Upgrading the Multi-Format Retrieval Core & Merging Datasets (`EXP_FLEX_01` + 6 New Folders)
* **Upgraded `stage1_ingest.py`:** Added support for recursive scanning across all `.pdf`, `.csv`, `.xlsx`, `.txt`, and `.json` formats in both the 6 new topic folders and `EXP_FLEX_01`, preserving original measurement units in raw data for consistent downstream pipeline processing.
* **Lossless Checkpoint Merging:** Applied a rolling execution strategy with safety backups (`stage2_vision_BACKUP.json`), merging all data from `EXP_FLEX_01` and the 18 new experiments into a unified index while taking only `0.01 seconds` to skip the 299 previously processed images.

### Phase 4: Building the Dynamic Weighted Retriever (Stage 3) & SI-Normalized Tables (Stage 5)
* **`search_weighted()` Function in `stage3_index.py`:**
  * Retrieves the Top-30 candidates from the FAISS vector index (`bge-small-en-v1.5`), then performs dynamic re-ranking according to the formula:
    $$\text{Final\_Weighted\_Score} = w_{\text{semantic}} \cdot S_{\text{FAISS}} + w_{\text{env\_target}} \cdot S_{\text{env}} + w_{\text{quantitative}} \cdot S_{\text{quant}} + w_{\text{pillar}} \cdot S_{\text{pillar}}$$
* **`build_summary_tables()` Function in `stage5_export.py`:**
  * Combines `psi_structured.db` and `stage4_rank.json` to directly export two `pandas.DataFrame` tables:
    1. `df_metrics_summary`: Automatically converts all parameters to standardized SI units:
       * Pressure: $1\text{ psi} = 6.89476\text{ kPa}$ (`14.7 psi` $\rightarrow$ $101.35\text{ kPa}$; `10.2 psi` $\rightarrow$ $70.33\text{ kPa}$; `4.3 psi` $\rightarrow$ $29.65\text{ kPa}$).
       * Airflow velocity: $1\text{ cm/s} = 10.0\text{ mm/s}$ (`40 cm/s` $\rightarrow$ $400.0\text{ mm/s}$).
    2. `df_evidence_chunks`: Source evidence cross-reference table including PDF page numbers, CSV filenames, and component scores.
* **Testing Interface (`minimal_ui_test.py`):** Provides a Streamlit UI (and `--cli` mode) allowing real-time weight slider adjustments and visual inspection of both output data tables.

### Phase 5: External Wrapper Architecture (Translator + Qwen3-8B Physics + FastAPI) & Google AI Studio Integration
* **Adherence to the "Zero Core Modification" Principle:** Without altering any core pipeline files (`stage1` $\rightarrow$ `stage5`), all new capabilities were implemented as external wrapper layers:
  1. **Bilingual Translator (`translator_layer.py`):** Automatically detects Vietnamese queries and translates them into standard NASA English combustion physics terminology prior to embedding with `bge-small-en-v1.5`.
  2. **Physics Explainer (`explain_physics_with_qwen` in `api_gateway.py`):** Queries the local `Qwen3-8B` server (using `/no_think` mode for responses in $< 5\text{ seconds}$) to summarize combustion physics mechanisms in SI units with `[PSI-ID]` citations.
  3. **REST API Gateway (`api_gateway.py`) & Cloudflare Tunnel:** Launches a Uvicorn server on port `8000` (exposing `POST /api/query`, `GET /api/studio-tool-schema`, and `GET /health`) and opens a public HTTPS tunnel via `cloudflared tunnel` so the React/Tailwind application in **Google AI Studio** communicates directly with the local machine.

---

## 4. VERIFICATION & TECHNICAL EVALUATION SUMMARY

| Verification Item | Achieved Result | Status |
| :--- | :--- | :---: |
| **Dataset Coverage** | 19 experiment sources (`EXP_FLEX_01` + 18 PSI experiments across 6 folders), 36 CSV/XLSX files, 13 NTRS PDF reports, 246 `.webp` images, 748 RAG chunks | **100% PASS** |
| **Visual Checkpoint Preservation (Stage 2)** | Preserved all 299 VLM analysis results in `stage2_vision.json` (+ `BACKUP` copy); re-run skip latency $< 0.01\text{s}$ | **100% PASS** |
| **SI Unit Conversion Accuracy** | `10.2 psi` $\rightarrow$ $70.33\text{ kPa}$, `14.7 psi` $\rightarrow$ $101.35\text{ kPa}$, `40 cm/s` $\rightarrow$ $400.0\text{ mm/s}$ | **100% PASS** |
| **`Lunar_Base` Environment Weighted Retrieval** | Accurately prioritizes Top 3 core experiments: `BASS-II (PSI-25)`, `SAFFIRE-III (PSI-100)`, `LUCI & FM2 (FUTURE-LUCI-FM2)` alongside `n-Heptane` data from `EXP_FLEX_01` | **100% PASS** |
| **Automated Testing (Unit Tests)** | All test cases in `04_Source_Code\tests\test_pipeline.py` returned `OK` | **PASS** |
| **Hybrid Cloud–Edge Connectivity** | `api_gateway.py` (`localhost:8000`) $\leftrightarrow$ `Cloudflare Tunnel (HTTPS)` $\leftrightarrow$ `Google AI Studio Dashboard` operates seamlessly | **100% PASS** |

---

## 5. QUICK OPERATIONS CHEAT SHEET

### 1. Run Full-System Automated Unit Tests
```cmd
D:\MCN\Hackathon_NASA_AI\02_Runtime_Engines\venv_hackathon\Scripts\python.exe -m unittest discover -s D:\MCN\Hackathon_NASA_AI\04_Source_Code\tests -v
```

### 2. Launch Internal Testing Interface (Streamlit UI or CLI)
* **Web UI Mode (`localhost:8501`):**
  ```cmd
  D:\MCN\Hackathon_NASA_AI\02_Runtime_Engines\venv_hackathon\Scripts\python.exe -m streamlit run D:\MCN\Hackathon_NASA_AI\04_Source_Code\minimal_ui_test.py
  ```
* **Quick Command-Line Mode (`--cli`):**
  ```cmd
  D:\MCN\Hackathon_NASA_AI\02_Runtime_Engines\venv_hackathon\Scripts\python.exe D:\MCN\Hackathon_NASA_AI\04_Source_Code\minimal_ui_test.py --cli
  ```

### 3. Launch API Gateway & HTTPS Tunnel for Google AI Studio
* **CMD Window 1 (Start FastAPI Gateway on port 8000):**
  ```cmd
  D:\MCN\Hackathon_NASA_AI\02_Runtime_Engines\venv_hackathon\Scripts\python.exe D:\MCN\Hackathon_NASA_AI\04_Source_Code\api_gateway.py
  ```
* **CMD Window 2 (Open Cloudflare Tunnel HTTPS endpoint):**
  ```cmd
  cloudflared tunnel --url http://localhost:8000
  ```
  *(Copy the generated `https://....trycloudflare.com` URL and paste it into the **API Endpoint Settings** field in Google AI Studio).*

### 4. Quick Stop Commands to Free Ports
* Press **`Ctrl + C`** in the active CMD window, or run the following commands to terminate processes and release the port:
  ```cmd
  taskkill /F /IM streamlit.exe 2>nul
  for /f "tokens=5" %a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %a
  ```