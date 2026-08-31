"""FastAPI adapter for the official XXL-JOB 2.4.1 executor protocol."""

from __future__ import annotations

import logging

from ._version import __version__
from .client import AdminCallResult, CallResult
from .config import XXLJobConfig
from .exceptions import (
    FastAPIXXLJobError,
    XXLJobAdminCallError,
    XXLJobAlreadyInitializedError,
    XXLJobCallbackError,
    XXLJobCallbackRegistrationError,
    XXLJobConfigError,
    XXLJobConfigurationError,
    XXLJobError,
    XXLJobInitializationError,
    XXLJobProtocolError,
    XXLJobRegistryError,
    XXLJobRequestError,
    XXLJobValidationError,
)
from .extension import FastAPIXXLJob
from .model.callback import CallbackRequest
from .model.idle_beat import IdleBeatRequest
from .model.kill import KillRequest
from .model.log import LogRequest
from .model.registry import RegistryRequest
from .model.trigger import TriggerRequest
from .response.executor import XXLJobResponse
from .response.log import LogResponse
from .status import XXLJobStatus

logging.getLogger("fastapi_xxljob").addHandler(logging.NullHandler())

__all__ = [
    "__version__",
    "FastAPIXXLJob",
    "XXLJobConfig",
    "TriggerRequest",
    "IdleBeatRequest",
    "KillRequest",
    "LogRequest",
    "LogResponse",
    "CallbackRequest",
    "RegistryRequest",
    "XXLJobResponse",
    "CallResult",
    "AdminCallResult",
    "XXLJobStatus",
    "FastAPIXXLJobError",
    "XXLJobError",
    "XXLJobConfigError",
    "XXLJobConfigurationError",
    "XXLJobInitializationError",
    "XXLJobAlreadyInitializedError",
    "XXLJobCallbackRegistrationError",
    "XXLJobValidationError",
    "XXLJobRequestError",
    "XXLJobProtocolError",
    "XXLJobAdminCallError",
    "XXLJobCallbackError",
    "XXLJobRegistryError",
]
