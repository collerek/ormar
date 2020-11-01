#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup

PACKAGE = "ormar"
URL = "https://github.com/collerek/ormar"


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    with open(os.path.join(package, "__init__.py")) as f:
        return re.search("__version__ = ['\"]([^'\"]+)['\"]", f.read()).group(1)


def get_long_description():
    """
    Return the README.
    """
    with open("README.md", encoding="utf8") as f:
        return f.read()


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    url=URL,
    license="MIT",
    description="An simple async ORM with fastapi in mind and pydantic validation.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords=['orm', 'sqlalchemy', 'fastapi', 'pydantic', 'databases', 'async', 'alembic'],
    author="Radosław Drążkiewicz",
    author_email="collerek@gmail.com",
    packages=get_packages(PACKAGE),
    package_data={PACKAGE: ["py.typed"]},
    data_files=[("", ["LICENSE.md"])],
    install_requires=["databases", "pydantic>=1.5", "sqlalchemy", "typing_extensions"],
    extras_require={
        "postgresql": ["asyncpg", "psycopg2"],
        "mysql": ["aiomysql", "pymysql"],
        "sqlite": ["aiosqlite"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
