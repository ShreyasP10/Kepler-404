import os
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
import rasterio
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from rasterio.transform import Affine

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "static" / "results"

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}
GEOTIFF_EXTENSIONS = {".tif", ".tiff"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MOCK_DELAY_SECONDS = 2.5
# Retention for uploaded + result files (hours). Keeps files around long enough
# to inspect during a live demo, then auto-cleans. Set to None to disable.
RETENTION_HOURS = 24

app = Flask(__name__)
CORS(app)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def purge_stale(directory: Path) -> None:
    """Delete files older than RETENTION_HOURS (skip during tests)."""
    if not RETENTION_HOURS:
        return
    cutoff = time.time() - RETENTION_HOURS * 3600
    for f in directory.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
        except OSError:
            pass


# Run cleanup at module load so it triggers on every server start (including
# debug reloader restarts). Safe across all Flask versions.
purge_stale(UPLOAD_DIR)
purge_stale(RESULTS_DIR)


def normalize_to_uint8(array: np.ndarray) -> np.ndarray:
    """Stretch an arbitrary array to 0–255 via robust percentile clipping."""
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


def super_resolve(gray: np.ndarray) -> np.ndarray:
    """Mock 2× super-resolution. Swap for ESRGAN/SwinIR when available."""
    h, w = gray.shape[:2]
    return cv2.resize(gray, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)


def colorize(gray: np.ndarray) -> np.ndarray:
    """Mock thermal→RGB mapping (Inferno colormap). Swap for Pix2Pix/Diffusion."""
    return cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)


# ---------------------------------------------------------------------------
# Inference pipeline
# ---------------------------------------------------------------------------
def run_inference(input_path: Path, job_id: str) -> dict:
    """
    Process an uploaded file end-to-end.

    GeoTIFFs (.tif/.tiff) go through rasterio and produce a georeferenced
    colorized GeoTIFF. Plain images (.png/.jpg) take an OpenCV-only path
    (no CRS/transform available) and skip the GeoTIFF export.
    """
    start = time.time()
    time.sleep(MOCK_DELAY_SECONDS)

    suffix = input_path.suffix.lower()
    is_geo = suffix in GEOTIFF_EXTENSIONS

    crs_label = "Unknown"
    orig_width = orig_height = 0
    src_transform = None
    band = None

    if is_geo:
        with rasterio.open(input_path) as src:
            band = src.read(1)
            src_transform = src.transform
            crs = src.crs
            orig_width = src.width
            orig_height = src.height
            crs_label = str(crs) if crs else "Unknown"
        input_gray = normalize_to_uint8(band)
    else:
        # Standard image: read as-is. If color, convert to luminance.
        raw = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
        if raw is None:
            raise ValueError("Could not decode the uploaded image.")
        if raw.ndim == 3:
            raw = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        input_gray = raw.astype(np.uint8)
        orig_height, orig_width = input_gray.shape

    # --- Stage outputs ---
    input_png_path = RESULTS_DIR / f"{job_id}_input.png"
    cv2.imwrite(str(input_png_path), input_gray)

    sr_gray = super_resolve(input_gray)
    sr_png_path = RESULTS_DIR / f"{job_id}_sr.png"
    cv2.imwrite(str(sr_png_path), sr_gray)

    colorized_bgr = colorize(sr_gray)
    colorized_png_path = RESULTS_DIR / f"{job_id}_colorized.png"
    cv2.imwrite(str(colorized_png_path), colorized_bgr)

    new_height, new_width = sr_gray.shape
    result = {
        "input": f"/static/results/{job_id}_input.png",
        "sr": f"/static/results/{job_id}_sr.png",
        "colorized": f"/static/results/{job_id}_colorized.png",
        "download_png": f"/api/download/{job_id}_colorized.png",
        "meta": {
            "job_id": job_id,
            "input_size": f"{orig_width}×{orig_height}",
            "output_size": f"{new_width}×{new_height}",
            "crs": crs_label,
            "elapsed": round(time.time() - start, 1),
            "file_type": "GeoTIFF" if is_geo else "Image",
        },
    }

    # --- Geospatial export (GeoTIFF only) ---
    if is_geo and src_transform is not None:
        colorized_rgb = cv2.cvtColor(colorized_bgr, cv2.COLOR_BGR2RGB)
        colorized_tif_path = RESULTS_DIR / f"{job_id}_colorized.tif"
        new_transform = src_transform * Affine.scale(
            orig_width / new_width,
            orig_height / new_height,
        )
        tif_profile = {
            "driver": "GTiff",
            "height": new_height,
            "width": new_width,
            "count": 3,
            "dtype": "uint8",
            "transform": new_transform,
            "crs": crs_label if crs_label != "Unknown" else None,
            "photometric": "RGB",
        }
        with rasterio.open(colorized_tif_path, "w", **tif_profile) as dst:
            for i in range(3):
                dst.write(colorized_rgb[:, :, i], i + 1)
        result["download_tif"] = f"/api/download/{job_id}_colorized.tif"
    else:
        # No georeferencing possible for a plain image.
        result["download_tif"] = None

    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/infer", methods=["POST"])
def infer():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Invalid file format. Please upload a .tif, .tiff, .png, .jpg, or .jpeg file.",
                }
            ),
            415,
        )

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size == 0:
        return jsonify({"success": False, "error": "Uploaded file is empty."}), 400
    if size > MAX_FILE_SIZE:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "File too large. Maximum allowed size is 50 MB.",
                }
            ),
            400,
        )

    job_id = uuid.uuid4().hex
    upload_path = UPLOAD_DIR / f"{job_id}{Path(file.filename).suffix.lower()}"

    try:
        file.save(upload_path)
        outputs = run_inference(upload_path, job_id)
        return jsonify(
            {
                "success": True,
                "images": {
                    "input": outputs["input"],
                    "sr": outputs["sr"],
                    "colorized": outputs["colorized"],
                },
                "download": outputs["download_png"],
                "download_tif": outputs["download_tif"],
                "meta": outputs["meta"],
            }
        )
    except Exception as exc:
        return (
            jsonify({"success": False, "error": f"Inference failed: {exc}"}),
            500,
        )
    # NOTE: uploads/results are intentionally retained for RETENTION_HOURS so
    # they can be inspected live during a demo. The 24h purge runs at startup.


@app.route("/api/download/<filename>")
def download(filename):
    safe_name = Path(filename).name
    if not safe_name.endswith((".png", ".tif", ".tiff")):
        return jsonify({"success": False, "error": "Invalid download request."}), 400

    file_path = RESULTS_DIR / safe_name
    if not file_path.exists():
        return jsonify({"success": False, "error": "File not found."}), 404

    return send_from_directory(RESULTS_DIR, safe_name, as_attachment=True)


if __name__ == "__main__":
    # debug=True for the hackathon: live reload on code/HTML/CSS/JS edits.
    app.run(host="127.0.0.1", port=5000, debug=True)
