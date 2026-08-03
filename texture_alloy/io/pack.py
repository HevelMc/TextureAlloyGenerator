"""Minecraft resource pack path resolution."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

from texture_alloy.io.png import load_rgba


def find_assets_root(input_root: Path) -> Path:
    input_root = input_root.resolve()
    if (input_root / "assets").is_dir():
        return input_root / "assets"
    return input_root



class PackContext:
    """Read-only context for loading textures from a resource pack."""

    def __init__(self, input_root: Path) -> None:
        self.input_root = input_root.resolve()
        self._texture_roots = self._find_texture_roots()

    def _find_texture_roots(self) -> list[Path]:
        roots: list[Path] = []
        if (self.input_root / "assets").is_dir():
            for ns_dir in sorted((self.input_root / "assets").iterdir()):
                tex = ns_dir / "textures"
                if tex.is_dir():
                    roots.append(tex)
        else:
            # input_root might already be assets/ or a textures folder
            if self.input_root.name == "textures":
                roots.append(self.input_root)
            else:
                for tex in sorted(self.input_root.rglob("textures")):
                    if tex.is_dir():
                        roots.append(tex)
        return roots

    def resolve_texture(self, texture_ref: str) -> Path:
        """Resolve texture path like 'block/oak_planks.png' or 'namespace:block/oak'."""
        ref = texture_ref.replace("\\", "/")
        if ref.endswith(".png"):
            ref = ref[:-4]

        namespace = None
        if ":" in ref:
            namespace, ref = ref.split(":", 1)

        candidates: list[Path] = []
        for root in self._texture_roots:
            if namespace and root.parent.name != namespace:
                continue
            candidates.append(root / f"{ref}.png")

        if namespace is None:
            for root in self._texture_roots:
                candidates.append(root / f"{ref}.png")

        for path in candidates:
            if path.is_file():
                return path

        raise FileNotFoundError(f"Texture not found: {texture_ref} (searched {candidates[:3]}...)")

    @lru_cache(maxsize=128)
    def load_texture(self, texture_ref: str) -> np.ndarray:
        return load_rgba(self.resolve_texture(texture_ref))
