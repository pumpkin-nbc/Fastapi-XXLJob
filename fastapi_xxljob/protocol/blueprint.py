"""FastAPI routes for the XXL-JOB 2.4.1 executor protocol."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Optional

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from ..client import ACCESS_TOKEN_HEADER
from ..model.coerce import ModelParseError
from ..model.idle_beat import IdleBeatRequest
from ..model.kill import KillRequest
from ..model.log import LogRequest
from ..model.trigger import TriggerRequest
from ..response.executor import XXLJobResponse
from ..response.log import LogResponse
from .parser import (
    RequestParseError,
    check_param_length,
    parse_json_object,
    read_limited_request_body,
)
from .validator import ACCESS_TOKEN_ERROR, check_access_token

RUN_NOT_CONFIGURED = "XXL-JOB run callback is not configured"
IDLE_BEAT_NOT_CONFIGURED = "XXL-JOB idleBeat callback is not configured"
KILL_NOT_CONFIGURED = "XXL-JOB kill callback is not configured"
LOG_NOT_CONFIGURED = "XXL-JOB log callback is not configured"
MAX_HANDLER_DISPLAY_LENGTH = 128


def _json(response: XXLJobResponse) -> JSONResponse:
    return JSONResponse(response.to_dict(), status_code=200)


def _coerce_response(result: Any, endpoint: str) -> XXLJobResponse:
    if isinstance(result, XXLJobResponse):
        return result
    return XXLJobResponse.failure(
        "XXL-JOB " + endpoint + " callback returned an unsupported response type"
    )


async def _invoke(callback: Callable[[Any], Any], model: Any) -> Any:
    if inspect.iscoroutinefunction(callback):
        return await callback(model)
    result = await run_in_threadpool(callback, model)
    if inspect.isawaitable(result):
        return await result
    return result


def build_router(
    runtime: Any,
    url_prefix: str,
    lifespan: Optional[Callable[..., Any]] = None,
) -> APIRouter:
    """Build an isolated protocol router for one FastAPI application."""
    router = APIRouter(
        prefix=url_prefix,
        include_in_schema=False,
        lifespan=lifespan,
    )

    def token_ok(request: Request) -> bool:
        valid = check_access_token(
            runtime.config.access_token,
            request.headers.get(ACCESS_TOKEN_HEADER),
        )
        if not valid:
            runtime.log_manager.get_logger("protocol").warning(
                "XXL-JOB access token validation failed path=%s.", request.url.path
            )
        return valid

    async def parse_body(request: Request) -> Any:
        try:
            raw_body = await read_limited_request_body(
                request, runtime.config.max_request_size
            )
            return parse_json_object(raw_body, runtime.config.max_request_size)
        except RequestParseError as exc:
            runtime.log_manager.get_logger("protocol").warning(
                "XXL-JOB request parsing failed reason=%s.", str(exc)
            )
            return _json(XXLJobResponse.failure(str(exc)))

    def build_model(model_cls: Any, data: dict) -> Any:
        try:
            return model_cls.from_wire(data)
        except ModelParseError as exc:
            runtime.log_manager.get_logger("protocol").warning(
                "XXL-JOB request model validation failed reason=%s.", str(exc)
            )
            return _json(
                XXLJobResponse.failure("invalid request field: " + str(exc))
            )

    async def dispatch(
        callback: Callable[[Any], Any], model: Any, endpoint: str
    ) -> JSONResponse:
        try:
            result = await _invoke(callback, model)
        except Exception as exc:  # noqa: BLE001 - isolate application callbacks
            runtime.log_manager.get_logger("protocol").exception(
                "XXL-JOB /%s callback failed exception_type=%s.",
                endpoint,
                type(exc).__name__,
            )
            return _json(
                XXLJobResponse.failure(
                    "XXL-JOB " + endpoint + " callback execution failed"
                )
            )
        response = _coerce_response(result, endpoint)
        if not isinstance(result, XXLJobResponse):
            runtime.log_manager.get_logger("protocol").warning(
                "XXL-JOB /%s callback returned unsupported_type=%s.",
                endpoint,
                type(result).__name__,
            )
        return _json(response)

    @router.post("/beat")
    async def beat(request: Request) -> JSONResponse:
        if not token_ok(request):
            return _json(XXLJobResponse.failure(ACCESS_TOKEN_ERROR))
        return _json(XXLJobResponse.success())

    @router.post("/run")
    async def run(request: Request) -> JSONResponse:
        if not token_ok(request):
            return _json(XXLJobResponse.failure(ACCESS_TOKEN_ERROR))
        data = await parse_body(request)
        if isinstance(data, JSONResponse):
            return data
        error = check_param_length(data, runtime.config.max_param_length)
        if error:
            return _json(XXLJobResponse.failure(error))
        model = build_model(TriggerRequest, data)
        if isinstance(model, JSONResponse):
            return model
        if not runtime.callback_registry.has_run_callbacks:
            return _json(XXLJobResponse.failure(RUN_NOT_CONFIGURED))
        callback = runtime.callback_registry.get_run(model.executor_handler)
        if callback is None:
            runtime.log_manager.get_logger("protocol").warning(
                "XXL-JOB run request rejected unsupported_handler=%s.",
                _display_executor_handler(model.executor_handler),
            )
            return _json(
                XXLJobResponse.failure(
                    "Unsupported JobHandler: "
                    + _display_executor_handler(model.executor_handler)
                )
            )
        return await dispatch(callback, model, "run")

    @router.post("/idleBeat")
    async def idle_beat(request: Request) -> JSONResponse:
        if not token_ok(request):
            return _json(XXLJobResponse.failure(ACCESS_TOKEN_ERROR))
        callback = runtime.callback_registry.idle_beat
        if callback is None:
            return _json(XXLJobResponse.failure(IDLE_BEAT_NOT_CONFIGURED))
        data = await parse_body(request)
        if isinstance(data, JSONResponse):
            return data
        model = build_model(IdleBeatRequest, data)
        if isinstance(model, JSONResponse):
            return model
        return await dispatch(callback, model, "idleBeat")

    @router.post("/kill")
    async def kill(request: Request) -> JSONResponse:
        if not token_ok(request):
            return _json(XXLJobResponse.failure(ACCESS_TOKEN_ERROR))
        callback = runtime.callback_registry.kill
        if callback is None:
            return _json(XXLJobResponse.failure(KILL_NOT_CONFIGURED))
        data = await parse_body(request)
        if isinstance(data, JSONResponse):
            return data
        model = build_model(KillRequest, data)
        if isinstance(model, JSONResponse):
            return model
        return await dispatch(callback, model, "kill")

    @router.post("/log")
    async def log(request: Request) -> JSONResponse:
        if not token_ok(request):
            return _json(XXLJobResponse.failure(ACCESS_TOKEN_ERROR))
        callback = runtime.callback_registry.log
        if callback is None:
            return _json(XXLJobResponse.failure(LOG_NOT_CONFIGURED))
        data = await parse_body(request)
        if isinstance(data, JSONResponse):
            return data
        model = build_model(LogRequest, data)
        if isinstance(model, JSONResponse):
            return model
        try:
            result = await _invoke(callback, model)
        except Exception as exc:  # noqa: BLE001 - isolate application callbacks
            runtime.log_manager.get_logger("protocol").exception(
                "XXL-JOB /log callback failed log_id=%s exception_type=%s.",
                model.log_id,
                type(exc).__name__,
            )
            return _json(
                XXLJobResponse.failure("XXL-JOB log callback execution failed")
            )
        if isinstance(result, XXLJobResponse):
            return _json(result)
        if isinstance(result, LogResponse):
            return _json(XXLJobResponse.success(content=result.to_wire()))
        return _json(
            XXLJobResponse.failure(
                "XXL-JOB log callback returned an unsupported response type"
            )
        )

    return router


def _display_executor_handler(executor_handler: str) -> str:
    if not executor_handler.strip():
        return "<empty>"
    if len(executor_handler) <= MAX_HANDLER_DISPLAY_LENGTH:
        return executor_handler
    return executor_handler[: MAX_HANDLER_DISPLAY_LENGTH - 3] + "..."


__all__ = ["build_router"]
