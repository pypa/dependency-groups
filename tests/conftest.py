from __future__ import annotations

import dataclasses
import functools
import typing as t

import pytest

if t.TYPE_CHECKING:
    import os
    from collections.abc import Mapping, Sequence

    # the "dependency_groups" argument type of the library APIs
    Groups = Mapping[str, Sequence[t.Union[str, Mapping[str, str]]]]


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

    def __call__(
        self, *argv: str | os.PathLike[str], expect_exit_code: int | None = 0
    ) -> CLIResult:
        __tracebackhide__ = True
        rc = 0
        try:
            self.entry_point(argv=[str(arg) for arg in argv])
        except SystemExit as e:
            assert isinstance(e.code, int), f"CLI exited with non-int code: {e.code!r}"
            rc = e.code

        stdio = self.capsys.readouterr()
        result = CLIResult(rc, stdio.out, stdio.err)

        if expect_exit_code is not None and result.code != expect_exit_code:
            pytest.fail(
                f"Expected exit({expect_exit_code}), saw exit({result.code}). "
                f"Result: {result}"
            )

        return result


RunnerFactory = t.Callable[[CliEntryPoint], CliRunner]


@pytest.fixture
def runner_factory(capsys: pytest.CaptureFixture[str]) -> RunnerFactory:
    return functools.partial(CliRunner, capsys=capsys)
