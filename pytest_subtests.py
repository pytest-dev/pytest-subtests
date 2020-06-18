import sys
from collections import ChainMap
from contextlib import contextmanager
from time import monotonic

import attr
import pytest
from _pytest._code import ExceptionInfo
from _pytest.capture import CaptureFixture
from _pytest.capture import FDCapture
from _pytest.capture import SysCapture
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
    yield SubTests(request.node.ihook, suspend_capture_ctx, request)


@pytest.fixture
def check(subtests):
    return subtests


@attr.s
class SubTestParams:
    msg = attr.ib(type=str, default=None)
    kwargs = attr.ib(type=dict, default=None)
    parent = attr.ib(type=ChainMap, default=None)
    contextmanager = attr.ib(default=None)

    def context(self):
        params = self.parent
        if self.kwargs:
            if params:
                params = params.new_child(self.kwargs)
            else:
                params = self.kwargs
        if not params:
            params = {}
        # xdist can not serialize ChainMap
        if isinstance(params, ChainMap):
            params = dict(params.items())
        return SubTestContext(self.msg, params)

    def child(self):
        chld = SubTestParams()
        if self.msg is not None:
            chld.msg = self.msg
        if self.parent is not None:
            if self.kwargs is not None:
                chld.parent = self.parent.new_child(self.kwargs)
            else:
                chld.parent = self.parent
        elif self.kwargs is not None:
            chld.parent = ChainMap(self.kwargs)
        return chld

    def updated(self, msg=None, **kwargs):
        copy = attr.evolve(self)
        if msg is not None:
            copy.msg = msg
        if kwargs:
            copy.kwargs = kwargs.copy()
        return copy


@attr.s
class SubTests(object):
    ihook = attr.ib()
    suspend_capture_ctx = attr.ib()
    request = attr.ib()
    _params = attr.ib(default=attr.Factory(SubTestParams), init=False)

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

    def test(self, msg=None, **kwargs):
        """Compatibility method, use ``subtest(msg, i=3)``"""
        return self.__call__(msg, **kwargs)

    @contextmanager
    def _nested_scope(self, saved_params):
        if saved_params is None:
            saved_params = self._params
        self._params = self._params.child()
        try:
            yield
        finally:
            self._params = saved_params

    @contextmanager
    def _subtest(self, saved_params=None):
        with self._nested_scope(saved_params), self._capture_result():
            yield

    @contextmanager
    def _capture_result(self):
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
        sub_report.context = self._params.context()

        captured.update_report(sub_report)

        with self.suspend_capture_ctx():
            self.ihook.pytest_runtest_logreport(report=sub_report)

    def __call__(self, msg=None, **kwargs):
        saved_params = self._params
        self._params = self._params.updated(msg, **kwargs)
        return self._subtest(saved_params)

    def __enter__(self):
        subtest = self._subtest()
        retval = subtest.__enter__()
        self._params.contextmanager = subtest
        return retval

    def __exit__(self, exc_type, exc_val, exc_tb):
        subtest = self._params.contextmanager
        self._params.contextmanager = None
        return subtest.__exit__(exc_type, exc_val, exc_tb)


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
