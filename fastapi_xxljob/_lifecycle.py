"""Internal executor-registration lifecycle helpers."""

from __future__ import annotations

import logging
import weakref
from typing import TYPE_CHECKING

from .runtime import XXLJobRuntime

if TYPE_CHECKING:
    from fastapi import FastAPI


def install_runtime_finalizer(
    app: "FastAPI", runtime: XXLJobRuntime
) -> "weakref.finalize":
    """Close a runtime when its FastAPI app is collected or at process exit."""
    return weakref.finalize(app, safe_close_runtime, runtime)


def safe_close_runtime(runtime: XXLJobRuntime) -> None:
    """Close quietly during garbage collection or interpreter teardown."""
    try:
        runtime.close()
    except Exception:  # noqa: BLE001 - interpreter shutdown must remain quiet
        try:
            logging.getLogger("fastapi_xxljob.lifecycle").exception(
                "Unexpected error while finalizing FastAPI-XXLJob runtime."
            )
        except Exception:  # noqa: BLE001 - logging may already be unavailable
            pass
