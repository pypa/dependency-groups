import pytest

PYPROJECT = """\
[dependency-groups]
test = ["pytest"]
docs = ["sphinx"]
"""


@pytest.fixture
def run(runner_factory):
    from dependency_groups.__main__ import main as cli_main

    return runner_factory(cli_main).invoke


def test_list_to_stdout(run, tmp_path):
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(PYPROJECT)

    res = run("-f", tomlfile, "--list")
    assert res.stdout == "test docs\n"


def test_list_respects_output_file(run, tmp_path):
    tomlfile = tmp_path / "pyproject.toml"
    tomlfile.write_text(PYPROJECT)
    outfile = tmp_path / "out.txt"

    res = run("-f", tomlfile, "--list", "-o", outfile)
    assert res.stdout == ""
    assert outfile.read_text() == "test docs\n"
