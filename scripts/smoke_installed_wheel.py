"""Smoke-test an isolated installed FastAPI-XXLJob wheel."""

from __future__ import annotations

import argparse
import json
import site
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

import fastapi_xxljob
from fastapi_xxljob import FastAPIXXLJob, LogResponse, XXLJobResponse


class AdminHandler(BaseHTTPRequestHandler):
    paths: List[str] = []

    def do_POST(self) -> None:  # noqa: N802 - standard-library server API
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        self.paths.append(self.path)
        body = json.dumps({"code": 200, "msg": "ok"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _assert_installed(source_root: Path) -> None:
    module_path = Path(fastapi_xxljob.__file__).resolve()
    site_paths = [Path(item).resolve() for item in site.getsitepackages()]
    assert any(_is_relative_to(module_path, item) for item in site_paths)
    assert not _is_relative_to(
        module_path, (source_root / "fastapi_xxljob").resolve()
    )
    assert fastapi_xxljob.__version__ == "0.1.0"
    assert version("fastapi-xxljob") == "0.1.0"


def _make_app(admin_url: str):
    app = FastAPI(title="installed-wheel-smoke")
    extension = FastAPIXXLJob(
        app,
        {
            "XXL_JOB_ADMIN_ADDRESSES": [admin_url],
            "XXL_JOB_EXECUTOR_APP_NAME": "installed-wheel-smoke",
            "XXL_JOB_EXECUTOR_ADDRESS": "http://127.0.0.1:5001",
            "XXL_JOB_AUTO_REGISTER": False,
            "XXL_JOB_REGISTRY_INTERVAL": 1,
        },
    )

    @extension.on_run("smoke")
    async def run(_request):
        return XXLJobResponse.success()

    @extension.on_idle_beat
    def idle(_request):
        return XXLJobResponse.success()

    @extension.on_kill
    def kill(_request):
        return XXLJobResponse.success()

    @extension.on_log
    def log(request):
        return LogResponse(
            from_line_num=request.from_line_num,
            to_line_num=request.from_line_num,
            log_content="smoke",
            is_end=True,
        )
    return app, extension


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args(argv)
    _assert_installed(args.source_root)

    server = ThreadingHTTPServer(("127.0.0.1", 0), AdminHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    admin_url = "http://127.0.0.1:" + str(server.server_address[1])
    try:
        app, extension = _make_app(admin_url)
        with TestClient(app) as client:
            requests = (
                ("/beat", None),
                ("/run", {"jobId": 1, "executorHandler": "smoke"}),
                ("/idleBeat", {"jobId": 1}),
                ("/kill", {"jobId": 1}),
                ("/log", {"fromLineNum": 1}),
            )
            for path, payload in requests:
                response = client.post(path, json=payload)
                assert response.status_code == 200
                assert response.json()["code"] == 200
        assert extension.register_executor_sync(app).success
        assert extension.callback_success_sync(1, 1, "smoke", app).success
        assert extension.remove_executor_sync(app).success
        assert any(path.endswith("/api/registry") for path in AdminHandler.paths)
        assert any(path.endswith("/api/callback") for path in AdminHandler.paths)
        assert any(path.endswith("/api/registryRemove") for path in AdminHandler.paths)

        executable = Path(sys.executable).with_name(
            "fastapi-xxljob.exe" if sys.platform == "win32" else "fastapi-xxljob"
        )
        result = subprocess.run(
            [str(executable), "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "0.1.0" in result.stdout
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    print("Installed-wheel smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
