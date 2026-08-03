"""Alpha-over layer compositing."""

from __future__ import annotations

import numpy as np
from PIL import Image

from texture_alloy.io.png import numpy_to_pil


def alpha_composite_layers(layers: list[np.ndarray]) -> np.ndarray:
    """Composite layers bottom-to-top using alpha-over."""
    if not layers:
        raise ValueError("No layers to composite")
    result = numpy_to_pil(layers[0])
    for layer in layers[1:]:
        overlay = numpy_to_pil(layer)
        result = Image.alpha_composite(result, overlay)
    return np.array(result, dtype=np.uint8)
