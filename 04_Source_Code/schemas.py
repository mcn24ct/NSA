"""Pydantic data contracts for the NASA microgravity combustion pipeline."""

from typing import Literal
from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    """Extracted text segment from a PDF page."""

    experiment_id: str = Field(..., description="Unique NASA experiment identifier")
    source_file: str = Field(..., description="Filename of the source PDF")
    page_or_sec: str = Field(..., description="Page locator, e.g., page_3")
    text: str = Field(..., description="Cleaned textual content")


class VisualAsset(BaseModel):
    """Filtered PDF image (>=200x200px) or video keyframe (<=1024px max side)."""

    experiment_id: str = Field(..., description="Unique NASA experiment identifier")
    source_file: str = Field(..., description="Source PDF or video filename")
    page_or_sec: str = Field(..., description="Page locator or timestamp in seconds")
    asset_type: Literal["pdf_image", "video_keyframe"] = Field(
        ..., description="Origin type of the visual asset"
    )
    image_path: str = Field(..., description="Absolute path to the resized PNG image")
    width: int = Field(..., ge=1, description="Resized image width in pixels")
    height: int = Field(..., ge=1, description="Resized image height in pixels")


class ExperimentIngestBundle(BaseModel):
    """Stage 1 output bundle for a single NASA experiment."""

    experiment_id: str
    text_blocks: list[TextBlock] = Field(default_factory=list)
    visual_assets: list[VisualAsset] = Field(default_factory=list)
    user_queries: list[str] = Field(default_factory=list)


class VisualDescription(BaseModel):
    """Stage 2 VLM technical transcription of a chart or microgravity flame frame."""

    experiment_id: str
    source_file: str
    page_or_sec: str
    asset_type: Literal["pdf_image", "video_keyframe"]
    image_path: str
    technical_description: str = Field(
        ...,
        description="Structured description of chart axes/extrema or flame morphology",
    )


class IndexedChunk(BaseModel):
    """Stage 3 multimodal chunk stored alongside FAISS vector index."""

    chunk_id: int
    experiment_id: str
    source_file: str
    page_or_sec: str
    modality: Literal["pdf_text", "vlm_vision"]
    token_count: int = Field(..., le=512, description="BGE token count (<=512)")
    prefixed_text: str = Field(
        ...,
        description="Chunk text prefixed with [EXP: <id> | SOURCE: <file> | LOC: <loc>]",
    )


class ExperimentExtraction(BaseModel):
    """Stage 4 LLM structured output with normalized physical units and citations."""

    experiment_id: str = Field(..., description="Unique NASA experiment identifier")
    fuel_or_material: str | None = Field(
        default=None, description="Tested fuel or solid material name"
    )
    pressure_kpa: float | None = Field(
        default=None, description="Ambient chamber pressure normalized to kPa"
    )
    oxygen_pct: float | None = Field(
        default=None, description="Ambient oxygen mole/volume concentration in %"
    )
    burn_rate_mm_s: float | None = Field(
        default=None, description="Flame spread or droplet regression rate in mm/s"
    )
    burn_duration_s: float | None = Field(
        default=None, description="Total combustion duration until extinction in s"
    )
    flame_stability_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Spherical symmetry and steady-state stability score (0-100)",
    )
    fire_safety_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Spacecraft fire safety & self-extinguishment score (0-100)",
    )
    data_completeness_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Experimental instrumentation & measurement clarity score (0-100)",
    )
    key_findings_summary: str = Field(
        ..., description="Concise technical synthesis of microgravity flame behavior"
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Exact citations in [SOURCE: <file> | LOC: <page/sec>] format",
    )


class ScoredExperiment(BaseModel):
    """Stage 5 mathematically normalized, penalized, and ranked experiment record."""

    rank: int = Field(..., ge=1, description="Final standing (1 = highest score)")
    experiment_id: str
    fuel_or_material: str | None = None
    pressure_kpa: float | None = None
    oxygen_pct: float | None = None
    burn_rate_mm_s: float | None = None
    burn_duration_s: float | None = None
    norm_burn_rate: float = Field(..., ge=0.0, le=100.0)
    norm_burn_duration: float = Field(..., ge=0.0, le=100.0)
    norm_oxygen_margin: float = Field(..., ge=0.0, le=100.0)
    flame_stability_score: float = Field(..., ge=0.0, le=100.0)
    fire_safety_score: float = Field(..., ge=0.0, le=100.0)
    data_completeness_score: float = Field(..., ge=0.0, le=100.0)
    raw_weighted_score: float = Field(..., ge=0.0, le=100.0)
    confidence_penalty: float = Field(..., ge=0.0, le=100.0)
    final_weighted_score: float = Field(..., ge=0.0, le=100.0)
    missing_fields: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    key_findings_summary: str
