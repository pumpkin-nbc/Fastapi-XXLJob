"""Package version tests."""

from __future__ import annotations

import fastapi_xxljob
from fastapi_xxljob._version import __version__ as source_version


def test_version_is_0_1_0():
    assert source_version == "0.1.0"
    assert fastapi_xxljob.__version__ == source_version
