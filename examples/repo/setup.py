from setuptools import setup

setup(
    name='click-example-repo',
    version='0.1',
    py_modules=['repo'],
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        repo=repo:cli
    ''',
)
