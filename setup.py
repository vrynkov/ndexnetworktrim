#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import os
import re
from setuptools import setup, find_packages


with open(os.path.join('ndexnetworktrim', '__init__.py')) as ver_file:
    for line in ver_file:
        if line.startswith('__version__'):
            version=re.sub("'", "", line[line.index("'"):])

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['ndex2',
                'ndexutil']

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Vladimir Rynkov",
    author_email='vrynkov@ucsd.edu',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python NDEx Content Loader package.",
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='ndexnetworktrim',
    name='ndexnetworktrim',
    packages=find_packages(include=['ndexnetworktrim']),
    package_dir={'ndexnetworktrim': 'ndexnetworktrim'},
    package_data={'ndexnetworktrim': ['loadplan.json',
                                       'style.cx']},
    scripts=[ 'ndexnetworktrim/ndexnetworktrimmer.py'],
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/vrynkov/ndexnetworktrim',
    version=version,
    zip_safe=False,
)
