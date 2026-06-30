"""Type-safe API contract.

`InferenceResult.to_dict()` is the single source of truth for the JSON shape
the frontend consumes — changing it here automatically updates the response.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FileType(str, Enum):
    """Input file category. `str` mixin so JSON serialization "just works"."""

    GEOTIFF = "GeoTIFF"
    IMAGE = "Image"


@dataclass
class JobMeta:
    """Per-job metadata shown in the UI telemetry line."""

    job_id: str
    input_size: str
    output_size: str
    crs: str
    elapsed: float
    file_type: FileType

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "input_size": self.input_size,
            "output_size": self.output_size,
            "crs": self.crs,
            "elapsed": self.elapsed,
            "file_type": self.file_type.value,
        }


@dataclass
class ImageSet:
    """Relative URLs to the three processed PNG outputs."""

    input: str
    sr: str
    colorized: str


@dataclass
class InferenceResult:
    """Full pipeline result. `to_dict()` produces the exact frontend contract."""

    job_id: str
    images: ImageSet
    download_png: str
    download_tif: Optional[str]   # None for plain-image inputs (no georeferencing)
    meta: JobMeta
    log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "success": True,
            "images": {
                "input": self.images.input,
                "sr": self.images.sr,
                "colorized": self.images.colorized,
            },
            "download": self.download_png,
            "download_tif": self.download_tif,
            "meta": self.meta.to_dict(),
        }
