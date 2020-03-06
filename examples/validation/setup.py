from setuptools import setup

setup(
    name="click-example-validation",
    version="1.0",
    py_modules=["validation"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        validation=validation:cli
    """,
)
