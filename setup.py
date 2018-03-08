#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import io
import os
from setuptools import setup, find_packages


def get_pkg_info(info_file, info):
    val = ""
    info_file.seek(0)
    for line in info_file:
        if line.startswith('__{}__'.format(info)):
            val = line.split("=")[1].replace("'", "").replace('"', "").strip()
    return val

with open(os.path.join('weather_report', '__init__.py')) as init_file:
    author = get_pkg_info(init_file, 'author')
    email = get_pkg_info(init_file, 'email')
    version = get_pkg_info(init_file, 'version')


requirements = ['html5lib', 'lxml', 'pandas',
                'numpy', 'beautifulsoup4']

setup_requirements = []

test_requirements = ['pytest']

package_data = {}

setup(
    name='weather_report',
    author=author,
    author_email=email,
    version=version,
    description="Top-level package for creating NOAA weather reports",
    long_description='',

    url='',
    packages=find_packages(),
    package_data=package_data,
    entry_points={
        'console_scripts': [
            'weather_report=weather_report.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='weather_report',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    setup_requires=setup_requirements,
)
