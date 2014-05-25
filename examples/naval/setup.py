from setuptools import setup

setup(
    name='click-example-naval',
    version='2.0',
    py_modules=['naval'],
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        naval=naval:cli
    ''',
)
