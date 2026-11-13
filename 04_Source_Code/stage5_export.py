"""Stage 5 Export: Generate formatted Excel (.xlsx) and Markdown analytical report (.md)."""

import json
from pathlib import Path

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

    _auto_fit_columns(ws1)
    _auto_fit_columns(ws2)
    wb.save(str(excel_path))
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
                f"- **Fuel / Material**: {item.fuel_or_material or 'N/A'}",
                f"- **Component Scores**: Stability `{item.flame_stability_score}`, "
                f"Safety `{item.fire_safety_score}`, Completeness `{item.data_completeness_score}`",
                f"- **Confidence Penalty**: `-{item.confidence_penalty:.2f}` "
                f"(Missing fields: `{', '.join(item.missing_fields) if item.missing_fields else 'None'}`)",
                f"- **Key Findings**: {item.key_findings_summary}",
                f"- **Verified Citations**: {'; '.join(item.citations) if item.citations else 'None'}",
                "",
            ]
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")
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
    scored_json_path.write_text(
        json.dumps([s.model_dump() for s in scored], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    export_to_excel(scored, excel_path=excel_path)
    export_to_markdown(scored, report_path=report_path)
    return scored
