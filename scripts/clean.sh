#!/bin/sh -e
PACKAGE="ormar"
if [ -d 'dist' ] ; then
    rm -r dist
fi
if [ -d 'site' ] ; then
    rm -r site
fi
if [ -d 'htmlcov' ] ; then
    rm -r htmlcov
fi
if [ -d "${PACKAGE}.egg-info" ] ; then
    rm -r "${PACKAGE}.egg-info"
fi
find ${PACKAGE} -type f -name "*.py[co]" -delete
find ${PACKAGE} -type d -name __pycache__ -delete

find tests -type f -name "*.py[co]" -delete
find tests -type d -name __pycache__ -delete