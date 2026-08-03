"""Repository path constants."""

from __future__ import annotations

from pathlib import Path

from texture_alloy.env import ROOT, _env_path

CONFIG = ROOT / "config"
GENERATOR_MANIFEST = CONFIG / "moonaris_generator.json"
TIC_TEMPLATES = ROOT / "templates" / "tic"
VANILLA_REFS = ROOT / "templates" / "vanilla_refs"
MATERIALS = ROOT / "materials" / "moonaris"
GENERATED = ROOT / "generated"
TIC_CACHE = ROOT / ".cache" / "TinkersConstruct"
VANILLA_CACHE = ROOT / ".cache" / "vanilla_tools"

MOONARIS_PACK = _env_path("MOONARIS_PACK")
MOONARIS_DATAPACK = _env_path("MOONARIS_DATAPACK") or (GENERATED / "moonaris_datapack")
