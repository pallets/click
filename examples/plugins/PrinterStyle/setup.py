#!/usr/bin/env python


"""
Setup script for `printer_style`
"""


from setuptools import setup


setup(
    name='printer_style',
    version='0.1dev0',
    packages=['printer_style'],
    entry_points='''
        [printer.plugins]
        background=printer_style.core:background
        color=printer_style.core:color
    '''
)
