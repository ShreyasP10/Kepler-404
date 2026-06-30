"""Flask routes — thin controllers that delegate to the Pipeline.

All error mapping lives in one `register_error_handlers` function so every
route stays ~10 lines and impossible to silently swallow exceptions.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import numpy as np
import rasterio
from flask import Blueprint, current_app, jsonify, request, send_from_directory
from rasterio.crs import CRS
from rasterio.transform import from_bounds

from .config import Settings
from .exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidFileError,
    KeplerError,
)
from .logging_setup import get_logger
from .pipeline import Pipeline

log = get_logger("routes")

bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------------------
# Error handler — one place for all KeplerError → JSON
# ---------------------------------------------------------------------------
def register_error_handlers(app) -> None:
    @app.errorhandler(KeplerError)
    def handle_kepler_error(exc: KeplerError):
        log.warning(f"{exc.__class__.__name__}: {exc.message}")
        return jsonify({"success": False, "error": exc.message}), exc.status_code


# ---------------------------------------------------------------------------
# POST /api/infer
# ---------------------------------------------------------------------------
@bp.route("/infer", methods=["POST"])
def infer():
    settings: Settings = current_app.config["KEPLER_SETTINGS"]
    pipeline: Pipeline = current_app.config["KEPLER_PIPELINE"]

    # --- File presence ---
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file selected."}), 400

    # --- Extension validation ---
    if not settings.is_allowed(file.filename):
        return jsonify(
            {
                "success": False,
                "error": "Invalid file format. Please upload a .tif or .tiff (GeoTIFF) file.",
            }
        ), 415

    # --- Size validation ---
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size == 0:
        return jsonify({"success": False, "error": "Uploaded file is empty."}), 400
    if size > settings.max_file_size:
        return jsonify(
            {
                "success": False,
                "error": "File too large. Maximum allowed size is 50 MB.",
            }
        ), 400

    # --- Run pipeline ---
    job_id = uuid.uuid4().hex
    upload_path = settings.upload_dir / f"{job_id}{Path(file.filename).suffix.lower()}"

    file.save(upload_path)
    log.info(f"upload saved: {upload_path.name} ({size} bytes, job {job_id[:8]})")

    try:
        result = pipeline.run(upload_path, job_id)
        return jsonify(result.to_dict())
    except KeplerError:
        raise
    except Exception as exc:
        return jsonify({"success": False, "error": f"Inference failed: {exc}"}), 500


# ---------------------------------------------------------------------------
# GET /api/sample/<seed>  — generate a synthetic GeoTIFF & run inference
# ---------------------------------------------------------------------------
@bp.route("/sample/<seed>")
def sample(seed: str):
    settings: Settings = current_app.config["KEPLER_SETTINGS"]
    pipeline: Pipeline = current_app.config["KEPLER_PIPELINE"]

    job_id = uuid.uuid4().hex
    tif_path = settings.upload_dir / f"{job_id}.tif"
    rng = np.random.default_rng(abs(hash(seed)) % (2**31))

    width, height = 256, 256
    band = rng.integers(40, 200, size=(height, width), dtype=np.uint8)

    if "urban" in seed:
        # Hot urban clusters
        for _ in range(6):
            cx, cy = rng.integers(30, width - 30, 2)
            band[cy - 20:cy + 20, cx - 20:cx + 20] = rng.integers(210, 255, (40, 40), dtype=np.uint8)
    elif "ocean" in seed:
        # Temperature gradient
        for y in range(height):
            band[y, :] = np.clip(band[y, :].astype(np.int16) + int(80 * y / height), 0, 255).astype(np.uint8)
    elif "volcanic" in seed:
        # Hot center
        cy, cx = height // 2, width // 2
        for y in range(height):
            for x in range(width):
                dist = np.sqrt((x - cx)**2 + (y - cy)**2)
                band[y, x] = np.clip(int(band[y, x]) + int(120 * max(0, 1 - dist / 100)), 0, 255).astype(np.uint8)
    elif "desert" in seed:
        # High base with dune ripples
        band = rng.integers(180, 245, size=(height, width), dtype=np.uint8)
        for y in range(height):
            band[y, :] = np.clip(band[y, :].astype(np.int16) + int(15 * np.sin(y * 0.15)), 0, 255).astype(np.uint8)

    transform = from_bounds(0.0, 0.0, 1.0, 1.0, width, height)
    with rasterio.open(
        tif_path, "w", driver="GTiff", height=height, width=width,
        count=1, dtype="uint8", crs=CRS.from_epsg(4326), transform=transform,
    ) as dst:
        dst.write(band, 1)

    log.info(f"sample generated: {seed} ({job_id[:8]})")
    result = pipeline.run(tif_path, job_id)
    return jsonify(result.to_dict())


# ---------------------------------------------------------------------------
# GET /api/download/<filename>  — only GeoTIFF downloads
# ---------------------------------------------------------------------------
@bp.route("/download/<filename>")
def download(filename: str):
    settings: Settings = current_app.config["KEPLER_SETTINGS"]
    safe = Path(filename).name
    if not safe.endswith((".tif", ".tiff")):
        return jsonify({"success": False, "error": "Invalid download request."}), 400

    path = settings.results_dir / safe
    if not path.exists():
        return jsonify({"success": False, "error": "File not found."}), 404

    return send_from_directory(settings.results_dir, safe, as_attachment=True)
