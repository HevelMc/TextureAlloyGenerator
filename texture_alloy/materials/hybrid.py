"""Hybrid palette + texture material."""

from __future__ import annotations

from typing import Any

import numpy as np

from texture_alloy.io.pack import PackContext
from texture_alloy.materials.base import Material
from texture_alloy.materials.palette import PaletteStop, normalize_palette, parse_color
from texture_alloy.transform.apply import apply_palette_lut
from texture_alloy.transform.grey import get_nearest_by_grey, scale_color
from texture_alloy.transform.lut import stops_to_lut_array


class HybridStop:
    def __init__(
        self,
        grey: int,
        rgba: tuple[int, int, int, int] | None = None,
        texture_path: str | None = None,
        tint: tuple[int, int, int, int] | None = None,
    ) -> None:
        self.grey = grey
        self.rgba = rgba
        self.texture_path = texture_path
        self.tint = tint


class HybridMaterial(Material):
    def __init__(self, name: str, stops: list[HybridStop], quality: str = "texture") -> None:
        self.name = name
        self.stops = sorted(stops, key=lambda s: s.grey)
        self.quality = quality

    @classmethod
    def from_dict(cls, data: dict[str, Any], quality: str = "texture") -> HybridMaterial:
        name = data["name"]
        stops: list[HybridStop] = []
        for entry in data["palette"]:
            grey = int(entry["grey"])
            rgba = None
            texture_path = entry.get("texture")
            tint = None
            if "color" in entry:
                rgba = parse_color(entry["color"])
            if "tint" in entry:
                tint = parse_color(entry["tint"])
            stops.append(HybridStop(grey, rgba=rgba, texture_path=texture_path, tint=tint))
        if len(stops) < 2:
            raise ValueError("Hybrid palette must have at least 2 stops")
        return cls(name, stops, quality=quality)

    def _resolve_stop_color(
        self, stop: HybridStop, x: int, y: int, ctx: PackContext
    ) -> tuple[int, int, int, int]:
        if stop.texture_path:
            tex = ctx.load_texture(stop.texture_path)
            h, w = tex.shape[:2]
            sx, sy = x % w, y % h
            sampled = tuple(int(tex[sy, sx, c]) for c in range(4))
            if stop.tint:
                return scale_color(sampled, stop.tint, 255)
            return sampled  # type: ignore[return-value]
        assert stop.rgba is not None
        return stop.rgba

    def _color_stops_for_lut(self, ctx: PackContext) -> list[PaletteStop]:
        result = []
        for stop in self.stops:
            if stop.texture_path:
                tex = ctx.load_texture(stop.texture_path)
                h, w = tex.shape[:2]
                cx, cy = w // 2, h // 2
                rgba = tuple(int(tex[cy, cx, c]) for c in range(4))
                if stop.tint:
                    rgba = scale_color(rgba, stop.tint, 255)
            else:
                rgba = stop.rgba
            assert rgba is not None
            result.append(PaletteStop(stop.grey, rgba))
        return result

    def transform_layer(self, rgba: np.ndarray, ctx: PackContext) -> np.ndarray:
        if self.quality == "fast":
            lut = stops_to_lut_array(self._color_stops_for_lut(ctx))
            return apply_palette_lut(rgba, lut)

        h, w, _ = rgba.shape
        out = np.zeros_like(rgba)
        palette_stops = self._color_stops_for_lut(ctx)

        for y in range(h):
            for x in range(w):
                r, g, b, a = (int(rgba[y, x, c]) for c in range(4))
                if a == 0:
                    continue
                grey = max(r, g, b)
                # Find bracketing hybrid stops for per-pixel texture
                before: HybridStop | None = None
                after: HybridStop | None = None
                for stop in self.stops:
                    if stop.grey <= grey:
                        before = stop
                    if stop.grey >= grey and after is None:
                        after = stop
                        break
                if before is None:
                    before = self.stops[0]
                if after is None:
                    after = self.stops[-1]

                c_before = self._resolve_stop_color(before, x, y, ctx)
                c_after = self._resolve_stop_color(after, x, y, ctx)
                if before.grey == after.grey or before is after:
                    mapped = c_before
                else:
                    from texture_alloy.transform.grey import interpolate_colors
                    mapped = interpolate_colors(c_before, before.grey, c_after, after.grey, grey)

                sr, sg, sb, sa = scale_color((r, g, b, a), mapped, grey)
                out[y, x] = (sr, sg, sb, sa)
        return out
