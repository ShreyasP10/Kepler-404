"""Flask routes — thin controllers that delegate to the Pipeline.

All error mapping lives in one `register_error_handlers` function so every
route stays ~10 lines and impossible to silently swallow exceptions.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory

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
                "error": "Invalid file format. Please upload a .tif, .tiff, .png, .jpg, or .jpeg file.",
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
# GET /api/download/<filename>
# ---------------------------------------------------------------------------
@bp.route("/download/<filename>")
def download(filename: str):
    settings: Settings = current_app.config["KEPLER_SETTINGS"]
    safe = Path(filename).name
    if not safe.endswith((".png", ".tif", ".tiff")):
        return jsonify({"success": False, "error": "Invalid download request."}), 400

    path = settings.results_dir / safe
    if not path.exists():
        return jsonify({"success": False, "error": "File not found."}), 404

    return send_from_directory(settings.results_dir, safe, as_attachment=True)
