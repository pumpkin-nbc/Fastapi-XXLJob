"""Shared pytest fixtures for FastAPI-XXLJob."""

from __future__ import annotations

from typing import Optional, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_xxljob import FastAPIXXLJob

BASE_CONFIG = {
    "XXL_JOB_ADMIN_ADDRESSES": ["http://admin-1:8080/xxl-job-admin"],
    "XXL_JOB_EXECUTOR_APP_NAME": "test-executor",
    "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:5001",
    "XXL_JOB_AUTO_REGISTER": False,
}


def make_app(
    extension: Optional[FastAPIXXLJob] = None,
    name: str = "test_app",
    **overrides: object,
) -> Tuple[FastAPI, FastAPIXXLJob]:
    app = FastAPI(title=name)
    config = dict(BASE_CONFIG)
    config.update(overrides)
    ext = extension or FastAPIXXLJob()
    ext.init_app(app, config)
    return app, ext


@pytest.fixture
def app_ext() -> Tuple[FastAPI, FastAPIXXLJob]:
    return make_app()


@pytest.fixture
def client(app_ext: Tuple[FastAPI, FastAPIXXLJob]):
    app, _ = app_ext
    with TestClient(app) as test_client:
        yield test_client
