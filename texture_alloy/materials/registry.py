"""Load material definitions from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from texture_alloy.materials.base import Material
from texture_alloy.materials.hybrid import HybridMaterial
from texture_alloy.materials.palette import PaletteMaterial


def load_material(path: Path, quality: str = "texture") -> Material:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "name" not in data:
        data["name"] = path.stem
    return material_from_dict(data, quality=quality)


def material_from_dict(data: dict[str, Any], quality: str = "texture") -> Material:
    material_type = data.get("type", "palette")
    if material_type == "palette":
        return PaletteMaterial.from_dict(data)
    if material_type == "hybrid":
        return HybridMaterial.from_dict(data, quality=quality)
    raise ValueError(f"Unknown material type: {material_type}")


def load_materials(
    directory: Path,
    names: set[str] | None = None,
    quality: str = "texture",
) -> dict[str, Material]:
    materials: dict[str, Material] = {}
    for path in sorted(directory.glob("*.json")):
        material = load_material(path, quality=quality)
        if names and material.name not in names:
            continue
        materials[material.name] = material
    return materials
