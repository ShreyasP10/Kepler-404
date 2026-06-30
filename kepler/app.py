"""Flask application factory.

`create_app(settings)` builds the app — used by both the web server and the
test suite. The root `app.py` entry point calls this with `Settings.from_env()`.
"""

from __future__ import annotations

import time
from pathlib import Path

from flask import Flask, render_template, send_from_directory

from .config import Settings
from .logging_setup import configure_logging, get_logger
from .pipeline import Pipeline
from .routes import bp, register_error_handlers

log = get_logger("app")


def purge_stale(directory: Path, retention_hours: int) -> None:
    """Delete files older than *retention_hours*. Runs once at startup."""
    if retention_hours is None or retention_hours <= 0:
        return
    cutoff = time.time() - retention_hours * 3600
    removed = 0
    for f in directory.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
                removed += 1
        except OSError:
            pass
    if removed:
        log.info(f"purged {removed} stale files from {directory}")


def create_app(settings: Settings | None = None) -> Flask:
    """Build and return a fully configured Flask application.

    Args:
        settings: Use `Settings.from_env()` by default, or inject a custom
                  instance (e.g. `Settings.for_test(tmp)` for testing).
    """
    if settings is None:
        settings = Settings.from_env()

    configure_logging()

    # --- Flask app ---
    app = Flask(
        __name__,
        template_folder=settings.base_dir / "templates",
        static_folder=settings.base_dir / "static",
    )
    app.config["KEPLER_SETTINGS"] = settings
    app.config["KEPLER_PIPELINE"] = Pipeline(settings)

    # --- Startup cleanup ---
    settings.ensure_dirs()
    if settings.retention_hours:
        purge_stale(settings.upload_dir, settings.retention_hours)
        purge_stale(settings.results_dir, settings.retention_hours)

    # --- Blueprint + error handler ---
    app.register_blueprint(bp)
    register_error_handlers(app)

    # --- Static file passthrough ---
    @app.route("/")
    def index():
        return render_template("index.html")

    return app
