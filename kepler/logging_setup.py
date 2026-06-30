"""Structured logging — one clear line per stage, with job context.

Replaces the prototype's silent operation. A sample run produces:

    2026-06-29 14:02:11 | INFO  | kepler.pipeline | [a1b2c3d4] ingest: GeoTIFF 256x256 (CRS EPSG:32643)
    2026-06-29 14:02:11 | INFO  | kepler.pipeline | [a1b2c3d4] super-resolve: 256x256 -> 512x512 in 0.31s
    2026-06-29 14:02:11 | INFO  | kepler.pipeline | [a1b2c3d4] colorize: 512x512 -> 3-channel in 0.04s
    2026-06-29 14:02:11 | INFO  | kepler.pipeline | [a1b2c3d4] export: wrote 4 files in 0.12s
    2026-06-29 14:02:11 | INFO  | kepler.pipeline | [a1b2c3d4] complete: 2.78s total
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotent logging setup. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger("kepler")
    root.setLevel(level)
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'kepler' namespace."""
    if not name.startswith("kepler"):
        name = f"kepler.{name}"
    return logging.getLogger(name)


def reset_for_tests() -> None:
    """Reset the configured flag so tests can reconfigure cleanly."""
    global _CONFIGURED
    _CONFIGURED = False
    for name, logger in list(logging.Logger.manager.loggerDict.items()):
        if isinstance(logger, logging.Logger) and name.startswith("kepler"):
            logger.handlers.clear()
