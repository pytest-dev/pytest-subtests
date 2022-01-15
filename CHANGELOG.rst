CHANGELOG
=========

UNRELEASED
----------

* Dropped support for Python 3.5.
* Use ``SUBPASS`` and ``,`` for passed subtests instead of general ``PASSED``,
  ``SUBFAIL`` and ``u`` for failed ones instead of ``FAILED`` (`#30`_).

.. _#30: https://github.com/pytest-dev/pytest-subtests/pull/30

0.5.0 (2021-05-29)
------------------

* Add support for ``pytest.mark.xfail`` (`#40`_).

.. _#40: https://github.com/pytest-dev/pytest-subtests/pull/40

0.4.0 (2020-12-13)
------------------

* Add support for ``--pdb`` (`#22`_).

.. _#22: https://github.com/pytest-dev/pytest-subtests/issues/22

0.3.2 (2020-08-01)
------------------

* Fix pytest 6.0 support.

0.3.1 (2020-05-20)
------------------

* Fix pytest 5.4 support.

0.3.0 (2020-01-22)
------------------

* Dropped support for Python 3.4.
* ``subtests`` now correctly captures and displays stdout/stderr (`#18`_).

.. _#18: https://github.com/pytest-dev/pytest-subtests/issues/18

0.2.1 (2019-04-04)
------------------

* Fix verbose output reporting on Linux (`#7`_).

.. _#7: https://github.com/pytest-dev/pytest-subtests/issues/7

0.2.0 (2019-04-03)
------------------

* Subtests are correctly reported with ``pytest-xdist>=1.28``.

0.1.0 (2019-04-01)
------------------

* First release to PyPI.
