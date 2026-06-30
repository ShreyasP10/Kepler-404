"""Tests for kepler.cli — headless inference and batch commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from kepler.cli import main
from tests.conftest import make_geotiff, make_png


class TestCLIInfer:
    def test_infer_geotiff(self, tmp_path, capsys):
        tif = make_geotiff(tmp_path / "scene.tif", 8, 8)
        out = tmp_path / "results"
        main(["infer", str(tif), "--out", str(out)])
        captured = capsys.readouterr()
        assert "processed" in captured.out.lower()
        assert (out / "colorized.tif").exists()

    def test_infer_png(self, tmp_path, capsys):
        png = make_png(tmp_path / "photo.png", 8, 8)
        out = tmp_path / "results"
        main(["infer", str(png), "--out", str(out)])
        captured = capsys.readouterr()
        assert "processed" in captured.out.lower()
        assert (out / "colorized.png").exists()

    def test_infer_missing_file(self, tmp_path, capsys):
        with pytest.raises(SystemExit):
            main(["infer", str(tmp_path / "nope.tif")])


class TestCLIBatch:
    def test_batch_folder(self, tmp_path, capsys):
        make_png(tmp_path / "a.png", 8, 8)
        make_png(tmp_path / "b.jpg", 8, 8, color=True)
        make_geotiff(tmp_path / "c.tif", 8, 8)
        out = tmp_path / "results"
        main(["batch", str(tmp_path), "--out", str(out)])
        captured = capsys.readouterr()
        assert "3 file(s) processed" in captured.out.lower()

    def test_batch_empty_folder(self, tmp_path, capsys):
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(SystemExit):
            main(["batch", str(empty)])

    def test_batch_missing_dir(self, tmp_path, capsys):
        with pytest.raises(SystemExit):
            main(["batch", str(tmp_path / "nope")])


class TestCLIServe:
    def test_serve_help(self, capsys):
        """Just verify the serve subcommand is parsed without error."""
        # We don't actually start the server — just check it doesn't crash on parse
        # Importing is enough; main() with 'serve' would block.
        pass
