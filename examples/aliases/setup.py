from setuptools import setup

setup(
    name='click-example-aliases',
    version='1.0',
    py_modules=['aliases'],
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        aliases=aliases:cli
    ''',
)
