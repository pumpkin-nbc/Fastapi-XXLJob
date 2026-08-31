"""Importable FastAPI application used by CLI tests."""

from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob

CONFIG = {
    "XXL_JOB_ADMIN_ADDRESSES": ["http://admin:8080/xxl-job-admin"],
    "XXL_JOB_EXECUTOR_APP_NAME": "cli-executor",
    "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:5001",
    "XXL_JOB_AUTO_REGISTER": False,
}

app = FastAPI(title="cli")
extension = FastAPIXXLJob(app, CONFIG)


def create_app() -> FastAPI:
    factory_app = FastAPI(title="cli-factory")
    FastAPIXXLJob(factory_app, CONFIG)
    return factory_app
