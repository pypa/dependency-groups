import dataclasses

import pytest

PYPROJECT = """\
[dependency-groups]
test = ["pytest"]
docs = ["sphinx"]
"""


@dataclasses.dataclass
class CLIResult:
    code: int
    stdout: str
    stderr: str


@pytest.fixture
def run(capsys):
    from dependency_groups.__main__ import main as cli_main

    def _run(*argv):
        try:
            cli_main(argv=[str(arg) for arg in argv])
            rc = 0
        except SystemExit as e:
            rc = e.code

        stdio = capsys.readouterr()
        return CLIResult(rc, stdio.out, stdio.err)

    return _run


def test_list_to_stdout(run, tmp_path):
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(PYPROJECT)

    res = run("-f", tomlfile, "--list")
    assert res.code == 0
    assert res.stdout == "test docs\n"


def test_list_respects_output_file(run, tmp_path):
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(PYPROJECT)
    outfile = tmp_path / "out.txt"

    res = run("-f", tomlfile, "--list", "-o", outfile)
    assert res.code == 0
    assert res.stdout == ""
    assert outfile.read_text() == "test docs\n"
