from setuptools import setup

setup(
    name='plick',
    version='0.1',
    py_modules=['plick'],
    include_package_data=True,
    install_requires=[
        'Click',
		'requests',
		'pyperclip',
    ],
    entry_points='''
	[console_scripts]
    plick=plick:plick
    ''',
)
