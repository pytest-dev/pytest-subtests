CHANGELOG
=========

0.14.1
------

*2024-12-09*

* Fix ``self.instance._outcome`` is ``None`` case in #173 (`#174`_).

.. _#174: https://github.com/pytest-dev/pytest-subtests/pull/174

0.14.0
------

*2024-12-07*

* Add support for Python 3.13.

* Dropped support for EOL Python 3.8.

* Fixed output when using ``TestCase.skipTest`` (`#169`_).

* Fixed ``pytest`` requirement to ``>=7.3`` (`#159`_).

.. _#159: https://github.com/pytest-dev/pytest-subtests/issues/159
.. _#169: https://github.com/pytest-dev/pytest-subtests/pull/169

0.13.1
------

*2024-07-16*

* Fixed bug were an extra test would execute when ``-x/--exitfirst`` was used (`#139`_).

.. _#139: https://github.com/pytest-dev/pytest-subtests/pull/139

0.13.0
------

*2024-07-07*

* Dropped support for EOL Python 3.7.
* Added support for ``-x/--exitfirst`` (`#134`_).
* Hide the traceback inside the ``SubTests.test()`` method (`#131`_).

.. _#131: https://github.com/pytest-dev/pytest-subtests/pull/131
.. _#134: https://github.com/pytest-dev/pytest-subtests/pull/134

0.12.1
------

*2024-03-07*

* Fixed compatibility with upcoming pytest ``8.1.x``.  (`#125`_).

.. _#125: https://github.com/pytest-dev/pytest-subtests/issues/125

0.12.0
------

*2024-03-06*

* Python 3.12 is now officially supported (`#113`_).
* Added typing support (`#115`_).
* ``SubTests`` can be imported from ``pytest_subtests`` to type-annotate the ``subtests`` fixture.

.. _#113: https://github.com/pytest-dev/pytest-subtests/pull/113
.. _#115: https://github.com/pytest-dev/pytest-subtests/pull/115


0.11.0
------

*2023-05-15*

* Logging is displayed for failing subtests (`#92`_)
* Passing subtests no longer turn the pytest output to yellow (as if warnings have been issued) (`#86`_). Thanks to `Andrew-Brock`_ for providing the solution.
* Now the ``msg`` contents of a subtest is displayed when running pytest with ``-v`` (`#6`_).

.. _#6: https://github.com/pytest-dev/pytest-subtests/issues/6
.. _#86: https://github.com/pytest-dev/pytest-subtests/issues/86
.. _#92: https://github.com/pytest-dev/pytest-subtests/issues/87

.. _`Andrew-Brock`: https://github.com/Andrew-Brock

0.10.0
------

*2022-02-15*

* Added experimental support for suppressing subtest output dots in non-verbose mode with ``--no-subtests-shortletter`` -- this allows the native pytest column calculations to not be disrupted and minimizes unneeded output for large CI systems.

0.9.0
-----

*2022-10-28*

* Python 3.11 is officially supported.
* Dropped support for Python 3.6.

0.8.0
-----

*2022-05-26*

* Now passing subtests are shown in the test run summary at the end (for example: ``10 failed, 1 passed, 10 subtests passed in 0.10s``) (`#70`_).

.. _#70: https://github.com/pytest-dev/pytest-subtests/pull/70

0.7.0
-----

*2022-02-13*

* Fixed support for pytest 7.0, and ``pytest>=7.0`` is now required.


0.6.0
-----

*2022-01-15*

* ``pytest>=6.0`` is now required.
* Added official support for Python 3.10.
* Dropped support for Python 3.5.
* Users no longer need to configure a warnings filter for the internal ``A private pytest class or function was used`` pytest warning (`#52`_).
* **Experimental**: Use ``SUBPASS`` and ``,`` for passed subtests instead of general ``PASSED``,
  ``SUBFAIL`` and ``u`` for failed ones instead of ``FAILED`` (`#30`_).

.. _#30: https://github.com/pytest-dev/pytest-subtests/pull/30
.. _#52: https://github.com/pytest-dev/pytest-subtests/pull/52

0.5.0
-----

*2021-05-29*

* Added support for ``pytest.mark.xfail`` (`#40`_).

.. _#40: https://github.com/pytest-dev/pytest-subtests/pull/40

0.4.0
-----

*2020-12-13*

* Added support for ``--pdb`` (`#22`_).

.. _#22: https://github.com/pytest-dev/pytest-subtests/issues/22

0.3.2
-----

*2020-08-01*

* Fixed pytest 6.0 support.

0.3.1
-----

*2020-05-20*

* Fixed pytest 5.4 support.

0.3.0
-----

*2020-01-22*

* Dropped support for Python 3.4.
* ``subtests`` now correctly captures and displays stdout/stderr (`#18`_).

.. _#18: https://github.com/pytest-dev/pytest-subtests/issues/18

0.2.1
-----

*2019-04-04*

* Fixed verbose output reporting on Linux (`#7`_).

.. _#7: https://github.com/pytest-dev/pytest-subtests/issues/7

0.2.0
-----

*2019-04-03*

* Subtests are correctly reported with ``pytest-xdist>=1.28``.

0.1.0
-----

*2019-04-01*

* First release to PyPI.
