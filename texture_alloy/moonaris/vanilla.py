"""
Vanilla-shaped handheld tools for Moonaris.

Uses Minecraft tool silhouettes (iron, diamond, or netherite): alloy palette on
metal, vanilla stick pixels unchanged.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from texture_alloy.io.composer import alpha_composite_layers
from texture_alloy.io.pack import PackContext
from texture_alloy.io.png import load_rgba, resize_rgba
from texture_alloy.materials.base import Material
from texture_alloy.paths import TIC_TEMPLATES, VANILLA_CACHE, VANILLA_REFS

# --- Constants ---

HANDHELD_TOOLS = frozenset({"pickaxe", "sword", "axe", "shovel", "hoe"})
BOW_VARIANTS = frozenset({"bow", "bow_pulling_0", "bow_pulling_1", "bow_pulling_2"})
CROSSBOW_VARIANTS = frozenset(
    {
        "crossbow_standby",
        "crossbow_pulling_0",
        "crossbow_pulling_1",
        "crossbow_pulling_2",
        "crossbow_arrow",
        "crossbow_firework",
    }
)
VANILLA_TOOL_TIERS = frozenset({"iron", "diamond", "netherite"})

MOONARIUM_REFERENCE_TEXTURES: dict[str, str] = {
    "item/echo_shard": "echo_shard.png",
    "block/netherite_block": "netherite_block.png",
    "block/sculk": "sculk.png",
    "block/sculk_catalyst_top": "sculk_catalyst_top.png",
    "block/soul_fire": "soul_fire.png",
    "block/budding_amethyst": "budding_amethyst.png",
}


# --- Path / cache helpers ---


def _copy_local_ref(filename: str, dest: Path) -> bool:
    local = VANILLA_REFS / filename
    if not local.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(local, dest)
    return True


def _require_local_ref(filename: str, dest: Path) -> None:
    if _copy_local_ref(filename, dest):
        return
    if dest.is_file():
        return
    raise FileNotFoundError(
        f"Missing bundled vanilla ref '{filename}' — run from repo with templates/vanilla_refs/"
    )


def material_pack_context() -> PackContext:
    ensure_moonarium_reference_textures(TIC_TEMPLATES)
    return PackContext(TIC_TEMPLATES)


def ensure_moonarium_reference_textures(*roots: Path | None) -> None:
    targets = [TIC_TEMPLATES, VANILLA_CACHE]
    if roots:
        targets = [root for root in roots if root is not None]
    for root in targets:
        for ref, filename in MOONARIUM_REFERENCE_TEXTURES.items():
            category, name = ref.split("/", 1)
            dest = root / "assets" / "minecraft" / "textures" / category / f"{name}.png"
            _require_local_ref(filename, dest)


# --- Vanilla asset fetch ---


def ensure_vanilla_item(item: str, cache_dir: Path | None = None) -> Path:
    cache = cache_dir or VANILLA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{item}.png"
    if not path.is_file():
        _require_local_ref(f"{item}.png", path)
    return path


def ensure_vanilla_shield(cache_dir: Path | None = None) -> Path:
    cache = cache_dir or VANILLA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / "shield_base.png"
    if not path.is_file():
        _require_local_ref("shield_base.png", path)
    return path


def ensure_vanilla_shield_nopattern(cache_dir: Path | None = None) -> Path:
    cache = cache_dir or VANILLA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / "shield_base_nopattern.png"
    if not path.is_file():
        _require_local_ref("shield_base_nopattern.png", path)
    return path


def ensure_vanilla_sprite(
    name: str,
    tier: str | None = "iron",
    cache_dir: Path | None = None,
) -> Path:
    if tier is None:
        return ensure_vanilla_item(name, cache_dir)
    cache = cache_dir or VANILLA_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    if tier not in VANILLA_TOOL_TIERS:
        raise ValueError(f"Unknown vanilla tool tier: {tier}")
    path = cache / f"{tier}_{name}.png"
    if not path.is_file():
        _require_local_ref(f"{tier}_{name}.png", path)
    return path


def ensure_vanilla_tool(
    tool: str,
    cache_dir: Path | None = None,
    *,
    tier: str = "iron",
) -> Path:
    return ensure_vanilla_sprite(tool, tier=tier, cache_dir=cache_dir)


# --- Mask / split utilities ---


def rgba_to_greyscale_template(rgba: np.ndarray) -> np.ndarray:
    out = np.zeros_like(rgba)
    opaque = rgba[:, :, 3] > 0
    for y in range(rgba.shape[0]):
        for x in range(rgba.shape[1]):
            if not opaque[y, x]:
                continue
            px = rgba[y, x]
            grey = int(px[:3].max())
            out[y, x] = (grey, grey, grey, px[3])
    return out


def wood_mask_from_vanilla(vanilla: np.ndarray) -> np.ndarray:
    opaque = vanilla[:, :, 3] > 0
    rgb = vanilla[:, :, :3].astype(np.int32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    wood = (r > 50) & (g > 30) & (r > b + 8) & (g >= b) & ((r - b) > 12)
    return opaque & wood


def vanilla_mask_layer(vanilla: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(vanilla)
    out[mask] = vanilla[mask]
    return out


def split_vanilla_tool(vanilla: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    wood = wood_mask_from_vanilla(vanilla)
    return split_sprite_by_mask(vanilla, wood)


def split_sprite_by_mask(
    vanilla: np.ndarray, handle_mask: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    opaque = vanilla[:, :, 3] > 0
    metal = opaque & ~handle_mask
    head = np.zeros_like(vanilla)
    handle = np.zeros_like(vanilla)

    for y in range(vanilla.shape[0]):
        for x in range(vanilla.shape[1]):
            px = vanilla[y, x]
            if not opaque[y, x]:
                continue
            grey = int(px[:3].max())
            if handle_mask[y, x]:
                handle[y, x] = (grey, grey, grey, px[3])
            elif metal[y, x]:
                head[y, x] = (grey, grey, grey, px[3])

    return head, handle


def _breeze_palette_from_sprite(breeze: np.ndarray) -> np.ndarray:
    return np.unique(breeze[breeze[:, :, 3] > 0][:, :3].astype(np.int16), axis=0)


def breeze_rod_mask_from_mace(mace: np.ndarray, breeze: np.ndarray) -> np.ndarray:
    opaque = mace[:, :, 3] > 0
    breeze_colors = _breeze_palette_from_sprite(breeze)
    mask = np.zeros(opaque.shape, dtype=bool)

    for y in range(mace.shape[0]):
        for x in range(mace.shape[1]):
            if not opaque[y, x]:
                continue
            color = mace[y, x, :3].astype(np.int16)
            color_dist = int(np.min(np.abs(breeze_colors - color).sum(axis=1)))
            red, green, blue = (int(color[0]), int(color[1]), int(color[2]))
            saturation = max(red, green, blue) - min(red, green, blue)
            grey_metal = saturation <= 22 and color_dist >= 45
            breeze_hit = color_dist <= 50 and (
                color_dist <= 32 or (blue >= red - 2 and saturation >= 30)
            )
            if breeze_hit and not grey_metal:
                mask[y, x] = True

    return mask


def breeze_rod_mask_from_vanilla(cache_dir: Path | None = None) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    mace = load_rgba(ensure_vanilla_item("mace", cache_dir=cache))
    breeze = load_rgba(ensure_vanilla_item("breeze_rod", cache_dir=cache))
    return breeze_rod_mask_from_mace(mace, breeze)


def wood_mask_from_spear_tiers(cache_dir: Path | None = None) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    tier_masks: list[np.ndarray] = []
    opaque: np.ndarray | None = None
    for tier in VANILLA_TOOL_TIERS:
        rgba = load_rgba(ensure_vanilla_sprite("spear", tier=tier, cache_dir=cache))
        tier_masks.append(wood_mask_from_vanilla(rgba))
        if opaque is None:
            opaque = rgba[:, :, 3] > 0
    votes = sum(mask.astype(np.int16) for mask in tier_masks)
    min_votes = max(2, (len(tier_masks) + 1) // 2)
    return (votes >= min_votes) & opaque


# --- Per-item compositors ---


def composite_vanilla_spear(
    alloy_material: Material,
    wood_material: Material,
    cache_dir: Path | None = None,
    *,
    tier: str = "iron",
) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    reference = load_rgba(ensure_vanilla_sprite("spear", tier=tier, cache_dir=cache))
    wood = wood_mask_from_spear_tiers(cache_dir=cache)
    head_tpl, _handle_tpl = split_sprite_by_mask(reference, wood)
    ctx = material_pack_context()
    colored_head = alloy_material.transform_layer(head_tpl, ctx)
    handle_layer = vanilla_mask_layer(reference, wood)
    return alpha_composite_layers([colored_head, handle_layer])


def composite_vanilla_spear_in_hand(
    alloy_material: Material,
    wood_material: Material,
    cache_dir: Path | None = None,
    *,
    tier: str = "iron",
) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    reference = load_rgba(
        ensure_vanilla_sprite("spear_in_hand", tier=tier, cache_dir=cache)
    )
    wood = wood_mask_from_vanilla(reference)
    head_tpl, _handle_tpl = split_sprite_by_mask(reference, wood)
    ctx = material_pack_context()
    colored_head = alloy_material.transform_layer(head_tpl, ctx)
    handle_layer = vanilla_mask_layer(reference, wood)
    return alpha_composite_layers([colored_head, handle_layer])


def bow_arrow_mask(pulling: np.ndarray, standby: np.ndarray) -> np.ndarray:
    return (pulling[:, :, 3] > 0) & ~(standby[:, :, 3] > 0)


def crossbow_projectile_mask(
    variant_sprite: np.ndarray, standby: np.ndarray, variant: str
) -> np.ndarray:
    if variant in {"crossbow_arrow", "crossbow_firework"}:
        return (variant_sprite[:, :, 3] > 0) & ~(standby[:, :, 3] > 0)
    return np.zeros(variant_sprite.shape[:2], dtype=bool)


def _composite_vanilla_weapon_sprite(
    reference: np.ndarray,
    alloy_material: Material,
    projectile_mask: np.ndarray,
) -> np.ndarray:
    wood = wood_mask_from_vanilla(reference)
    opaque = reference[:, :, 3] > 0
    metal = opaque & ~wood & ~projectile_mask

    metal_tpl = np.zeros_like(reference)
    for y in range(reference.shape[0]):
        for x in range(reference.shape[1]):
            if metal[y, x]:
                grey = int(reference[y, x, :3].max())
                metal_tpl[y, x] = (grey, grey, grey, reference[y, x, 3])

    ctx = material_pack_context()
    colored_metal = alloy_material.transform_layer(metal_tpl, ctx)
    handle_layer = vanilla_mask_layer(reference, wood)
    projectile_layer = vanilla_mask_layer(reference, projectile_mask)
    return alpha_composite_layers([colored_metal, handle_layer, projectile_layer])


def composite_vanilla_bow(
    variant: str,
    alloy_material: Material,
    cache_dir: Path | None = None,
) -> np.ndarray:
    if variant not in BOW_VARIANTS:
        raise ValueError(f"Unknown bow variant: {variant}")
    cache = cache_dir or VANILLA_CACHE
    reference = load_rgba(ensure_vanilla_item(variant, cache_dir=cache))
    standby = load_rgba(ensure_vanilla_item("bow", cache_dir=cache))
    arrow = (
        bow_arrow_mask(reference, standby)
        if variant != "bow"
        else np.zeros(reference.shape[:2], dtype=bool)
    )
    return _composite_vanilla_weapon_sprite(reference, alloy_material, arrow)


def composite_vanilla_crossbow(
    variant: str,
    alloy_material: Material,
    cache_dir: Path | None = None,
) -> np.ndarray:
    if variant not in CROSSBOW_VARIANTS:
        raise ValueError(f"Unknown crossbow variant: {variant}")
    cache = cache_dir or VANILLA_CACHE
    reference = load_rgba(ensure_vanilla_item(variant, cache_dir=cache))
    standby = load_rgba(ensure_vanilla_item("crossbow_standby", cache_dir=cache))
    projectile = crossbow_projectile_mask(reference, standby, variant)
    return _composite_vanilla_weapon_sprite(reference, alloy_material, projectile)


def composite_vanilla_mace(
    alloy_material: Material,
    breeze_material: Material,
    cache_dir: Path | None = None,
) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    mace = load_rgba(ensure_vanilla_item("mace", cache_dir=cache))
    handle_mask = breeze_rod_mask_from_vanilla(cache_dir=cache)
    head_tpl, handle_tpl = split_sprite_by_mask(mace, handle_mask)
    ctx = material_pack_context()
    colored_head = alloy_material.transform_layer(head_tpl, ctx)
    colored_handle = breeze_material.transform_layer(handle_tpl, ctx)
    return alpha_composite_layers([colored_head, colored_handle])


def plank_mask_from_shield_comparison(
    shield: np.ndarray, nopattern: np.ndarray
) -> np.ndarray:
    opaque = shield[:, :, 3] > 0
    identical = np.all(shield[:, :, :3] == nopattern[:, :, :3], axis=2) & opaque
    return opaque & ~identical


def composite_vanilla_shield(
    alloy_material: Material,
    cache_dir: Path | None = None,
    *,
    item_size: tuple[int, int] = (64, 64),
) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    shield = load_rgba(ensure_vanilla_shield(cache_dir=cache))
    nopattern = load_rgba(ensure_vanilla_shield_nopattern(cache_dir=cache))
    plank_mask = plank_mask_from_shield_comparison(shield, nopattern)

    plank_tpl = np.zeros_like(shield)
    plank_grey = rgba_to_greyscale_template(nopattern)
    plank_tpl[plank_mask] = plank_grey[plank_mask]

    frame = shield.copy()
    frame[plank_mask] = (0, 0, 0, 0)

    ctx = material_pack_context()
    colored_planks = alloy_material.transform_layer(plank_tpl, ctx)
    result = alpha_composite_layers([colored_planks, frame])
    return resize_rgba(result, item_size)


def composite_vanilla_sprite(
    sprite_name: str,
    alloy_material: Material,
    wood_material: Material | None = None,
    *,
    tier: str | None = "iron",
    alloy_only: bool = False,
    cache_dir: Path | None = None,
) -> np.ndarray:
    cache = cache_dir or VANILLA_CACHE
    vanilla = load_rgba(ensure_vanilla_sprite(sprite_name, tier=tier, cache_dir=cache))
    ctx = material_pack_context()

    if alloy_only:
        return alloy_material.transform_layer(rgba_to_greyscale_template(vanilla), ctx)

    if wood_material is None:
        raise ValueError("wood material required for split vanilla tools")

    wood = wood_mask_from_vanilla(vanilla)
    head_tpl, _handle_tpl = split_sprite_by_mask(vanilla, wood)
    colored_head = alloy_material.transform_layer(head_tpl, ctx)
    handle_layer = vanilla_mask_layer(vanilla, wood)
    return alpha_composite_layers([colored_head, handle_layer])


def composite_vanilla_tool(
    tool_name: str,
    alloy_material: Material,
    wood_material: Material,
    cache_dir: Path | None = None,
    *,
    tier: str = "iron",
    alloy_only: bool = False,
) -> np.ndarray:
    return composite_vanilla_sprite(
        tool_name,
        alloy_material,
        wood_material,
        tier=tier,
        alloy_only=alloy_only,
        cache_dir=cache_dir,
    )
