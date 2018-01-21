#!/usr/bin/python
from setuptools import setup
import mister_bump
from m2r import parse_from_file


setup(
    name='mister-bump',
    description='Increment (bump) git version numbers for a project.',
    long_description=parse_from_file('README.md'),
    version=mister_bump.bump(style='rc'),
    author='Jon Grace-Cox',
    author_email='jongracecox@gmail.com',
    py_modules = ['mister_bump'],
    setup_requires=['setuptools', 'm2r'],
    tests_require=[],
    install_requires=[],
    data_files=[],
    options={
        'bdist_wheel': {'universal': True}
    },
    url='https://github.com/jongracecox/mister-bump',
    entry_points = {
        'console_scripts': ['get-git-version=mister_bump:main',
                            'mister-bump=mister_bump:main'],
    }
)
