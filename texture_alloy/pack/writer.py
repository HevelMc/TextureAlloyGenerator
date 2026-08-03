"""Write full Moonaris resource pack JSON and sync to target."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from texture_alloy.catalog import MATERIALS, NAMESPACE, PACK_META
from texture_alloy.pack.models import write_item_models, write_shield_items
from texture_alloy.pack.routing import write_item_routing
from texture_alloy.paths import PACK_ICON


def write_equipment(pack: Path) -> int:
    out_dir = pack / "assets" / NAMESPACE / "equipment"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for material in MATERIALS:
        texture = f"{NAMESPACE}:{material.name}"
        armor = {
            "layers": {
                "horse_body": [{"texture": texture}],
                "humanoid": [{"texture": texture}],
                "humanoid_leggings": [{"texture": texture}],
            }
        }
        elytra = {"layers": {"wings": [{"texture": texture}]}}
        (out_dir / f"{material.name}.json").write_text(
            json.dumps(armor, indent=2) + "\n",
            encoding="utf-8",
        )
        (out_dir / f"{material.name}_elytra.json").write_text(
            json.dumps(elytra, indent=2) + "\n",
            encoding="utf-8",
        )
        written += 2
    return written


def write_pack_meta(pack: Path) -> None:
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "pack.mcmeta").write_text(
        json.dumps({"pack": PACK_META}, indent=2) + "\n",
        encoding="utf-8",
    )


def write_pack_icon(pack: Path) -> None:
    if not PACK_ICON.is_file():
        raise FileNotFoundError(f"Pack icon not found: {PACK_ICON}")
    shutil.copy2(PACK_ICON, pack / "pack.png")


def write_pack(pack: Path) -> dict[str, int]:
    write_pack_meta(pack)
    write_pack_icon(pack)
    return {
        "models": write_item_models(pack),
        "shield_items": write_shield_items(pack),
        "equipment": write_equipment(pack),
        "routing": write_item_routing(pack),
    }


def sync_pack(staging: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for rel in ("assets", "pack.mcmeta", "pack.png"):
        src = staging / rel
        dst = target / rel
        if not src.exists():
            continue
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
