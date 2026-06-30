"""Command-line interface — run the pipeline headless or launch the web server.

Usage:
    python -m kepler serve [--port 5000]              # start web server
    python -m kepler infer <file> [--out DIR]         # process one file
    python -m kepler batch <dir> [--out DIR]          # process a folder
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Settings
from .logging_setup import configure_logging, get_logger


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="kepler",
        description="Kepler-404: TIR Super-Resolution & Colorization",
    )
    sub = parser.add_subparsers(dest="command")

    # serve
    serve_p = sub.add_parser("serve", help="Start the Flask web server")
    serve_p.add_argument("--port", type=int, default=5000)
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--debug", action="store_true", default=True)

    # infer (single file)
    infer_p = sub.add_parser("infer", help="Process a single file headless")
    infer_p.add_argument("path", type=Path, help="Path to .tif / .png / .jpg")
    infer_p.add_argument("--out", type=Path, default=None, help="Output directory (default: static/results/)")

    # batch (folder)
    batch_p = sub.add_parser("batch", help="Process all images in a folder")
    batch_p.add_argument("dir", type=Path, help="Directory containing images")
    batch_p.add_argument("--out", type=Path, default=None, help="Output directory (default: static/results/)")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    configure_logging()

    if args.command == "serve":
        _cmd_serve(args)
    elif args.command == "infer":
        _cmd_infer(args)
    elif args.command == "batch":
        _cmd_batch(args)


def _cmd_serve(args: argparse.Namespace) -> None:
    settings = Settings.from_env()
    # Allow CLI flags to override env
    settings = Settings(
        base_dir=settings.base_dir,
        upload_dir=settings.upload_dir,
        results_dir=settings.results_dir,
        allowed_extensions=settings.allowed_extensions,
        geotiff_extensions=settings.geotiff_extensions,
        max_file_size=settings.max_file_size,
        retention_hours=settings.retention_hours,
        mock_delay_seconds=settings.mock_delay_seconds,
        host=args.host,
        port=args.port,
        debug=args.debug,
    )

    from .app import create_app
    app = create_app(settings)
    log = get_logger("cli")
    log.info(f"starting server at http://{settings.host}:{settings.port}")
    app.run(host=settings.host, port=settings.port, debug=settings.debug)


def _cmd_infer(args: argparse.Namespace) -> None:
    settings = Settings.from_env()
    if args.out:
        settings = _with_out_dir(settings, args.out)

    from .pipeline import Pipeline
    pipeline = Pipeline(settings)
    logger = get_logger("cli")

    path = args.path.resolve()
    if not path.exists():
        logger.error(f"file not found: {path}")
        sys.exit(1)
    if not settings.is_allowed(path.name):
        logger.error(f"unsupported extension: {path.name}")
        sys.exit(1)

    logger.info(f"processing: {path.name}")
    result = pipeline.run(path)
    logger.info(f"input   -> {result.images.input}")
    logger.info(f"sr      -> {result.images.sr}")
    logger.info(f"color   -> {result.images.colorized}")
    if result.download_tif:
        logger.info(f"tif     -> {result.download_tif}")
    logger.info(f"elapsed: {result.meta.elapsed}s")
    print(f"\n✓ {path.name} → {result.meta.output_size} processed in {result.meta.elapsed}s")


def _cmd_batch(args: argparse.Namespace) -> None:
    settings = Settings.from_env()
    if args.out:
        settings = _with_out_dir(settings, args.out)

    from .pipeline import Pipeline
    pipeline = Pipeline(settings)
    logger = get_logger("cli")

    folder = args.dir.resolve()
    if not folder.is_dir():
        logger.error(f"not a directory: {folder}")
        sys.exit(1)

    files = sorted(f for f in folder.iterdir() if f.is_file() and settings.is_allowed(f.name))
    if not files:
        logger.error(f"no supported files in {folder}")
        sys.exit(1)

    logger.info(f"batch: {len(files)} file(s) in {folder}")
    for i, f in enumerate(files, 1):
        logger.info(f"[{i}/{len(files)}] {f.name}")
        try:
            result = pipeline.run(f)
            print(f"  ✓ {f.name} → {result.meta.output_size} ({result.meta.elapsed}s)")
        except Exception as exc:
            logger.error(f"  ✗ {f.name}: {exc}")
            print(f"  ✗ {f.name}: {exc}")

    print(f"\nBatch complete: {len(files)} file(s) processed")


def _with_out_dir(settings: Settings, out: Path) -> Settings:
    """Return a new Settings with results_dir redirected."""
    out = out.resolve()
    return Settings(
        base_dir=settings.base_dir,
        upload_dir=settings.upload_dir,
        results_dir=out,
        allowed_extensions=settings.allowed_extensions,
        geotiff_extensions=settings.geotiff_extensions,
        max_file_size=settings.max_file_size,
        retention_hours=None,
        mock_delay_seconds=settings.mock_delay_seconds,
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
    )
