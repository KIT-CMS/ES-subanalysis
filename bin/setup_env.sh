#!/bin/bash
set +e

EXECFROM_DIR="$( dirname "${BASH_SOURCE[0]}" )"

source $EXECFROM_DIR/setup_cvmfs_sft.sh

source $EXECFROM_DIR/setup_python.sh
