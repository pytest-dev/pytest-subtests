import pytest
import six

pytestmark = pytest.mark.skipif(six.PY2, reason="plugin will be Python 3 only")


class TestFixture:
    """
    TODO: test skips, xfails
    """

    def test_simple_terminal_out(self, testdir):
        testdir.makepyfile(
            """
            def test_foo(subtests):
                for i in range(5):
                    with subtests.test(msg="custom", i=i):
                        assert i % 2 == 0
        """
        )
        result = testdir.runpytest()
        result.stdout.fnmatch_lines(
            [
                "collected 1 item",
                "* test_foo [[]custom[]] (i=1) *",
                "* test_foo [[]custom[]] (i=3) *",
                "* 2 failed, 1 passed in *",
            ]
        )

        # TODO: test skips, xfail


class TestSubTest:
    """
    # TODO: test skips, xfails
    """

    @pytest.mark.parametrize("runner", ["unittest", "pytest"])
    def test_simple_terminal_out(self, testdir, runner):
        p = testdir.makepyfile(
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
        if runner == "unittest":
            result = testdir.runpython(p)
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
            result = testdir.runpytest(p)
            result.stdout.fnmatch_lines(
                [
                    "collected 1 item",
                    "* T.test_foo [[]custom[]] (i=1) *",
                    "E  * AssertionError: 1 != 0",
                    "* T.test_foo [[]custom[]] (i=3) *",
                    "E  * AssertionError: 1 != 0",
                    "* 2 failed, 1 passed in *",
                ]
            )
