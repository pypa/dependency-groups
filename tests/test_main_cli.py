from __future__ import annotations

import typing as t

import pytest

if t.TYPE_CHECKING:
    import pathlib

    from conftest import CliRunner, RunnerFactory

PYPROJECT = """\
[dependency-groups]
test = ["pytest"]
docs = ["sphinx"]
"""


@pytest.fixture
def run(runner_factory: RunnerFactory) -> CliRunner:
    from dependency_groups.__main__ import main as cli_main

    return runner_factory(cli_main)


def test_list_to_stdout(run: CliRunner, tmp_path: pathlib.Path) -> None:
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(PYPROJECT)

    res = run("-f", tomlfile, "--list")
    assert res.stdout == "test docs\n"


def test_list_respects_output_file(run: CliRunner, tmp_path: pathlib.Path) -> None:
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(PYPROJECT)
    outfile = tmp_path / "out.txt"

    res = run("-f", tomlfile, "--list", "-o", outfile)
    assert res.stdout == ""
    assert outfile.read_text() == "test docs\n"
