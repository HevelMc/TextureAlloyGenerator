"""PNG I/O with deterministic encoding."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def load_rgba(path: Path) -> np.ndarray:
    img = Image.open(path).convert("RGBA")
    return np.array(img, dtype=np.uint8)


def save_rgba(path: Path, rgba: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(rgba, mode="RGBA")
    img.save(path, format="PNG", compress_level=6, optimize=False)


def resize_rgba(rgba: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    img = Image.fromarray(rgba, mode="RGBA").resize(size, Image.Resampling.LANCZOS)
    return np.array(img, dtype=np.uint8)


def numpy_to_pil(rgba: np.ndarray) -> Image.Image:
    return Image.fromarray(rgba, mode="RGBA")
