#!/bin/bash
shopt -s expand_aliases

# setshapes # must be defined in your system!
workind_dir=$(dirname "$0")/..
cd ${workind_dir}
source bin/setup_env.sh

echo "@ : " $@
echo "current dir : " $(pwd)
eval "${@:2}"
