#!/bin/bash
set -e

# check_logs() {
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

    w=$(cat ${dirpath}/arguments.txt | wc -l)
    echo "expecting $w logs (found $(ls ${dirpath}/out | wc -l))"
    # echo $w
    if [ $w -gt 1 ] ; then
        let w=w-1
    else
        w=0
    fi
    # echo $w
    # for i in $(seq $w ) ; do ls ${dirpath}/out/$i.* &> /dev/null || (flag=1 ; echo "$i out") ; done
    for htcoondor_job_i in $(seq 0 $w) ; do
        # ls ${dirpath}/out/${htcoondor_job_i}.* &> /dev/null || (let flag=flag+1 ; echo "${htcoondor_job_i} [condorid] out -> check periodic removed jobs first")
        [ $(ls -l ${dirpath}/out/${htcoondor_job_i}.* 2> /dev/null | wc -l ) -gt 1 ]  && (echo "Multiple iterations:" ; ls -l ${dirpath}/out/${htcoondor_job_i}.* )

        if ! ls ${dirpath}/out/${htcoondor_job_i}.* 1> /dev/null 2>&1; then
            # echo "missed: ls ${dirpath}/out/${htcoondor_job_i}.*" ; exit 1
            let flag=flag+1
            echo "${htcoondor_job_i} [condorid] out -> check periodic removed jobs first"

        # else
        #     echo "fouond ls ${dirpath}/out/${htcoondor_job_i}.*"
        fi

        # ((j=htcoondor_job_i + 1))
        # sed -n ${j}p ${dirpath}/arguments.txt
    done
    echo "after missed check : $flag"

    if [ $(ls ${dirpath}/${i}/out | wc -l) -gt 0 ] ; then
        for fullfile in ${dirpath}/out/*
        do
            filename="${fullfile##*/}"
            extension="${filename##*.}"
            condorid="${filename#*.}"
            condorid="${condorid%.*}"
            # condorid="${filename%.*}"
            jobid="${filename%%.*}"
            if [[ ! $(tail -n 1 $fullfile) == "done"* ]]
            then
                let flag=flag+1
                echo "Error: ${jobid} [${condorid}]"
            # else
            #     echo "OK: ${jobid} [${condorid}]"
            #     mv $fullfile $success_dir/$fullfile
            fi
        done
    fi
    echo "after failed check : $flag"


    if [[ ! ${flag} -eq 0 ]] ; then
        printf "\t\t${Red} done -> with errors ${NC}\n"
    else
        printf "\t\t${Green} done -> no errors ${NC}\n"
    fi
# }
