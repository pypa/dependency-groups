from __future__ import annotations

import dataclasses
import typing as t

import pytest


class CliEntryPoint(t.Protocol):
    def __call__(self, *, argv: list[str] | None = None) -> None: ...


@dataclasses.dataclass
class CLIResult:
    code: int
    stdout: str
    stderr: str


@dataclasses.dataclass
class CliRunner:
    entry_point: CliEntryPoint
    capsys: pytest.CaptureFixture[str]

    def invoke(self, *argv: str, expect_exit_code: int | None = 0) -> CLIResult:
        __tracebackhide__ = True
        try:
            self.entry_point(argv=[str(arg) for arg in argv])
            rc = 0
        except SystemExit as e:
            rc = e.code

        stdio = self.capsys.readouterr()
        result = CLIResult(rc, stdio.out, stdio.err)

        if expect_exit_code is not None and result.code != expect_exit_code:
            pytest.fail(
                f"Expected exit({expect_exit_code}), saw exit({result.code}). "
                f"Result: {result}"
            )

        return result


@pytest.fixture
def runner_factory(capsys: pytest.CaptureFixture[str]):
    def bind(entry_point: CliEntryPoint, /) -> CliRunner:
        return CliRunner(entry_point, capsys)

    return bind
