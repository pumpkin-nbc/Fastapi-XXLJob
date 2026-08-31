"""FastAPI-XXLJob extension entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, Callable, Mapping, Optional, Union

from fastapi import APIRouter, FastAPI
from starlette.concurrency import run_in_threadpool

from ._app import (
    ApplicationRegistry,
    ProtocolErrorMiddleware,
    ensure_executor_routes_available,
    executor_paths,
)
from ._lifecycle import install_runtime_finalizer
from ._logging import XXLJobLogManager
from .callback.registry import (
    CallbackRegistry,
    IdleBeatCallback,
    KillCallback,
    LogCallback,
    RunCallback,
    validate_executor_handler,
)
from .client.admin_client import AdminClient
from .client.callback_client import CallbackClient
from .config import XXLJobConfig
from .exceptions import (
    XXLJobAlreadyInitializedError,
    XXLJobConfigError,
    XXLJobError,
    XXLJobRequestError,
)
from .protocol.blueprint import build_router
from .registry.registry_service import RegistryService
from .response.executor import FAIL_CODE, SUCCESS_CODE
from .runtime import XXLJobRuntime

if TYPE_CHECKING:
    from typing import Sequence

    from .client import CallResult
    from .client.callback_client import CallbackLike
    from .status import XXLJobStatus

EXTENSION_KEY = "xxljob"
logger = logging.getLogger("fastapi_xxljob.extension")
ConfigInput = Optional[Union[Mapping[str, Any], XXLJobConfig]]


class FastAPIXXLJob:
    """Adapt a FastAPI application to the official XXL-JOB 2.4.1 protocol."""

    def __init__(
        self,
        app: Optional[FastAPI] = None,
        config: ConfigInput = None,
    ) -> None:
        self._applications = ApplicationRegistry()
        self._deferred_callbacks = CallbackRegistry()
        if app is not None:
            self.init_app(app, config)
        elif config is not None:
            raise XXLJobConfigError("config requires an app; pass it to init_app(app, config)")

    def init_app(self, app: FastAPI, config: ConfigInput = None) -> None:
        """Initialize the extension during application construction."""
        if getattr(app.state, EXTENSION_KEY, None) is not None:
            raise XXLJobAlreadyInitializedError(
                "FastAPI-XXLJob has already been initialized on this application."
            )

        runtime_config = self._load_config(config)
        if runtime_config.enabled and runtime_config.auto_register:
            runtime_config.validate_registry()
        if runtime_config.enabled:
            ensure_executor_routes_available(app, runtime_config.route_prefix)

        log_manager: Optional[XXLJobLogManager] = None
        runtime: Optional[XXLJobRuntime] = None
        finalizer = None
        middleware_count = len(app.user_middleware)
        application_added = False
        state_published = False
        try:
            log_manager = XXLJobLogManager(app, runtime_config)
            callback_registry = CallbackRegistry()
            callback_registry.seed_from(self._deferred_callbacks)
            admin_client = AdminClient(
                runtime_config, logger=log_manager.get_logger("admin")
            )
            callback_client = CallbackClient(
                runtime_config, logger=log_manager.get_logger("callback")
            )
            registry_service = RegistryService(
                runtime_config,
                admin_client,
                logger=log_manager.get_logger("registry"),
                close_logs=log_manager.close,
            )
            runtime = XXLJobRuntime(
                config=runtime_config,
                callback_registry=callback_registry,
                admin_client=admin_client,
                callback_client=callback_client,
                registry_service=registry_service,
                log_manager=log_manager,
            )

            @asynccontextmanager
            async def lifespan(_: FastAPI) -> AsyncIterator[None]:
                if runtime_config.enabled and runtime_config.auto_register:
                    registry_service.start()
                try:
                    yield
                finally:
                    runtime.close()

            if runtime_config.enabled:
                app.add_middleware(
                    ProtocolErrorMiddleware,
                    paths=executor_paths(runtime_config.route_prefix),
                )
                router = build_router(
                    runtime,
                    runtime_config.route_prefix,
                    lifespan=lifespan,
                )
            else:
                router = APIRouter(lifespan=lifespan)

            setattr(app.state, EXTENSION_KEY, runtime)
            state_published = True
            self._applications.add(app)
            application_added = True
            finalizer = install_runtime_finalizer(app, runtime)
            runtime.attach_finalizer(finalizer)
            app.include_router(router)
            log_manager.get_logger("runtime").info(
                "FastAPI-XXLJob initialized enabled=%s auto_register=%s.",
                runtime_config.enabled,
                runtime_config.auto_register,
            )
        except Exception:
            logger.exception("FastAPI-XXLJob initialization failed.")
            if finalizer is not None:
                finalizer.detach()
            if application_added:
                self._applications.discard(app)
            if state_published and getattr(app.state, EXTENSION_KEY, None) is runtime:
                delattr(app.state, EXTENSION_KEY)
            while len(app.user_middleware) > middleware_count:
                app.user_middleware.pop(0)
            if log_manager is not None:
                log_manager.close()
            raise

    @staticmethod
    def _load_config(config: ConfigInput) -> XXLJobConfig:
        if isinstance(config, XXLJobConfig):
            config.validate()
            return config
        return XXLJobConfig.from_mapping(config or {})

    # Callback registration -------------------------------------------------
    def on_run(self, executor_handler: str) -> Callable[[RunCallback], RunCallback]:
        name = validate_executor_handler(executor_handler)

        def decorator(func: RunCallback) -> RunCallback:
            return self._target_registry().set_run(name, func)

        return decorator

    def on_idle_beat(self, func: IdleBeatCallback) -> IdleBeatCallback:
        return self._target_registry().set_idle_beat(func)

    def on_kill(self, func: KillCallback) -> KillCallback:
        return self._target_registry().set_kill(func)

    def on_log(self, func: LogCallback) -> LogCallback:
        return self._target_registry().set_log(func)

    def register_callbacks(
        self,
        app: Optional[FastAPI] = None,
        *,
        run: Optional[Mapping[str, RunCallback]] = None,
        idle_beat: Optional[IdleBeatCallback] = None,
        kill: Optional[KillCallback] = None,
        log: Optional[LogCallback] = None,
        replace: bool = False,
    ) -> None:
        self._registry_for(app).register_callbacks(
            run=run,
            idle_beat=idle_beat,
            kill=kill,
            log=log,
            replace=replace,
        )

    def set_run_callback(
        self,
        app: Optional[FastAPI],
        executor_handler: str,
        func: RunCallback,
        replace: bool = False,
    ) -> RunCallback:
        return self._registry_for(app).set_run(executor_handler, func, replace)

    def set_idle_beat_callback(
        self,
        app: Optional[FastAPI],
        func: IdleBeatCallback,
        replace: bool = False,
    ) -> IdleBeatCallback:
        return self._registry_for(app).set_idle_beat(func, replace)

    def set_kill_callback(
        self,
        app: Optional[FastAPI],
        func: KillCallback,
        replace: bool = False,
    ) -> KillCallback:
        return self._registry_for(app).set_kill(func, replace)

    def set_log_callback(
        self,
        app: Optional[FastAPI],
        func: LogCallback,
        replace: bool = False,
    ) -> LogCallback:
        return self._registry_for(app).set_log(func, replace)

    def get_run_callback(
        self, app: Optional[FastAPI], executor_handler: str
    ) -> Optional[RunCallback]:
        return self._registry_for(app).get_run(
            validate_executor_handler(executor_handler)
        )

    def get_idle_beat_callback(
        self, app: Optional[FastAPI] = None
    ) -> Optional[IdleBeatCallback]:
        return self._registry_for(app).idle_beat

    def get_kill_callback(
        self, app: Optional[FastAPI] = None
    ) -> Optional[KillCallback]:
        return self._registry_for(app).kill

    def get_log_callback(
        self, app: Optional[FastAPI] = None
    ) -> Optional[LogCallback]:
        return self._registry_for(app).log

    # Synchronous Admin APIs ------------------------------------------------
    def register_executor_sync(
        self, app: Optional[FastAPI] = None
    ) -> "CallResult":
        return self._get_runtime(app).registry_service.register_once_result()

    def remove_executor_sync(
        self, app: Optional[FastAPI] = None
    ) -> "CallResult":
        return self._get_runtime(app).registry_service.remove_once_result()

    def callback_sync(
        self,
        log_id: int,
        log_date_time: int,
        handle_code: int,
        handle_msg: Optional[str] = None,
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        runtime = self._get_runtime(app)
        if runtime.config.enabled:
            _require_int("log_id", log_id)
            _require_int("log_date_time", log_date_time)
            _require_int("handle_code", handle_code)
        return runtime.callback_client.callback(
            log_id, log_date_time, handle_code, handle_msg
        )

    def callback_success_sync(
        self,
        log_id: int,
        log_date_time: int,
        message: Optional[str] = None,
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return self.callback_sync(
            log_id, log_date_time, SUCCESS_CODE, message, app
        )

    def callback_failure_sync(
        self,
        log_id: int,
        log_date_time: int,
        message: Optional[str] = None,
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return self.callback_sync(log_id, log_date_time, FAIL_CODE, message, app)

    def callback_many_sync(
        self,
        callbacks: "Sequence[CallbackLike]",
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return self._get_runtime(app).callback_client.callback_many(callbacks)

    # Async-first Admin APIs ------------------------------------------------
    async def register_executor(
        self, app: Optional[FastAPI] = None
    ) -> "CallResult":
        return await run_in_threadpool(self.register_executor_sync, app)

    async def remove_executor(
        self, app: Optional[FastAPI] = None
    ) -> "CallResult":
        return await run_in_threadpool(self.remove_executor_sync, app)

    async def callback(
        self,
        log_id: int,
        log_date_time: int,
        handle_code: int,
        handle_msg: Optional[str] = None,
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return await run_in_threadpool(
            self.callback_sync,
            log_id,
            log_date_time,
            handle_code,
            handle_msg,
            app,
        )

    async def callback_success(
        self,
        log_id: int,
        log_date_time: int,
        message: Optional[str] = None,
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return await run_in_threadpool(
            self.callback_success_sync, log_id, log_date_time, message, app
        )

    async def callback_failure(
        self,
        log_id: int,
        log_date_time: int,
        message: Optional[str] = None,
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return await run_in_threadpool(
            self.callback_failure_sync, log_id, log_date_time, message, app
        )

    async def callback_many(
        self,
        callbacks: "Sequence[CallbackLike]",
        app: Optional[FastAPI] = None,
    ) -> "CallResult":
        return await run_in_threadpool(self.callback_many_sync, callbacks, app)

    # Status and lifecycle --------------------------------------------------
    def get_status(self, app: Optional[FastAPI] = None) -> "XXLJobStatus":
        from .status import XXLJobStatus

        runtime = self._get_runtime(app)
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

    def start_registry(self, app: Optional[FastAPI] = None) -> None:
        self._get_runtime(app).registry_service.start()

    def stop_registry(
        self, app: Optional[FastAPI] = None, *, remove: bool = False
    ) -> None:
        self._get_runtime(app).registry_service.stop(remove=remove)

    def _get_runtime(self, app: Optional[FastAPI] = None) -> XXLJobRuntime:
        target = self._applications.resolve(app)
        runtime = getattr(target.state, EXTENSION_KEY, None)
        if runtime is None:
            raise XXLJobError(
                "FastAPI-XXLJob is not initialized on this application. "
                "Call init_app(app, config) first."
            )
        return runtime

    def _target_registry(self) -> CallbackRegistry:
        if self._applications.is_empty:
            return self._deferred_callbacks
        return self._get_runtime().callback_registry

    def _registry_for(self, app: Optional[FastAPI]) -> CallbackRegistry:
        if app is not None:
            return self._get_runtime(app).callback_registry
        return self._target_registry()


def _require_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise XXLJobRequestError(
            name + " must be an integer, got " + type(value).__name__
        )


__all__ = ["FastAPIXXLJob", "EXTENSION_KEY"]
