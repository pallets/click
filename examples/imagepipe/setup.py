from setuptools import setup

setup(
    name='click-example-imagepipe',
    version='1.0',
    py_modules=['imagepipe'],
    include_package_data=True,
    install_requires=[
        'Click',
        'pillow',
    ],
    entry_points='''
        [console_scripts]
        imagepipe=imagepipe:cli
    ''',
)
