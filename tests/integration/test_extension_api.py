"""Public extension API integration tests."""

from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI

from fastapi_xxljob import (
    CallResult,
    FastAPIXXLJob,
    XXLJobAlreadyInitializedError,
    XXLJobCallbackRegistrationError,
    XXLJobResponse,
)
from tests.conftest import BASE_CONFIG, make_app


def test_duplicate_initialization_and_atomic_registration():
    app, extension = make_app()
    with pytest.raises(XXLJobAlreadyInitializedError):
        extension.init_app(app, BASE_CONFIG)

    def first(_request):
        return XXLJobResponse.success()

    extension.register_callbacks(app, run={"first": first})
    with pytest.raises(XXLJobCallbackRegistrationError):
        extension.register_callbacks(
            app,
            run={"second": first},
            idle_beat="not callable",  # type: ignore[arg-type]
        )
    assert extension.get_run_callback(app, "first") is first
    assert extension.get_run_callback(app, "second") is None


def test_application_level_set_get_and_replace():
    app, extension = make_app()

    def one(_request):
        return XXLJobResponse.success(content=1)

    def two(_request):
        return XXLJobResponse.success(content=2)

    extension.set_run_callback(app, "handler", one)
    assert extension.get_run_callback(app, "handler") is one
    with pytest.raises(XXLJobCallbackRegistrationError):
        extension.set_run_callback(app, "handler", two)
    extension.set_run_callback(app, "handler", two, replace=True)
    assert extension.get_run_callback(app, "handler") is two


def test_async_admin_methods_delegate_to_sync_core(mocker):
    app, extension = make_app()
    runtime = app.state.xxljob
    registered = CallResult(success=True, code=200, address="http://admin")
    removed = CallResult(success=True, code=200, address="http://admin")
    mocker.patch.object(
        runtime.registry_service, "register_once_result", return_value=registered
    )
    mocker.patch.object(
        runtime.registry_service, "remove_once_result", return_value=removed
    )
    assert asyncio.run(extension.register_executor(app)) is registered
    assert asyncio.run(extension.remove_executor(app)) is removed


def test_async_and_sync_result_callbacks(mocker):
    app, extension = make_app()
    response = mocker.Mock(status_code=200)
    response.json.return_value = {"code": 200, "msg": "ok"}
    post = mocker.patch("fastapi_xxljob.client.requests.post", return_value=response)
    sync_result = extension.callback_success_sync(1, 2, "sync", app)
    async_result = asyncio.run(extension.callback_failure(3, 4, "async", app))
    batch_result = asyncio.run(
        extension.callback_many(
            [{"log_id": 5, "log_date_time": 6, "handle_code": 200}], app
        )
    )
    assert sync_result.success and async_result.success and batch_result.success
    assert post.call_count == 3


def test_lifecycle_controls_and_status(mocker):
    app, extension = make_app()
    service = app.state.xxljob.registry_service
    start = mocker.patch.object(service, "start")
    stop = mocker.patch.object(service, "stop")
    extension.start_registry(app)
    extension.stop_registry(app, remove=True)
    start.assert_called_once_with()
    stop.assert_called_once_with(remove=True)
    status = extension.get_status(app)
    assert status.enabled is True
    assert status.auto_register is False


def test_constructor_config_without_app_is_rejected():
    with pytest.raises(Exception, match="config requires an app"):
        FastAPIXXLJob(config=BASE_CONFIG)


def test_factory_style_initialization():
    extension = FastAPIXXLJob()

    @extension.on_run("factoryHandler")
    async def handler(_request):
        return XXLJobResponse.success()

    app = FastAPI(title="factory")
    extension.init_app(app, BASE_CONFIG)
    assert extension.get_run_callback(app, "factoryHandler") is handler
