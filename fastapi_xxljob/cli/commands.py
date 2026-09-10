"""Standalone FastAPI-XXLJob management CLI."""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, List, Optional

from fastapi import FastAPI

from .._version import __version__
from ..extension import EXTENSION_KEY
from ..status import XXLJobStatus


def _load_app(import_path: str, factory: bool) -> FastAPI:
    if ":" not in import_path:
        raise ValueError("application path must use module:attribute syntax")
    module_name, attribute_path = import_path.split(":", 1)
    if not module_name or not attribute_path:
        raise ValueError("application path must use module:attribute syntax")
    value: Any = importlib.import_module(module_name)
    for name in attribute_path.split("."):
        value = getattr(value, name)
    if factory:
        if not callable(value):
            raise TypeError("--factory target is not callable")
        value = value()
    if not isinstance(value, FastAPI):
        raise TypeError("loaded object is not a FastAPI application")
    return value


def _runtime(app: FastAPI) -> Any:
    runtime = getattr(app.state, EXTENSION_KEY, None)
    if runtime is None:
        raise RuntimeError("FastAPI-XXLJob is not initialized on this application")
    return runtime


def _build_status(runtime: Any) -> XXLJobStatus:
    config = runtime.config
    snapshot = runtime.registry_service.status_snapshot()
    return XXLJobStatus(
        enabled=config.enabled,
        auto_register=config.auto_register,
        registered=snapshot["registered"],
        last_registry_time=snapshot["last_registry_time"],
        last_registry_success=snapshot["last_registry_success"],
        last_registry_admin_address=snapshot["last_registry_admin_address"],
        last_registry_error_type=snapshot["last_registry_error_type"],
        last_registry_message=snapshot["last_registry_message"],
        registry_thread_running=snapshot["registry_thread_running"],
        log_enabled=runtime.log_manager.effective_enabled,
        log_level=runtime.log_manager.level,
        log_file_enabled=runtime.log_manager.file_enabled,
        log_console_enabled=runtime.log_manager.console_enabled,
        log_file=runtime.log_manager.log_file,
    )


def _print_status(status: XXLJobStatus) -> None:
    print("FastAPI-XXLJob status")
    print("  Enabled:", status.enabled)
    print("  Auto register:", status.auto_register)
    print("  Registered:", status.registered)
    print("  Registry thread running:", status.registry_thread_running)
    print("  Log enabled:", status.log_enabled)
    print("  Log level:", status.log_level)
    print("  File logging:", status.log_file_enabled)
    if status.log_file is not None:
        print("  Log file:", status.log_file)
    print("  Console logging:", status.log_console_enabled)
    if status.last_registry_time is None:
        print("  Last registry: (no attempt yet)")
    else:
        print("  Last registry time:", status.last_registry_time)
        print("  Last registry admin:", status.last_registry_admin_address)
        result = "success" if status.last_registry_success else "failure"
        print("  Last registry result:", result)
        if status.last_registry_success is False:
            print("  Last registry error type:", status.last_registry_error_type)
            print("  Last registry message:", status.last_registry_message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fastapi-xxljob")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--app", required=True, help="FastAPI app as module:attribute")
    parser.add_argument(
        "--factory", action="store_true", help="Treat the selected attribute as a factory"
    )
    parser.add_argument("command", choices=("register", "remove", "status"))
    return parser


def main(args: Optional[List[str]] = None) -> None:
    namespace = build_parser().parse_args(args)
    try:
        app = _load_app(namespace.app, namespace.factory)
        runtime = _runtime(app)
        if namespace.command == "status":
            status = _build_status(runtime)
            _print_status(status)
            if status.last_registry_success is False:
                raise SystemExit(1)
            return
        if namespace.command == "remove":
            runtime.registry_service.stop()
            result = runtime.registry_service.remove_once_result()
            verb = "removed"
        else:
            result = runtime.registry_service.register_once_result()
            verb = "registered"
        if result.success:
            print("Executor " + verb + " successfully via " + str(result.address) + ".")
            return
        print(
            "Executor " + namespace.command + " failed: "
            + str(result.error or result.msg),
            file=sys.stderr,
        )
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print("fastapi-xxljob: " + str(exc), file=sys.stderr)
        raise SystemExit(2) from exc


__all__ = ["build_parser", "main"]
