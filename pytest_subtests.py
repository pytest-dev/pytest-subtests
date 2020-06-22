import sys
from contextlib import contextmanager
from time import monotonic

import attr
import pytest
from _pytest._code import ExceptionInfo
from _pytest.capture import CaptureFixture
from _pytest.capture import FDCapture
from _pytest.capture import SysCapture
from _pytest.outcomes import OutcomeException
from _pytest.outcomes import Skipped
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.unittest import TestCaseFunction

if sys.version_info[:2] < (3, 7):

    @contextmanager
    def nullcontext():
        yield


else:
    from contextlib import nullcontext

_ATTR_COUNTER = "_subtests_failed"


class SubTestFailed(OutcomeException):
    """Exception to report failures due to subtest errors

    Raised to modify outcome of otherwise passed or skipped test
    if it has failed subtests.
    """

    @classmethod
    def from_count(cls, count):
        return cls("Failed subtests: {}".format(count))


@attr.s
class SubTestContext(object):
    msg = attr.ib()
    kwargs = attr.ib()


@attr.s(init=False)
class SubTestReport(TestReport):
    context = attr.ib()

    @property
    def count_towards_summary(self):
        return not self.passed

    @property
    def head_line(self):
        _, _, domain = self.location
        return "{} {}".format(domain, self.sub_test_description())

    def sub_test_description(self):
        parts = []
        if isinstance(self.context.msg, str):
            parts.append("[{}]".format(self.context.msg))
        if self.context.kwargs:
            params_desc = ", ".join(
                "{}={!r}".format(k, v) for (k, v) in sorted(self.context.kwargs.items())
            )
            parts.append("({})".format(params_desc))
        return " ".join(parts) or "(<subtest>)"

    def _to_json(self):
        data = super()._to_json()
        del data["context"]
        data["_report_type"] = "SubTestReport"
        data["_subtest.context"] = attr.asdict(self.context)
        return data

    @classmethod
    def _from_json(cls, reportdict):
        report = super()._from_json(reportdict)
        context_data = reportdict["_subtest.context"]
        report.context = SubTestContext(
            msg=context_data["msg"], kwargs=context_data["kwargs"]
        )
        return report


def _addSubTest(self, test_case, test, exc_info):
    if exc_info is not None:
        msg = test._message if isinstance(test._message, str) else None
        exc_info = ExceptionInfo(exc_info)
        call_info = CallInfo(None, exc_info, 0, 0, when="call")
        sub_report = SubTestReport.from_item_and_call(item=self, call=call_info)
        sub_report.context = SubTestContext(msg, dict(test.params))
        self.ihook.pytest_runtest_logreport(report=sub_report)
        _increment_failed_subtests(exc_info, self)


def pytest_configure(config):
    TestCaseFunction.addSubTest = _addSubTest
    TestCaseFunction.failfast = False


def pytest_unconfigure():
    if hasattr(TestCaseFunction, "_addSubTest"):
        del TestCaseFunction.addSubTest
    if hasattr(TestCaseFunction, "failfast"):
        del TestCaseFunction.failfast


@pytest.fixture
def subtests(request):
    capmam = request.node.config.pluginmanager.get_plugin("capturemanager")
    if capmam is not None:
        suspend_capture_ctx = capmam.global_and_fixture_disabled
    else:
        suspend_capture_ctx = nullcontext
    yield SubTests(request.node.ihook, suspend_capture_ctx, request)


@attr.s
class SubTests(object):
    ihook = attr.ib()
    suspend_capture_ctx = attr.ib()
    request = attr.ib()

    @property
    def item(self):
        return self.request.node

    @contextmanager
    def _capturing_output(self):
        option = self.request.config.getoption("capture", None)

        # capsys or capfd are active, subtest should not capture

        # pytest<5.4 support: node holds the active fixture
        capture_fixture_active = getattr(self.request.node, "_capture_fixture", None)
        if capture_fixture_active is None:
            # pytest>=5.4 support: capture manager plugin holds the active fixture
            capman = self.request.config.pluginmanager.getplugin("capturemanager")
            capture_fixture_active = getattr(capman, "_capture_fixture", None)

        if option == "sys" and not capture_fixture_active:
            fixture = CaptureFixture(SysCapture, self.request)
        elif option == "fd" and not capture_fixture_active:
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
    def test(self, msg=None, **kwargs):
        start = monotonic()
        exc_info = None

        with self._capturing_output() as captured:
            try:
                yield
            except (Exception, OutcomeException):
                exc_info = ExceptionInfo.from_current()

        stop = monotonic()

        call_info = CallInfo(None, exc_info, start, stop, when="call")
        sub_report = SubTestReport.from_item_and_call(item=self.item, call=call_info)
        sub_report.context = SubTestContext(msg, kwargs.copy())
        _increment_failed_subtests(exc_info, self.item)

        captured.update_report(sub_report)

        with self.suspend_capture_ctx():
            self.ihook.pytest_runtest_logreport(report=sub_report)


@attr.s
class Captured:
    out = attr.ib(default="", type=str)
    err = attr.ib(default="", type=str)

    def update_report(self, report):
        if self.out:
            report.sections.append(("Captured stdout call", self.out))
        if self.err:
            report.sections.append(("Captured stderr call", self.err))


def pytest_report_to_serializable(report):
    if isinstance(report, SubTestReport):
        return report._to_json()


def pytest_report_from_serializable(data):
    if data.get("_report_type") == "SubTestReport":
        return SubTestReport._from_json(data)
    elif data.get("$report_type") == "SubTestFailureReport":
        return SubTestFailureReport._from_json(data)


def _increment_failed_subtests(exc_info, item):
    # For unittest.TestCase.subTest skipped tests
    # are processed through TestResult.addSkip, not here
    if exc_info is None or exc_info.errisinstance(Skipped):
        return
    setattr(item, _ATTR_COUNTER, getattr(item, _ATTR_COUNTER, 0) + 1)


# a function to be shown in traceback instead of less informative hook name
def check_failed_subtests(item):
    failed = getattr(item, _ATTR_COUNTER, 0)
    if failed > 0:
        raise SubTestFailed.from_count(failed)


# more tricky alternative is pytest_runtest_makereport hook
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Wrapper to avoid accounting of tests with failed subtests as passed

    Force ``SubTestFailed`` exception if some subtests failed
    but the test outcome is from passed or skipped categories.
    """
    __tracebackhide__ = True
    try:
        outcome = yield
        try:
            outcome.get_result()
        except Skipped:
            pass
        except (Exception, OutcomeException):
            return

        # Due to pluggy#244 could not just raise the exception
        try:
            check_failed_subtests(item)
        except SubTestFailed:
            outcome._excinfo = sys.exc_info()
    finally:
        if hasattr(item, _ATTR_COUNTER):
            delattr(item, _ATTR_COUNTER)


class SubTestFailureReport(TestReport):
    @property
    def count_towards_summary(self):
        return False


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    excinfo = call.excinfo
    if excinfo is None or not isinstance(excinfo.value, SubTestFailed):
        return

    report = SubTestFailureReport.from_item_and_call(item=item, call=call)
    report.longrepr = str(excinfo.value)
    return report
