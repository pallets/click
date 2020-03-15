from setuptools import setup

setup(
    name="click-example-colors",
    version="1.0",
    py_modules=["colors"],
    include_package_data=True,
    install_requires=[
        "click",
        # Colorama is only required for Windows.
        "colorama",
    ],
    entry_points="""
        [console_scripts]
        colors=colors:cli
    """,
)
