"""Material type definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from texture_alloy.io.pack import PackContext


@dataclass
class Material:
    name: str

    @abstractmethod
    def transform_layer(self, rgba: np.ndarray, ctx: PackContext) -> np.ndarray:
        """Transform a layer RGBA array (HxWx4 uint8)."""
