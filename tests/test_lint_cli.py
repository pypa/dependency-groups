from __future__ import annotations

import typing as t

import pytest

if t.TYPE_CHECKING:
    import pathlib

    from conftest import CliRunner, RunnerFactory


@pytest.fixture
def run(runner_factory: RunnerFactory) -> CliRunner:
    from dependency_groups._lint_dependency_groups import main as cli_main

    return runner_factory(cli_main)


def test_lint_no_groups_ok(run: CliRunner, tmp_path: pathlib.Path) -> None:
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text("[project]\n")

    res = run("-f", tomlfile)
    assert res.stdout == "ok\n"
    assert res.stderr == ""


def test_lint_bad_group_item(run: CliRunner, tmp_path: pathlib.Path) -> None:
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(
        """\
[dependency-groups]
foo = [{badkey = "value"}]
"""
    )

    res = run("-f", tomlfile, expect_exit_code=1)
    assert (
        res.stdout
        == """\
errors encountered while examining dependency groups:
  ValueError: Invalid dependency group item: {'badkey': 'value'}
"""
    )
    assert res.stderr == ""


def test_no_toml_failure(
    run: CliRunner, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("dependency_groups._lint_dependency_groups.tomllib", None)

    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text("")

    res = run("-f", tomlfile, expect_exit_code=2)
    assert "requires tomli or Python 3.11+" in res.stderr


def test_dependency_groups_list_format(run: CliRunner, tmp_path: pathlib.Path) -> None:
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text("[[dependency-groups]]")

    res = run("-f", tomlfile, expect_exit_code=1)
    assert (
        res.stdout
        == """\
errors encountered while examining dependency groups:
  TypeError: Dependency Groups table is not a mapping
"""
    )
    assert res.stderr == ""
