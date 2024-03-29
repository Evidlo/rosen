#!/usr/bin/env python3

from setuptools import find_packages, setup

with open("README.md") as f:
    README = f.read()

version = {}
# manually read version from file
with open("rosen/version.py") as file:
    exec(file.read(), version)

setup(
    # some basic project information
    name="rosen",
    version=version["__version__"],
    license="GPL3",
    description="Rosen ground software for SEAQUE mission",
    long_description=README,
    long_description_content_type='text/markdown',
    author="Evan Widloski",
    author_email="evan_github@widloski.com",
    url="https://github.com/evidlo/rosen",
    # your project's pip dependencies
    install_requires=[
        "asyncio-dgram",
        "construct",
        "rich",
        "python-dateutil",
        "construct",
        "msgpack",
        "ptpython"
    ],
    include_package_data=True,
    # automatically look for subfolders with __init__.py
    packages=find_packages(),
    # if you want your code to be able to run directly from command line
    entry_points={
        'console_scripts': [
            'rosen = rosen.main:main',
        ]
    },
)
