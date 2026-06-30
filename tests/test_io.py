"""Tests for kepler.io — read/write round-trips."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from kepler.exceptions import DecodingError
from kepler.io import (
    GeoReadResult,
    normalize_to_uint8,
    read_geotiff,
    read_image,
    write_png,
    write_geotiff,
)
from tests.conftest import make_geotiff, make_png


class TestNormalizeToUint8:
    def test_basic_stretch(self):
        arr = np.array([[0, 128], [200, 255]], dtype=np.uint8)
        out = normalize_to_uint8(arr)
        assert out.dtype == np.uint8
        assert out.shape == arr.shape

    def test_all_same_value(self):
        arr = np.full((4, 4), 100, dtype=np.uint8)
        out = normalize_to_uint8(arr)
        assert out.dtype == np.uint8

    def test_float_input(self):
        arr = np.random.rand(8, 8).astype(np.float32)
        out = normalize_to_uint8(arr)
        assert out.dtype == np.uint8
        assert out.min() >= 0
        assert out.max() <= 255

    def test_empty_array(self):
        arr = np.array([], dtype=np.float32)
        out = normalize_to_uint8(arr)
        assert out.size == 0


class TestReadGeoTIFF:
    def test_reads_valid_geotiff(self, tmp_path):
        tif = make_geotiff(tmp_path / "sample.tif", 16, 16)
        result = read_geotiff(tif)
        assert isinstance(result, GeoReadResult)
        assert result.band.shape == (16, 16)
        assert result.width == 16
        assert result.height == 16
        assert result.crs is not None
        assert result.transform is not None

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(DecodingError):
            read_geotiff(tmp_path / "nonexistent.tif")

    def test_raises_on_corrupt_file(self, tmp_path):
        bad = tmp_path / "bad.tif"
        bad.write_bytes(b"not a geotiff at all")
        with pytest.raises(DecodingError):
            read_geotiff(bad)


class TestReadImage:
    def test_reads_grayscale_png(self, tmp_path):
        make_png(tmp_path / "gray.png", 16, 16, color=False)
        arr = read_image(tmp_path / "gray.png")
        assert arr.dtype == np.uint8
        assert arr.shape == (16, 16)

    def test_reads_color_png_as_gray(self, tmp_path):
        make_png(tmp_path / "color.png", 16, 16, color=True)
        arr = read_image(tmp_path / "color.png")
        assert arr.ndim == 2  # should be grayscale

    def test_reads_jpeg(self, tmp_path):
        make_png(tmp_path / "sample.jpg", 12, 12, color=True)
        arr = read_image(tmp_path / "sample.jpg")
        assert arr.dtype == np.uint8

    def test_raises_on_missing(self, tmp_path):
        with pytest.raises(DecodingError):
            read_image(tmp_path / "nope.png")

    def test_raises_on_corrupt(self, tmp_path):
        bad = tmp_path / "corrupt.png"
        bad.write_bytes(b"not an image")
        with pytest.raises(DecodingError):
            read_image(bad)


class TestWritePng:
    def test_roundtrip(self, tmp_path):
        gray = np.random.randint(0, 255, (8, 8), dtype=np.uint8)
        path = tmp_path / "out.png"
        write_png(path, gray)
        assert path.exists()
        # Verify it's a valid PNG
        img = Image.open(path)
        assert img.size == (8, 8)


class TestWriteGeoTIFF:
    def test_writes_valid_tif(self, tmp_path):
        rgb = np.random.randint(0, 255, (8, 8, 3), dtype=np.uint8)
        from rasterio.transform import Affine
        transform = Affine.translation(0.0, 0.0)

        path = tmp_path / "out.tif"
        write_geotiff(path, rgb, transform, "EPSG:4326")
        assert path.exists()

        import rasterio
        with rasterio.open(path) as src:
            assert src.count == 3
            assert src.width == 8
            assert src.height == 8

    def test_rejects_non_3d(self, tmp_path):
        gray = np.zeros((8, 8), dtype=np.uint8)
        from rasterio.transform import Affine
        with pytest.raises(ValueError):
            write_geotiff(tmp_path / "bad.tif", gray, Affine.identity(), None)
