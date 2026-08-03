"""Greyscale math ported from Tinkers' Construct GreyToColorMapping."""

from __future__ import annotations

import colorsys
from dataclasses import dataclass


@dataclass(frozen=True)
class PaletteStop:
    grey: int
    rgba: tuple[int, int, int, int]


def interpolate(a: int, b: int, x: int, divisor: int) -> int:
    return a + (((b - a) * x) // divisor)


def interpolate_colors(
    color_before: tuple[int, int, int, int],
    grey_before: int,
    color_after: tuple[int, int, int, int],
    grey_after: int,
    grey: int,
) -> tuple[int, int, int, int]:
    diff = grey - grey_before
    divisor = grey_after - grey_before
    return (
        interpolate(color_before[0], color_after[0], diff, divisor),
        interpolate(color_before[1], color_after[1], diff, divisor),
        interpolate(color_before[2], color_after[2], diff, divisor),
        interpolate(color_before[3], color_after[3], diff, divisor),
    )


def get_nearest_by_grey(stops: list[PaletteStop], grey: int) -> tuple[int, int, int, int]:
    if not stops:
        raise ValueError("Palette must have at least one stop")
    if len(stops) == 1 or grey <= stops[0].grey:
        return stops[0].rgba

    first = stops[0]
    second = stops[1]
    for i in range(1, len(stops)):
        new_grey = second.grey
        if grey < new_grey:
            return interpolate_colors(first.rgba, first.grey, second.rgba, second.grey, grey)
        if grey == new_grey:
            return second.rgba
        first = second
        if i + 1 < len(stops):
            second = stops[i + 1]

    if grey > second.grey:
        return second.rgba
    return interpolate_colors(first.rgba, first.grey, second.rgba, second.grey, grey)


def build_grey_lut(stops: list[PaletteStop]) -> list[tuple[int, int, int, int]]:
    if len(stops) < 2:
        raise ValueError("Palette must have at least 2 stops")
    return [get_nearest_by_grey(stops, grey) for grey in range(256)]


def scale_color(
    original: tuple[int, int, int, int],
    new_color: tuple[int, int, int, int],
    grey: int,
) -> tuple[int, int, int, int]:
    """Scale mapped color based on original channel ratios (TC scaleColor)."""
    r, g, b, a = original
    nr, ng, nb, na = new_color

    if a < 255:
        na = (na * a) // 255

    if grey <= 0:
        return (nr, ng, nb, na)

    if r < grey:
        nr = (nr * r) // grey
    if g < grey:
        ng = (ng * g) // grey
    if b < grey:
        nb = (nb * b) // grey

    return (nr, ng, nb, na)


def boost_saturation_rgb(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Increase color saturation while preserving hue and lightness."""
    if factor <= 0 or factor == 1.0:
        return rgb
    r, g, b = rgb
    hue, lightness, saturation = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    saturation = min(1.0, saturation * factor)
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return (
        int(round(red * 255)),
        int(round(green * 255)),
        int(round(blue * 255)),
    )
