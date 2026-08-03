"""Moonaris batch generation."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from texture_alloy.io.pack import PackContext
from texture_alloy.io.png import load_rgba, save_rgba
from texture_alloy.materials.base import Material
from texture_alloy.materials.registry import load_material
from texture_alloy.moonaris.jobs import MoonarisJob, load_moonaris_material_opts, material_item_tier
from texture_alloy.moonaris.tic import composite_tc_item, tc_item_key
from texture_alloy.moonaris.vanilla import (
    HANDHELD_TOOLS,
    VANILLA_CACHE,
    composite_vanilla_mace,
    composite_vanilla_shield,
    composite_vanilla_spear,
    composite_vanilla_spear_in_hand,
    composite_vanilla_sprite,
    composite_vanilla_tool,
    ensure_vanilla_tool,
)
from texture_alloy.paths import TIC_TEMPLATES

CompositorFn = Callable[
    [MoonarisJob, dict, str, Material, Material, Path],
    np.ndarray,
]


def _load_breeze_rod(materials_dir: Path | None) -> Material:
    base = materials_dir or Path()
    breeze_path = base / "moonaris" / "breeze_rod.json"
    if not breeze_path.is_file():
        breeze_path = base / "breeze_rod.json"
    if not breeze_path.is_file():
        raise FileNotFoundError("breeze_rod material not found for mace handle")
    return load_material(breeze_path)


def _load_wood(materials_dir: Path | None) -> Material:
    base = materials_dir or Path()
    wood_path = base / "moonaris" / "wood.json"
    if not wood_path.is_file():
        wood_path = base / "wood.json"
    if not wood_path.is_file():
        raise FileNotFoundError("wood material not found for TC wood/string parts")
    return load_material(wood_path)


def _composite_mace(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    return composite_vanilla_mace(job.material, breeze, cache_dir=VANILLA_CACHE)


def _composite_spear(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    return composite_vanilla_spear(job.material, wood, cache_dir=VANILLA_CACHE, tier=tool_tier)


def _composite_spear_in_hand(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    return composite_vanilla_spear_in_hand(
        job.material, wood, cache_dir=VANILLA_CACHE, tier=tool_tier
    )


def _composite_shield_entity(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    return composite_vanilla_shield(job.material, cache_dir=VANILLA_CACHE)


def _composite_vanilla_item(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    return composite_vanilla_sprite(
        job.item.template_name,
        job.material,
        tier=None,
        alloy_only=True,
        cache_dir=VANILLA_CACHE,
    )


def _composite_pearl(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    return composite_vanilla_sprite(
        "ghast_tear",
        job.material,
        tier=None,
        alloy_only=True,
        cache_dir=VANILLA_CACHE,
    )


def _composite_handheld(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    alloy_only = bool(opts.get("vanilla_tool_alloy_only", False))
    ensure_vanilla_tool(job.item.template_name, tier=tool_tier, cache_dir=VANILLA_CACHE)
    return composite_vanilla_tool(
        job.item.template_name,
        job.material,
        wood,
        cache_dir=VANILLA_CACHE,
        tier=tool_tier,
        alloy_only=alloy_only,
    )


def _composite_ingot_shape(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    ingot_shape = opts.get("ingot_shape")
    if not ingot_shape:
        raise ValueError("ingot_shape required for shaped ingot")
    return composite_vanilla_sprite(
        ingot_shape,
        job.material,
        tier=None,
        alloy_only=True,
        cache_dir=VANILLA_CACHE,
    )


def _composite_tconstruct(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    tc_key = tc_item_key(job.item.template_name, job.item.category)
    if tc_key is None:
        raise ValueError(f"No TC recipe for {job.item.category}:{job.item.template_name}")
    return composite_tc_item(tc_key, job.material, wood, tc_root=TIC_TEMPLATES)


def _composite_template(
    job: MoonarisJob,
    opts: dict,
    tool_tier: str,
    wood: Material,
    breeze: Material,
    input_root: Path,
) -> np.ndarray:
    ctx = PackContext(input_root)
    rgba = load_rgba(job.item.template_path)
    return job.material.transform_layer(rgba, ctx)


SOURCE_COMPOSITORS: dict[str, CompositorFn] = {
    "vanilla_mace": _composite_mace,
    "vanilla_spear": _composite_spear,
    "vanilla_spear_in_hand": _composite_spear_in_hand,
    "vanilla_shield_entity": _composite_shield_entity,
    "vanilla_item": _composite_vanilla_item,
    "vanilla_pearl": _composite_pearl,
    "tconstruct": _composite_tconstruct,
}


def _resolve_compositor(job: MoonarisJob, opts: dict) -> CompositorFn:
    if job.item.source in SOURCE_COMPOSITORS:
        if (
            job.item.source == "tconstruct"
            and job.item.template_name == "ingot"
            and job.item.category == "item"
            and opts.get("ingot_shape")
        ):
            return _composite_ingot_shape
        return SOURCE_COMPOSITORS[job.item.source]

    if job.item.category == "item" and job.item.template_name in HANDHELD_TOOLS:
        return _composite_handheld

    return _composite_template


def run_moonaris_job(
    job: MoonarisJob,
    input_root: Path,
    materials_dir: Path | None = None,
) -> tuple[str, bool, str | None]:
    try:
        opts = load_moonaris_material_opts(materials_dir, job.material_name)
        tool_tier = material_item_tier(job.material_name, opts)
        wood = _load_wood(materials_dir)
        breeze = _load_breeze_rod(materials_dir)

        compositor = _resolve_compositor(job, opts)
        result = compositor(job, opts, tool_tier, wood, breeze, input_root)

        save_rgba(job.item.output_path, result)
        return (str(job.item.output_path), True, None)
    except Exception as exc:
        return (str(job.item.output_path), False, str(exc))


def run_moonaris_batch(
    jobs: list[MoonarisJob],
    input_root: Path,
    threads: int,
    materials_dir: Path | None = None,
) -> tuple[int, int]:
    success = failures = 0
    if threads <= 1:
        for job in jobs:
            path, ok, err = run_moonaris_job(job, input_root, materials_dir)
            if ok:
                success += 1
            else:
                failures += 1
                print(f"FAIL {path}: {err}")
    else:
        with ThreadPoolExecutor(max_workers=threads) as pool:
            futures = {
                pool.submit(run_moonaris_job, job, input_root, materials_dir): job
                for job in jobs
            }
            for future in as_completed(futures):
                path, ok, err = future.result()
                if ok:
                    success += 1
                else:
                    failures += 1
                    print(f"FAIL {path}: {err}")
    return success, failures
