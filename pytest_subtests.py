import sys
from contextlib import contextmanager
from time import monotonic

import attr
import pytest
from _pytest._code import ExceptionInfo
from _pytest.capture import CaptureFixture
from _pytest.capture import FDCapture
from _pytest.capture import SysCapture
from _pytest.outcomes import Failed
from _pytest.outcomes import OutcomeException
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.unittest import TestCaseFunction


_ATTR_SUBREPORTS = "_subtests_reports"


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
        call_info = CallInfo(None, ExceptionInfo(exc_info), 0, 0, when="call")
        sub_report = SubTestReport.from_item_and_call(item=self, call=call_info)
        sub_report.context = SubTestContext(msg, dict(test.params))
        _push_report(self, sub_report)


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
    yield SubTests(request)


@attr.s
class SubTests(object):
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
        captured.update_report(sub_report)
        _push_report(self.item, sub_report)


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


def _push_report(item, report):
    if not hasattr(item, _ATTR_SUBREPORTS):
        setattr(item, _ATTR_SUBREPORTS, [])
    queue = getattr(item, _ATTR_SUBREPORTS)
    queue.append(report)


def _get_subreports(item):
    return getattr(item, _ATTR_SUBREPORTS, None)


class SubTestFailure(Exception):
    """Container to pass values between ``pytest_runtest_call`` and ``pytest_runtest_makereport``

    Allows to generate correct ``CallInfo`` after ``pytest.skip()``
    and to use subtest failure report as the test result.
    """

    def __init__(self, count, report, exc_info):
        # message for the case of unexpectedly skipped pytest_runtest_makereport
        super(SubTestFailure, self).__init__(
            "Subtest failures: {}".format(count), count
        )
        self.report = report
        self.outcome_excinfo = ExceptionInfo(exc_info) if exc_info is not None else None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Put subtest exception to outcome of otherwise passed test

    It causes reorder of subtest results if last ones are successful.
    Failure becomes the latest result.
    """
    outcome = yield
    report_list = _get_subreports(item)
    if not report_list:
        return

    outcome_exc_info = None
    try:
        outcome.get_result()
    except (Exception, Failed):
        # FIXME XFailed is inherited from Failed
        return
    except OutcomeException:
        outcome_exc_info = sys.exc_info()

    failure_report = None
    i_failure = -1
    for i, report in enumerate(reversed(report_list)):
        if report.outcome == "failed":
            i_failure, failure_report = i, report
            break

    if failure_report is None:
        return

    try:
        raise SubTestFailure(len(report_list), failure_report, outcome_exc_info)
    except SubTestFailure:
        outcome._excinfo = sys.exc_info()
        report_list.pop(-i_failure - 1)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Log subtest reports

    If test failed, returns nothing to transfer control to default hook.
    In the case of failed subtests, "pass" result of whole test is ignored,
    "skip" is logged and latest subtest failure becomes the return value.
    """
    if call.when != "call":
        return

    try:
        report_list = _get_subreports(item)
        if report_list is None:
            return
        for report in report_list:
            item.ihook.pytest_runtest_logreport(report=report)

        excinfo = call.excinfo
        result_report = None
        if excinfo is not None and isinstance(excinfo.value, SubTestFailure):
            exception = excinfo.value
            result_report = exception.report
            if exception.outcome_excinfo is not None:
                test_call_info = attr.evolve(call, excinfo=exception.outcome_excinfo)
                report = TestReport.from_item_and_call(item=item, call=test_call_info)
                item.ihook.pytest_runtest_logreport(report=report)

        return result_report
    finally:
        if hasattr(item, _ATTR_SUBREPORTS):
            delattr(item, _ATTR_SUBREPORTS)
