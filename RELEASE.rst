Release
-------

This file provides the steps for releasing a new version of Papyrus.

Verify that the version number is correct in ``setup.py`` and ``docs/conf.py``.
If not then change it, then commit and push.

Verify that the tests pass, with 100% (or close) coverage::

    $ nosetests
    ......................................................
    Name                               Stmts   Miss  Cover   Missing
    ----------------------------------------------------------------
    papyrus                               29      0   100%
    papyrus.geo_interface                 47      0   100%
    papyrus.protocol                     180      0   100%
    papyrus.renderers                     17      0   100%
    papyrus.tests                          0      0   100%
    papyrus.tests.test_geo_interface     112      0   100%
    papyrus.tests.test_init               90      0   100%
    papyrus.tests.test_protocol          606      0   100%
    papyrus.tests.test_renderers          49      0   100%
    papyrus.tests.views                    7      0   100%
    ----------------------------------------------------------------
    TOTAL                               1137      0   100%
    ----------------------------------------------------------------------
    Ran 54 tests in 0.998s

    OK

Create Git tag and push it::

    $ git tag -a x.y -m 'version x.y'
    $ git push origin x.y

Go to https://readthedocs.org/dashboard/papyrus/advanced/ and set "Default
version" to x.y. Now go to https://readthedocs.org/dashboard/papyrus/versions/
and change that version to "Active".

Upload the packages to PyPI::

    $ python setup.py sdist bdist_wheel upload
