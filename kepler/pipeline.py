"""Pipeline orchestrator.

`Pipeline.run(path, job_id)` is the single entry point for processing a file
end-to-end. It branches on GeoTIFF vs Image, logs each stage, and returns a
fully populated `InferenceResult` whose `.to_dict()` matches the frontend contract.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import cv2
import numpy as np
from rasterio.transform import Affine

from .config import Settings
from .exceptions import DecodingError, ProcessingError
from .io import (
    normalize_to_uint8,
    read_geotiff,
    read_image,
    write_geotiff,
    write_png,
)
from .logging_setup import get_logger
from .models import FileType, ImageSet, InferenceResult, JobMeta
from .transforms import colorize, super_resolve


class Pipeline:
    """Stateless-ish inference pipeline bound to a `Settings` instance."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        settings.ensure_dirs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, input_path: Path, job_id: str | None = None) -> InferenceResult:
        """Process one file. Raises KeplerError subclasses on failure."""
        if job_id is None:
            job_id = uuid.uuid4().hex

        short_id = job_id[:8] if len(job_id) >= 8 else job_id
        log = get_logger("pipeline")
        log.info(f"[{short_id}] ingest: {input_path.name}")

        is_geo = self.settings.is_geotiff(input_path.name)
        start = time.perf_counter()

        try:
            if is_geo:
                result = self._process_geotiff(input_path, job_id, log)
            else:
                result = self._process_image(input_path, job_id, log)
        except (DecodingError, ProcessingError):
            raise
        except Exception as exc:
            # Wrap anything unexpected so routes return a clean 500
            raise ProcessingError(f"Pipeline failure: {exc}") from exc

        elapsed = round(time.perf_counter() - start, 1)
        # Patch elapsed (delay may have run inside) — recompute honestly
        result.meta.elapsed = elapsed
        log.info(f"[{short_id}] complete: {elapsed}s total")
        return result

    # ------------------------------------------------------------------
    # GeoTIFF path — full geospatial treatment
    # ------------------------------------------------------------------
    def _process_geotiff(
        self, path: Path, job_id: str, log
    ) -> InferenceResult:
        short_id = job_id[:8] if len(job_id) >= 8 else job_id
        geo = read_geotiff(path)
        gray = normalize_to_uint8(geo.band)
        crs_label = str(geo.crs) if geo.crs else "Unknown"
        log.info(f"[{short_id}] ingest: GeoTIFF {geo.width}x{geo.height} (CRS {crs_label})")

        stages = self._shared_stages(gray, job_id, log)
        sr_gray, colorized_bgr, input_png, sr_png, colorized_png = stages

        new_h, new_w = sr_gray.shape
        new_transform = geo.transform * Affine.scale(
            geo.width / new_w, geo.height / new_h
        )
        colorized_rgb = cv2.cvtColor(colorized_bgr, cv2.COLOR_BGR2RGB)
        tif_path = self.settings.results_dir / f"{job_id}_colorized.tif"
        write_geotiff(tif_path, colorized_rgb, geo.transform, geo.crs, new_transform)
        log.info(f"[{short_id}] export: georeferenced GeoTIFF written ({new_w}x{new_h})")

        return InferenceResult(
            job_id=job_id,
            images=ImageSet(
                input=self._url(input_png),
                sr=self._url(sr_png),
                colorized=self._url(colorized_png),
            ),
            download_png=self._download_url(input_png.parent, f"{job_id}_colorized.png"),
            download_tif=self._download_url(tif_path.parent, f"{job_id}_colorized.tif"),
            meta=JobMeta(
                job_id=job_id,
                input_size=f"{geo.width}×{geo.height}",
                output_size=f"{new_w}×{new_h}",
                crs=crs_label,
                elapsed=0.0,
                file_type=FileType.GEOTIFF,
            ),
        )

    # ------------------------------------------------------------------
    # Image path — no georeferencing possible
    # ------------------------------------------------------------------
    def _process_image(self, path: Path, job_id: str, log) -> InferenceResult:
        short_id = job_id[:8] if len(job_id) >= 8 else job_id
        gray = read_image(path)
        h, w = gray.shape[:2]
        log.info(f"[{short_id}] ingest: Image {w}x{h} (no CRS)")

        stages = self._shared_stages(gray, job_id, log)
        sr_gray, colorized_bgr, input_png, sr_png, colorized_png = stages

        new_h, new_w = sr_gray.shape
        log.info(f"[{short_id}] export: PNG outputs written ({new_w}x{new_h}), no GeoTIFF (no CRS)")

        return InferenceResult(
            job_id=job_id,
            images=ImageSet(
                input=self._url(input_png),
                sr=self._url(sr_png),
                colorized=self._url(colorized_png),
            ),
            download_png=self._download_url(colorized_png.parent, f"{job_id}_colorized.png"),
            download_tif=None,   # plain image — no georeferencing
            meta=JobMeta(
                job_id=job_id,
                input_size=f"{w}×{h}",
                output_size=f"{new_w}×{new_h}",
                crs="Unknown",
                elapsed=0.0,
                file_type=FileType.IMAGE,
            ),
        )

    # ------------------------------------------------------------------
    # Shared stages (used by both paths)
    # ------------------------------------------------------------------
    def _shared_stages(
        self, gray: np.ndarray, job_id: str, log
    ) -> tuple[np.ndarray, np.ndarray, Path, Path, Path]:
        """Run SR + colorize + write PNGs. Returns (sr, colorized, 3 paths)."""
        short_id = job_id[:8] if len(job_id) >= 8 else job_id
        # Optional artificial latency (disabled in tests)
        if self.settings.mock_delay_seconds > 0:
            time.sleep(self.settings.mock_delay_seconds)

        input_png = self.settings.results_dir / f"{job_id}_input.png"
        write_png(input_png, gray)

        t0 = time.perf_counter()
        sr_gray = super_resolve(gray)
        log.info(f"[{short_id}] super-resolve: {gray.shape[1]}x{gray.shape[0]} -> {sr_gray.shape[1]}x{sr_gray.shape[0]} in {time.perf_counter()-t0:.2f}s")

        sr_png = self.settings.results_dir / f"{job_id}_sr.png"
        write_png(sr_png, sr_gray)

        t0 = time.perf_counter()
        colorized_bgr = colorize(sr_gray)
        log.info(f"[{short_id}] colorize: {sr_gray.shape[1]}x{sr_gray.shape[0]} -> 3-channel in {time.perf_counter()-t0:.2f}s")

        colorized_png = self.settings.results_dir / f"{job_id}_colorized.png"
        write_png(colorized_png, colorized_bgr)

        return sr_gray, colorized_bgr, input_png, sr_png, colorized_png

    # ------------------------------------------------------------------
    # URL helpers — relative paths the frontend can request
    # ------------------------------------------------------------------
    def _url(self, path: Path) -> str:
        """Convert an absolute results path to a /static/results/... URL."""
        try:
            rel = path.relative_to(self.settings.results_dir)
        except ValueError:
            rel = Path(path.name)
        return f"/static/results/{rel.as_posix()}"

    def _download_url(self, _dir: Path, filename: str) -> str:
        return f"/api/download/{filename}"
