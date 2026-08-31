"""Public exception-hierarchy tests."""

from __future__ import annotations

import fastapi_xxljob
from fastapi_xxljob.exceptions import (
    FastAPIXXLJobError,
    XXLJobAdminCallError,
    XXLJobAlreadyInitializedError,
    XXLJobCallbackError,
    XXLJobCallbackRegistrationError,
    XXLJobConfigError,
    XXLJobConfigurationError,
    XXLJobError,
    XXLJobInitializationError,
    XXLJobRegistryError,
    XXLJobRequestError,
    XXLJobValidationError,
)


def test_base_alias():
    assert XXLJobError is FastAPIXXLJobError
    assert issubclass(FastAPIXXLJobError, Exception)


def test_config_aliases():
    assert XXLJobConfigError is XXLJobConfigurationError
    assert issubclass(XXLJobConfigurationError, FastAPIXXLJobError)


def test_validation_aliases():
    assert XXLJobRequestError is XXLJobValidationError
    assert issubclass(XXLJobValidationError, FastAPIXXLJobError)


def test_initialization_hierarchy():
    assert issubclass(XXLJobInitializationError, FastAPIXXLJobError)
    assert issubclass(XXLJobAlreadyInitializedError, XXLJobInitializationError)


def test_admin_call_hierarchy():
    assert issubclass(XXLJobAdminCallError, FastAPIXXLJobError)
    assert issubclass(XXLJobCallbackError, XXLJobAdminCallError)
    assert issubclass(XXLJobRegistryError, XXLJobAdminCallError)


def test_callback_registration_error():
    assert issubclass(XXLJobCallbackRegistrationError, FastAPIXXLJobError)


def test_all_public_exceptions_catchable_as_base():
    for exc_cls in (
        XXLJobConfigurationError,
        XXLJobInitializationError,
        XXLJobAlreadyInitializedError,
        XXLJobCallbackRegistrationError,
        XXLJobValidationError,
        XXLJobAdminCallError,
        XXLJobCallbackError,
        XXLJobRegistryError,
    ):
        try:
            raise exc_cls("boom")
        except FastAPIXXLJobError:
            pass


def test_exceptions_exported_from_package():
    for name in (
        "FastAPIXXLJobError",
        "XXLJobError",
        "XXLJobConfigError",
        "XXLJobConfigurationError",
        "XXLJobInitializationError",
        "XXLJobAlreadyInitializedError",
        "XXLJobCallbackRegistrationError",
        "XXLJobValidationError",
        "XXLJobRequestError",
        "XXLJobAdminCallError",
        "XXLJobCallbackError",
        "XXLJobRegistryError",
    ):
        assert name in fastapi_xxljob.__all__
        assert hasattr(fastapi_xxljob, name)
