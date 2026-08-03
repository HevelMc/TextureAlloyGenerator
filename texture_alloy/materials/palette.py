"""Palette-based material (TC grey_to_color)."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from texture_alloy.io.pack import PackContext
from texture_alloy.materials.base import Material
from texture_alloy.transform.apply import apply_palette_lut
from texture_alloy.transform.grey import PaletteStop
from texture_alloy.transform.lut import stops_to_lut_array

# TC standard stops for shorthand palettes
TC_STANDARD_STOPS = [0, 63, 102, 140, 178, 216, 255]


def parse_color(value: str) -> tuple[int, int, int, int]:
    """Parse #RGB, #RRGGBB, #RRGGBBAA, or AARRGGBB hex strings."""
    value = value.strip()
    if value.startswith("#"):
        hex_str = value[1:]
    else:
        hex_str = value

    if len(hex_str) == 8 and not value.startswith("#"):
        # AARRGGBB (TC format)
        a = int(hex_str[0:2], 16)
        r = int(hex_str[2:4], 16)
        g = int(hex_str[4:6], 16)
        b = int(hex_str[6:8], 16)
        return (r, g, b, a)

    if len(hex_str) == 3:
        r = int(hex_str[0] * 2, 16)
        g = int(hex_str[1] * 2, 16)
        b = int(hex_str[2] * 2, 16)
        return (r, g, b, 255)
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[2:4], 16) if len(hex_str) == 4 else int(hex_str[4:6], 16)
        if len(hex_str) == 4:
            pass
        b = int(hex_str[4:6], 16)
        return (r, g, b, 255)
    if len(hex_str) == 8:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        a = int(hex_str[6:8], 16)
        return (r, g, b, a)

    raise ValueError(f"Invalid color format: {value}")


def _fix_parse_color(value: str) -> tuple[int, int, int, int]:
    value = value.strip()
    if value.startswith("#"):
        hex_str = value[1:]
    else:
        hex_str = value

    if len(hex_str) == 8 and not value.startswith("#"):
        a = int(hex_str[0:2], 16)
        r = int(hex_str[2:4], 16)
        g = int(hex_str[4:6], 16)
        b = int(hex_str[6:8], 16)
        return (r, g, b, a)
    if len(hex_str) == 6:
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), 255)
    if len(hex_str) == 8 and value.startswith("#"):
        return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16))
    if len(hex_str) == 3:
        return (int(hex_str[0] * 2, 16), int(hex_str[1] * 2, 16), int(hex_str[2] * 2, 16), 255)
    raise ValueError(f"Invalid color format: {value}")


parse_color = _fix_parse_color


def normalize_palette(raw: list[Any]) -> list[PaletteStop]:
    """Convert palette JSON (shorthand or explicit) to sorted PaletteStop list."""
    if not raw:
        raise ValueError("Palette must not be empty")

    stops: list[PaletteStop] = []

    if all(isinstance(entry, str) for entry in raw):
        colors: list[str] = raw  # type: ignore[assignment]
        n = len(colors)
        if n < 2:
            raise ValueError("Shorthand palette needs at least 2 colors")
        greys = TC_STANDARD_STOPS[:n] if n <= len(TC_STANDARD_STOPS) else [
            int(255 * i / (n - 1)) for i in range(n)
        ]
        if greys[0] != 0:
            stops.append(PaletteStop(0, (0, 0, 0, 255)))
        for grey, color in zip(greys, colors):
            stops.append(PaletteStop(grey, parse_color(color)))
    else:
        for entry in raw:
            if not isinstance(entry, dict):
                raise ValueError(f"Invalid palette entry: {entry}")
            grey = int(entry["grey"])
            color = entry.get("color", "#000000")
            stops.append(PaletteStop(grey, parse_color(color)))

    stops.sort(key=lambda s: s.grey)
    # Deduplicate grey values
    deduped: list[PaletteStop] = []
    for stop in stops:
        if deduped and deduped[-1].grey == stop.grey:
            deduped[-1] = stop
        else:
            deduped.append(stop)

    if len(deduped) < 2:
        raise ValueError("Palette must have at least 2 stops")
    return deduped


class PaletteMaterial(Material):
    def __init__(self, name: str, stops: list[PaletteStop], lut: np.ndarray | None = None) -> None:
        self.name = name
        self.stops = stops
        self._lut = lut if lut is not None else stops_to_lut_array(stops)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PaletteMaterial:
        name = data["name"]
        stops = normalize_palette(data["palette"])
        return cls(name, stops)

    def transform_layer(self, rgba: np.ndarray, ctx: PackContext) -> np.ndarray:
        return apply_palette_lut(rgba, self._lut)
