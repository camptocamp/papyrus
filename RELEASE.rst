Release
-------

This file provides the steps for releasing a new version of Papyrus.

Check that version number is correct in ``setup.py``. If not set it to the
correct value, then commit and push that.

Verify that the tests pass, with 100% coverage::

    $ python setup.py nosetests --with-coverage
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

Upload the package to PyPI::

    $ python setup.py sdist upload
