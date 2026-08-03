"""Tinkers' Construct part compositing for Moonaris items."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from texture_alloy.io.composer import alpha_composite_layers
from texture_alloy.io.pack import PackContext
from texture_alloy.io.png import load_rgba
from texture_alloy.materials.base import Material
from texture_alloy.paths import TIC_CACHE, TIC_TEMPLATES

TC_CACHE_ROOTS = (
    TIC_CACHE / "src" / "main" / "resources" / "assets" / "tconstruct" / "textures",
    TIC_CACHE / "src" / "generated" / "resources" / "assets" / "tconstruct" / "textures",
)

TC_ARROW_PARTS: tuple[tuple[str, int], ...] = (
    ("item/tool/ammo/arrow_head", 0),
    ("item/tool/ammo/arrow_shaft", 1),
    ("item/tool/ammo/arrow_feather", 2),
)

TC_ARROW_COLORED_PARTS: dict[str, str] = {
    "item/tool/ammo/arrow_head": "item/tool/ammo/arrow_head_tconstruct_flint",
    "item/tool/ammo/arrow_shaft": "item/tool/ammo/arrow_shaft_tconstruct_wood",
    "item/tool/ammo/arrow_feather": "item/tool/ammo/arrow_feather_tconstruct_wool_white",
}

TC_ARROW_OVERLAY_OFFSETS: dict[str, tuple[int, int]] = {
    "bow_pulling_0": (-3, -4),
    "bow_pulling_1": (-2, -3),
    "bow_pulling_2": (-1, -2),
    "crossbow_arrow": (-1, -1),
}

TC_ARROW_OVERLAY_ITEMS = frozenset(TC_ARROW_OVERLAY_OFFSETS)


@dataclass(frozen=True)
class TcPart:
    path: str
    role: str
    index: int


@dataclass(frozen=True)
class TcToolRecipe:
    parts: tuple[TcPart, ...]

    @property
    def draw_order(self) -> tuple[TcPart, ...]:
        return tuple(sorted(self.parts, key=lambda p: p.index))


def _parts(*entries: tuple[str, str, int]) -> TcToolRecipe:
    return TcToolRecipe(tuple(TcPart(path, role, index) for path, role, index in entries))


def _bow(suffix: str = "") -> TcToolRecipe:
    sfx = f"_{suffix}" if suffix else ""
    return _parts(
        (f"item/tool/longbow/limb_bottom{sfx}", "alloy", 0),
        (f"item/tool/longbow/limb_top{sfx}", "alloy", 1),
        ("item/tool/longbow/grip", "wood", 2),
        (f"item/tool/longbow/bowstring{sfx}", "preserve", 3),
    )


def _crossbow(suffix: str = "", extra: tuple[tuple[str, str, int], ...] = ()) -> TcToolRecipe:
    sfx = f"_{suffix}" if suffix else ""
    base = (
        ("item/tool/crossbow/limb", "alloy", 0),
        ("item/tool/crossbow/body", "wood", 1),
        (f"item/tool/crossbow/bowstring{sfx}", "preserve", 2),
    )
    return _parts(*base, *extra)


def _armor(slot: str) -> TcToolRecipe:
    return _parts(
        (f"item/tool/armor/plate/{slot}/plating", "alloy", 0),
        (f"item/tool/armor/plate/{slot}/maille", "alloy", 1),
    )


MOONARIS_TC_ITEMS: dict[str, TcToolRecipe] = {
    "ingot": _parts(("item/tool/parts/ingot", "alloy", 0)),
    "helmet": _armor("helmet"),
    "chestplate": _armor("chestplate"),
    "leggings": _armor("leggings"),
    "boots": _armor("boots"),
    "fishing_rod": _parts(
        ("item/tool/fishing_rod/rod", "wood", 0),
        ("item/tool/fishing_rod/string", "preserve", 1),
        ("item/tool/fishing_rod/hook", "alloy", 2),
    ),
    "fishing_rod_cast": _parts(
        ("item/tool/fishing_rod/rod", "wood", 0),
        ("item/tool/fishing_rod/string_cast", "preserve", 1),
        ("item/tool/fishing_rod/hook_cast", "alloy", 2),
    ),
    "bow": _bow(),
    "bow_pulling_0": _bow("1"),
    "bow_pulling_1": _bow("2"),
    "bow_pulling_2": _bow("3"),
    "crossbow_standby": _crossbow(),
    "crossbow_pulling_0": _crossbow("1"),
    "crossbow_pulling_1": _crossbow("2"),
    "crossbow_pulling_2": _crossbow("3"),
    "crossbow_arrow": _crossbow("3"),
    "crossbow_firework": _crossbow(
        "3",
        (("item/tool/crossbow/firework", "preserve", 3),),
    ),
    "equipment_humanoid": _parts(
        ("tinker_armor/plate/plating_armor", "alloy", 0),
        ("tinker_armor/plate/maille_armor", "alloy", 1),
    ),
    "equipment_leggings": _parts(
        ("tinker_armor/plate/plating_leggings", "alloy", 0),
        ("tinker_armor/plate/maille_leggings", "alloy", 1),
    ),
    "equipment_wings": _parts(
        ("tinker_armor/plate/maille_wings", "alloy", 0),
    ),
    "shield": _parts(
        ("item/tool/armor/plate/shield/core", "wood", 0),
        ("item/tool/armor/plate/shield/plating", "alloy", 1),
    ),
}


def resolve_tc_part_path(tc_root: Path, part_path: str) -> Path:
    candidates = [
        tc_root / "assets" / "tconstruct" / "textures" / f"{part_path}.png",
    ]
    for cache_root in TC_CACHE_ROOTS:
        candidates.append(cache_root / f"{part_path}.png")
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"TiC part template missing: {part_path}.png")


def preserve_layer(rgba: np.ndarray) -> np.ndarray:
    return rgba.copy()


def composite_tc_part_layer(
    part: TcPart,
    rgba: np.ndarray,
    ctx: PackContext,
    alloy_material: Material,
    wood_material: Material,
) -> np.ndarray:
    if part.role == "alloy":
        return alloy_material.transform_layer(rgba, ctx)
    if part.role == "wood":
        return wood_material.transform_layer(rgba, ctx)
    if part.role == "preserve":
        return preserve_layer(rgba)
    raise ValueError(f"Unknown TC part role: {part.role}")


def composite_tc_arrow_sprite(tc_root: Path | None = None) -> np.ndarray:
    root = tc_root or TIC_TEMPLATES
    layers: list[np.ndarray] = []
    for part_path, _index in sorted(TC_ARROW_PARTS, key=lambda entry: entry[1]):
        colored_path = TC_ARROW_COLORED_PARTS.get(part_path, part_path)
        rgba = load_rgba(resolve_tc_part_path(root, colored_path))
        layers.append(rgba.copy())
    return alpha_composite_layers(layers)


def overlay_tc_arrow(
    base: np.ndarray,
    arrow: np.ndarray,
    offset: tuple[int, int],
    *,
    flip: bool = True,
) -> np.ndarray:
    sprite = np.fliplr(arrow) if flip else arrow
    ox, oy = offset
    layer = np.zeros_like(base)
    height, width = sprite.shape[:2]
    for y in range(height):
        for x in range(width):
            alpha = sprite[y, x, 3]
            if alpha == 0:
                continue
            bx, by = x + ox, y + oy
            if 0 <= bx < base.shape[1] and 0 <= by < base.shape[0]:
                layer[by, bx] = sprite[y, x]
    return alpha_composite_layers([base, layer])


def composite_tc_item(
    item_name: str,
    alloy_material: Material,
    wood_material: Material,
    tc_root: Path | None = None,
) -> np.ndarray:
    recipe = MOONARIS_TC_ITEMS[item_name]
    root = tc_root or TIC_TEMPLATES
    ctx = PackContext(root)

    layers: list[np.ndarray] = []
    for part in recipe.draw_order:
        rgba = load_rgba(resolve_tc_part_path(root, part.path))
        layers.append(
            composite_tc_part_layer(part, rgba, ctx, alloy_material, wood_material)
        )

    result = alpha_composite_layers(layers)
    if item_name in TC_ARROW_OVERLAY_ITEMS:
        arrow = composite_tc_arrow_sprite(root)
        result = overlay_tc_arrow(result, arrow, TC_ARROW_OVERLAY_OFFSETS[item_name])
    return result


def tc_item_key(template_name: str, category: str) -> str | None:
    if category in MOONARIS_TC_ITEMS:
        return category
    if template_name in MOONARIS_TC_ITEMS:
        return template_name
    return None
