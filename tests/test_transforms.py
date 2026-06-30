"""Tests for kepler.transforms — super_resolve + colorize."""

from __future__ import annotations

import numpy as np
import pytest

from kepler.transforms import colorize, super_resolve


class TestSuperResolve:
    def test_doubles_dimensions(self):
        gray = np.random.randint(0, 255, (16, 32), dtype=np.uint8)
        out = super_resolve(gray)
        assert out.shape == (32, 64)
        assert out.dtype == np.uint8

    def test_default_scale(self):
        gray = np.zeros((10, 10), dtype=np.uint8)
        out = super_resolve(gray)
        assert out.shape == (20, 20)

    def test_custom_scale(self):
        gray = np.zeros((8, 8), dtype=np.uint8)
        out = super_resolve(gray, scale=4)
        assert out.shape == (32, 32)

    def test_rejects_3d(self):
        rgb = np.zeros((8, 8, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            super_resolve(rgb)


class TestColorize:
    def test_returns_3d_bgr(self):
        gray = np.random.randint(0, 255, (16, 16), dtype=np.uint8)
        out = colorize(gray)
        assert out.ndim == 3
        assert out.shape[2] == 3
        assert out.dtype == np.uint8

    def test_preserves_size(self):
        gray = np.zeros((10, 20), dtype=np.uint8)
        out = colorize(gray)
        assert out.shape[:2] == (10, 20)

    def test_rejects_3d(self):
        rgb = np.zeros((8, 8, 3), dtype=np.uint8)
        with pytest.raises(ValueError):
            colorize(rgb)
