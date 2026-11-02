"""Loads the editable taxonomy (categories, tones, lexicons, templates).

The taxonomy lives in taxonomy.json so categories and vocabulary can be
changed without code changes.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")


@lru_cache
def get_taxonomy() -> dict[str, Any]:
    with TAXONOMY_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def public_options() -> dict[str, Any]:
    """Subset of the taxonomy that is safe and useful to expose to the frontend."""
    t = get_taxonomy()
    return {
        "knowledge_categories": list(t["knowledge_categories"].keys()),
        "post_types": t["post_types"],
        "tones": t["tones"],
        "emotions": t["emotions"],
        "audiences": t["audiences"],
        "lengths": t["length_options"],
        "cta_types": t["cta_types"],
    }
