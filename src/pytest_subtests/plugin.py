from __future__ import annotations

import sys
import time
from contextlib import contextmanager
from contextlib import nullcontext
from typing import Any
from typing import Callable
from typing import ContextManager
from typing import Generator
from typing import Mapping
from typing import TYPE_CHECKING
from unittest import TestCase

import attr
import pytest
from _pytest._code import ExceptionInfo
from _pytest.capture import CaptureFixture
from _pytest.capture import FDCapture
from _pytest.capture import SysCapture
from _pytest.config.compat import PathAwareHookProxy
from _pytest.fixtures import SubRequest
from _pytest.logging import catching_logs
from _pytest.logging import LogCaptureHandler
from _pytest.outcomes import OutcomeException
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.runner import check_interactive_exception
from _pytest.unittest import TestCaseFunction

if TYPE_CHECKING:
    from types import TracebackType

    if sys.version_info < (3, 8):
        from typing_extensions import Literal
    else:
        from typing import Literal


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("subtests")
    group.addoption(
        "--no-subtests-shortletter",
        action="store_true",
        dest="no_subtests_shortletter",
        default=False,
        help="Disables subtest output 'dots' in non-verbose mode (EXPERIMENTAL)",
    )


@attr.s
class SubTestContext:
    msg: str | None = attr.ib()
    kwargs: dict[str, Any] = attr.ib()


@attr.s(init=False)
class SubTestReport(TestReport):  # type: ignore[misc]
    context: SubTestContext = attr.ib()

    @property
    def head_line(self) -> str:
        _, _, domain = self.location
        return f"{domain} {self.sub_test_description()}"

    def sub_test_description(self) -> str:
        parts = []
        if isinstance(self.context.msg, str):
            parts.append(f"[{self.context.msg}]")
        if self.context.kwargs:
            params_desc = ", ".join(
                f"{k}={v!r}" for (k, v) in sorted(self.context.kwargs.items())
            )
            parts.append(f"({params_desc})")
        return " ".join(parts) or "(<subtest>)"

    def _to_json(self) -> dict:
        data = super()._to_json()
        del data["context"]
        data["_report_type"] = "SubTestReport"
        data["_subtest.context"] = attr.asdict(self.context)
        return data

    @classmethod
    def _from_json(cls, reportdict: dict[str, Any]) -> SubTestReport:
        report = super()._from_json(reportdict)
        context_data = reportdict["_subtest.context"]
        report.context = SubTestContext(
            msg=context_data["msg"], kwargs=context_data["kwargs"]
        )
        return report

    @classmethod
    def _from_test_report(cls, test_report: TestReport) -> SubTestReport:
        return super()._from_json(test_report._to_json())


def _addSubTest(
    self: TestCaseFunction,
    test_case: Any,
    test: TestCase,
    exc_info: tuple[type[BaseException], BaseException, TracebackType] | None,
) -> None:
    if exc_info is not None:
        msg = test._message if isinstance(test._message, str) else None  # type: ignore[attr-defined]
        call_info = make_call_info(
            ExceptionInfo(exc_info, _ispytest=True),
            start=0,
            stop=0,
            duration=0,
            when="call",
        )
        report = self.ihook.pytest_runtest_makereport(item=self, call=call_info)
        sub_report = SubTestReport._from_test_report(report)
        sub_report.context = SubTestContext(msg, dict(test.params))  # type: ignore[attr-defined]
        self.ihook.pytest_runtest_logreport(report=sub_report)
        if check_interactive_exception(call_info, sub_report):
            self.ihook.pytest_exception_interact(
                node=self, call=call_info, report=sub_report
            )


def pytest_configure(config: pytest.Config) -> None:
    TestCaseFunction.addSubTest = _addSubTest  # type: ignore[attr-defined]
    TestCaseFunction.failfast = False  # type: ignore[attr-defined]

    # Hack (#86): the terminal does not know about the "subtests"
    # status, so it will by default turn the output to yellow.
    # This forcibly adds the new 'subtests' status.
    import _pytest.terminal

    new_types = tuple(
        f"subtests {outcome}" for outcome in ("passed", "failed", "skipped")
    )
    # We need to check if we are not re-adding because we run our own tests
    # with pytester in-process mode, so this will be called multiple times.
    if new_types[0] not in _pytest.terminal.KNOWN_TYPES:
        _pytest.terminal.KNOWN_TYPES = _pytest.terminal.KNOWN_TYPES + new_types  # type: ignore[assignment]

    _pytest.terminal._color_for_type.update(
        {
            f"subtests {outcome}": _pytest.terminal._color_for_type[outcome]
            for outcome in ("passed", "failed", "skipped")
            if outcome in _pytest.terminal._color_for_type
        }
    )


def pytest_unconfigure() -> None:
    if hasattr(TestCaseFunction, "addSubTest"):
        del TestCaseFunction.addSubTest
    if hasattr(TestCaseFunction, "failfast"):
        del TestCaseFunction.failfast


@pytest.fixture
def subtests(request: SubRequest) -> Generator[SubTests, None, None]:
    capmam = request.node.config.pluginmanager.get_plugin("capturemanager")
    if capmam is not None:
        suspend_capture_ctx = capmam.global_and_fixture_disabled
    else:
        suspend_capture_ctx = nullcontext
    yield SubTests(request.node.ihook, suspend_capture_ctx, request)


