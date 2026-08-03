"""Moonaris job definitions and manifest loading."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from texture_alloy.materials.base import Material
from texture_alloy.moonaris.tic import tc_item_key
from texture_alloy.moonaris.vanilla import HANDHELD_TOOLS as VANILLA_HANDHELD, VANILLA_CACHE
from texture_alloy.paths import GENERATOR_MANIFEST


@dataclass
class MoonarisItem:
    """One generatable texture entry."""

    template_name: str
    output_name: str
    category: str
    template_path: Path
    output_path: Path
    source: str = "template"


@dataclass
class MoonarisJob:
    item: MoonarisItem
    material_name: str
    material: Material


def load_manifest() -> dict:
    return json.loads(GENERATOR_MANIFEST.read_text(encoding="utf-8"))


def load_moonaris_material_opts(materials_dir: str | Path | None, material_name: str) -> dict:
    if not materials_dir:
        return {}
    base = Path(materials_dir)
    path = base / "moonaris" / f"{material_name}.json"
    if not path.is_file():
        path = base / f"{material_name}.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(data.get("moonaris", {}))


def material_item_tier(material_name: str, opts: dict) -> str:
    return opts.get("vanilla_tool_tier", "iron")


def _output_path(output_root: Path, namespace: str, category: str, material: str, template_name: str) -> Path:
    base = output_root / "assets" / namespace / "textures"
    if template_name == "ingot":
        filename = f"{material}.png"
    elif category == "item":
        filename = f"{material}_{template_name}.png" if template_name != "ingot" else f"{material}.png"
    else:
        filename = f"{material}.png"
    if category == "item":
        return base / "item" / filename
    if category == "equipment_humanoid":
        return base / "entity" / "equipment" / "humanoid" / filename
    if category == "equipment_leggings":
        return base / "entity" / "equipment" / "humanoid_leggings" / filename
    if category == "equipment_wings":
        return base / "entity" / "equipment" / "wings" / filename
    raise ValueError(f"Unknown category: {category}")


def build_moonaris_jobs(
    output_root: Path,
    materials: dict[str, Material],
    material_filter: set[str] | None = None,
) -> tuple[list[MoonarisJob], list[str]]:
    manifest = load_manifest()
    namespace = manifest.get("namespace", "moonaris")
    items = manifest.get("items", [])
    jobs: list[MoonarisJob] = []
    missing: list[str] = []

    for mat_name, material in sorted(materials.items()):
        if material_filter and mat_name not in material_filter:
            continue
        for entry in items:
            template_name = entry["template"]
            category = entry.get("category", "item")
            exclude_materials = set(entry.get("exclude_materials", []))
            if mat_name in exclude_materials:
                continue
            source = entry.get("source", "template")
            tc_key = tc_item_key(template_name, category)
            tpl_path = VANILLA_CACHE / f"{template_name}.png"

            if source == "vanilla":
                if template_name not in VANILLA_HANDHELD:
                    missing.append(f"vanilla:{template_name}")
                    continue
                tpl_path = VANILLA_CACHE / f"iron_{template_name}.png"
            elif source == "vanilla_item":
                tpl_path = VANILLA_CACHE / f"{template_name}.png"
            elif source == "vanilla_spear":
                tpl_path = VANILLA_CACHE / "iron_spear.png"
            elif source in {"vanilla_bow", "vanilla_crossbow"}:
                tpl_path = VANILLA_CACHE / f"{template_name}.png"
            elif source == "vanilla_spear_in_hand":
                tpl_path = VANILLA_CACHE / "iron_spear_in_hand.png"
            elif source == "vanilla_shield_entity":
                tpl_path = VANILLA_CACHE / "shield_base.png"
            elif source == "vanilla_mace":
                tpl_path = VANILLA_CACHE / "mace.png"
            elif source == "vanilla_pearl":
                tpl_path = VANILLA_CACHE / "ghast_tear.png"
            elif source == "tconstruct":
                if tc_key is None:
                    missing.append(f"tconstruct:{category}:{template_name}")
                    continue
            elif source != "template":
                missing.append(f"unsupported source: {source}")
                continue

            out_path = _output_path(output_root, namespace, category, mat_name, template_name)
            if template_name == "ingot":
                out_name = f"{mat_name}"
            elif category == "item":
                out_name = f"{mat_name}_{template_name}"
            else:
                out_name = mat_name
            jobs.append(
                MoonarisJob(
                    item=MoonarisItem(
                        template_name=template_name,
                        output_name=out_name,
                        category=category,
                        template_path=tpl_path,
                        output_path=out_path,
                        source=source,
                    ),
                    material_name=mat_name,
                    material=material,
                )
            )

    return jobs, missing


def write_pack_mcmeta(output_root: Path, description: str = "Moonaris material textures") -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    pack = {"pack": {"pack_format": 34, "description": description}}
    (output_root / "pack.mcmeta").write_text(json.dumps(pack, indent=2) + "\n", encoding="utf-8")
