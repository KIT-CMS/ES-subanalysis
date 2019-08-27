#!/bin/bash
set +e

LCG_RELEASE=94
function version_gteq() { test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1" -o "$2" == "$1" ; }

# if version_gteq $OSVER '7' ; then echo 1; else echo 0; fi
if uname -a | grep ekpdeepthought
then
    if version_gteq $OSVER '7' ; then
        source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-centos7-gcc62-dbg/setup.sh
    elif version_gteq $OSVER '6' ; then
        source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-ubuntu1604-gcc54-dbg/setup.sh
    fi
else
    if version_gteq $OSVER '7' ; then
        source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-centos7-gcc62-dbg/setup.sh
    elif version_gteq $OSVER '6' ; then
        source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-slc6-gcc62-opt/setup.sh
    fi
fi

[[ ":$PYTHONPATH:" != *"$HOME/.local/lib/python2.7/site-packages:"* ]] && PYTHONPATH="$HOME/.local/lib/python2.7/site-packages:${PYTHONPATH}"

export PYTHONPATH
