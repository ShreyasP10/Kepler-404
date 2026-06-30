"""I/O layer — focused read/write functions, one format per helper.

GeoTIFFs go through rasterio (preserving CRS + transform).
Plain images go through **Pillow** (cleaner decode + color→gray + EXIF handling).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import rasterio
from PIL import Image
from rasterio.transform import Affine

from .exceptions import DecodingError


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------
@dataclass
class GeoReadResult:
    """Result of reading a GeoTIFF: the band + its geospatial context."""

    band: np.ndarray
    transform: Affine
    crs: object
    width: int
    height: int


def read_geotiff(path: Path) -> GeoReadResult:
    """Open a GeoTIFF and return band 1 + geospatial metadata.

    Raises DecodingError if the file cannot be opened by rasterio.
    """
    try:
        with rasterio.open(path) as src:
            return GeoReadResult(
                band=src.read(1),
                transform=src.transform,
                crs=src.crs,
                width=src.width,
                height=src.height,
            )
    except Exception as exc:
        raise DecodingError(f"Could not read GeoTIFF {path.name}: {exc}") from exc


def read_image(path: Path) -> np.ndarray:
    """Decode a plain image (.png/.jpg) to a uint8 grayscale numpy array.

    Uses Pillow for robust decode + color→gray conversion. Falls back to
    OpenCV if PIL cannot identify the file.
    """
    try:
        img = Image.open(path)
        if img.mode != "L":
            img = img.convert("L")
        return np.array(img, dtype=np.uint8)
    except Exception as pil_exc:
        # Last-resort OpenCV fallback
        raw = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if raw is None:
            raise DecodingError(
                f"Could not decode image {path.name}: {pil_exc}"
            ) from pil_exc
        if raw.ndim == 3:
            raw = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        return raw.astype(np.uint8)


def normalize_to_uint8(array: np.ndarray) -> np.ndarray:
    """Stretch an arbitrary array to 0–255 via robust 2nd/98th percentile clipping."""
    data = array.astype(np.float32)
    valid = data[np.isfinite(data)]
    if valid.size == 0:
        return np.zeros(array.shape, dtype=np.uint8)

    low, high = np.percentile(valid, [2, 98])
    if high <= low:
        low, high = float(valid.min()), float(valid.max())
    if high <= low:
        return np.zeros(array.shape, dtype=np.uint8)

    scaled = np.clip((data - low) / (high - low), 0, 1)
    return (scaled * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------
def write_png(path: Path, gray: np.ndarray) -> None:
    """Write a single-channel uint8 array as a PNG via OpenCV.

    Raises RuntimeError if OpenCV fails to write the file.
    """
    success = cv2.imwrite(str(path), gray)
    if not success:
        raise RuntimeError(f"OpenCV failed to write PNG to {path}")


def write_geotiff(
    path: Path,
    rgb: np.ndarray,
    transform: Affine,
    crs: object,
    new_transform: Optional[Affine] = None,
) -> None:
    """Write a 3-band uint8 RGB array as a georeferenced GeoTIFF.

    `new_transform` (if provided) overrides `transform` — used when the
    output has been resampled to a new resolution.
    """
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"write_geotiff expects an HxWx3 array, got {rgb.shape}")

    height, width = rgb.shape[:2]
    tif_transform = new_transform if new_transform is not None else transform
    crs_value = str(crs) if crs else None

    profile = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 3,
        "dtype": "uint8",
        "transform": tif_transform,
        "crs": crs_value,
        "photometric": "RGB",
    }
    with rasterio.open(path, "w", **profile) as dst:
        for i in range(3):
            dst.write(rgb[:, :, i], i + 1)
