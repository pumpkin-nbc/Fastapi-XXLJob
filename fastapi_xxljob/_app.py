"""FastAPI application, route, and middleware helpers."""

from __future__ import annotations

import json
import threading
import weakref
from typing import Iterable, Optional, Set

from fastapi import FastAPI
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .exceptions import XXLJobError, XXLJobInitializationError

EXECUTOR_ROUTE_SUFFIXES = ("/beat", "/idleBeat", "/run", "/kill", "/log")


def executor_paths(route_prefix: str) -> Set[str]:
    """Return the exact executor paths mounted below a normalized prefix."""
    prefix = route_prefix or ""
    return {prefix + suffix for suffix in EXECUTOR_ROUTE_SUFFIXES}


def ensure_executor_routes_available(app: FastAPI, route_prefix: str) -> None:
    """Fail when an existing host POST route would shadow an executor route."""
    paths = executor_paths(route_prefix)
    conflicts = sorted(
        {
            getattr(route, "path", "")
            for route in app.routes
            if getattr(route, "path", "") in paths
            and "POST" in (getattr(route, "methods", None) or set())
        }
    )
    if conflicts:
        raise XXLJobInitializationError(
            "FastAPI-XXLJob executor route conflict for POST: "
            + ", ".join(conflicts)
            + ". Configure XXL_JOB_ROUTE_PREFIX or remove the host route."
        )


class ProtocolErrorMiddleware:
    """Convert only executor-path 404/405 responses to XXL-JOB JSON."""

    def __init__(self, app: ASGIApp, paths: Iterable[str]) -> None:
        self.app = app
        self.paths = frozenset(paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") not in self.paths:
            await self.app(scope, receive, send)
            return

        started = False
        replace = False
        replacement_status = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal started, replace, replacement_status
            if message["type"] == "http.response.start":
                status = int(message["status"])
                replace = status in (404, 405)
                if replace:
                    replacement_status = status
                    return
                started = True
                await send(message)
                return
            if message["type"] == "http.response.body" and replace:
                if message.get("more_body", False):
                    return
                name = (
                    "Not Found"
                    if replacement_status == 404
                    else "Method Not Allowed"
                )
                body = json.dumps(
                    {
                        "code": 500,
                        "msg": "XXL-JOB request error: " + name,
                        "content": None,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                await send(
                    {
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode("ascii")),
                        ],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                replace = False
                started = True
                return
            if not replace:
                await send(message)

        await self.app(scope, receive, send_wrapper)
        if replace and not started:
            body = b'{"code":500,"msg":"XXL-JOB request error","content":null}'
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode("ascii")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})


class ApplicationRegistry:
    """Track initialized applications without retaining them indefinitely."""

    def __init__(self) -> None:
        self._apps: "weakref.WeakSet[FastAPI]" = weakref.WeakSet()
        self._lock = threading.RLock()

    def add(self, app: FastAPI) -> None:
        with self._lock:
            self._apps.add(app)

    def discard(self, app: FastAPI) -> None:
        with self._lock:
            self._apps.discard(app)

    def snapshot(self) -> Iterable[FastAPI]:
        with self._lock:
            return tuple(self._apps)

    def resolve(self, app: Optional[FastAPI] = None) -> FastAPI:
        if app is not None:
            return app
        apps = tuple(self.snapshot())
        if not apps:
            raise XXLJobError(
                "No FastAPI application available. Pass app=... or call init_app()."
            )
        if len(apps) > 1:
            raise XXLJobError(
                "Multiple FastAPI applications are initialized. Pass app=... explicitly."
            )
        return apps[0]

    @property
    def is_empty(self) -> bool:
        with self._lock:
            return not self._apps


__all__ = [
    "ApplicationRegistry",
    "EXECUTOR_ROUTE_SUFFIXES",
    "ProtocolErrorMiddleware",
    "ensure_executor_routes_available",
    "executor_paths",
]
