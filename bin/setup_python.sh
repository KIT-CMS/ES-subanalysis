#!/bin/bash
declare -a modules=(
    $PWD
    $PWD/shape-producer
    $PWD/datacard-producer
)

for i in "${modules[@]}"
do
    if [ -d "$i" ]
    then
        [[ ":$PYTHONPATH:" != *"$i:"* ]] && PYTHONPATH="$i:${PYTHONPATH}"
    else
        echo "Couldn't find package: " $i
    fi
done

export PYTHONPATH
