#!/usr/bin/env python3

import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mal_automaton",
    version="0.1.0",
    author="Logan Swartzendruber",
    author_email="logan.swartzendruber@gmail.com",
    description="Automatic updating of your MAL via Plex webhooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/loganswartz/mal_automaton",
    packages=setuptools.find_packages(),
    install_requires=[
        'pyyaml',
        'requests',
        'jikanpy',
        'mementos',
        'dateutil',
        'tvdbsimple',
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Framework :: Pytest",
        "Topic :: Games/Entertainment",
        "Topic :: Home Automation",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],
    python_requires='>=3.6',
)
