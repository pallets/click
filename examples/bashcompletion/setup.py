from setuptools import setup

setup(
    name="click-example-bashcompletion",
    version="1.0",
    py_modules=["bashcompletion"],
    include_package_data=True,
    install_requires=["click"],
    entry_points="""
        [console_scripts]
        bashcompletion=bashcompletion:cli
    """,
)
