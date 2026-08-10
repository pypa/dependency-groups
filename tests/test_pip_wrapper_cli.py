from __future__ import annotations

import typing as t

import pytest

if t.TYPE_CHECKING:
    import pathlib

    from conftest import CliRunner, RunnerFactory


@pytest.fixture
def invoked_pip_args(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []
    monkeypatch.setattr("dependency_groups._pip_wrapper._invoke_pip", calls.append)
    return calls


@pytest.fixture
def run(runner_factory: RunnerFactory, invoked_pip_args: list[list[str]]) -> CliRunner:
    from dependency_groups._pip_wrapper import main as cli_main

    return runner_factory(cli_main)


def test_empty_group_skips_pip(
    run: CliRunner, invoked_pip_args: list[list[str]], tmp_path: pathlib.Path
) -> None:
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(
        """\
[dependency-groups]
empty = []
"""
    )

    res = run("-f", tomlfile, "empty")
    assert invoked_pip_args == []
    assert "Nothing to install" in res.stdout
