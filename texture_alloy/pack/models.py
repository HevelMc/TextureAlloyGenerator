"""Generate moonaris/models/item and moonaris/items JSON."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from texture_alloy.catalog import MATERIALS, MODEL_PARENTS, NAMESPACE, SHIELD_DISPLAYS
from texture_alloy.pack.builders import model_ref

MODEL_VARIANTS = tuple(MODEL_PARENTS.keys())


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _parent_model(material: str, variant: str) -> dict[str, Any]:
    parent = MODEL_PARENTS[variant]
    texture = model_ref(material, None if variant == "ingot" else variant)
    return {"parent": parent, "textures": {"layer0": texture}}


def _shield_special_model(material: str, display_key: str) -> dict[str, Any]:
    model = copy.deepcopy(SHIELD_DISPLAYS[display_key])
    model["textures"] = {"particle": model_ref(material, "shield_entity")}
    return model


def write_item_models(pack: Path) -> int:
    model_dir = pack / "assets" / NAMESPACE / "models" / "item"
    written = 0

    for material in MATERIALS:
        name = material.name
        for variant in MODEL_VARIANTS:
            if variant == "pearl" and material.pearl_cmd is None:
                continue
            if variant == "ingot":
                path = model_dir / f"{name}.json"
                _write_json(path, _parent_model(name, variant))
            else:
                path = model_dir / f"{name}_{variant}.json"
                _write_json(path, _parent_model(name, variant))
            written += 1

        for variant, display_key in (
            ("shield_entity", "entity"),
            ("shield_blocking", "blocking"),
        ):
            path = model_dir / f"{name}_{variant}.json"
            _write_json(path, _shield_special_model(name, display_key))
            written += 1

    return written


def write_shield_items(pack: Path) -> int:
    items_dir = pack / "assets" / NAMESPACE / "items"
    written = 0
    for material in MATERIALS:
        path = items_dir / f"{material.name}_shield.json"
        _write_json(
            path,
            {"model": {"type": "minecraft:model", "model": model_ref(material.name, "shield")}},
        )
        written += 1
    return written
