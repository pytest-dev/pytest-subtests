=========================
Releasing pytest-subtests
=========================

This document describes the steps to make a new ``pytest-subtests`` release.

Version
-------

``master`` should always be green and a potential release candidate. ``pytest-subtests`` follows
semantic versioning, so given that the current version is ``X.Y.Z``, to find the next version number
one needs to look at the ``CHANGELOG.rst`` file:

- If there any new feature, then we must make a new **minor** release: next
  release will be ``X.Y+1.0``.

- Otherwise it is just a **bug fix** release: ``X.Y.Z+1``.


Steps
-----

To publish a new release ``X.Y.Z``, the steps are as follows:

#. Create a new branch named ``release-X.Y.Z`` from the latest ``master``.

#. Update the ``CHANGELOG.rst`` file with the new release information.

#. Commit and push the branch for review.

#. Once PR is **green** and **approved**, create and push a tag::

    $ export VERSION=X.Y.Z
    $ git tag v$VERSION release-$VERSION
    $ git push git@github.com:pytest-dev/pytest-subtests.git v$VERSION

That will build the package and publish it on ``PyPI`` automatically.
