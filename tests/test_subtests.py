import sys

import pytest


@pytest.mark.parametrize("mode", ["normal", "xdist"])
class TestFixture:
    """
    Tests for ``subtests`` fixture.
    """

    @pytest.fixture
    def simple_script(self, testdir):
        testdir.makepyfile(
            """
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        assert i % 2 == 0
        """
        )

    def test_simple_terminal_normal(self, simple_script, testdir, mode):
        if mode == "normal":
            result = testdir.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            pytest.importorskip("xdist")
            result = testdir.runpytest("-n1")
            expected_lines = ["gw0 [1]"]

        expected_lines += [
            "* test_foo [[]custom[]] (i=1) *",
            "* test_foo [[]custom[]] (i=3) *",
            "* 2 failed, 1 passed in *",
        ]
        result.stdout.fnmatch_lines(expected_lines)

    def test_simple_terminal_verbose(self, simple_script, testdir, mode):
        if mode == "normal":
            result = testdir.runpytest("-v")
            expected_lines = [
                "*collected 1 item",
                "test_simple_terminal_verbose.py::test_foo PASSED *100%*",
                "test_simple_terminal_verbose.py::test_foo FAILED *100%*",
                "test_simple_terminal_verbose.py::test_foo PASSED *100%*",
                "test_simple_terminal_verbose.py::test_foo FAILED *100%*",
                "test_simple_terminal_verbose.py::test_foo PASSED *100%*",
                "test_simple_terminal_verbose.py::test_foo PASSED *100%*",
            ]
        else:
            pytest.importorskip("xdist")
            result = testdir.runpytest("-n1", "-v")
            expected_lines = [
                "gw0 [1]",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
                "*gw0*100%* test_simple_terminal_verbose.py::test_foo*",
            ]

        expected_lines += [
            "* test_foo [[]custom[]] (i=1) *",
            "* test_foo [[]custom[]] (i=3) *",
            "* 2 failed, 1 passed in *",
        ]
        result.stdout.fnmatch_lines(expected_lines)

    def test_skip(self, testdir, mode):
        testdir.makepyfile(
            """
            import pytest
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        if i % 2 == 0:
                            pytest.skip('even number')
        """
        )
        if mode == "normal":
            result = testdir.runpytest()
            expected_lines = ["collected 1 item"]
        else:
            pytest.importorskip("xdist")
            result = testdir.runpytest("-n1")
            expected_lines = ["gw0 [1]"]
        expected_lines += ["* 1 passed, 3 skipped in *"]
        result.stdout.fnmatch_lines(expected_lines)


class TestSubTest:
    """
    Test Test.subTest functionality.
    """

    @pytest.fixture
    def simple_script(self, testdir):
        return testdir.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            self.assertEqual(i % 2, 0)

            if __name__ == '__main__':
                main()
        """
        )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_simple_terminal_normal(self, simple_script, testdir, runner):

        if runner == "unittest":
            result = testdir.run(sys.executable, simple_script)
            result.stderr.fnmatch_lines(
                [
                    "FAIL: test_foo (__main__.T) [custom] (i=1)",
                    "AssertionError: 1 != 0",
                    "FAIL: test_foo (__main__.T) [custom] (i=3)",
                    "AssertionError: 1 != 0",
                    "Ran 1 test in *",
                    "FAILED (failures=2)",
                ]
            )
        else:
            if runner == "pytest-normal":
                result = testdir.runpytest(simple_script)
                expected_lines = ["collected 1 item"]
            else:
                pytest.importorskip("xdist")
                result = testdir.runpytest(simple_script, "-n1")
                expected_lines = ["gw0 [1]"]
            result.stdout.fnmatch_lines(
                expected_lines
                + [
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed in *",
                ]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_simple_terminal_verbose(self, simple_script, testdir, runner):

        if runner == "unittest":
            result = testdir.run(sys.executable, simple_script, "-v")
            result.stderr.fnmatch_lines(
                [
                    "test_foo (__main__.T) ... ",
                    "FAIL: test_foo (__main__.T) [custom] (i=1)",
                    "AssertionError: 1 != 0",
                    "FAIL: test_foo (__main__.T) [custom] (i=3)",
                    "AssertionError: 1 != 0",
                    "Ran 1 test in *",
                    "FAILED (failures=2)",
                ]
            )
        else:
            if runner == "pytest-normal":
                result = testdir.runpytest(simple_script, "-v")
                expected_lines = [
                    "*collected 1 item",
                    "test_simple_terminal_verbose.py::T::test_foo FAILED *100%*",
                    "test_simple_terminal_verbose.py::T::test_foo FAILED *100%*",
                    "test_simple_terminal_verbose.py::T::test_foo PASSED *100%*",
                ]
            else:
                pytest.importorskip("xdist")
                result = testdir.runpytest(simple_script, "-n1", "-v")
                expected_lines = [
                    "gw0 [1]",
                    "*gw0*100%* FAILED test_simple_terminal_verbose.py::T::test_foo*",
                    "*gw0*100%* FAILED test_simple_terminal_verbose.py::T::test_foo*",
                    "*gw0*100%* PASSED test_simple_terminal_verbose.py::T::test_foo*",
                ]
            result.stdout.fnmatch_lines(
                expected_lines
                + [
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed in *",
                ]
            )

    @pytest.mark.parametrize("runner", ["unittest", "pytest-normal", "pytest-xdist"])
    def test_skip(self, testdir, runner):
        p = testdir.makepyfile(
            """
            from unittest import TestCase, main

            class T(TestCase):

                def test_foo(self):
                    for i in range(5):
                        with self.subTest(msg="custom", i=i):
                            if i % 2 == 0:
                                self.skipTest('even number')

            if __name__ == '__main__':
                main()
        """
        )
        if runner == "unittest":
            result = testdir.runpython(p)
            result.stderr.fnmatch_lines(["Ran 1 test in *", "OK (skipped=3)"])
        else:
            pytest.xfail("Not producing the expected results (#5)")
            result = testdir.runpytest(p)
            result.stdout.fnmatch_lines(
                ["collected 1 item", "* 3 skipped, 1 passed in *"]
            )
