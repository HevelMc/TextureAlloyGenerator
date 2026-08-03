"""Minimal Moonaris datapack: one give function per alloy."""

from __future__ import annotations

import json
from pathlib import Path

from texture_alloy.catalog import (
    MATERIALS,
    NAMESPACE,
    MaterialDef,
    cmd_component,
    equippable_component,
    equipment_asset_id,
    glint_component,
    item_name_json,
)


def _give_line(
    material: MaterialDef,
    base_item: str,
    cmd: int,
    display: str,
    *,
    equip_slot: str | None = None,
) -> str:
    parts = [
        cmd_component(cmd),
        f"minecraft:item_name={item_name_json(display)}",
    ]
    if material.glint:
        parts.append(glint_component())
    if equip_slot is not None:
        parts.append(equippable_component(equip_slot, equipment_asset_id(material.name)))
    return f"give @s minecraft:{base_item}[{','.join(parts)}] 1"


def _tool_give(material: MaterialDef, tool: str, label: str) -> str:
    return _give_line(
        material,
        f"{material.tier}_{tool}",
        material.tool_cmd,
        f"{material.display} {label}",
    )


def _armor_give(material: MaterialDef, piece: str, slot: str, label: str) -> str:
    return _give_line(
        material,
        f"{material.tier}_{piece}",
        material.armor_cmd,
        f"{material.display} {label}",
        equip_slot=slot,
    )


def _material_give_lines(material: MaterialDef) -> list[str]:
    lines = [
        f"# Moonaris — {material.name}",
        _give_line(
            material,
            material.ingot_item,
            material.ingot_cmd,
            f"{material.display} Ingot",
        ),
        _tool_give(material, "pickaxe", "Pickaxe"),
        _armor_give(material, "helmet", "head", "Helmet"),
    ]
    if material.pearl_cmd is not None:
        lines.append(
            _give_line(material, "ghast_tear", material.pearl_cmd, f"{material.display} Pearl")
        )
    return lines


def write_datapack(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    pack_meta = {"pack": {"pack_format": 48, "description": "Moonaris give functions"}}
    (root / "pack.mcmeta").write_text(json.dumps(pack_meta, indent=2) + "\n", encoding="utf-8")

    for material in MATERIALS:
        path = root / "data" / NAMESPACE / "function" / "give" / f"{material.name}.mcfunction"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(_material_give_lines(material)) + "\n", encoding="utf-8")
