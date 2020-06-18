"""Tests of convenience shortcuts for the subtests fixture."""
import pytest

_cases = [
    (
        "concise",
        """
        from datetime import datetime

        def test_fields({fixturename}):
            dt = datetime.utcfromtimestamp(1234567890)
            with {fixturename}: assert dt.year == 2009, "OK"
            with {fixturename}: assert dt.month == 1
            with {fixturename}: assert dt.day == 13, "OK"
            with {fixturename}: assert dt.hour == 27
        """,
        [
            "*= FAILURES =*",
            "*_ test_fields (<subtest>) _*",
            "E*assert 2 == 1",
            "*_ test_fields (<subtest>) _*",
            "E*assert 23 == 27",
            # "FAILED *::test_fields - assert 2 == 1*",
            # "FAILED *::test_fields - assert 23 == 27*",
            # "*= 2 failed*",
        ],
    ),
    (
        "steps",
        """
        from datetime import datetime

        def test_steps({fixturename}):
            '''Document steps using {fixturename}.__call__()'''
            dt = datetime.utcfromtimestamp(1234567890)
            {fixturename}("date")
            with {fixturename}: assert dt.year == 2009, "OK"
            with {fixturename}: assert dt.month == 1
            with {fixturename}: assert dt.day == 13, "OK"
            {fixturename}("time")
            with {fixturename}: assert dt.hour == 27
            with {fixturename}: assert dt.minute == 31, "OK"
            with {fixturename}: assert dt.second == 30, "OK"
        """,
        [
            "*= FAILURES =*",
            "*_ test_steps [[]date[]] _*",
            "E*assert 2 == 1",
            "*_ test_steps [[]time[]] _*",
            "E*assert 23 == 27",
            # "FAILED *::test_steps - assert 2 == 1*",
            # "FAILED *::test_steps - assert 23 == 27*",
            # "*= 2 failed*",
        ],
    ),
    (
        "test_subtest_steps",
        """
        from datetime import datetime

        def test_subtest_steps({fixturename}):
            '''Document steps using {fixturename}.__call__()'''
            dt = datetime.utcfromtimestamp(1234567890)
            with {fixturename}:
                {fixturename}("date")
                with {fixturename}: assert dt.year == 2009, "OK"
                with {fixturename}: assert dt.month == 1
                with {fixturename}: assert dt.day == 13, "OK"
                {fixturename}("time")
                with {fixturename}: assert dt.hour == 27
                with {fixturename}: assert dt.minute == 31, "OK"
                with {fixturename}: assert dt.second == 30, "OK"
        """,
        [
            "*= FAILURES =*",
            "*_ test_subtest_steps [[]date[]] _*",
            "E*assert 2 == 1",
            "*_ test_subtest_steps [[]time[]] _*",
            "E*assert 23 == 27",
            # "FAILED *::test_subtest_steps - assert 2 ==*",
            # "FAILED *::test_subtest_steps - assert 23 =*",
            # "*= 2 failed*",
        ],
    ),
    (
        "nested",
        """
        def test_unit_nested_args({fixturename}):
            with {fixturename}('outer subtest', outer=1, to_override='out'):
                with {fixturename}('inner subtest', to_override='in', inner=1):
                    assert 5 == 2*2, 'inner assert msg'
                assert 3 == 1 + 1, 'outer assert msg'
        """,
        [
            "*= FAILURES =*",
            "*_ test_unit_nested_args [[]inner subtest[]] (inner=1, outer=1, to_override='in') _*",
            "E*AssertionError: inner assert msg*",
            "*_ test_unit_nested_args [[]outer subtest[]] (outer=1, to_override='out') _*",
            "E*AssertionError: outer assert msg",
            # "FAILED *::test_unit_nested_args - AssertionError: inner a*",
            # "FAILED *::test_unit_nested_args - AssertionError: outer a*",
            # "*= 2 failed*",
        ],
    ),
]


def _get_case_id(case):
    return case[0]


@pytest.mark.parametrize("runner", ["normal", "xdist"])
@pytest.mark.parametrize("fixturename", ["subtests", "check"])
@pytest.mark.parametrize("case", _cases, ids=_get_case_id)
def test_subtest_sugar(testdir, case, runner, fixturename):
    _id, script_template, expected_lines_template = case

    testdir.makepyfile(script_template.format(fixturename=fixturename))
    if runner == "normal":
        result = testdir.runpytest()
        collected_message = "collected 1 item"
    elif runner == "xdist":
        result = testdir.runpytest("-n1")
        collected_message = "gw0 [1]"
    else:
        pytest.fail("Unsupported runner {}".format(runner))

    expected_lines = [
        template.format(collected_message=collected_message)
        for template in ["{collected_message}"] + expected_lines_template
    ]
    result.stdout.fnmatch_lines(expected_lines)
