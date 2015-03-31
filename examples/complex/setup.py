from setuptools import setup

setup(
    name='click-example-complex',
    version='1.0',
    packages=['complex', 'complex.commands'],
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        complex=complex.cli:cli
    ''',
)
