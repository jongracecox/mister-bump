#!/usr/bin/env python3
from setuptools import setup
import mister_bump
from m2r import parse_from_file
import restructuredtext_lint
import fileinput
import re


# Update version number in file
def set_module_version(filename, version):
    with fileinput.FileInput(filename, inplace=True, backup='.bak') as file:
        for line in file:
            print(re.sub(r"__version__ = '.*'", "__version__ = '%s'" % version, line), end='')


# Parser README.md into reStructuredText format
rst_readme = parse_from_file('README.md')

# Validate the README, checking for errors
errors = restructuredtext_lint.lint(rst_readme)

# Raise an exception for any errors found
if errors:
    print(rst_readme)
    raise ValueError('README.md contains errors: ',
                     ', '.join([e.message for e in errors]))

# Get version number
package_version = mister_bump.bump(style='rc')

# Update __version__ variable inside module
set_module_version('mister_bump.py', package_version)

setup(
    name='mister-bump',
    description='Increment (bump) git version numbers for a project.',
    long_description=rst_readme,
    version=package_version,
    author='Jon Grace-Cox',
    author_email='jongracecox@gmail.com',
    py_modules=['mister_bump'],
    setup_requires=['setuptools', 'm2r'],
    tests_require=[],
    install_requires=[],
    data_files=[],
    options={
        'bdist_wheel': {'universal': True}
    },
    url='https://github.com/jongracecox/mister-bump',
    entry_points={
        'console_scripts': ['get-git-version=mister_bump:main',
                            'mister-bump=mister_bump:main'],
    }
)

# Reset __version__ variable inside module
set_module_version('mister_bump.py', '')
