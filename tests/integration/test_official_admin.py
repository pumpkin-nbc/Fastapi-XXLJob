"""Optional live integration test for a disposable XXL-JOB 2.4.1 Admin."""

import os

import pytest
from fastapi import FastAPI

from fastapi_xxljob import FastAPIXXLJob


@pytest.mark.official_admin
def test_official_admin_registry_round_trip():
    admin_url = os.getenv("XXLJOB_ADMIN_URL")
    executor_address = os.getenv("XXLJOB_EXECUTOR_ADDRESS")
    if not admin_url or not executor_address:
        pytest.skip("set XXLJOB_ADMIN_URL and XXLJOB_EXECUTOR_ADDRESS to enable")

    app = FastAPI()
    extension = FastAPIXXLJob(
        app,
        {
            "XXL_JOB_ADMIN_ADDRESSES": admin_url,
            "XXL_JOB_ACCESS_TOKEN": os.getenv("XXLJOB_ACCESS_TOKEN", ""),
            "XXL_JOB_EXECUTOR_APP_NAME": os.getenv(
                "XXLJOB_EXECUTOR_APP_NAME", "fastapi-xxljob-integration"
            ),
            "XXL_JOB_EXECUTOR_ADDRESS": executor_address,
            "XXL_JOB_AUTO_REGISTER": False,
        },
    )

    registered = extension.register_executor_sync()
    try:
        assert registered.success, registered
    finally:
        removed = extension.remove_executor_sync()
    assert removed.success, removed
