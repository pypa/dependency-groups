import dataclasses

import pytest


@dataclasses.dataclass
class CLIResult:
    code: int
    stdout: str
    stderr: str


@pytest.fixture
def invoked_pip_args(monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr("dependency_groups._pip_wrapper._invoke_pip", calls.append)
    return calls


@pytest.fixture
def run(capsys, invoked_pip_args):
    from dependency_groups._pip_wrapper import main as cli_main

    def _run(*argv):
        try:
            cli_main(argv=[str(arg) for arg in argv])
            rc = 0
        except SystemExit as e:
            rc = e.code

        stdio = capsys.readouterr()
        return CLIResult(rc, stdio.out, stdio.err)

    return _run


def test_empty_group_skips_pip(run, invoked_pip_args, tmp_path):
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(
        """\
[dependency-groups]
empty = []
"""
    )

    res = run("-f", tomlfile, "empty")
    assert res.code == 0
    assert invoked_pip_args == []
    assert "Nothing to install" in res.stdout
