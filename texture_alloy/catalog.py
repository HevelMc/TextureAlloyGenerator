"""Moonaris pack catalog loaded from config/moonaris_pack.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from texture_alloy.paths import ROOT

CONFIG_PATH = ROOT / "config" / "moonaris_pack.json"
NAMESPACE = "moonaris"
HELPER_MATERIALS = frozenset({"wood", "breeze_rod"})


@dataclass(frozen=True)
class MaterialDef:
    name: str
    display: str
    tier: str
    ingot_item: str
    ingot_cmd: int
    tool_cmd: int
    armor_cmd: int
    spear_cmd: int
    elytra_cmd: int
    pearl_cmd: int | None = None
    glint: bool = False


@lru_cache
def load_pack_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _material_from_dict(data: dict[str, Any]) -> MaterialDef:
    cmds = data["cmds"]
    return MaterialDef(
        name=data["name"],
        display=data["display"],
        tier=data["tier"],
        ingot_item=data["ingot_item"],
        ingot_cmd=cmds["ingot"],
        tool_cmd=cmds["tool"],
        armor_cmd=cmds["armor"],
        spear_cmd=cmds["spear"],
        elytra_cmd=cmds["elytra"],
        pearl_cmd=cmds.get("pearl"),
        glint=bool(data.get("glint", False)),
    )


def materials() -> tuple[MaterialDef, ...]:
    return tuple(_material_from_dict(item) for item in load_pack_config()["materials"])


MATERIALS = materials()

CMD_BASES: dict[str, int] = load_pack_config()["cmd_bases"]
GUI_CONTEXTS: list[str] = load_pack_config()["gui_contexts"]
TIERS: list[str] = load_pack_config()["tiers"]
TOOLS: list[str] = load_pack_config()["tools"]
ARMOR_PIECES: list[str] = load_pack_config()["armor_pieces"]
MODEL_PARENTS: dict[str, str] = load_pack_config()["model_parents"]
SHIELD_DISPLAYS: dict[str, dict] = load_pack_config()["shield_displays"]
PACK_META: dict[str, Any] = load_pack_config()["pack"]

FISHING_ROD_CMD_BASE = CMD_BASES["fishing_rod"]
BOW_CMD_BASE = CMD_BASES["bow"]
SHIELD_CMD_BASE = CMD_BASES["shield"]
TRIDENT_CMD_BASE = CMD_BASES["trident"]
CROSSBOW_CMD_BASE = CMD_BASES["crossbow"]
MACE_CMD_BASE = CMD_BASES["mace"]


def material_index(name: str) -> int:
    for index, material in enumerate(MATERIALS):
        if material.name == name:
            return index
    raise KeyError(name)


def materials_for_tier(tier: str) -> tuple[MaterialDef, ...]:
    return tuple(material for material in MATERIALS if material.tier == tier)


def pearl_materials() -> tuple[MaterialDef, ...]:
    return tuple(material for material in MATERIALS if material.pearl_cmd is not None)


def item_name_json(display: str) -> str:
    return f'\'{{"text":"{display}","color":"aqua","italic":false}}\''


def equipment_asset_id(material: str, *, elytra: bool = False) -> str:
    return f"{material}_elytra" if elytra else material


def equippable_component(slot: str, asset_id: str) -> str:
    return f'minecraft:equippable={{slot:"{slot}",asset_id:"{NAMESPACE}:{asset_id}"}}'


def cmd_component(value: int, *, string_id: str | None = None) -> str:
    parts = [f"floats:[{value}.0f]"]
    if string_id is not None:
        parts.append(f'strings:["{string_id}"]')
    return f"minecraft:custom_model_data={{{','.join(parts)}}}"


def trident_cmd_component(material: str, value: int) -> str:
    return cmd_component(value, string_id=f"{material}_trident")


def glint_component() -> str:
    return "minecraft:enchantment_glint_override=true"
