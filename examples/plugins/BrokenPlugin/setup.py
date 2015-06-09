#!/usr/bin/env python


"""
Setup script for `printer_bold`
"""


from setuptools import setup


setup(
    name='printer_bold',
    version='0.1dev0',
    packages=['printer_bold'],
    entry_points='''
        [printer.plugins]
        bold=printer_bold.core:bolddddddddddd
    '''
)
