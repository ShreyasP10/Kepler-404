"""Transformation layer — the mock "AI" functions.

These pure functions mirror the contract of the real generative models
(ESRGAN/SwinIR for super-resolution, Pix2Pix/Diffusion for colorization)
so swapping in trained checkpoints is a localized change.

Drop-in target signatures stay identical:
    super_resolve(gray: np.ndarray) -> np.ndarray   # 2x upscale
    colorize(gray: np.ndarray) -> np.ndarray         # thermal -> RGB (BGR order)
"""

from __future__ import annotations

import cv2
import numpy as np


def super_resolve(gray: np.ndarray, scale: int = 2) -> np.ndarray:
    """Mock 2x super-resolution via bicubic interpolation.

    Replace with ESRGAN/SwinIR forward pass when checkpoints are available:

        import torch
        t = torch.from_numpy(gray).float().div(255)[None, None].to(device)
        with torch.no_grad():
            out = _sr_model(t)
        return (out.squeeze().cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    """
    if gray.ndim != 2:
        raise ValueError(f"super_resolve expects a 2D grayscale array, got {gray.shape}")
    h, w = gray.shape
    return cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)


def colorize(gray: np.ndarray) -> np.ndarray:
    """Mock thermal->RGB mapping using the Inferno colormap.

    Returns a BGR uint8 array (OpenCV convention) for direct cv2.imwrite.

    Replace with Pix2Pix/Diffusion forward pass when checkpoints are available:

        rgb = _color_model(t).squeeze().permute(1, 2, 0).cpu().numpy()
        return cv2.cvtColor((rgb * 255).clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    """
    if gray.ndim != 2:
        raise ValueError(f"colorize expects a 2D grayscale array, got {gray.shape}")
    return cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
