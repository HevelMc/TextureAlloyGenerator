"""JSON builders for Moonaris pack routing."""

from __future__ import annotations

from typing import Any

from texture_alloy.catalog import GUI_CONTEXTS, NAMESPACE


def model_ref(material: str, variant: str | None = None) -> str:
    if variant is None or variant == "ingot":
        return f"{NAMESPACE}:item/{material}"
    return f"{NAMESPACE}:item/{material}_{variant}"


def simple_model(model_id: str) -> dict[str, Any]:
    return {"type": "minecraft:model", "model": model_id}


def wrap_model(model: dict[str, Any]) -> dict[str, Any]:
    return {"model": model}


def range_dispatch(
    entries: list[dict[str, Any]],
    fallback: dict[str, Any],
    *,
    index: int = 0,
) -> dict[str, Any]:
    return {
        "type": "minecraft:range_dispatch",
        "property": "minecraft:custom_model_data",
        "index": index,
        "entries": entries,
        "fallback": fallback,
    }


def display_context_select(gui_model: str, fallback_model: str) -> dict[str, Any]:
    return {
        "type": "minecraft:select",
        "property": "minecraft:display_context",
        "cases": [{"when": GUI_CONTEXTS, "model": simple_model(gui_model)}],
        "fallback": simple_model(fallback_model),
    }


def display_context_special(gui_model: str, special_base: str) -> dict[str, Any]:
    return {
        "type": "minecraft:select",
        "property": "minecraft:display_context",
        "cases": [{"when": GUI_CONTEXTS, "model": simple_model(gui_model)}],
        "fallback": {
            "type": "minecraft:special",
            "base": special_base,
            "model": {"type": "minecraft:shield"},
        },
    }


def cmd_entry(threshold: int, model: dict[str, Any]) -> dict[str, Any]:
    return {"threshold": threshold, "model": model}
