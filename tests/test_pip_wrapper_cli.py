import pytest


@pytest.fixture
def invoked_pip_args(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr("dependency_groups._pip_wrapper._invoke_pip", calls.append)
    return calls


@pytest.fixture
def run(runner_factory, invoked_pip_args):
    from dependency_groups._pip_wrapper import main as cli_main

    return runner_factory(cli_main).invoke


def test_empty_group_skips_pip(run, invoked_pip_args, tmp_path):
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
