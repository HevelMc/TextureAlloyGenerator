# Moonaris texture generator

Python tool that builds **Moonaris-alliages** resource-pack textures for Minecraft 26.2.

It composites Tinkers' Construct greyscale parts and vanilla tool silhouettes with alloy palettes from JSON, then installs the PNGs into your Moonaris pack. It also writes pack JSON (equipment layers, trident CMD routing) and a small datapack with one `/function moonaris:give/<alloy>` per material.

## Usage

```bash
cp .env.example .env   # set MOONARIS_PACK to your resource pack folder
pip install -e .
python generate.py
```

Generates all six alloys (bronze, acier, ombralite, titane, obsidian, moonarium), rebuilds the full resource pack (textures + all JSON), and syncs it to `MOONARIS_PACK`. Datapack output goes to `generated/moonaris_datapack/` (override with `MOONARIS_DATAPACK` in `.env`).

## Customization

- Alloy colors and options: `materials/moonaris/*.json` (palette, `vanilla_tool_tier`, `ingot_shape`, etc.)
- CMD values, tiers, pack metadata, shield displays: `config/moonaris_pack.json`
- Texture generation manifest: `config/moonaris_generator.json`
- Compositing inputs: `templates/tic/` (TiC parts), `templates/vanilla_refs/` (vanilla sprites)
