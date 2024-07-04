#!/bin/bash
set -e

# Make sure .bashrc is sourced
. /root/.bashrc

# Allow the workdir to be set using an env var.
# Useful for CI pipelines which use docker for their build steps
# and don't allow that much flexibility to mount volumes
WORKDIR=${SRCDIR:-/src}

cd $WORKDIR

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

if [[ "$@" == "" ]]; then
    pyinstaller -y --dist ./dist/windows *.spec
    chown -R --reference=. ./dist/windows
else
    sh -c "$@"
fi
