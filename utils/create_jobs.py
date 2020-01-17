#!/usr/bin/env python

# Example:
'''
test:
    N jobs:
        python utils/create_jobs.py \
            --shifts nominal  Zpt prefiring Tpt TrgEff TES EES ZTTpTT METES \
            --channels et mt em tt \
            --mask-btag-region 'nbtag_zero' nbtag_nonzero \
            --mask-pZetaMissVis-region 'dzeta_low' dzeta_medium dzeta_high \
            --mask-mt_1-region mt_1_tight mt_1_loose \
            --year 2017 \
            --output-file-dir /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/test0/shapes \
            --jobdir-name test0 --force

    1 job:
        python utils/create_jobs.py \
            --shifts EES \
            --channels em \
            --mask-btag-region 'nbtag_zero' \
            --mask-pZetaMissVis-region 'dzeta_low' \
            --year 2017 \
            --output-file-dir /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/test0/shapes \
            --jobdir-name test0

    2 jobs:
        python utils/create_jobs.py \
            --shifts EES \
            --channels et mt tt em \
            --mask-btag-region 'nbtag_zero' \
            --mask-pZetaMissVis-region 'dzeta_low' \
            --year 2017 \
            --output-file-dir /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/test0/shapes \
            --jobdir-name test0 --force

    note: to switch to htcondor:
    pip install --user htcondor
    python -c 'import htcondor; print(htcondor.__file__)'
    naf system: /usr/lib64/python2.6/site-packages/htcondor.so
'''
import os
import shutil
import sys
import argparse
import subprocess
import itertools
import fileinput

from six import string_types

jdl_local = """\
universe = vanilla
executable = ./batch_run.sh
output = out/$(ProcId).$(ClusterID).out
error = err/$(ProcId).$(ClusterID).err
log = log/$(ProcId).$(ClusterID).log
requirements = (OpSys == "LINUX")
getenv = true
max_retries = 3
RequestCpus = 1
+MaxRuntime = 10800
queue arguments from arguments.txt\
"""
# transfer_output_files = ""
# requirements = (OpSysAndVer =?= "SLCern6")
# notification  = Complete


def mkdir(path):
    print(path)
    if not os.path.exists(path):
        os.makedirs(path)  # thanks to the exist_ok flag this will not even complain if the directory exists


def parse_arguments():
    defaultArguments = {}
    parser = argparse.ArgumentParser(description='create_job.py parser')

    # structure: <jobdirs>/<jobdir_name>/job
    parser.add_argument("--jobdirs", type=str, default='/nfs/dust/cms/user/glusheno/shapes/MSSM/mva/job_dirs', help="The root where all tasks/jobdirs are")  # TODO config
    parser.add_argument("--jobdir-name", type=str, required=True, help="Name for task/jobdir")
    parser.add_argument("--force", default=False, action='store_true', help="")
    parser.add_argument("--submit", default=False, action='store_true', help="")

    # mssm
    parser.add_argument("--shifts", default=['default'], nargs='+', type=str, help="Pipelines, uncertainties variations, shifts : processed is the intersection of this list with list from _known_estimation_methods")
    parser.add_argument("--processes", default=['default'], nargs='+', type=str, help="Processes from the standart map of processes")  # TODO: enable passing via syntax <name>:<class name>
    parser.add_argument("--channels", default=['default'], nargs='+', type=str, help="Channels to be considered.")

    parser.add_argument("--mask-pZetaMissVis-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: dzeta_low, dzeta_medium, dzeta_high")
    parser.add_argument("--mask-mt_1-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: mt_1_tight, mt_1_loose")
    parser.add_argument("--mask-btag-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: nbtag_zero, nbtag_nonzero")
    # parser.add_argument("--mask-eta-1-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: eta_1_barel, eta_1_endcap, eta_1_endcap_real")
    # parser.add_argument("--mask-decay-mode", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: all, dm0, dm1, dm10")
    # parser.add_argument("--mask-jets-multiplicity", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: njetN, njet0")

    parser.add_argument("--year", "--era", default='default', type=str, help="Experiment era.")
    parser.add_argument("--output-file-dir", type=str, help="Output file directory")
    parser.add_argument("--output-file-name", default='', type=str, help="Output file name for file with final shapes that enter datacards. If none is given context_analysis is used as a root for this name")

    args = parser.parse_args()

    return args


