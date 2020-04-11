from setuptools import setup

setup(
    name="click-example-aliases",
    version="1.0",
    py_modules=["aliases"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        aliases=aliases:cli
    """,
)
