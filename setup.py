from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='papyrus',
      version=version,
      description="Geospatial Extensions for Pyramid",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='FOSS4G, Pylons, Pyramid',
      author='\xc3\x89ric Lemoine',
      author_email='eric.lemoine@gmail.com',
      url='',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
