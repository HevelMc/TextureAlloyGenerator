"""Generate minecraft/items CMD routing JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from texture_alloy.catalog import (
    ARMOR_PIECES,
    BOW_CMD_BASE,
    CROSSBOW_CMD_BASE,
    FISHING_ROD_CMD_BASE,
    MACE_CMD_BASE,
    MATERIALS,
    SHIELD_CMD_BASE,
    TOOLS,
    TRIDENT_CMD_BASE,
    MaterialDef,
    material_index,
    materials_for_tier,
    pearl_materials,
)
from texture_alloy.pack.builders import (
    cmd_entry,
    display_context_select,
    display_context_special,
    model_ref,
    range_dispatch,
    simple_model,
    wrap_model,
)
from texture_alloy.paths import VANILLA_REFS

TRIDENT_HAND_TRANSFORMATION = {
    "left_rotation": [0.0, 0.0, 0.0, 1.0],
    "right_rotation": [0.0, 0.0, 0.0, 1.0],
    "scale": [1.0, -1.0, -1.0],
    "translation": [0.0, 0.0, 0.0],
}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _tier_entries(
    tier: str,
    cmd_attr: str,
    variant: str,
) -> list[dict[str, Any]]:
    entries = []
    for material in materials_for_tier(tier):
        cmd = getattr(material, cmd_attr)
        entries.append(
            cmd_entry(cmd, simple_model(model_ref(material.name, variant)))
        )
    return sorted(entries, key=lambda entry: entry["threshold"])


def _tier_routing(tier: str, item: str, cmd_attr: str, variant: str | None = None) -> dict[str, Any]:
    variant = variant or item
    return wrap_model(
        range_dispatch(
            _tier_entries(tier, cmd_attr, variant),
            simple_model(f"minecraft:item/{tier}_{item}"),
        )
    )


def _ingot_routing(material: MaterialDef) -> dict[str, Any]:
    return wrap_model(
        range_dispatch(
            [cmd_entry(material.ingot_cmd, simple_model(model_ref(material.name)))],
            simple_model(f"minecraft:item/{material.ingot_item}"),
        )
    )


def _spear_routing(tier: str) -> dict[str, Any]:
    entries = []
    for material in materials_for_tier(tier):
        entries.append(
            cmd_entry(
                material.spear_cmd,
                display_context_select(
                    model_ref(material.name, "spear"),
                    model_ref(material.name, "spear_in_hand"),
                ),
            )
        )
    return wrap_model(
        range_dispatch(
            sorted(entries, key=lambda entry: entry["threshold"]),
            display_context_select(
                f"minecraft:item/{tier}_spear",
                f"minecraft:item/{tier}_spear_in_hand",
            ),
        )
    )


def _bow_model(material: MaterialDef) -> dict[str, Any]:
    name = material.name
    return {
        "type": "minecraft:condition",
        "property": "minecraft:using_item",
        "on_false": simple_model(model_ref(name, "bow")),
        "on_true": {
            "type": "minecraft:range_dispatch",
            "property": "minecraft:use_duration",
            "scale": 0.05,
            "fallback": simple_model(model_ref(name, "bow_pulling_0")),
            "entries": [
                {"threshold": 0.65, "model": simple_model(model_ref(name, "bow_pulling_1"))},
                {"threshold": 0.9, "model": simple_model(model_ref(name, "bow_pulling_2"))},
            ],
        },
    }


def _bow_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(BOW_CMD_BASE + material_index(material.name), _bow_model(material))
        for material in MATERIALS
    ]
    return wrap_model(
        range_dispatch(
            entries,
            {
                "type": "minecraft:condition",
                "property": "minecraft:using_item",
                "on_false": simple_model("minecraft:item/bow"),
                "on_true": {
                    "type": "minecraft:range_dispatch",
                    "property": "minecraft:use_duration",
                    "scale": 0.05,
                    "fallback": simple_model("minecraft:item/bow_pulling_0"),
                    "entries": [
                        {"threshold": 0.65, "model": simple_model("minecraft:item/bow_pulling_1")},
                        {"threshold": 0.9, "model": simple_model("minecraft:item/bow_pulling_2")},
                    ],
                },
            },
        )
    )


def _crossbow_model(material: MaterialDef) -> dict[str, Any]:
    name = material.name
    return {
        "type": "minecraft:select",
        "property": "minecraft:charge_type",
        "cases": [
            {"when": "arrow", "model": simple_model(model_ref(name, "crossbow_arrow"))},
            {"when": "rocket", "model": simple_model(model_ref(name, "crossbow_firework"))},
        ],
        "fallback": {
            "type": "minecraft:condition",
            "property": "minecraft:using_item",
            "on_false": simple_model(model_ref(name, "crossbow_standby")),
            "on_true": {
                "type": "minecraft:range_dispatch",
                "property": "minecraft:crossbow/pull",
                "fallback": simple_model(model_ref(name, "crossbow_pulling_0")),
                "entries": [
                    {"threshold": 0.58, "model": simple_model(model_ref(name, "crossbow_pulling_1"))},
                    {"threshold": 1.0, "model": simple_model(model_ref(name, "crossbow_pulling_2"))},
                ],
            },
        },
    }


def _crossbow_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(CROSSBOW_CMD_BASE + material_index(material.name), _crossbow_model(material))
        for material in MATERIALS
    ]
    return wrap_model(
        range_dispatch(
            entries,
            {
                "type": "minecraft:select",
                "property": "minecraft:charge_type",
                "cases": [
                    {"when": "arrow", "model": simple_model("minecraft:item/crossbow_arrow")},
                    {"when": "rocket", "model": simple_model("minecraft:item/crossbow_firework")},
                ],
                "fallback": {
                    "type": "minecraft:condition",
                    "property": "minecraft:using_item",
                    "on_false": simple_model("minecraft:item/crossbow"),
                    "on_true": {
                        "type": "minecraft:range_dispatch",
                        "property": "minecraft:crossbow/pull",
                        "fallback": simple_model("minecraft:item/crossbow_pulling_0"),
                        "entries": [
                            {
                                "threshold": 0.58,
                                "model": simple_model("minecraft:item/crossbow_pulling_1"),
                            },
                            {
                                "threshold": 1.0,
                                "model": simple_model("minecraft:item/crossbow_pulling_2"),
                            },
                        ],
                    },
                },
            },
        )
    )


def _fishing_rod_routing() -> dict[str, Any]:
    entries = []
    for material in MATERIALS:
        name = material.name
        entries.append(
            cmd_entry(
                FISHING_ROD_CMD_BASE + material_index(name),
                {
                    "type": "minecraft:condition",
                    "property": "minecraft:fishing_rod/cast",
                    "on_true": simple_model(model_ref(name, "fishing_rod_cast")),
                    "on_false": simple_model(model_ref(name, "fishing_rod")),
                },
            )
        )
    return wrap_model(
        range_dispatch(entries, simple_model("minecraft:item/fishing_rod"))
    )


def _shield_material_model(material: MaterialDef, *, blocking: bool) -> dict[str, Any]:
    suffix = "shield_blocking" if blocking else "shield_entity"
    return display_context_special(
        model_ref(material.name, "shield"),
        model_ref(material.name, suffix),
    )


def _shield_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(SHIELD_CMD_BASE + material_index(material.name), _shield_material_model(material, blocking=False))
        for material in MATERIALS
    ]
    blocking_entries = [
        cmd_entry(SHIELD_CMD_BASE + material_index(material.name), _shield_material_model(material, blocking=True))
        for material in MATERIALS
    ]
    return {
        "model": {
            "type": "minecraft:condition",
            "property": "minecraft:using_item",
            "on_false": range_dispatch(
                entries,
                {
                    "type": "minecraft:special",
                    "base": "minecraft:item/shield",
                    "model": {"type": "minecraft:shield"},
                },
            ),
            "on_true": range_dispatch(
                blocking_entries,
                {
                    "type": "minecraft:special",
                    "base": "minecraft:item/shield_blocking",
                    "model": {"type": "minecraft:shield"},
                },
            ),
        }
    }


def _mace_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(MACE_CMD_BASE + material_index(material.name), simple_model(model_ref(material.name, "mace")))
        for material in MATERIALS
    ]
    return wrap_model(range_dispatch(entries, simple_model("minecraft:item/mace")))


def _elytra_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(material.elytra_cmd, simple_model(model_ref(material.name, "elytra")))
        for material in MATERIALS
    ]
    return wrap_model(range_dispatch(entries, simple_model("minecraft:item/elytra")))


def _pearl_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(material.pearl_cmd, simple_model(model_ref(material.name, "pearl")))
        for material in pearl_materials()
    ]
    return wrap_model(range_dispatch(entries, simple_model("minecraft:item/ghast_tear")))


def _load_vanilla_model(name: str) -> dict:
    path = VANILLA_REFS / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _vanilla_trident_hand_fallback() -> dict[str, Any]:
    return {
        "type": "minecraft:condition",
        "property": "minecraft:using_item",
        "on_false": {
            "type": "minecraft:special",
            "base": "minecraft:item/trident_in_hand",
            "model": {"type": "minecraft:trident"},
        },
        "on_true": {
            "type": "minecraft:special",
            "base": "minecraft:item/trident_throwing",
            "model": {"type": "minecraft:trident"},
        },
        "transformation": TRIDENT_HAND_TRANSFORMATION,
    }


def _material_trident_gui(material: str) -> dict[str, Any]:
    import copy

    model = copy.deepcopy(_load_vanilla_model("trident"))
    model["textures"]["layer0"] = model_ref(material, "trident")
    return model


def _material_trident_cmd_entry(material: str) -> dict[str, Any]:
    from texture_alloy.catalog import GUI_CONTEXTS

    prefix = model_ref(material, "trident")
    return {
        "type": "minecraft:select",
        "property": "minecraft:display_context",
        "cases": [{"when": GUI_CONTEXTS, "model": simple_model(prefix)}],
        "fallback": _vanilla_trident_hand_fallback(),
    }


def trident_routing() -> dict[str, Any]:
    entries = [
        cmd_entry(
            TRIDENT_CMD_BASE + material_index(material.name),
            _material_trident_cmd_entry(material.name),
        )
        for material in MATERIALS
    ]
    string_cases = [
        {
            "when": f"{material.name}_trident",
            "model": _material_trident_cmd_entry(material.name),
        }
        for material in MATERIALS
    ]
    return wrap_model(
        {
            "type": "minecraft:select",
            "property": "minecraft:custom_model_data",
            "index": 0,
            "cases": string_cases,
            "fallback": range_dispatch(
                entries,
                {
                    "type": "minecraft:select",
                    "property": "minecraft:display_context",
                    "cases": [
                        {
                            "when": ["gui", "ground", "fixed", "on_shelf"],
                            "model": simple_model("minecraft:item/trident"),
                        }
                    ],
                    "fallback": _vanilla_trident_hand_fallback(),
                },
            ),
        }
    )


def write_item_routing(pack: Path) -> int:
    items_dir = pack / "assets" / "minecraft" / "items"
    written = 0

    for material in MATERIALS:
        path = items_dir / f"{material.ingot_item}.json"
        _write_json(path, _ingot_routing(material))
        written += 1

    for tier in ("iron", "diamond", "netherite"):
        for tool in TOOLS:
            path = items_dir / f"{tier}_{tool}.json"
            _write_json(path, _tier_routing(tier, tool, "tool_cmd", tool))
            written += 1
        for piece in ARMOR_PIECES:
            path = items_dir / f"{tier}_{piece}.json"
            _write_json(path, _tier_routing(tier, piece, "armor_cmd", piece))
            written += 1
        path = items_dir / f"{tier}_spear.json"
        _write_json(path, _spear_routing(tier))
        written += 1

    routing_files = {
        "bow.json": _bow_routing(),
        "shield.json": _shield_routing(),
        "crossbow.json": _crossbow_routing(),
        "fishing_rod.json": _fishing_rod_routing(),
        "mace.json": _mace_routing(),
        "elytra.json": _elytra_routing(),
        "ghast_tear.json": _pearl_routing(),
        "trident.json": trident_routing(),
    }
    for filename, payload in routing_files.items():
        _write_json(items_dir / filename, payload)
        written += 1

    return written
