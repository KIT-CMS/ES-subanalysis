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
    if [[ -e ${dirpath}/${name}.${ext} || -L ${dirpath}/${name}.${ext} ]] ; then
        i=0
        while [[ -e ${dirpath}/${i}  || -e ${dirpath}/${name}-${i}.${ext} || -L ${dirpath}/${name}-${i}.${ext} ]] ; do
            printf "exist..++\\n"
            let i++
        done
        name=${name}-${i}
    fi
    if [[ -e ${dirpath}/${i} || -L ${dirpath}/${i} ]] ; then
        echo "${dirpath}/${i} already exist! Something is wrong - check manually"
        return 1
    else
        mkdir ${dirpath}/${i}
    fi
    # touch -- "${name}".${ext}
    arguments_finished=${dirpath}/${i}/"${name}".${ext}
    mv ${arguments} ${arguments_finished}
    # cp ${arguments_finished} ${dirpath}/${i}/
    mv ${dirpath}/log ${dirpath}/${i}/log
    mv ${dirpath}/err ${dirpath}/${i}/err
    mv ${dirpath}/out ${dirpath}/${i}/out
    mkdir ${dirpath}/log ${dirpath}/err ${dirpath}/out

    # return
    # arguments_resubmit=${dirpath}/${f}_resubmit.txt
    # echo arguments: $arguments
    # echo arguments: $arguments
    ERRORED_MYID=()
    ERRORED_CONDORID=()
    ERRORRED_COMMANDS=()
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
    # printf "Preparint the list\\n"
    for fullfile in ${dirpath}/${i}/out/*.out
    do
        # echo "-->fullfile: $fullfile"
        filename="${fullfile##*/}"
        extension="${filename##*.}"
        condorid="${filename#*.}"
        condorid="${condorid%.*}"
        jobid="${filename%%.*}"
        # echo "-->filename: $filename"
        # echo "-->filename: $filename"
        # echo "-->jobid:$jobid"
        if [[ ! $(tail -n 1 $fullfile) == "done"* ]]
        then
            # printf "\\t in file $fullfile : errored\\n"
            ERRORED_MYID+=($jobid)
            ERRORED_CONDORID+=($condorid)
            first_line=$(head -n 1 ${fullfile})
            prefix="@ :  "
            err_command=${first_line#"$prefix"}
            ERRORRED_COMMANDS+=(${err_command})
            echo "${err_command}" >> ${arguments}
            # mv $fullfile $fail_dir/$fullfile
        # else
        #     printf "\\t in file $fullfile : done\\n"
            # mv $fullfile $success_dir/$fullfile
        fi
    done
    sed -i '/^$/d' ${arguments}  # remove empty lines
    sort -u -o ${arguments} ${arguments}  # sort and remove duplicates if met

    # echo "${ERRORED_MYID[@]}"
    # echo "${ERRORRED_COMMANDS[@]}"
    # return
    # while IFS= read -r line
    # do
    #     printf "line: ${line}\\n"
    #     for jobid in "${ERRORED_MYID[@]}"
    #     do
    #         if [[ ${line} == "${jobid} "* ]] ; then
    #             printf "\\t taking jobid: $jobid\\n"
    #             # echo "$line" #>> ${arguments}
    #         else
    #             printf "\\t skipping jobid: $jobid\\n"
    #         fi
    #     done
    # done < ${arguments_finished}
    # set +x
    echo $arguments
}
# prep_resubmit_silent /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/job_dirs/control_plots_ff_full_syst_signal_2017

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
    cd $dirpath && condor_submit job.jdl && cd -
}
# submit_prep_resubmit
