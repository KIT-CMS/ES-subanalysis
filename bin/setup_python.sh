#!/bin/bash
set +e

declare -a modules=(
    $PWD/datacard-producer
    $PWD/shape-producer
    $PWD/shape-producer/shape_producer/
    $PWD
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
