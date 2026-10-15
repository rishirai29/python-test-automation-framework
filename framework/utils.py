"""Small reusable helpers shared by all test layers."""
import json
from pathlib import Path

from framework.config import TESTDATA_DIR


def load_json(name: str):
    return json.loads(Path(TESTDATA_DIR, name).read_text(encoding="utf-8"))


def price_to_float(text: str) -> float:
    """'$29.99' -> 29.99"""
    return float(text.replace("$", "").replace(",", "").strip())


def is_sorted(values, reverse: bool = False) -> bool:
    return list(values) == sorted(values, reverse=reverse)
