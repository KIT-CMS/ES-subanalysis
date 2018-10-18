#!/bin/bash
set +e

LCG_RELEASE=94

if uname -a | grep ekpdeepthought
then
    source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-ubuntu1604-gcc54-dbg/setup.sh
else
    source /cvmfs/sft.cern.ch/lcg/views/LCG_${LCG_RELEASE}/x86_64-slc6-gcc62-opt/setup.sh
fi

[[ ":$PYTHONPATH:" != *"$HOME/.local/lib/python2.7/site-packages:"* ]] && PYTHONPATH="$HOME/.local/lib/python2.7/site-packages:${PYTHONPATH}"

export PYTHONPATH
