"""Application and runtime lifecycle tests."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_xxljob import FastAPIXXLJob
from fastapi_xxljob._app import ApplicationRegistry
from fastapi_xxljob._lifecycle import install_runtime_finalizer, safe_close_runtime
from fastapi_xxljob.exceptions import XXLJobConfigError, XXLJobError


def config(**overrides):
    values = {
        "XXL_JOB_ADMIN_ADDRESSES": ["http://admin:8080/xxl-job-admin"],
        "XXL_JOB_EXECUTOR_APP_NAME": "lifecycle-app",
        "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:5001",
        "XXL_JOB_AUTO_REGISTER": False,
    }
    values.update(overrides)
    return values


def test_application_registry_explicit_and_discard():
    registry = ApplicationRegistry()
    app = FastAPI(title="explicit")
    assert registry.resolve(app) is app
    registry.add(app)
    assert tuple(registry.snapshot()) == (app,)
    registry.discard(app)
    registry.discard(app)
    assert registry.is_empty
    with pytest.raises(XXLJobError, match="No FastAPI application"):
        registry.resolve()


def test_multiple_applications_require_explicit_app():
    extension = FastAPIXXLJob()
    app_a = FastAPI(title="a")
    app_b = FastAPI(title="b")
    extension.init_app(app_a, config())
    extension.init_app(app_b, config())
    with pytest.raises(XXLJobError, match="Multiple FastAPI applications"):
        extension.get_status()
    assert extension.get_status(app_a).enabled is True


def test_auto_registration_starts_only_inside_lifespan(mocker):
    app = FastAPI(title="lifespan")
    FastAPIXXLJob(app, config(XXL_JOB_AUTO_REGISTER=True))
    runtime = app.state.xxljob
    start = mocker.patch.object(runtime.registry_service, "start")
    close = mocker.patch.object(runtime, "close")
    assert start.call_count == 0
    with TestClient(app):
        start.assert_called_once_with()
    close.assert_called_once_with()


def test_host_and_extension_lifespans_are_composed(mocker):
    events = []

    @asynccontextmanager
    async def host_lifespan(_app):
        events.append("host-start")
        try:
            yield
        finally:
            events.append("host-stop")

    app = FastAPI(title="composed", lifespan=host_lifespan)
    FastAPIXXLJob(app, config(XXL_JOB_AUTO_REGISTER=True))
    runtime = app.state.xxljob
    mocker.patch.object(
        runtime.registry_service,
        "start",
        side_effect=lambda: events.append("registry-start"),
    )
    mocker.patch.object(runtime, "close", side_effect=lambda: events.append("runtime-stop"))

    with TestClient(app):
        assert "host-start" in events
        assert "registry-start" in events

    assert "runtime-stop" in events
    assert "host-stop" in events


def test_disabled_is_total_switch_without_routes_or_network(mocker):
    post = mocker.patch("fastapi_xxljob.client.requests.post")
    app = FastAPI(title="disabled")
    extension = FastAPIXXLJob(
        app,
        {
            "XXL_JOB_ENABLED": False,
            "XXL_JOB_AUTO_REGISTER": True,
            "XXL_JOB_ADMIN_ADDRESSES": ["not a URL"],
            "XXL_JOB_EXECUTOR_ADDRESS": "also not a URL",
            "XXL_JOB_ROUTE_PREFIX": "//unused/<path:value>? ",
        },
    )
    route_paths = {getattr(route, "path", None) for route in app.routes}
    assert not {"/beat", "/idleBeat", "/run", "/kill", "/log"} & route_paths
    results = [
        extension.register_executor_sync(app),
        extension.remove_executor_sync(app),
        extension.callback_sync(1, 2, 200, app=app),
        asyncio.run(extension.callback_success(1, 2, app=app)),
    ]
    assert all(result.success is False for result in results)
    assert all(result.error_type == "config" for result in results)
    post.assert_not_called()


def test_enabled_protocol_only_does_not_require_admin_configuration():
    app = FastAPI(title="protocol-only")
    extension = FastAPIXXLJob(
        app,
        {
            "XXL_JOB_ENABLED": True,
            "XXL_JOB_AUTO_REGISTER": False,
            "XXL_JOB_ADMIN_ADDRESSES": [],
            "XXL_JOB_EXECUTOR_ADDRESS": "",
        },
    )
    assert extension.get_status(app).registry_thread_running is False
    with TestClient(app) as client:
        responses = {
            "/beat": client.post("/beat"),
            "/idleBeat": client.post("/idleBeat", json={}),
            "/run": client.post("/run", json={}),
            "/kill": client.post("/kill", json={}),
            "/log": client.post("/log", json={}),
        }
    assert responses["/beat"].json()["code"] == 200
    assert all(response.status_code == 200 for response in responses.values())
    assert all(
        response.json()["code"] == 500
        for path, response in responses.items()
        if path != "/beat"
    )


@pytest.mark.parametrize("removed_value", [False, True, "false"])
def test_removed_config_is_always_rejected(removed_value):
    app = FastAPI(title="removed")
    with pytest.raises(XXLJobConfigError, match="已删除"):
        FastAPIXXLJob(
            app,
            {
                "XXL_JOB_ENABLED": False,
                "XXL_JOB_AUTO_REGISTER_ON_INIT": removed_value,
            },
        )


def test_install_runtime_finalizer_uses_app_lifetime(mocker):
    app = FastAPI(title="finalizer")
    runtime = mocker.Mock()
    finalize = mocker.patch("fastapi_xxljob._lifecycle.weakref.finalize")
    result = install_runtime_finalizer(app, runtime)
    finalize.assert_called_once_with(app, safe_close_runtime, runtime)
    assert result is finalize.return_value


def test_safe_close_runtime_swallows_errors(mocker):
    runtime = mocker.Mock()
    runtime.close.side_effect = RuntimeError("shutdown")
    safe_close_runtime(runtime)
    runtime.close.assert_called_once_with()
