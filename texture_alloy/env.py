"""Load repository .env and resolve path settings."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")


def _env_path(name: str, *, required: bool = False) -> Path | None:
    value = os.environ.get(name)
    if not value:
        if required:
            raise RuntimeError(
                f"{name} is not set. Copy .env.example to .env and set {name}."
            )
        return None
    return Path(value).expanduser()
