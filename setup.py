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
    description="A simple async ORM with fastapi in mind and pydantic validation.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords=['orm', 'sqlalchemy', 'fastapi', 'pydantic', 'databases', 'async',
              'alembic'],
    author="Radosław Drążkiewicz",
    author_email="collerek@gmail.com",
    packages=get_packages(PACKAGE),
    package_data={PACKAGE: ["py.typed"]},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.6",
    data_files=[("", ["LICENSE.md"])],
    install_requires=["databases>=0.3.2,<=0.4.1", "pydantic>=1.6.1,<=1.8",
                      "sqlalchemy>=1.3.18,<=1.3.23",
                      "typing_extensions>=3.7,<=3.7.4.3"],
    extras_require={
        "postgresql": ["asyncpg", "psycopg2"],
        "mysql": ["aiomysql", "pymysql"],
        "sqlite": ["aiosqlite"],
        "orjson": ["orjson"],
        "crypto": ["cryptography"]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP",
        "Framework :: AsyncIO",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
