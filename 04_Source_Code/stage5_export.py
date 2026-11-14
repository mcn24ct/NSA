"""Stage 5 Export: Generate formatted Excel (.xlsx) and Markdown analytical report (.md)."""

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import config
from schemas import ExperimentExtraction, ScoredExperiment
from scoring_engine import WEIGHTS, score_and_rank_experiments


def _auto_fit_columns(worksheet) -> None:
    """Adjust Excel column widths for clean readability."""
    for col in worksheet.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            max_len = max(max_len, len(val_str))
        worksheet.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 55)


def export_to_excel(
    scored_list: list[ScoredExperiment], excel_path: Path = config.STAGE5_EXCEL_PATH
) -> Path:
    """Create a 2-sheet professionally styled Excel workbook from scored experiments."""
    config.ensure_artifact_dirs()
    wb = Workbook()

    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    body_font = Font(name="Calibri", size=10)
    thin_side = Side(border_style="thin", color="D9D9D9")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    ws1 = wb.active
    ws1.title = "Executive_Ranking_Summary"
    headers_s1 = [
        "Rank",
        "Experiment ID",
        "Fuel / Material",
        "Final Score (/100)",
        "Raw Weighted Score",
        "Confidence Penalty",
        "Pressure (kPa)",
        "Oxygen (%)",
        "Burn Rate (mm/s)",
        "Burn Duration (s)",
        "Key Findings Summary",
    ]
    ws1.append(headers_s1)
    for cell in ws1[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for item in scored_list:
        ws1.append(
            [
                item.rank,
                item.experiment_id,
                item.fuel_or_material or "N/A",
                item.final_weighted_score,
                item.raw_weighted_score,
                item.confidence_penalty,
                item.pressure_kpa if item.pressure_kpa is not None else "N/A",
                item.oxygen_pct if item.oxygen_pct is not None else "N/A",
                item.burn_rate_mm_s if item.burn_rate_mm_s is not None else "N/A",
                item.burn_duration_s if item.burn_duration_s is not None else "N/A",
                item.key_findings_summary,
            ]
        )

    for row in ws1.iter_rows(min_row=2, max_row=ws1.max_row):
        for cell in row:
            cell.font = body_font
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws2 = wb.create_sheet(title="Component_Scores_Citations")
    headers_s2 = [
        "Rank",
        "Experiment ID",
        "Stability Score (25%)",
        "Fire Safety Score (25%)",
        "Completeness Score (15%)",
        "Norm Burn Rate (15%)",
        "Norm Burn Duration (10%)",
        "Norm O2 Margin (10%)",
        "Missing Fields",
        "Verified Source Citations [SOURCE | LOC]",
    ]
    ws2.append(headers_s2)
    for cell in ws2[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for item in scored_list:
        ws2.append(
            [
                item.rank,
                item.experiment_id,
                item.flame_stability_score,
                item.fire_safety_score,
                item.data_completeness_score,
                item.norm_burn_rate,
                item.norm_burn_duration,
                item.norm_oxygen_margin,
                ", ".join(item.missing_fields) if item.missing_fields else "None",
                " ; ".join(item.citations) if item.citations else "None",
            ]
        )

    for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row):
        for cell in row:
            cell.font = body_font
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws3 = wb.create_sheet(title="BTC_Technical_Attributes")
    headers_s3 = [
        "Rank",
        "Experiment ID",
        "Gravity Regime (Bounding 0g-1g)",
        "Experimental Objectives",
        "Hardware / Apparatus (CIR/MDCA/MSG/ACME/SPICE)",
        "Sample Geometry & Size (mm)",
        "Airflow Speed (mm/s)",
        "Controlled vs. Varied Variables",
        "Sensors & Diagnostics Used",
        "ISS/Earth Score (101.35 kPa, 21% O2)",
        "Lunar Base Score (<=70.33 kPa, >=30% O2)",
        "Spacesuit EVA Score (29.65 kPa, 100% O2)",
        "Earth Applications (Fine-Mist / SAME / Gear)",
    ]
    ws3.append(headers_s3)
    for cell in ws3[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for item in scored_list:
        ws3.append(
            [
                item.rank,
                item.experiment_id,
                item.gravity_regime,
                item.experimental_objectives,
                item.hardware_apparatus,
                item.sample_geometry_size,
                item.airflow_speed_mm_s if item.airflow_speed_mm_s is not None else 0.0,
                item.controlled_vs_varied_vars,
                item.sensors_used,
                item.iss_earth_score,
                item.lunar_base_rover_score,
                item.spacesuit_eva_score,
                item.earth_applications,
            ]
        )

    for row in ws3.iter_rows(min_row=2, max_row=ws3.max_row):
        for cell in row:
            cell.font = body_font
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    _auto_fit_columns(ws1)
    _auto_fit_columns(ws2)
    _auto_fit_columns(ws3)
    try:
        wb.save(str(excel_path))
        return excel_path
    except PermissionError:
        return excel_path


def export_to_markdown(
    scored_list: list[ScoredExperiment], report_path: Path = config.STAGE5_REPORT_PATH
) -> Path:
    """Write a comprehensive Markdown analytical report of the ranked NASA experiments."""
    config.ensure_artifact_dirs()
    lines: list[str] = [
        "# NASA Microgravity Combustion — Analytical Ranking Report",
        "",
        "## 1. Scoring Methodology & Weight Distribution",
        "| Component Metric | Weight | Description |",
        "| :--- | :---: | :--- |",
        f"| `flame_stability_score` | {WEIGHTS['flame_stability_score']:.2f} | Spherical flame symmetry and steady state |",
        f"| `fire_safety_score` | {WEIGHTS['fire_safety_score']:.2f} | Spacecraft material safety & quenching behavior |",
        f"| `data_completeness_score` | {WEIGHTS['data_completeness_score']:.2f} | Diagnostic resolution and sensor completeness |",
        f"| `norm_burn_rate` | {WEIGHTS['norm_burn_rate']:.2f} | Min-Max normalized burn/regression rate (`mm/s`) |",
        f"| `norm_burn_duration` | {WEIGHTS['norm_burn_duration']:.2f} | Min-Max normalized combustion duration (`s`) |",
        f"| `norm_oxygen_margin` | {WEIGHTS['norm_oxygen_margin']:.2f} | Min-Max normalized oxygen concentration (`%`) |",
        "",
        "## 2. Executive Ranking Table",
        "| Rank | Experiment ID | Fuel / Material | Pressure (kPa) | O2 (%) | Burn Rate (mm/s) | Duration (s) | Penalty | Final Score |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for item in scored_list:
        p_str = f"{item.pressure_kpa:.2f}" if item.pressure_kpa is not None else "N/A"
        o_str = f"{item.oxygen_pct:.2f}" if item.oxygen_pct is not None else "N/A"
        r_str = f"{item.burn_rate_mm_s:.3f}" if item.burn_rate_mm_s is not None else "N/A"
        d_str = f"{item.burn_duration_s:.2f}" if item.burn_duration_s is not None else "N/A"
        lines.append(
            f"| **{item.rank}** | `{item.experiment_id}` | {item.fuel_or_material or 'N/A'} | "
            f"{p_str} | {o_str} | {r_str} | {d_str} | -{item.confidence_penalty:.2f} | "
            f"**{item.final_weighted_score:.2f}** |"
        )

    lines.extend(["", "## 3. Detailed Experiment Breakdown & Citations", ""])
    for item in scored_list:
        lines.extend(
            [
                f"### Rank #{item.rank}: `{item.experiment_id}` (Score: {item.final_weighted_score:.2f} / 100)",
                f"- **Fuel / Material**: {item.fuel_or_material or 'N/A'} | **Gravity Regime**: `{item.gravity_regime}`",
                f"- **Experimental Objectives**: {item.experimental_objectives}",
                f"- **Hardware / Apparatus**: {item.hardware_apparatus}",
                f"- **Sample Geometry & Size**: {item.sample_geometry_size} | **Airflow Speed**: `{item.airflow_speed_mm_s if item.airflow_speed_mm_s is not None else 0.0} mm/s`",
                f"- **Controlled vs. Varied Variables**: {item.controlled_vs_varied_vars}",
                f"- **Sensors & Diagnostics Used**: {item.sensors_used}",
                f"- **NASA Environment Relevance Scores**: ISS/Earth (`101.35 kPa, 21% O2`): `{item.iss_earth_score:.2f}` | "
                f"Lunar Base (`<=70.33 kPa, >=30% O2`): `{item.lunar_base_rover_score:.2f}` | "
                f"Spacesuit (`29.65 kPa, 100% O2`): `{item.spacesuit_eva_score:.2f}`",
                f"- **Earth Applications**: {item.earth_applications}",
                f"- **Component Scores**: Stability `{item.flame_stability_score}`, "
                f"Safety `{item.fire_safety_score}`, Completeness `{item.data_completeness_score}`",
                f"- **Confidence Penalty**: `-{item.confidence_penalty:.2f}` "
                f"(Missing fields: `{', '.join(item.missing_fields) if item.missing_fields else 'None'}`)",
                f"- **Key Findings**: {item.key_findings_summary}",
                f"- **Verified Citations**: {'; '.join(item.citations) if item.citations else 'None'}",
                "",
            ]
        )

    try:
        report_path.write_text("\n".join(lines), encoding="utf-8")
    except PermissionError:
        pass
    return report_path


def run_stage5_export(
    extractions: list[ExperimentExtraction] | None = None,
    stage4_checkpoint: Path = config.STAGE4_CHECKPOINT,
    scored_json_path: Path = config.STAGE5_SCORED_JSON,
    excel_path: Path = config.STAGE5_EXCEL_PATH,
    report_path: Path = config.STAGE5_REPORT_PATH,
) -> list[ScoredExperiment]:
    """Compute final mathematical rankings and export JSON, Excel (.xlsx), and Markdown (.md)."""
    config.ensure_artifact_dirs()
    if extractions is None:
        if not stage4_checkpoint.exists():
            raise FileNotFoundError(
                f"Stage 4 checkpoint not found: {stage4_checkpoint}"
            )
        raw_s4 = json.loads(stage4_checkpoint.read_text(encoding="utf-8"))
        extractions = [ExperimentExtraction.model_validate(item) for item in raw_s4]

    scored = score_and_rank_experiments(extractions)
    payload = json.dumps([s.model_dump() for s in scored], indent=2, ensure_ascii=False)
    try:
        scored_json_path.write_text(payload, encoding="utf-8")
    except PermissionError:
        pass
    export_to_excel(scored, excel_path=excel_path)
    export_to_markdown(scored, report_path=report_path)
    return scored


def build_summary_tables(
    search_results: list[dict[str, Any]],
    db_path: Path = config.DATASETS_DIR / "psi_structured.db",
    stage4_path: Path = config.STAGE4_CHECKPOINT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build SI-normalized df_metrics_summary and df_evidence_chunks DataFrames from Stage 3 results."""
    evidence_rows: list[dict[str, Any]] = []
    best_score_by_exp: dict[str, float] = {}

    for idx, res in enumerate(search_results, start=1):
        exp_code = str(res.get("experiment_id") or "").strip()
        psi_id = str(res.get("psi_id") or "").strip()
        w_score = float(res.get("weighted_score", 0.0))
        if exp_code:
            best_score_by_exp[exp_code.upper()] = max(
                best_score_by_exp.get(exp_code.upper(), 0.0), w_score
            )
        if psi_id:
            best_score_by_exp[psi_id.upper()] = max(
                best_score_by_exp.get(psi_id.upper(), 0.0), w_score
            )

        evidence_rows.append(
            {
                "Rank": int(res.get("rank", idx)),
                "Investigation": str(res.get("investigation") or exp_code),
                "Source": f"{res.get('source_file', '')} | {res.get('page_or_sec', '')}",
                "Base_FAISS_Score": round(float(res.get("base_faiss_score", 0.0)), 4),
                "Final_Weighted_Score": round(w_score, 4),
                "Extracted_Snippet": str(res.get("extracted_snippet") or res.get("prefixed_text") or ""),
            }
        )

    df_evidence_chunks = pd.DataFrame(
        evidence_rows,
        columns=[
            "Rank",
            "Investigation",
            "Source",
            "Base_FAISS_Score",
            "Final_Weighted_Score",
            "Extracted_Snippet",
        ],
    )

    metrics_rows: list[dict[str, Any]] = []
    seen_codes: set[str] = set()

    if db_path.exists():
        con = sqlite3.connect(str(db_path))
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute("SELECT * FROM investigations_catalog").fetchall()
            for r in rows:
                row_d = dict(r)
                psi_id = str(row_d.get("psi_id") or "")
                code = str(row_d.get("code") or "")
                rel_score = max(
                    best_score_by_exp.get(code.upper(), -1.0),
                    best_score_by_exp.get(psi_id.upper(), -1.0),
                )
                if best_score_by_exp and rel_score < 0.0:
                    continue
                rel_val = round(max(0.0, rel_score), 4)
                p_psi = float(row_d.get("pressure_psi") or 14.7)
                o2_min = float(row_d.get("o2_min") or 21.0)
                o2_max = float(row_d.get("o2_max") or 21.0)
                af_cm_s = float(row_d.get("airflow_max_cm_s") or 0.0)
                sim_pg = int(row_d.get("simulates_partial_g") or 0)

                metrics_rows.append(
                    {
                        "PSI_ID": psi_id,
                        "Experiment_Code": code,
                        "Pillar": str(row_d.get("pillar") or "Prevention"),
                        "Hardware_Rack": str(row_d.get("rack") or "CIR / MSG"),
                        "Fuels": str(row_d.get("fuels") or "N/A"),
                        "Pressure_kPa": round(p_psi * 6.89476, 2),
                        "O2_Range_%": f"{o2_min:.1f} - {o2_max:.1f}%",
                        "Max_Airflow_mm_s": round(af_cm_s * 10.0, 1),
                        "Partial_G_Proxy": "Yes (Partial-g)" if sim_pg == 1 else "No (0g)",
                        "Weighted_Relevance_Score": rel_val,
                    }
                )
                seen_codes.add(code.upper())
        finally:
            con.close()

    if stage4_path.exists():
        raw_s4 = json.loads(stage4_path.read_text(encoding="utf-8"))
        for item in raw_s4:
            exp_id = str(item.get("experiment_id") or "EXP_FLEX_01")
            if exp_id.upper() in seen_codes:
                continue
            rel_score = best_score_by_exp.get(exp_id.upper(), -1.0)
            if best_score_by_exp and rel_score < 0.0 and metrics_rows:
                continue
            p_kpa = float(item.get("pressure_kpa") or 101.325)
            o2_pct = float(item.get("oxygen_pct") or 20.0)
            af_mm = float(item.get("airflow_speed_mm_s") or 0.0)
            metrics_rows.append(
                {
                    "PSI_ID": "PSI-FLEX",
                    "Experiment_Code": exp_id,
                    "Pillar": "Prevention",
                    "Hardware_Rack": str(item.get("hardware_apparatus") or "CIR / MDCA"),
                    "Fuels": str(item.get("fuel_or_material") or "n-Heptane"),
                    "Pressure_kPa": round(p_kpa, 2),
                    "O2_Range_%": f"{o2_pct:.1f}%",
                    "Max_Airflow_mm_s": round(af_mm, 1),
                    "Partial_G_Proxy": str(item.get("gravity_regime") or "No (0g)"),
                    "Weighted_Relevance_Score": round(max(0.0, rel_score), 4),
                }
            )

    metrics_rows.sort(key=lambda r: r["Weighted_Relevance_Score"], reverse=True)
    df_metrics_summary = pd.DataFrame(
        metrics_rows,
        columns=[
            "PSI_ID",
            "Experiment_Code",
            "Pillar",
            "Hardware_Rack",
            "Fuels",
            "Pressure_kPa",
            "O2_Range_%",
            "Max_Airflow_mm_s",
            "Partial_G_Proxy",
            "Weighted_Relevance_Score",
        ],
    )
    return df_metrics_summary, df_evidence_chunks


def export_studio_payload(
    query: str,
    weights: dict[str, Any],
    df_metrics: pd.DataFrame,
    df_evidence: pd.DataFrame,
    output_path: Path = config.ARTIFACTS_DIR / "studio_payload.json",
) -> Path:
    """Export query, weights, and both SI-normalized summary tables to studio_payload.json."""
    config.ensure_artifact_dirs()
    payload = {
        "query": query,
        "weights": weights,
        "metrics_summary": df_metrics.to_dict(orient="records"),
        "evidence_chunks": df_evidence.to_dict(orient="records"),
    }
    text_json = json.dumps(payload, indent=2, ensure_ascii=False)
    try:
        output_path.write_text(text_json, encoding="utf-8")
    except PermissionError:
        pass
    return output_path
