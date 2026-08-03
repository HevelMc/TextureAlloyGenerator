"""256-entry LUT cache for materials."""

from __future__ import annotations

import numpy as np

from texture_alloy.transform.grey import PaletteStop, build_grey_lut


def stops_to_lut_array(stops: list[PaletteStop]) -> np.ndarray:
    """Build uint8 array shape (256, 4) in RGBA order."""
    lut = build_grey_lut(stops)
    return np.array(lut, dtype=np.uint8)


class LutCache:
    def __init__(self) -> None:
        self._cache: dict[str, np.ndarray] = {}

    def get(self, key: str, stops: list[PaletteStop]) -> np.ndarray:
        if key not in self._cache:
            self._cache[key] = stops_to_lut_array(stops)
        return self._cache[key]

    def set(self, key: str, lut: np.ndarray) -> None:
        self._cache[key] = lut
