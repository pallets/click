from setuptools import setup

setup(
    name="click",
    install_requires=[
        "colorama; platform_system == 'Windows'",
        "importlib-metadata; python_version < '3.8'",
    ],
)
