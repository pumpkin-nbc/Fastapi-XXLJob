"""Standalone CLI integration tests."""

from __future__ import annotations

import pytest

from fastapi_xxljob.cli.commands import build_parser, main


def test_parser_exposes_management_commands():
    namespace = build_parser().parse_args(
        ["--app", "tests.fixtures.cli_app:app", "status"]
    )
    assert namespace.command == "status"


def test_status_command(capsys):
    main(["--app", "tests.fixtures.cli_app:app", "status"])
    output = capsys.readouterr().out
    assert "FastAPI-XXLJob status" in output
    assert "Registered: False" in output


def test_factory_status_command(capsys):
    main(
        [
            "--app",
            "tests.fixtures.cli_app:create_app",
            "--factory",
            "status",
        ]
    )
    assert "FastAPI-XXLJob status" in capsys.readouterr().out


def test_register_and_remove_commands(mocker, capsys):
    response = mocker.Mock(status_code=200)
    response.json.return_value = {"code": 200, "msg": "ok"}
    post = mocker.patch("fastapi_xxljob.client.requests.post", return_value=response)
    main(["--app", "tests.fixtures.cli_app:app", "register"])
    main(["--app", "tests.fixtures.cli_app:app", "remove"])
    assert post.call_count == 2
    output = capsys.readouterr().out
    assert "registered successfully" in output
    assert "removed successfully" in output


def test_cli_load_error_is_exit_two(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--app", "missing.module:app", "status"])
    assert exc_info.value.code == 2
    assert "fastapi-xxljob:" in capsys.readouterr().err
