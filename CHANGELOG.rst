CHANGELOG
=========

0.6.0 (2022-01-15)
------------------

* ``pytest>=6.0`` is now required.
* Added official support for Python 3.10.
* Dropped support for Python 3.5.
* Users no longer need to configure a warnings filter for the internal ``A private pytest class or function was used`` pytest warning (`#52`_).
* **Experimental**: Use ``SUBPASS`` and ``,`` for passed subtests instead of general ``PASSED``,
  ``SUBFAIL`` and ``u`` for failed ones instead of ``FAILED`` (`#30`_).

.. _#30: https://github.com/pytest-dev/pytest-subtests/pull/30
.. _#52: https://github.com/pytest-dev/pytest-subtests/pull/52

0.5.0 (2021-05-29)
------------------

* Added support for ``pytest.mark.xfail`` (`#40`_).

.. _#40: https://github.com/pytest-dev/pytest-subtests/pull/40

0.4.0 (2020-12-13)
------------------

* Added support for ``--pdb`` (`#22`_).

.. _#22: https://github.com/pytest-dev/pytest-subtests/issues/22

0.3.2 (2020-08-01)
------------------

* Fixed pytest 6.0 support.

0.3.1 (2020-05-20)
------------------

* Fixed pytest 5.4 support.

0.3.0 (2020-01-22)
------------------

* Dropped support for Python 3.4.
* ``subtests`` now correctly captures and displays stdout/stderr (`#18`_).

.. _#18: https://github.com/pytest-dev/pytest-subtests/issues/18

0.2.1 (2019-04-04)
------------------

* Fixed verbose output reporting on Linux (`#7`_).

.. _#7: https://github.com/pytest-dev/pytest-subtests/issues/7

0.2.0 (2019-04-03)
------------------

* Subtests are correctly reported with ``pytest-xdist>=1.28``.

0.1.0 (2019-04-01)
------------------

* First release to PyPI.
