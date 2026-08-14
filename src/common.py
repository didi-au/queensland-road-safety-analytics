from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def snake_case(value: str) -> str:
    value = value.strip().replace("+", "plus")
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    return value.strip("_").lower()


def latest_raw_dir(raw_root: Path | None = None) -> Path:
    root = raw_root or PROJECT_ROOT / "data" / "raw"
    retrieval_id = (root / "LATEST").read_text(encoding="utf-8").strip()
    directory = root / retrieval_id
    if not (directory / "manifest.json").exists():
        raise FileNotFoundError(f"Missing manifest for retrieval {retrieval_id}")
    return directory


def read_manifest(raw_dir: Path) -> dict[str, Any]:
    return json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))
