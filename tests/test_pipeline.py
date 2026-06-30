"""Tests for kepler.pipeline — end-to-end orchestration."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from kepler.models import FileType, InferenceResult
from tests.conftest import make_geotiff, make_png


class TestPipelineGeoTIFF:
    def test_geotiff_returns_full_result(self, pipeline, tmp_path):
        tif = make_geotiff(tmp_path / "scene.tif", 16, 16)
        result = pipeline.run(tif)
        assert isinstance(result, InferenceResult)
        assert result.meta.file_type == FileType.GEOTIFF
        assert result.download_tif is not None
        assert "input.png" in result.images.input
        assert "sr.png" in result.images.sr
        assert "colorized.png" in result.images.colorized

    def test_geotiff_preserves_crs(self, pipeline, tmp_path):
        tif = make_geotiff(tmp_path / "scene.tif", 8, 8)
        result = pipeline.run(tif)
        assert result.meta.crs != "Unknown"

    def test_geotiff_output_doubled(self, pipeline, tmp_path):
        tif = make_geotiff(tmp_path / "scene.tif", 12, 12)
        result = pipeline.run(tif)
        assert result.meta.input_size == "12×12"
        assert result.meta.output_size == "24×24"

    def test_geotiff_writes_all_files(self, pipeline, tmp_path):
        tif = make_geotiff(tmp_path / "scene.tif", 8, 8)
        result = pipeline.run(tif)
        base = pipeline.settings.results_dir
        assert (base / f"{result.job_id}_input.png").exists()
        assert (base / f"{result.job_id}_sr.png").exists()
        assert (base / f"{result.job_id}_colorized.png").exists()
        assert (base / f"{result.job_id}_colorized.tif").exists()

    def test_to_dict_matches_frontend_contract(self, pipeline, tmp_path):
        tif = make_geotiff(tmp_path / "scene.tif", 8, 8)
        d = pipeline.run(tif).to_dict()
        assert d["success"] is True
        assert "input" in d["images"]
        assert "sr" in d["images"]
        assert "colorized" in d["images"]
        assert "download" in d
        assert "download_tif" in d
        assert "meta" in d
        assert d["meta"]["file_type"] == "GeoTIFF"


class TestPipelineImage:
    def test_image_returns_result_no_tif(self, pipeline, tmp_path):
        png = make_png(tmp_path / "photo.png", 16, 16)
        result = pipeline.run(png)
        assert result.meta.file_type == FileType.IMAGE
        assert result.download_tif is None

    def test_image_output_doubled(self, pipeline, tmp_path):
        png = make_png(tmp_path / "photo.png", 10, 20)
        result = pipeline.run(png)
        assert result.meta.input_size == "10×20"
        assert result.meta.output_size == "20×40"

    def test_image_no_crs(self, pipeline, tmp_path):
        png = make_png(tmp_path / "photo.png", 8, 8)
        result = pipeline.run(png)
        assert result.meta.crs == "Unknown"

    def test_jpeg_works(self, pipeline, tmp_path):
        make_png(tmp_path / "photo.jpg", 8, 8, color=True)
        result = pipeline.run(tmp_path / "photo.jpg")
        assert result.meta.file_type == FileType.IMAGE


class TestPipelineErrors:
    def test_missing_file_raises(self, pipeline, tmp_path):
        from kepler.exceptions import DecodingError
        with pytest.raises(DecodingError):
            pipeline.run(tmp_path / "nonexistent.tif")

    def test_corrupt_file_raises(self, pipeline, tmp_path):
        from kepler.exceptions import DecodingError
        bad = tmp_path / "garbage.tif"
        bad.write_bytes(b"not a real file")
        with pytest.raises(DecodingError):
            pipeline.run(bad)
