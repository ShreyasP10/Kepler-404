"""Shared test fixtures — synthetic files, Flask test client, temp dirs.

Every test that needs a GeoTIFF or PNG can use `make_geotiff` / `make_png`
to generate deterministic files in a tmp_path that auto-cleans.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from kepler.app import create_app
from kepler.config import Settings
from kepler.logging_setup import reset_for_tests

# Reset logging between test sessions so handlers don't accumulate
reset_for_tests()


# ---------------------------------------------------------------------------
# Synthetic file generators
# ---------------------------------------------------------------------------
def make_geotiff(path: Path, width: int = 32, height: int = 32, seed: int = 42) -> Path:
    """Write a small valid GeoTIFF with random band data and EPSG:4326."""
    rng = np.random.default_rng(seed)
    band = rng.integers(0, 255, size=(height, width), dtype=np.uint8)
    transform = from_bounds(0.0, 0.0, 1.0, 1.0, width, height)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype="uint8",
        crs=CRS.from_epsg(4326),
        transform=transform,
    ) as dst:
        dst.write(band, 1)
    return path


def make_png(path: Path, width: int = 32, height: int = 32, color: bool = False, seed: int = 42) -> Path:
    """Write a small PNG using Pillow."""
    from PIL import Image
    rng = np.random.default_rng(seed)
    if color:
        arr = rng.integers(0, 255, size=(height, width, 3), dtype=np.uint8)
        mode = "RGB"
    else:
        arr = rng.integers(0, 255, size=(height, width), dtype=np.uint8)
        mode = "L"
    Image.fromarray(arr, mode=mode).save(path)
    return path


def make_jpeg(path: Path, width: int = 32, height: int = 32, seed: int = 42) -> Path:
    """Write a small JPEG using Pillow."""
    return make_png(path.with_suffix(".jpg"), width, height, color=True, seed=seed)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def settings(tmp_path):
    """Isolated settings with temp dirs for every test."""
    s = Settings.for_test(tmp_path)
    s.ensure_dirs()
    return s


@pytest.fixture()
def pipeline(settings):
    """Pipeline bound to isolated temp settings."""
    from kepler.pipeline import Pipeline
    return Pipeline(settings)


@pytest.fixture()
def client(settings, tmp_path):
    """Flask test client pointed at a temp dir with a template stub.

    We copy the real templates/static so render_template works. If the
    project root isn't on disk (CI), the index route simply returns 404 —
    that's fine for API-only tests.
    """
    from kepler.app import create_app

    # Point base_dir to the real project root so templates/static resolve
    real_root = Path(__file__).resolve().parent.parent
    s = Settings(
        base_dir=real_root,
        upload_dir=tmp_path / "uploads",
        results_dir=tmp_path / "results",
        allowed_extensions=settings.allowed_extensions,
        geotiff_extensions=settings.geotiff_extensions,
        max_file_size=settings.max_file_size,
        retention_hours=None,
        mock_delay_seconds=0.0,
        host="127.0.0.1",
        port=5000,
        debug=False,
        test_mode=True,
    )
    s.ensure_dirs()
    app = create_app(s)
    app.config["TESTING"] = True
    return app.test_client()
