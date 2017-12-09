import re
import ast
from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')


with open('click/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


setup(
    name='click',
    author='Armin Ronacher',
    author_email='armin.ronacher@active-4.com',
    version=version,
    url='http://github.com/mitsuhiko/click',
    packages=['click'],
    tests_require=['pytest>=2.8'],
    description='A simple wrapper around optparse for '
                'powerful command line utilities.',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
