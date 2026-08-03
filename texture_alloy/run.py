"""Orchestrate full Moonaris texture + pack generation."""

from __future__ import annotations

import shutil
from pathlib import Path

from texture_alloy.catalog import HELPER_MATERIALS
from texture_alloy.materials.registry import load_materials
from texture_alloy.moonaris.batch import run_moonaris_batch
from texture_alloy.moonaris.jobs import build_moonaris_jobs, write_pack_mcmeta
from texture_alloy.pack.datapack import write_datapack
from texture_alloy.pack.writer import sync_pack, write_pack
from texture_alloy.paths import (
    GENERATED,
    MATERIALS,
    MOONARIS_DATAPACK,
    MOONARIS_PACK,
    TIC_TEMPLATES,
)

PACK_STAGING = GENERATED / "moonaris_pack"


def discover_alloys() -> list[str]:
    return sorted(
        path.stem for path in MATERIALS.glob("*.json") if path.stem not in HELPER_MATERIALS
    )


def generate_material(name: str, output: Path) -> None:
    material_filter = {name}
    materials = load_materials(MATERIALS, names=material_filter)
    if not materials:
        raise ValueError(f"Material not found: {name}")

    jobs, missing = build_moonaris_jobs(output, materials, material_filter)
    if not jobs:
        raise RuntimeError(f"No jobs for {name}: missing={missing}")

    write_pack_mcmeta(output)
    _success, failures = run_moonaris_batch(
        jobs,
        TIC_TEMPLATES,
        threads=1,
        materials_dir=MATERIALS,
    )
    if failures:
        raise RuntimeError(f"{failures} texture job(s) failed for {name}")


def _generated_textures(output: Path, material: str) -> list[Path]:
    tex_root = output / "assets" / "moonaris" / "textures"
    if not tex_root.is_dir():
        return []
    paths: list[Path] = []
    for path in tex_root.rglob("*.png"):
        name = path.name
        if name == f"{material}.png" or name.startswith(f"{material}_"):
            paths.append(path)
    return sorted(paths)


def install_textures(output: Path, pack: Path, material: str) -> None:
    src_tex = output / "assets" / "moonaris" / "textures"
    dst_tex = pack / "assets" / "moonaris" / "textures"
    paths = _generated_textures(output, material)
    if not paths:
        raise FileNotFoundError(f"No generated textures for material '{material}'")

    for path in paths:
        rel = path.relative_to(src_tex)
        target = dst_tex / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def main() -> None:
    if MOONARIS_PACK is None:
        raise RuntimeError(
            "MOONARIS_PACK is not set. Copy .env.example to .env and set MOONARIS_PACK."
        )
    target = MOONARIS_PACK
    target.mkdir(parents=True, exist_ok=True)

    if PACK_STAGING.exists():
        shutil.rmtree(PACK_STAGING)
    PACK_STAGING.mkdir(parents=True)

    for name in discover_alloys():
        out = GENERATED / f"moonaris_{name}"
        generate_material(name, out)
        install_textures(out, PACK_STAGING, name)
        print(name)

    write_pack(PACK_STAGING)
    sync_pack(PACK_STAGING, target)
    write_datapack(MOONARIS_DATAPACK)
    print("Done.")


if __name__ == "__main__":
    main()
