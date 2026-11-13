"""Stage 2: Vision-to-technical-text transcription using Qwen2.5-VL-3B + mmproj-F16."""

import json
from pathlib import Path

import config
from llm_client import LlamaServerManager
from schemas import ExperimentIngestBundle, VisualAsset, VisualDescription

VLM_SYSTEM_PROMPT = (
    "You are a NASA microgravity combustion diagnostics specialist. "
    "Analyze the provided scientific image with high technical precision."
)

VLM_USER_PROMPT = (
    "Identify whether this image is a scientific plot/chart or a flame photograph/keyframe:\n"
    "1. If it is a chart/plot: extract exact X-axis label and unit, Y-axis label and unit, "
    "maximum peak value, minimum value, and physical trend.\n"
    "2. If it is a flame photograph or video keyframe: describe flame color (blue, yellow, "
    "luminous soot), spherical symmetry in microgravity, soot shell formation, radiative "
    "quenching, or re-ignition phenomena.\n"
    "Provide a concise, dense paragraph of technical facts."
)


def describe_visual_asset(
    server: LlamaServerManager, asset: VisualAsset
) -> VisualDescription:
    """Query VLM for a single visual asset and preserve full source metadata."""
    img_path = Path(asset.image_path)
    description_text = server.analyze_image(
        image_path=img_path,
        system_prompt=VLM_SYSTEM_PROMPT,
        user_prompt=VLM_USER_PROMPT,
    )
    return VisualDescription(
        experiment_id=asset.experiment_id,
        source_file=asset.source_file,
        page_or_sec=asset.page_or_sec,
        asset_type=asset.asset_type,
        image_path=asset.image_path,
        technical_description=description_text,
    )


def run_stage2_vision(
    bundles: list[ExperimentIngestBundle] | None = None,
    stage1_checkpoint: Path = config.STAGE1_CHECKPOINT,
    checkpoint_path: Path = config.STAGE2_CHECKPOINT,
    force: bool = False,
) -> list[VisualDescription]:
    """Run VLM over all filtered visual assets from Stage 1 and release VRAM via finally."""
    config.ensure_artifact_dirs()
    if checkpoint_path.exists() and not force:
        raw_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        return [VisualDescription.model_validate(item) for item in raw_data]

    if bundles is None:
        if not stage1_checkpoint.exists():
            raise FileNotFoundError(
                f"Stage 1 checkpoint not found: {stage1_checkpoint}"
            )
        raw_s1 = json.loads(stage1_checkpoint.read_text(encoding="utf-8"))
        bundles = [ExperimentIngestBundle.model_validate(item) for item in raw_s1]

    all_assets: list[VisualAsset] = [
        asset for bundle in bundles for asset in bundle.visual_assets
    ]
    descriptions: list[VisualDescription] = []

    if all_assets:
        server = LlamaServerManager(
            model_path=config.VLM_MODEL_PATH,
            mmproj_path=config.VLM_MMPROJ_PATH,
            ctx_size=config.VLM_CTX,
            disable_thinking=False,
        )
        try:
            server.start()
            for asset in all_assets:
                descriptions.append(describe_visual_asset(server, asset))
        finally:
            server.stop()

    checkpoint_path.write_text(
        json.dumps(
            [d.model_dump() for d in descriptions], indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    return descriptions
