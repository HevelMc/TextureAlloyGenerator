"""Vectorized palette application (TC-compatible)."""

from __future__ import annotations

import numpy as np

from texture_alloy.transform.grey import scale_color


def apply_palette_lut(rgba: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """
    Apply a 256-entry RGBA LUT to an HxWx4 uint8 array.

    Matches GreyToColorMapping.mapColor + scaleColor from Tinkers' Construct.
    """
    if rgba.dtype != np.uint8:
        rgba = rgba.astype(np.uint8)

    h, w, _ = rgba.shape
    out = np.zeros_like(rgba)

    alpha = rgba[:, :, 3]
    transparent = alpha == 0
    if transparent.all():
        return out

    rgb = rgba[:, :, :3].astype(np.int32)
    grey = rgb.max(axis=2)

    mapped = lut[grey]  # HxWx4 RGBA

    # Vectorized scaleColor for common case (pure grey templates)
    src_a = alpha.astype(np.int32)
    out_a = mapped[:, :, 3].astype(np.int32)
    mask_partial = (src_a < 255) & ~transparent
    out_a[mask_partial] = (out_a[mask_partial] * src_a[mask_partial]) // 255

    for c in range(3):
        src_c = rgb[:, :, c]
        mapped_c = mapped[:, :, c].astype(np.int32)
        out_c = mapped_c.copy()
        needs_scale = (src_c < grey) & (grey > 0) & ~transparent
        out_c[needs_scale] = (mapped_c[needs_scale] * src_c[needs_scale]) // grey[needs_scale]
        out[:, :, c] = out_c.astype(np.uint8)

    out[:, :, 3] = out_a.astype(np.uint8)
    out[transparent] = 0
    return out


def apply_palette_lut_pixel_perfect(rgba: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Fallback per-pixel apply using exact scale_color for edge cases."""
    h, w, _ = rgba.shape
    out = np.zeros_like(rgba)
    for y in range(h):
        for x in range(w):
            r, g, b, a = (int(rgba[y, x, c]) for c in range(4))
            if a == 0:
                continue
            grey = max(r, g, b)
            mr, mg, mb, ma = (int(lut[grey, c]) for c in range(4))
            sr, sg, sb, sa = scale_color((r, g, b, a), (mr, mg, mb, ma), grey)
            out[y, x] = (sr, sg, sb, sa)
    return out
