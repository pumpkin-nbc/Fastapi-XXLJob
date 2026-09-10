"""
FastAPI-XXLJob 命令行接口。

FastAPI-XXLJob command-line interface.
"""

from __future__ import annotations

from .commands import build_parser, main

__all__ = ["build_parser", "main"]
