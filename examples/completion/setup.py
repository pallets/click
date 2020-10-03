from setuptools import setup

setup(
    name="click-example-completion",
    version="1.0",
    py_modules=["completion"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        completion=completion:cli
    """,
)
