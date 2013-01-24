from setuptools import setup, find_packages
import sys, os

version = '1.3'
long_description = """The raisin.restyler package is a part of Raisin, the web application
used for publishing the summary statistics of Grape, a pipeline used for processing and
analyzing RNA-Seq data."""

setup(name='raisin.restyler',
      version=version,
      description="A package used in the Raisin web application",
      long_description=long_description,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Natural Language :: English',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Operating System :: POSIX :: Linux'],
      keywords='RNA-Seq pipeline ngs transcriptome bioinformatics ETL',
      author='Maik Roder',
      author_email='maikroeder@gmail.com',
      url='http://big.crg.cat/services/grape',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      namespace_packages = ['raisin'],
      package_data = {'raisin.restyler':['templates/*.pt']},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'configobj',
          'zope.pagetemplate'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
