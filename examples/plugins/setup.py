#!/usr/bin/env python


"""
Setup script for `printer`
"""


from setuptools import setup


setup(
    name='printer',
    version='0.1dev0',
    packages=['printer'],
    entry_points='''
        [console_scripts]
        printer=printer.cli:cli
    '''
)
