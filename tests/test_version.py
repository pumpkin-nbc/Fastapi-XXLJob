"""Package version tests."""

from __future__ import annotations

import re

import fastapi_xxljob
from fastapi_xxljob._version import __version__ as source_version


def test_version_uses_semantic_release_format():
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", source_version)
    assert fastapi_xxljob.__version__ == source_version
