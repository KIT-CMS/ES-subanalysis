#!/bin/bash

# prep_resubmit_silent arguments.txt
set -e

# # for i in $(seq $(cat arguments.txt | wc -l)) ; do ls out/$i.* &> /dev/null || echo "$i out" ; done

# prep_resubmit_silent() {
    # TODO: add filelock on creation to prevent from prepresub those jobs that aren't checked as not running
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
    echo arguments: $arguments
    dirpath=$(dirname "$arguments")
    sed -ri 's/^\+MaxRuntime = 7200/+MaxRuntime = 10780/g' ${dirpath}/job.jdl
    f="$(basename -- $arguments)"
    f="${f%.*}"
    # arguments_finished=${dirpath}/${f}_finished.txt
    name=arguments
    ext=txt
    if [[ -e ${dirpath}/${name}.${ext} || -L ${dirpath}/${name}.${ext} ]] ; then
        i=0
        # while [[ -e ${dirpath}/${i}  || -e ${dirpath}/${name}-${i}.${ext} || -L ${dirpath}/${name}-${i}.${ext} ]] ; do
        while [[ -e ${dirpath}/${i}  ]] ; do
            # printf "exist..++ $i\\n"
            let i=i+1
        done
        # name=${name}-${i}
    fi
    echo "final i: $i"
    if [[ -e ${dirpath}/${i} || -L ${dirpath}/${i} ]] ; then
        echo "${dirpath}/${i} already exist! Something is wrong - check manually"
        return
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

    flag=0

    echo "Prepare missing jobs"
    w=$(cat ${arguments_finished} | wc -l)
    n_logs=$(ls ${dirpath}/${i}/out/* | wc -l)
    n_periodic_removed=$(($w - ${n_logs}))
    echo "expecting $w logs (found ${n_logs}) --> ${n_periodic_removed} jobs removed by condor"
    if [ $w -gt 1 ] ; then
        let w=w-1
    else
        w=0
    fi
    for htcoondor_job_i in $(seq 0 $w) ; do
        [ $(ls -l ${dirpath}/${i}/out/${htcoondor_job_i}.* 2> /dev/null | wc -l ) -gt 1 ]  && (echo "Multiple iterations:" ; ls -l ${dirpath}/${i}/out/${htcoondor_job_i}.* )
        # if [[ ! ls ${dirpath}/${i}/out/${htcoondor_job_i}.* &> /dev/null ]] ; then
        if ! ls ${dirpath}/${i}/out/${htcoondor_job_i}.* 1> /dev/null 2>&1; then
            let flag=flag+1
            echo "${htcoondor_job_i} [condorid] out -> check periodic removed jobs first"
            ((j=htcoondor_job_i + 1))
            # this gets line Number -> jobs numbers are given by line number
            sed -n ${j}p ${arguments_finished}  >> ${arguments}
        fi
        # this gets the line Matching
        # sed -n -e "/^${i} /p" ${arguments_finished}  >> ${arguments}
    done
    echo "after missed check : $flag"
    sed -i '/^$/d' ${arguments}  # remove empty lines
    sort -u -o ${arguments} ${arguments}  # sort and remove duplicates if met

    if [ $(ls ${dirpath}/${i}/out | wc -l) -gt 0 ] ; then
        echo "Prepare errored job"
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
                echo "Error: ${jobid} [${condorid}]"
                err_c2=$(sed -n -e "/^@ : /p" ${fullfile})
                err_c2=${err_c2#"$prefix"}
                echo "${err_c2}" >> ${arguments}
                let flag=flag+1
                # echo "${err_command}" #>> ${arguments}
                # mv $fullfile $fail_dir/$fullfile
            # else
            #     printf "\\t in file $fullfile : done\\n"
                # mv $fullfile $success_dir/$fullfile
            fi
        done
        echo "after failed check : $flag"
    fi
    sed -i '/^$/d' ${arguments}  # remove empty lines
    sort -u -o ${arguments} ${arguments}  # sort and remove duplicates if met

    echo "arguments after the errored jobs added N:" $(cat ${arguments} | wc -l)

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
    # echo "after the lost jobs added:" $(cat ${arguments} | wc -l)
    echo $arguments

    if [[ ! ${flag} -eq 0 ]] ; then
        printf "\t\t${Red} done -> with errors ${NC}\n"
    else
        printf "\t\t${Green} done -> no errors ${NC}\n"
    fi

    # if [[ $# -eq 2 ]] ; then
    #     (cd $dirpath && condor_submit job.jdl && cd -)
    # fi
# }
