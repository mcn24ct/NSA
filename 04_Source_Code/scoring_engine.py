"""Stage 5 Mathematical Scoring Engine: Min-Max normalization, WEIGHTS, and confidence penalties."""

from typing import Final

from schemas import ExperimentExtraction, ScoredExperiment

WEIGHTS: Final[dict[str, float]] = {
    "flame_stability_score": 0.25,
    "fire_safety_score": 0.25,
    "data_completeness_score": 0.15,
    "norm_burn_rate": 0.15,
    "norm_burn_duration": 0.10,
    "norm_oxygen_margin": 0.10,
}

NULL_FIELD_PENALTY: Final[float] = 4.0
MISSING_CITATION_PENALTY: Final[float] = 10.0
MAX_PENALTY_CAP: Final[float] = 35.0


def min_max_normalize(values: list[float | None], default_if_null: float = 50.0) -> list[float]:
    """Normalize a list of optional floats to the [0.0, 100.0] scale via Min-Max."""
    valid = [v for v in values if v is not None]
    if not valid:
        return [default_if_null for _ in values]
    v_min = min(valid)
    v_max = max(valid)
    span = v_max - v_min

    normalized: list[float] = []
    for val in values:
        if val is None:
            normalized.append(default_if_null)
        elif span == 0.0:
            normalized.append(100.0)
        else:
            score = ((val - v_min) / span) * 100.0
            normalized.append(round(max(0.0, min(100.0, score)), 2))
    return normalized


def compute_confidence_penalty(
    extraction: ExperimentExtraction,
) -> tuple[float, list[str]]:
    """Calculate penalty points for null quantitative fields or missing citations."""
    missing_fields: list[str] = []
    tracked_fields = (
        "fuel_or_material",
        "pressure_kpa",
        "oxygen_pct",
        "burn_rate_mm_s",
        "burn_duration_s",
    )
    for field_name in tracked_fields:
        if getattr(extraction, field_name) is None:
            missing_fields.append(field_name)

    penalty = len(missing_fields) * NULL_FIELD_PENALTY
    valid_citations = [
        c.strip()
        for c in extraction.citations
        if c.strip() and ("SOURCE" in c or "LOC" in c or "|" in c)
    ]
    if not valid_citations:
        missing_fields.append("citations")
        penalty += MISSING_CITATION_PENALTY

    return round(min(MAX_PENALTY_CAP, penalty), 2), missing_fields


def compute_environment_relevance_scores(
    extraction: ExperimentExtraction,
) -> tuple[float, float, float]:
    """Compute compatibility scores (0-100) for ISS/Earth, Lunar Base/Rover, and Spacesuit (EVA)."""
    p_kpa = extraction.pressure_kpa if extraction.pressure_kpa is not None else 101.325
    o2_pct = extraction.oxygen_pct if extraction.oxygen_pct is not None else 21.0
    regime = (extraction.gravity_regime or "0g").lower()
    bounding_bonus = 5.0 if ("0g" in regime or "partial" in regime or "1g" in regime) else 0.0
    text_blob = f"{extraction.experimental_objectives} {extraction.key_findings_summary}".lower()
    high_o2_bonus = 8.0 if any(k in text_blob for k in ("loi", "cfi", "bre", "dilution", "extinction")) else 0.0

    iss_p_diff = abs(p_kpa - 101.35) / 101.35
    iss_o2_diff = abs(o2_pct - 21.0) / 21.0
    iss_phys = max(0.0, 100.0 * (1.0 - (0.5 * iss_p_diff + 0.5 * iss_o2_diff)))
    iss_score = round(
        min(100.0, 0.6 * iss_phys + 0.4 * extraction.iss_earth_score + bounding_bonus),
        2,
    )

    lunar_p_gap = max(0.0, p_kpa - 70.33) / 70.33
    lunar_o2_gap = max(0.0, 30.0 - o2_pct) / 30.0
    lunar_phys = max(0.0, 100.0 * (1.0 - (0.5 * lunar_p_gap + 0.5 * lunar_o2_gap)))
    lunar_score = round(
        min(
            100.0,
            0.5 * lunar_phys + 0.5 * extraction.lunar_base_rover_score + bounding_bonus + high_o2_bonus,
        ),
        2,
    )

    suit_p_diff = abs(p_kpa - 29.65) / 101.35
    suit_o2_diff = abs(100.0 - o2_pct) / 100.0
    suit_phys = max(0.0, 100.0 * (1.0 - (0.45 * suit_p_diff + 0.55 * suit_o2_diff)))
    suit_score = round(
        min(100.0, 0.5 * suit_phys + 0.5 * extraction.spacesuit_eva_score + bounding_bonus),
        2,
    )
    return iss_score, lunar_score, suit_score


