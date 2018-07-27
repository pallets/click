#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import re
from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')


with io.open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()

with io.open('click/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name='click',
    version=version,
    url='https://www.palletsprojects.com/p/click/',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    maintainer='Pallets team',
    maintainer_email='contact@palletsprojects.com',
    long_description=readme,
    packages=['click'],
    description='A simple wrapper around optparse for '
                'powerful command line utilities.',
    license='BSD',
    extras_require={
        'dev': [
            'pytest>=3',
            'coverage',
            'tox',
            'sphinx',
        ],
        'docs': [
            'sphinx',
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
)
