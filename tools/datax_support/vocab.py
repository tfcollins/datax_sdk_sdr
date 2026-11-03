"""Vocabulary and schema shipped with the package."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

STATUS_RANK = {"planned": 1, "integration-artifacts": 2, "validated": 3}
STATUS_TEXT = {
    "planned": "planned",
    "integration-artifacts": "integration artifacts",
    "validated": "validated",
}


def _read(name: str) -> dict:
    with resources.files("datax_support.data").joinpath(name).open("rb") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def load() -> dict:
    """The vocabulary: platforms, features, capabilities, repos, statuses."""
    return _read("vocabulary.json")


@lru_cache(maxsize=None)
def schema() -> dict:
    """The JSON Schema for a support manifest."""
    return _read("schema.json")
