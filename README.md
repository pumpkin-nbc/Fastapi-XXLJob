# FastAPI-XXLJob

[English](README.md) | [简体中文](README.zh-CN.md)

`fastapi-xxljob` is a typed FastAPI adapter for the XXL-JOB 2.4.1 executor protocol. Version 0.1.0 is protocol-compatible with Flask-XXLJob 0.4.0 while preserving FastAPI's async and lifespan model.

## Features

- All five executor endpoints: `/beat`, `/idleBeat`, `/run`, `/kill`, and `/log`.
- Sync and async handlers, isolated per FastAPI application.
- Automatic registry renewal, deregistration, callbacks, retry, and failover.
- Bounded requests, constant-time token checks, sensitive-data filtering, and managed logs.
- Async-first API plus explicit `*_sync` methods for scripts and workers.

## Install

Requires Python 3.8 or later and FastAPI 0.124.4 or later (before 1.0). Dependency resolution keeps Python 3.8 on FastAPI 0.124.4 while newer Python versions can use newer FastAPI releases.

```bash
pip install fastapi-xxljob==0.1.0
```

## Quick start

```python
from fastapi import FastAPI
from fastapi_xxljob import FastAPIXXLJob

app = FastAPI()
xxljob = FastAPIXXLJob(app, {
    "XXL_JOB_ADMIN_ADDRESSES": "http://127.0.0.1:8080/xxl-job-admin",
    "XXL_JOB_ACCESS_TOKEN": "default_token",
    "XXL_JOB_EXECUTOR_APP_NAME": "fastapi-xxljob-executor",
    "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:8000",
})

@xxljob.on_run("demoJobHandler")
async def demo(param):
    return f"processed: {param.executor_params}"
```

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The protocol routes default to the application root and are hidden from OpenAPI; use `XXL_JOB_ROUTE_PREFIX` when a prefix such as `/xxl-job` is required. Run, idle-beat, and kill handlers return `XXLJobResponse`; log handlers may also return `LogResponse`.

Callbacks are async-first:

```python
await xxljob.callback_success(log_id=1, log_date_time=1730000000000)
xxljob.callback_failure_sync(log_id=2, log_date_time=1730000000000, message="failed")
```

## Main configuration

| Key | Purpose |
| --- | --- |
| `XXL_JOB_ENABLED` | Enable protocol and Admin operations. |
| `XXL_JOB_ADMIN_ADDRESSES` | Comma-separated Admin base URLs. |
| `XXL_JOB_ACCESS_TOKEN` | Shared executor token. |
| `XXL_JOB_EXECUTOR_APP_NAME` | Executor application name. |
| `XXL_JOB_EXECUTOR_ADDRESS` | Public executor URL. |
| `XXL_JOB_ROUTE_PREFIX` | Optional route prefix; empty by default. |
| `XXL_JOB_AUTO_REGISTER` | Start registry renewal with application lifespan. |
| `XXL_JOB_DEREGISTER_ON_EXIT` | Remove registration during clean shutdown. |
| `XXL_JOB_REGISTRY_INTERVAL` | Renewal interval in seconds. |
| `XXL_JOB_HTTP_CONNECT_TIMEOUT` | Admin connection timeout. |
| `XXL_JOB_HTTP_READ_TIMEOUT` | Admin response timeout. |
| `XXL_JOB_ADMIN_RETRY_COUNT` | Bounded retry count per Admin address. |
| `XXL_JOB_MAX_REQUEST_SIZE` | Maximum protocol request bytes. |
| `XXL_JOB_MAX_PARAM_LENGTH` | Maximum string field length. |
| `XXL_JOB_CALLBACK_BATCH_MAX_SIZE` | Maximum atomic callback batch size. |
| `XXL_JOB_CALLBACK_MESSAGE_MAX_LENGTH` | Maximum callback message length. |
| `XXL_JOB_LOG_ENABLED` | Enable managed library logging. |
| `XXL_JOB_LOG_FILE_ENABLED` | Enable rotating file output. |
| `XXL_JOB_LOG_CONSOLE_ENABLED` | Enable console output. |
| `XXL_JOB_LOG_PATH` | Managed log directory. |

See [Getting started](docs/getting-started.md), [configuration](docs/configuration.md), [API reference](docs/api-reference.md), and the [examples](examples/basic/README.md).

## Command line

```bash
fastapi-xxljob --app app:app register
fastapi-xxljob --app app:create_app --factory status
fastapi-xxljob --app app:app remove
```

## Scope

This package adapts the executor protocol. It intentionally does not schedule business jobs, create a task queue, store task logs, provide a callback outbox, or retry forever.

Licensed under Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
