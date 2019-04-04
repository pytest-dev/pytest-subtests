===============
pytest-subtests
===============

unittest ``subTest()`` support and ``subtests`` fixture.

.. image:: https://img.shields.io/pypi/v/pytest-subtests.svg
    :target: https://pypi.org/project/pytest-subtests
    :alt: PyPI version

.. image:: https://img.shields.io/conda/vn/conda-forge/pytest-subtests.svg
    :target: https://anaconda.org/conda-forge/pytest-subtests

.. image:: https://img.shields.io/pypi/pyversions/pytest-subtests.svg
    :target: https://pypi.org/project/pytest-subtests
    :alt: Python versions

.. image:: https://travis-ci.com/pytest-dev/pytest-subtests.svg?branch=master
    :target: https://travis-ci.com/pytest-dev/pytest-subtests
    :alt: See Build Status on Travis CI

.. image:: https://pytest-dev.visualstudio.com/pytest-subtests/_apis/build/status/pytest-dev.pytest-subtests?branchName=master
    :target: https://dev.azure.com/pytest-dev/pytest-subtests
    :alt: See Build Status on Azure

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

----

This `pytest`_ plugin was generated with `Cookiecutter`_ along with `@hackebrot`_'s `cookiecutter-pytest-plugin`_ template.


Features
--------

* Adds support for `TestCase.subTest <https://docs.python.org/3/library/unittest.html#distinguishing-test-iterations-using-subtests>`__.

* New ``subtests`` fixture, providing similar functionality for pure pytest tests.


Requirements
------------

* ``Python`` >= 3.4.
* ``pytest`` >= 4.4.

Installation
------------

You can install ``pytest-subtests`` via `pip`_ from `PyPI`_::

    $ pip install pytest-subtests



Usage
-----

unittest subTest() example
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import unittest


    class T(unittest.TestCase):
        def test_foo(self):
            for i in range(5):
                with self.subTest("custom message", i=i):
                    self.assertEqual(i % 2, 0)


    if __name__ == "__main__":
        unittest.main()


**Output**

.. code-block::

    λ pytest .tmp\test-unit-subtest.py
    ======================== test session starts ========================
    ...
    collected 1 item

    .tmp\test-unit-subtest.py FF.                                  [100%]

    ============================= FAILURES ==============================
    _________________ T.test_foo [custom message] (i=1) _________________

    self = <test-unit-subtest.T testMethod=test_foo>

        def test_foo(self):
            for i in range(5):
                with self.subTest('custom message', i=i):
    >               self.assertEqual(i % 2, 0)
    E               AssertionError: 1 != 0

    .tmp\test-unit-subtest.py:9: AssertionError
    _________________ T.test_foo [custom message] (i=3) _________________

    self = <test-unit-subtest.T testMethod=test_foo>

        def test_foo(self):
            for i in range(5):
                with self.subTest('custom message', i=i):
    >               self.assertEqual(i % 2, 0)
    E               AssertionError: 1 != 0

    .tmp\test-unit-subtest.py:9: AssertionError
    ================ 2 failed, 1 passed in 0.07 seconds =================


``subtests`` fixture example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def test(subtests):
        for i in range(5):
            with subtests.test(msg="custom message", i=i):
                assert i % 2 == 0


**Output**

.. code-block::

    λ pytest .tmp\test-subtest.py
    ======================== test session starts ========================
    ...
    collected 1 item

    .tmp\test-subtest.py .F.F..                                    [100%]

    ============================= FAILURES ==============================
    ____________________ test [custom message] (i=1) ____________________

        def test(subtests):
            for i in range(5):
                with subtests.test(msg='custom message', i=i):
    >               assert i % 2 == 0
    E               assert (1 % 2) == 0

    .tmp\test-subtest.py:4: AssertionError
    ____________________ test [custom message] (i=3) ____________________

        def test(subtests):
            for i in range(5):
                with subtests.test(msg='custom message', i=i):
    >               assert i % 2 == 0
    E               assert (3 % 2) == 0

    .tmp\test-subtest.py:4: AssertionError
    ================ 2 failed, 1 passed in 0.07 seconds =================

Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_:

.. code-block::

    tox -e py37,linting

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-subtests" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

.. _`Cookiecutter`: https://github.com/audreyr/cookiecutter
.. _`@hackebrot`: https://github.com/hackebrot
.. _`MIT`: http://opensource.org/licenses/MIT
.. _`BSD-3`: http://opensource.org/licenses/BSD-3-Clause
.. _`GNU GPL v3.0`: http://www.gnu.org/licenses/gpl-3.0.txt
.. _`Apache Software License 2.0`: http://www.apache.org/licenses/LICENSE-2.0
.. _`cookiecutter-pytest-plugin`: https://github.com/pytest-dev/cookiecutter-pytest-plugin
.. _`file an issue`: https://github.com/nicoddemus/pytest-subtests/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
