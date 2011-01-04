from setuptools import setup, find_packages
import sys, os

version = '0.1'


install_requires = [
    'pyramid',
    'geojson>=1.0,<=1.0.99'
    ]

tests_require = install_requires + ['WebTest']

setup(name='papyrus',
      version=version,
      description="Geospatial Extensions for Pyramid",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='FOSS4G, Pylons, Pyramid',
      author='\xc3\x89ric Lemoine',
      author_email='eric.lemoine@gmail.com',
      url='https://github.com/elemoine/papyrus',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      test_suite="papyrus.tests",
      entry_points="""
      # -*- Entry points: -*-
      """,
      long_description="""\
      """,
      )