@attr.s
class SubTests:
    ihook: PathAwareHookProxy = attr.ib()
    suspend_capture_ctx: Callable[[], ContextManager] = attr.ib()
    request: SubRequest = attr.ib()

    @property
    def item(self) -> pytest.Item:
        return self.request.node

    @contextmanager
    def _capturing_output(self) -> Generator[Captured, None, None]:
        option = self.request.config.getoption("capture", None)

        # capsys or capfd are active, subtest should not capture

        capman = self.request.config.pluginmanager.getplugin("capturemanager")
        capture_fixture_active = getattr(capman, "_capture_fixture", None)

        if option == "sys" and not capture_fixture_active:
            with ignore_pytest_private_warning():
                fixture = CaptureFixture(SysCapture, self.request)
        elif option == "fd" and not capture_fixture_active:
            with ignore_pytest_private_warning():
                fixture = CaptureFixture(FDCapture, self.request)
        else:
            fixture = None

        if fixture is not None:
            fixture._start()

        captured = Captured()
        try:
            yield captured
        finally:
            if fixture is not None:
                out, err = fixture.readouterr()
                fixture.close()
                captured.out = out
                captured.err = err

    @contextmanager
    def _capturing_logs(self) -> Generator[CapturedLogs | NullCapturedLogs, None, None]:
        logging_plugin = self.request.config.pluginmanager.getplugin("logging-plugin")
        if logging_plugin is None:
            yield NullCapturedLogs()
        else:
            handler = LogCaptureHandler()
            handler.setFormatter(logging_plugin.formatter)

            captured_logs = CapturedLogs(handler)
            with catching_logs(handler):
                yield captured_logs

    @contextmanager
    def test(
        self,
        msg: str | None = None,
        **kwargs: Any,
    ) -> Generator[None, None, None]:
        start = time.time()
        precise_start = time.perf_counter()
        exc_info = None

        with self._capturing_output() as captured_output, self._capturing_logs() as captured_logs:
            try:
                yield
            except (Exception, OutcomeException):
                exc_info = ExceptionInfo.from_current()

        precise_stop = time.perf_counter()
        duration = precise_stop - precise_start
        stop = time.time()

        call_info = make_call_info(
            exc_info, start=start, stop=stop, duration=duration, when="call"
        )
        report = self.ihook.pytest_runtest_makereport(item=self.item, call=call_info)
        sub_report = SubTestReport._from_test_report(report)
        sub_report.context = SubTestContext(msg, kwargs.copy())

        captured_output.update_report(sub_report)
        captured_logs.update_report(sub_report)

        with self.suspend_capture_ctx():
            self.ihook.pytest_runtest_logreport(report=sub_report)

        if check_interactive_exception(call_info, sub_report):
            self.ihook.pytest_exception_interact(
                node=self.item, call=call_info, report=sub_report
            )


def make_call_info(
    exc_info: ExceptionInfo[BaseException] | None,
    *,
    start: float,
    stop: float,
    duration: float,
    when: Literal["collect", "setup", "call", "teardown"],
) -> CallInfo:
    return CallInfo(
        None,
        exc_info,
        start=start,
        stop=stop,
        duration=duration,
        when=when,
        _ispytest=True,
    )


@contextmanager
def ignore_pytest_private_warning() -> Generator[None, None, None]:
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            "A private pytest class or function was used.",
            category=pytest.PytestDeprecationWarning,
        )
        yield


@attr.s
class Captured:
    out = attr.ib(default="", type=str)
    err = attr.ib(default="", type=str)

    def update_report(self, report: pytest.TestReport) -> None:
        if self.out:
            report.sections.append(("Captured stdout call", self.out))
        if self.err:
            report.sections.append(("Captured stderr call", self.err))


class CapturedLogs:
    def __init__(self, handler: LogCaptureHandler) -> None:
        self._handler = handler

    def update_report(self, report: pytest.TestReport) -> None:
        report.sections.append(("Captured log call", self._handler.stream.getvalue()))


class NullCapturedLogs:
    def update_report(self, report: pytest.TestReport) -> None:
        pass


def pytest_report_to_serializable(report: pytest.TestReport) -> dict[str, Any] | None:
    if isinstance(report, SubTestReport):
        return report._to_json()
    return None


def pytest_report_from_serializable(data: dict[str, Any]) -> SubTestReport | None:
    if data.get("_report_type") == "SubTestReport":
        return SubTestReport._from_json(data)
    return None


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(
    report: pytest.TestReport,
    config: pytest.Config,
) -> tuple[str, str, str | Mapping[str, bool]] | None:
    if report.when != "call" or not isinstance(report, SubTestReport):
        return None

    if hasattr(report, "wasxfail"):
        return None

    outcome = report.outcome
    description = report.sub_test_description()
    if report.passed:
        short = "" if config.option.no_subtests_shortletter else ","
        return f"subtests {outcome}", short, f"{description} SUBPASS"
    elif report.skipped:
        short = "" if config.option.no_subtests_shortletter else "-"
        return outcome, short, f"{description} SUBSKIP"
    elif outcome == "failed":
        short = "" if config.option.no_subtests_shortletter else "u"
        return outcome, short, f"{description} SUBFAIL"

    return None
