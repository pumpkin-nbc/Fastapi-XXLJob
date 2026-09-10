"""Supported FastAPI version range checks."""

from __future__ import annotations

import re

import fastapi


def _release(version: str):
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    assert match is not None, "FastAPI must expose a semantic release version"
    return tuple(int(part) for part in match.groups())


def test_installed_fastapi_is_in_supported_range():
    release = _release(fastapi.__version__)
    assert release >= (0, 124, 4)
    assert release < (1, 0, 0)
