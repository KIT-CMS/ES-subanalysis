#!/bin/bash

prep_resubmit_silent() {
    if [[ $# -eq 0 ]] ; then
        arguments=$(pwd)/arguments.txt
    elif [[ $# -eq 1 ]] ; then
        if [ -f "$1" ]; then
            # echo "$1 exist"
            arguments=$1
        elif [ -f "$1/arguments.txt" ]; then
            arguments=$1/arguments.txt
        else
            echo "$1[/arguments.txt] is not a valid file"
            return
        fi
    fi
    # echo arguments: $arguments
    dirpath=$(dirname "$arguments")
    f="$(basename -- $arguments)"
    f="${f%.*}"
    # arguments_finished=${dirpath}/${f}_finished.txt
    name=arguments
    ext=txt
    if [[ -e ${name}.${ext} || -L ${name}.${ext} ]] ; then
        i=0
        while [[ -e ${name}-${i}.${ext} || -L ${name}-${i}.${ext} ]] ; do
            let i++
        done
        name=${name}-${i}
    fi
    # echo "${name}".${ext}
    # touch -- "${name}".${ext}
    mkdir ${dirpath}/${i}
    arguments_finished=${dirpath}/${i}/"${name}".${ext}
    mv ${arguments} ${arguments_finished}
    # cp ${arguments_finished} ${dirpath}/${i}/
    mv ${dirpath}/log ${dirpath}/${i}/log
    mv ${dirpath}/err ${dirpath}/${i}/err
    mv ${dirpath}/out ${dirpath}/${i}/out
    mkdir ${dirpath}/log ${dirpath}/err ${dirpath}/out


    # arguments_resubmit=${dirpath}/${f}_resubmit.txt
    # echo arguments: $arguments
    # echo arguments: $arguments
    ERRORED_MYID=()
    ERRORED_CONDORID=()
    touch ${arguments}
    # success_dir=${dirpath}/out/success
    # fail_dir=${dirpath}/out/prepared_to_resubmit
    # if [[ ! -d "${fail_dir}" ]]
    # then
    #     mkdir -p ${fail_dir}
    # fi
    # if [[ ! -d "${success_dir}" ]]
    # then
    #     mkdir -p ${success_dir}
    # fi
    for fullfile in ${dirpath}/${i}/out/*
    do
        filename="${fullfile##*/}"
        extension="${filename##*.}"
        condorid="${filename#*.}"
        condorid="${condorid%.*}"
        jobid="${filename%%.*}"
        if [[ ! $(tail -n 1 $fullfile) == "done"* ]]
        then
            ERRORED_MYID+=($jobid)
            ERRORED_CONDORID+=($condorid)
            # mv $fullfile $fail_dir/$fullfile
        # else
        #     mv $fullfile $success_dir/$fullfile
        fi
    done
    while IFS= read -r line
    do
        for jobid in "${ERRORED_MYID[@]}"
        do
            if [[ ${line} == ${jobid}* ]] ; then
                echo "$line" >> ${arguments}
            fi
        done
    done < ${arguments_finished}

    echo $arguments
}
# prep_resubmit_silent /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/job_dirs/control_plots_ff_2017

prep_resubmit() {
    arguments=$(prep_resubmit_silent $@)
    echo "Number to resubmit:"
    cat ${arguments} | wc -l
    echo "$arguments"
}
# prep_resubmit /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/job_dirs/control_plots_ff_2017

check_logs() {
    if [[ $# -eq 0 ]] ; then
        dirpath=$(pwd)
    elif [[ $# -eq 1 ]] ; then
        if [ -d "$1" ]; then
            # echo "$1 exist"
            dirpath=$1
        else
            echo "$1 is not a valid dirpath"
            return
        fi
    else
        echo "uncknown extra parameters"
        return
    fi

    flag=0
    for fullfile in ${dirpath}/out/*
    do
        filename="${fullfile##*/}"
        extension="${filename##*.}"
        condorid="${filename#*.}"
        condorid="${condorid%.*}"
        jobid="${filename%%.*}"
        if [[ ! $(tail -n 1 $fullfile) == "done"* ]]
        then
            flag=1
            echo "Error: ${jobid} [${condorid}]"
            # mv $fullfile $fail_dir/$fullfile
        # else
        #     mv $fullfile $success_dir/$fullfile
        fi
    done

    if [[ ${flag} -eq 1 ]] ; then
        echo "done -> with errors"
    else
        echo "done -> no errors"
    fi
}

submit_prep_resubmit() {
    arguments=$(prep_resubmit_silent $@)
    echo "Number to resubmit:"
    cat ${arguments} | wc -l
    echo "$arguments"
    dirpath=$(dirname "$arguments")
    # cd $dirpath && condor_submit job.jdl
    # cd -
}
# submit_prep_resubmit
