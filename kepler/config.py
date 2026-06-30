"""Centralized configuration — one source of truth for all tunables.

All values default to the original prototype behavior but can be overridden
via environment variables (prefix `KEPLER_`), so the same code runs in dev,
test, and demo environments without editing source.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_bool(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Immutable application configuration.

    Construct via `Settings.from_env()` for normal runs, or `Settings(...)`
    directly in tests for deterministic setup.
    """

    base_dir: Path
    upload_dir: Path
    results_dir: Path
    allowed_extensions: frozenset[str]
    geotiff_extensions: frozenset[str]
    max_file_size: int            # bytes
    retention_hours: int | None   # None disables auto-purge
    mock_delay_seconds: float
    host: str
    port: int
    debug: bool
    test_mode: bool = field(default=False, repr=False)

    # ---- constructors ----
    @classmethod
    def from_env(cls, base_dir: Path | None = None) -> "Settings":
        base = base_dir or Path(__file__).resolve().parent.parent
        return cls(
            base_dir=base,
            upload_dir=base / _env_str("KEPLER_UPLOAD_DIR", "uploads"),
            results_dir=base / _env_str("KEPLER_RESULTS_DIR", "static/results"),
            allowed_extensions=frozenset({".tif", ".tiff"}),
            geotiff_extensions=frozenset({".tif", ".tiff"}),
            max_file_size=_env_int("KEPLER_MAX_FILE_SIZE", 50 * 1024 * 1024),
            retention_hours=_env_int("KEPLER_RETENTION_HOURS", 24),
            mock_delay_seconds=float(_env_str("KEPLER_MOCK_DELAY", "2.5")),
            host=_env_str("KEPLER_HOST", "127.0.0.1"),
            port=_env_int("KEPLER_PORT", 5000),
            debug=_env_bool("KEPLER_DEBUG", True),
        )

    @classmethod
    def for_test(cls, tmp_root: Path) -> "Settings":
        """Isolated config pointing at temp dirs — no writes to the real project."""
        return cls(
            base_dir=tmp_root,
            upload_dir=tmp_root / "uploads",
            results_dir=tmp_root / "results",
            allowed_extensions=frozenset({".tif", ".tiff"}),
            geotiff_extensions=frozenset({".tif", ".tiff"}),
            max_file_size=50 * 1024 * 1024,
            retention_hours=None,            # never purge during tests
            mock_delay_seconds=0.0,          # no artificial latency in tests
            host="127.0.0.1",
            port=5000,
            debug=False,
            test_mode=True,
        )

    # ---- helpers ----
    def is_geotiff(self, filename: str) -> bool:
        return Path(filename).suffix.lower() in self.geotiff_extensions

    def is_allowed(self, filename: str) -> bool:
        return Path(filename).suffix.lower() in self.allowed_extensions

    def ensure_dirs(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
