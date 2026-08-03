"""End-to-end smoke tests."""

from __future__ import annotations

from texture_alloy.pack.writer import write_pack
from texture_alloy.run import generate_material


def test_generate_bronze(tmp_path):
    output = tmp_path / "bronze"
    generate_material("bronze", output)
    pickaxe = output / "assets" / "moonaris" / "textures" / "item" / "bronze_pickaxe.png"
    assert pickaxe.is_file()


def test_write_pack_json(tmp_path):
    counts = write_pack(tmp_path)
    assert counts["models"] == 180
    assert counts["shield_items"] == 6
    assert counts["equipment"] == 12
    assert counts["routing"] == 43
    assert (tmp_path / "pack.mcmeta").is_file()
    assert (tmp_path / "assets" / "minecraft" / "items" / "bow.json").is_file()
