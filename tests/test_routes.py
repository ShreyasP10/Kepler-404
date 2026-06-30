"""Tests for kepler.routes — API integration via Flask test client."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from tests.conftest import make_geotiff


class TestInferEndpoint:
    def _upload_bytes(self, client, filename, content, content_type="image/png"):
        data = {"file": (BytesIO(content), filename, content_type)}
        return client.post("/api/infer", data=data, content_type="multipart/form-data")

    def test_no_file_400(self, client):
        resp = client.post("/api/infer")
        assert resp.status_code == 400
        assert resp.json["success"] is False

    def test_empty_file_400(self, client):
        resp = self._upload_bytes(client, "empty.tif", b"")
        assert resp.status_code == 400
        assert "empty" in resp.json["error"].lower()

    def test_wrong_extension_415(self, client):
        resp = self._upload_bytes(client, "readme.txt", b"hello world", "text/plain")
        assert resp.status_code == 415

    def test_png_success(self, client, tmp_path):
        buf = BytesIO()
        Image.fromarray(np.random.randint(0, 255, (8, 8), dtype=np.uint8), "L").save(buf, "PNG")
        buf.seek(0)
        resp = self._upload_bytes(client, "sample.png", buf.getvalue())
        assert resp.status_code == 200
        data = resp.json
        assert data["success"] is True
        assert "input" in data["images"]
        assert "sr" in data["images"]
        assert "colorized" in data["images"]
        assert data["download_tif"] is None  # no CRS for PNG

    def test_geotiff_success(self, client, tmp_path):
        tif = make_geotiff(tmp_path / "scene.tif", 8, 8)
        with open(tif, "rb") as f:
            resp = self._upload_bytes(client, "scene.tif", f.read(), "image/tiff")
        assert resp.status_code == 200
        data = resp.json
        assert data["success"] is True
        assert data["download_tif"] is not None
        assert data["meta"]["file_type"] == "GeoTIFF"

    def test_jpeg_success(self, client):
        buf = BytesIO()
        Image.fromarray(np.random.randint(0, 255, (8, 8, 3), dtype=np.uint8), "RGB").save(buf, "JPEG")
        buf.seek(0)
        resp = self._upload_bytes(client, "photo.jpg", buf.getvalue(), "image/jpeg")
        assert resp.status_code == 200
        assert resp.json["success"] is True

    def test_contract_keys(self, client, tmp_path):
        """Verify the exact frontend contract: success, images.*, download, download_tif, meta.*"""
        buf = BytesIO()
        Image.fromarray(np.zeros((8, 8), dtype=np.uint8), "L").save(buf, "PNG")
        buf.seek(0)
        resp = self._upload_bytes(client, "sample.png", buf.getvalue())
        d = resp.json
        # Top-level
        assert "success" in d
        assert "images" in d
        assert "download" in d
        assert "download_tif" in d
        assert "meta" in d
        # images
        assert "input" in d["images"]
        assert "sr" in d["images"]
        assert "colorized" in d["images"]
        # meta
        assert "job_id" in d["meta"]
        assert "input_size" in d["meta"]
        assert "output_size" in d["meta"]
        assert "crs" in d["meta"]
        assert "elapsed" in d["meta"]
        assert "file_type" in d["meta"]


class TestDownloadEndpoint:
    def test_download_existing_file(self, client, tmp_path):
        # First infer a file to generate results
        buf = BytesIO()
        from PIL import Image
        Image.fromarray(np.zeros((8, 8), dtype=np.uint8), "L").save(buf, "PNG")
        buf.seek(0)
        data = {"file": (BytesIO(buf.getvalue()), "sample.png", "image/png")}
        resp = client.post("/api/infer", data=data, content_type="multipart/form-data")
        d = resp.json

        # Then download the PNG
        png_name = d["images"]["colorized"].split("/")[-1]
        dl = client.get(f"/api/download/{png_name}")
        assert dl.status_code == 200

    def test_download_nonexistent_404(self, client):
        resp = client.get("/api/download/nope.png")
        assert resp.status_code == 404

    def test_download_bad_ext_400(self, client):
        resp = client.get("/api/download/readme.txt")
        assert resp.status_code == 400

    def test_index_route(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
