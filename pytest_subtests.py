import sys
from contextlib import contextmanager
from time import time

import attr
import pytest
from _pytest._code import ExceptionInfo
from _pytest.outcomes import OutcomeException
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.unittest import TestCaseFunction

if sys.version_info[:2] < (3, 7):

    @contextmanager
    def nullcontext():
        yield


else:
    from contextlib import nullcontext


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
        self.ihook.pytest_runtest_logreport(report=sub_report)


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
    yield SubTests(request.node.ihook, request.node, suspend_capture_ctx)


@attr.s
class SubTests(object):
    ihook = attr.ib()
    item = attr.ib()
    suspend_capture_ctx = attr.ib()

    @contextmanager
    def test(self, msg=None, **kwargs):
        start = time()
        exc_info = None
        try:
            yield
        except (Exception, OutcomeException):
            exc_info = ExceptionInfo.from_current()
        stop = time()
        call_info = CallInfo(None, exc_info, start, stop, when="call")
        sub_report = SubTestReport.from_item_and_call(item=self.item, call=call_info)
        sub_report.context = SubTestContext(msg, kwargs.copy())
        with self.suspend_capture_ctx():
            self.ihook.pytest_runtest_logreport(report=sub_report)


def pytest_report_to_serializable(report):
    if isinstance(report, SubTestReport):
        return report._to_json()


def pytest_report_from_serializable(data):
    if data.get("_report_type") == "SubTestReport":
        return SubTestReport._from_json(data)
