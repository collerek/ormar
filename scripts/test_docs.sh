#!/bin/sh -e

PACKAGE="docs_src"

PREFIX=""
if [ -d 'venv' ] ; then
    PREFIX="venv/bin/"
fi

set -x

PYTHONPATH=. ${PREFIX}pytest --ignore venv docs_src/ "${@}"