def score_and_rank_experiments(
    extractions: list[ExperimentExtraction],
) -> list[ScoredExperiment]:
    """Normalize metrics across experiments, apply WEIGHTS & penalties, and rank 1..N."""
    if not extractions:
        return []

    norm_burn_rates = min_max_normalize([e.burn_rate_mm_s for e in extractions])
    norm_burn_durations = min_max_normalize([e.burn_duration_s for e in extractions])
    norm_oxygen_margins = min_max_normalize([e.oxygen_pct for e in extractions])

    unranked: list[ScoredExperiment] = []
    for idx, ext in enumerate(extractions):
        nbr = norm_burn_rates[idx]
        nbd = norm_burn_durations[idx]
        nox = norm_oxygen_margins[idx]
        iss_rel, lunar_rel, suit_rel = compute_environment_relevance_scores(ext)

        raw_score = (
            ext.flame_stability_score * WEIGHTS["flame_stability_score"]
            + ext.fire_safety_score * WEIGHTS["fire_safety_score"]
            + ext.data_completeness_score * WEIGHTS["data_completeness_score"]
            + nbr * WEIGHTS["norm_burn_rate"]
            + nbd * WEIGHTS["norm_burn_duration"]
            + nox * WEIGHTS["norm_oxygen_margin"]
        )
        raw_score = round(max(0.0, min(100.0, raw_score)), 2)
        penalty, missing = compute_confidence_penalty(ext)
        final_score = round(max(0.0, min(100.0, raw_score - penalty)), 2)

        unranked.append(
            ScoredExperiment(
                rank=1,
                experiment_id=ext.experiment_id,
                fuel_or_material=ext.fuel_or_material,
                pressure_kpa=ext.pressure_kpa,
                oxygen_pct=ext.oxygen_pct,
                burn_rate_mm_s=ext.burn_rate_mm_s,
                burn_duration_s=ext.burn_duration_s,
                airflow_speed_mm_s=ext.airflow_speed_mm_s,
                experimental_objectives=ext.experimental_objectives,
                hardware_apparatus=ext.hardware_apparatus,
                sample_geometry_size=ext.sample_geometry_size,
                controlled_vs_varied_vars=ext.controlled_vs_varied_vars,
                sensors_used=ext.sensors_used,
                gravity_regime=ext.gravity_regime,
                iss_earth_score=iss_rel,
                lunar_base_rover_score=lunar_rel,
                spacesuit_eva_score=suit_rel,
                iss_earth_relevance_score=iss_rel,
                lunar_base_rover_relevance_score=lunar_rel,
                spacesuit_relevance_score=suit_rel,
                earth_applications=ext.earth_applications,
                norm_burn_rate=nbr,
                norm_burn_duration=nbd,
                norm_oxygen_margin=nox,
                flame_stability_score=round(ext.flame_stability_score, 2),
                fire_safety_score=round(ext.fire_safety_score, 2),
                data_completeness_score=round(ext.data_completeness_score, 2),
                raw_weighted_score=raw_score,
                confidence_penalty=penalty,
                final_weighted_score=final_score,
                missing_fields=missing,
                citations=ext.citations,
                key_findings_summary=ext.key_findings_summary,
            )
        )

    sorted_exps = sorted(
        unranked,
        key=lambda item: (item.final_weighted_score, item.raw_weighted_score),
        reverse=True,
    )
    for rank_idx, item in enumerate(sorted_exps, start=1):
        item.rank = rank_idx
    return sorted_exps
