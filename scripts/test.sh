#!/bin/sh -e

PACKAGE="async-orm"

PREFIX=""
if [ -d 'venv' ] ; then
    PREFIX="venv/bin/"
fi

set -x

PYTHONPATH=. ${PREFIX}pytest --ignore venv --cov=${PACKAGE} --cov=tests --cov-fail-under=100 --cov-report=term-missing "${@}"