def main(args):
    # Creating arguments for all jobs
    arguments = []
    id_counter = 0

    # Create task dir
    jobdir = os.path.join(args.jobdirs, args.jobdir_name)
    if os.path.exists(jobdir):
        if args.force:
            shutil.rmtree(jobdir)
        else:
            print(jobdir + ' exist and overriten is not set. use a different --jobdir-name')
            exit(1)
    mkdir(jobdir)
    for s, c, p, d, m, b in itertools.product(args.shifts, args.channels, args.processes, args.mask_pZetaMissVis_region, args.mask_mt_1_region, args.mask_btag_region):

        cmnd = 'python utils/produce_shapes_mssm.py --log-level info'
        cmnd = ' '.join([cmnd, '--year', args.year]) if args.year != 'default' else cmnd
        cmnd = ' '.join([cmnd, '--channels', c]) if c != 'default' else cmnd
        cmnd = ' '.join([cmnd, '--shifts', s]) if s != 'default' else cmnd
        cmnd = ' '.join([cmnd, '--processes', p]) if p != 'default' else cmnd
        cmnd = ' '.join([cmnd, '--mask-pZetaMissVis-region', d]) if d != 'default' else cmnd
        cmnd = ' '.join([cmnd, '--mask-mt_1-region', m]) if m != 'default' else cmnd
        cmnd = ' '.join([cmnd, '--mask-btag-region', b]) if b != 'default' else cmnd

        cmnd = ' '.join([cmnd, '--output-file-dir', args.output_file_dir]) if args.output_file_dir is not None and args.output_file_dir != '' else cmnd

        output_file_name = args.output_file_name + '__'.join([
            '_'.join(['year', args.year]),
            '_'.join(['channels', c]),
            '_'.join(['processes', p]),
            '_'.join(['shifts', s]),
            '_'.join(['mask_pZetaMissVis_region', d]),
            '_'.join(['mask_mt_1_region', m]),
            '_'.join(['mask_btag_region', b]),
        ])
        cmnd = ' '.join([cmnd, '--output-file-name', output_file_name])

        print([str(id_counter), cmnd, "\n"])
        arguments.append(" ".join([str(id_counter), cmnd, "\n"]))
        id_counter += 1

    # Create jobdir and subdirectories
    mkdir(jobdir)
    print("Jobdir: %s" % os.path.abspath(jobdir))
    for sd in ['out', 'log', 'err']:
        mkdir(os.path.join(jobdir, sd))

    # Create job execution file
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    job_executable_initial = os.path.join(project_dir, 'bin/batch_run.sh')
    job_executable = os.path.join(jobdir, "batch_run.sh")
    if not os.path.exists(job_executable_initial):
        print('no init batch file')
        exit(1)
    # copy with preserving the permissions
    p = subprocess.Popen(['cp', '-p', '--preserve', job_executable_initial, job_executable])
    p.wait()

    # replace hardcoded location
    for line in fileinput.input(job_executable, inplace=True):
        print line.replace('workind_dir=$(dirname "$0")/..', 'workind_dir=%s' % project_dir),
    # python 3
    # with fileinput.FileInput(job_executable, inplace=True, backup='.bak') as file:
    #     for line in file:
    #         print(line.replace(
    #             'workind_dir=$(dirname "$0")/..',
    #             'workind_dir=%s' % project_dir))

    # Write jdl file
    out = open(os.path.join(jobdir, "job.jdl"), "w")
    out.write(jdl_local)
    out.close()

    # Write argument list
    arglist = open(os.path.join(jobdir, "arguments.txt"), "w")
    for a in arguments:
        arglist.write(a)
    arglist.close()

    # Submit jobs
    if args.submit:
        os.chdir(jobdir)
        subprocess.call('pwd', shell=True)
        print('\n >>> ls jobdir')
        subprocess.call('ls', shell=True)
        print('\n >>> cat job.jdl')
        subprocess.call('cat job.jdl', shell=True)
        print('\n >>> run')
        subprocess.call('condor_submit job.jdl', shell=True)

    print('done')


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
