from setuptools import setup

setup(
    name='inout',
    version='0.1',
    py_modules=['inout'],
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        inout=inout:cli
    ''',
)
