import io
import re
from setuptools import setup

with io.open("README.rst", "rt", encoding="utf8") as f:
    readme = f.read()

with io.open("click/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r"__version__ = \'(.*?)\'", f.read()).group(1)

setup(
    name="click",
    version=version,
    url="https://palletsprojects.com/p/click/",
    project_urls={
        "Documentation": "https://click.palletsprojects.com/",
        "Code": "https://github.com/pallets/click",
        "Issue tracker": "https://github.com/pallets/click/issues",
    },
    license="BSD",
    author="Armin Ronacher",
    author_email="armin.ronacher@active-4.com",
    maintainer="Pallets Team",
    maintainer_email="contact@palletsprojects.com",
    description="Composable command line interface toolkit",
    long_description=readme,
    packages=["click"],
    include_package_data=True,
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
