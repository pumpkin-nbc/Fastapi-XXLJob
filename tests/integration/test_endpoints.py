"""FastAPI executor endpoint integration tests."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_xxljob import FastAPIXXLJob, LogResponse, XXLJobResponse
from fastapi_xxljob._app import ProtocolErrorMiddleware
from tests.conftest import BASE_CONFIG, make_app


def test_beat_and_access_token():
    app, _ = make_app(XXL_JOB_ACCESS_TOKEN="token")
    with TestClient(app) as client:
        denied = client.post("/beat")
        accepted = client.post(
            "/beat", headers={"XXL-JOB-ACCESS-TOKEN": "token"}
        )
    assert denied.status_code == 200
    assert denied.json()["code"] == 500
    assert accepted.json() == {"code": 200, "msg": None, "content": None}


def test_named_run_dispatches_sync_and_async_handlers():
    app, extension = make_app()

    @extension.on_run("syncHandler")
    def sync_handler(request):
        return XXLJobResponse.success(content=request.parse_params())

    @extension.on_run("asyncHandler")
    async def async_handler(request):
        return XXLJobResponse.success(content=request.job_id)

    with TestClient(app) as client:
        sync_response = client.post(
            "/run",
            json={
                "jobId": 1,
                "executorHandler": "syncHandler",
                "executorParams": '{"name":"pumpkin"}',
            },
        )
        async_response = client.post(
            "/run", json={"jobId": 2, "executorHandler": "asyncHandler"}
        )
        unknown = client.post(
            "/run", json={"executorHandler": "missingHandler"}
        )
    assert sync_response.json()["content"] == {"name": "pumpkin"}
    assert async_response.json()["content"] == 2
    assert unknown.json()["msg"] == "Unsupported JobHandler: missingHandler"


def test_idle_beat_kill_and_log_callbacks_support_both_styles():
    app, extension = make_app()

    @extension.on_idle_beat
    async def idle(request):
        return XXLJobResponse.success(content=request.job_id)

    @extension.on_kill
    def kill(request):
        return XXLJobResponse.success(content=request.job_id)

    @extension.on_log
    async def log(request):
        return LogResponse(
            from_line_num=request.from_line_num,
            to_line_num=request.from_line_num + 1,
            log_content="done",
            is_end=True,
        )

    with TestClient(app) as client:
        idle_response = client.post("/idleBeat", json={"jobId": 3})
        kill_response = client.post("/kill", json={"jobId": 4})
        log_response = client.post("/log", json={"fromLineNum": 5})
    assert idle_response.json()["content"] == 3
    assert kill_response.json()["content"] == 4
    assert log_response.json()["content"] == {
        "fromLineNum": 5,
        "toLineNum": 6,
        "logContent": "done",
        "isEnd": True,
    }


def test_protocol_errors_are_http_200_xxljob_json():
    app, extension = make_app()

    @extension.on_run("raises")
    def raises(_request):
        raise RuntimeError("private detail")

    @extension.on_run("badResult")
    def bad_result(_request):
        return {"code": 200}

    with TestClient(app) as client:
        invalid_json = client.post(
            "/run", content=b"{", headers={"Content-Type": "application/json"}
        )
        array_body = client.post("/run", json=[])
        bad_field = client.post("/run", json={"executorHandler": []})
        raised = client.post("/run", json={"executorHandler": "raises"})
        bad_result_response = client.post(
            "/run", json={"executorHandler": "badResult"}
        )
    for response in (
        invalid_json,
        array_body,
        bad_field,
        raised,
        bad_result_response,
    ):
        assert response.status_code == 200
        assert response.json()["code"] == 500
        assert "private detail" not in response.text


def test_protocol_405_is_scoped_and_host_get_route_is_preserved():
    app = FastAPI(title="routing")

    @app.get("/beat")
    def host_beat():
        return {"host": True}

    FastAPIXXLJob(app, BASE_CONFIG)
    with TestClient(app) as client:
        host = client.get("/beat")
        protocol_405 = client.put("/beat")
        unrelated = client.get("/does-not-exist")
    assert host.json() == {"host": True}
    assert protocol_405.status_code == 200
    assert protocol_405.json()["code"] == 500
    assert unrelated.status_code == 404


def test_route_prefix_and_post_conflict():
    app, extension = make_app(XXL_JOB_ROUTE_PREFIX="/xxl-job/")

    @extension.on_run("prefixed")
    def prefixed(_request):
        return XXLJobResponse.success()

    with TestClient(app) as client:
        assert client.post("/xxl-job/beat").json()["code"] == 200
        assert client.post("/beat").status_code == 404

    conflicting = FastAPI(title="conflicting")

    @conflicting.post("/run")
    def host_run():
        return {"host": True}

    try:
        FastAPIXXLJob(conflicting, BASE_CONFIG)
    except Exception as exc:  # narrow assertion kept below for Python 3.8 typing
        assert "route conflict" in str(exc)
    else:
        raise AssertionError("route conflict was not rejected")


@pytest.mark.parametrize("path", ["/beat", "/run", "/idleBeat", "/kill", "/log"])
def test_access_token_failure_for_every_protocol_endpoint(path):
    app, _ = make_app(XXL_JOB_ACCESS_TOKEN="secret")
    with TestClient(app) as client:
        response = client.post(path, json={})
    assert response.status_code == 200
    assert response.json()["code"] == 500
    assert "secret" not in response.text


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/run", {"executorHandler": []}),
        ("/idleBeat", {"jobId": []}),
        ("/kill", {"jobId": []}),
        ("/log", {"logId": []}),
    ],
)
def test_invalid_fields_for_body_endpoints(path, payload):
    app, extension = make_app()

    @extension.on_run("handler")
    def run(_request):
        return XXLJobResponse.success()

    @extension.on_idle_beat
    def idle(_request):
        return XXLJobResponse.success()

    @extension.on_kill
    def kill(_request):
        return XXLJobResponse.success()

    @extension.on_log
    def log(_request):
        return LogResponse()

    with TestClient(app) as client:
        response = client.post(path, json=payload)
    assert response.status_code == 200
    assert response.json()["code"] == 500
    assert "invalid request field" in response.json()["msg"]


@pytest.mark.parametrize("path", ["/run", "/idleBeat", "/kill", "/log"])
def test_invalid_json_for_every_body_endpoint(path):
    app, extension = make_app()

    @extension.on_run("handler")
    def run(_request):
        return XXLJobResponse.success()

    @extension.on_idle_beat
    def idle(_request):
        return XXLJobResponse.success()

    @extension.on_kill
    def kill(_request):
        return XXLJobResponse.success()

    @extension.on_log
    def log(_request):
        return LogResponse()

    with TestClient(app) as client:
        response = client.post(
            path, content=b"{", headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 200
    assert response.json()["code"] == 500
    assert "invalid JSON" in response.json()["msg"]


def test_oversized_request_is_rejected_before_handler():
    app, extension = make_app(XXL_JOB_MAX_REQUEST_SIZE=16)
    called = False

    @extension.on_run("handler")
    def run(_request):
        nonlocal called
        called = True
        return XXLJobResponse.success()

    with TestClient(app) as client:
        response = client.post(
            "/run",
            content=b'{"executorHandler":"handler"}',
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 200
    assert response.json()["code"] == 500
    assert "maximum allowed size" in response.json()["msg"]
    assert called is False


def test_scoped_middleware_converts_protocol_404():
    app = FastAPI(title="protocol-404")
    app.add_middleware(ProtocolErrorMiddleware, paths={"/beat"})
    with TestClient(app) as client:
        response = client.post("/beat")
        unrelated = client.post("/not-an-executor-route")
    assert response.status_code == 200
    assert response.json()["code"] == 500
    assert "Not Found" in response.json()["msg"]
    assert unrelated.status_code == 404
