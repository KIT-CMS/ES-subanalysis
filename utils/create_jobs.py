#!/usr/bin/env python

# Example:
'''
TODO:
    - test oopotion for --single-categories (done almost)
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
            --jobdir-name test0 --clear

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
            --jobdir-name test0 --clear

    note: to switch to htcondor:
    pip install --user htcondor
    python -c 'import htcondor; print(htcondor.__file__)'
    naf system: /usr/lib64/python2.6/site-packages/htcondor.so
'''
import os
import ast
import struct
import shutil
import math
import sys
import copy
import argparse
import subprocess
import itertools
import fileinput
from shapes.mssm import MSSM as analysis_shapes_mssm

from multiprocessing import Manager, Pool, Value, Process

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
from rootpy.logger.magic import DANGER
DANGER.enabled = True  # set True to raise exceptions

from six import string_types

logging.getLogger('shape_producer').setLevel(log.INFO)
logging.getLogger('shape_producer.histogram').setLevel(log.INFO)
logging.getLogger('shapes.baseshapes').setLevel(log.ERROR)
logging.getLogger('shapes.mssm.mssm').setLevel(log.ERROR)

jdl_local = """\
universe = vanilla
executable = ./batch_run.sh
output = out/$(ProcId).$(ClusterID).out
error = out/$(ProcId).$(ClusterID).out
log = log/$(ProcId).$(ClusterID).log
requirements = (OpSys == "LINUX")
getenv = true
max_retries = 3
RequestCpus = 1
+MaxRuntime = 10800
queue arguments from arguments.txt\
"""
# +MaxRuntime = 10800 7200
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
    parser.add_argument("--clear", default=False, action='store_true', help="Clear the htcondor job workdir")
    parser.add_argument("--clear-all", default=False, action='store_true', help="Clear the htcondor job workdir and .root files in output folder")
    parser.add_argument("--dry", default=False, action='store_true', help="dry run")
    parser.add_argument("--submit", default=False, action='store_true', help="")
    parser.add_argument("--debug", default=False, action='store_true', help="debug")
    parser.add_argument('-n', "--n-threads", default=1, type=int, help="n threads")

    # mssm
    parser.add_argument("--shifts", default=['default'], nargs='+', type=str, help="Pipelines, uncertainties variations, shifts : processed is the intersection of this list with list from _known_estimation_methods")
    parser.add_argument("--skip-shifts", default=None, nargs='+', type=str, help="Pipelines, uncertainties variations, shifts : processed is the intersection of this list with list from _known_estimation_methods")
    parser.add_argument("--processes", default=['default'], nargs='+', type=str, help="Processes from the standart map of processes")  # TODO: enable passing via syntax <name>:<class name>
    parser.add_argument("--channels", default=['default'], nargs='+', type=str, help="Channels to be considered.")

    parser.add_argument("--mask-pZetaMissVis-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: inc_dzeta, dzeta_low, dzeta_medium, dzeta_high")
    parser.add_argument("--mask-mt_1-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: inc_mt_1, mt_1_tight, mt_1_loose")
    parser.add_argument("--mask-btag-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: inc_nbtag, nbtag_zero, nbtag_nonzero")
    # parser.add_argument("--mask-eta-1-region", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: eta_1_barel, eta_1_endcap, eta_1_endcap_real")
    # parser.add_argument("--mask-decay-mode", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: all, dm0, dm1, dm10")
    # parser.add_argument("--mask-jets-multiplicity", default=['default'], nargs='+', type=str, help="Needed for categorisation. Choices: njetN, njet0")
    parser.add_argument("--variables-names", default=['default'], nargs='*', type=str, help="Variable names.")

    parser.add_argument("--mass-susy-ggH", default=['default'], nargs='*', type=int, help="SUSY ggH masspoints")
    parser.add_argument("--mass-susy-qqH", default=['default'], nargs='*', type=int, help="SUSY bbH masspoints")

    #TODO: this option needs a test!
    parser.add_argument('--single-categories', type=ast.literal_eval, help="Dict of cuts to force. Format: --single-categories=\"\{'cut_key': 'cut_exp', 'cut_key': 'cut_exp'\}\"")

    parser.add_argument('--filter-channels-grid', type=ast.literal_eval, help="Dict of cuts to force. Format: --single-categories=\"\{'cut_key': 'cut_exp', 'cut_key': 'cut_exp'\}\"")
    parser.add_argument("--mssm-categories-filtering", default=False, action='store_true', help="dry run")
    # parser.add_argument('--single-categories', type=str, help="Dict of cuts to force. Format: --single-categories=\"\{'cut_key': 'cut_exp', 'cut_key': 'cut_exp'\}\"")

    parser.add_argument('--no-grid-categories', action='store_true', default=None, help='drop categorisation defined by grid_categories config.')
    parser.add_argument('--no-single-categories', action='store_true', default=None, help='drop categorisation defined by single_categories config.')
    parser.add_argument('--use-grid-categories', action='store_true', default=None, help='use categorisation defined by grid_categories config.')
    parser.add_argument('--use-single-categories', action='store_true', default=None, help='use categorisation defined by single_categories config.')

    parser.add_argument("--year", "--era", default='default', type=str, help="Experiment era.")
    parser.add_argument("--output-file-dir", type=str, help="Output file directory")
    parser.add_argument("--output-file-name", default='', type=str, help="Output file name for file with final shapes that enter datacards. If none is given context_analysis is used as a root for this name")

    args = parser.parse_args()

    return args


def convertToNumberSum(l):
    n = 0
    for i in l:
        n += convertToNumber(str(i))
    return n


def convertToNumber(s):

    if sys.version_info < (3, 0):
        import codecs
        # data = bytes(data)
        # return int(codecs.encode(b'f483', 'hex'), 16)
        return int(codecs.encode(s, 'hex'), 16)
    else:
        # data = bytes(data, 'utf8')
        return int.from_bytes(s.encode(), 'little')


def convertFromNumber(n):
    if sys.version_info < (3, 0):
        # data = bytes(data)
        return codecs.decode(str(n), 'hex')
    else:
        # data = bytes(data, 'utf8')
        return n.to_bytes(math.ceil(n.bit_length() / 8), 'little').decode()


def prepare_command(config_initial, idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, single_categories=None, skip_shifts=None):
    # shared across processes
    global dict_of_categ
    global id_counter
    global arguments
    # global config_initial
    global gargs
    # global skip_per_channel_record
    # print('channel: %s, shifts: %s, var: %s, mask_pZetaMissVis: %s, mask_mt_1: %s, mask_btag: %s' % (channel, shift, variables, pZeta, mt_1, btag))

    cat_add = 0
    # 00 - initial
    # 01 - use_single_categories
    # 02 - no_use_single_categories
    # 10 - use_group_categories
    # 20 - no_use_group_categories
    # TODOO -> fix
    for i, k in enumerate(["use_single_categories", "use_grid_categories"]):
        if k not in config_initial.keys() or config_initial[k] is None:
            continue
        else:
            # cat_add += (1 + i * 10) if config_initial[k] else (2 + i * 10) if config_initial[k] else 0
            # toadd = (1 + i * 10) if config_initial[k] else (2 + i * 10) if config_initial[k.replace('use_', 'no_')] else 0
            toadd = (1 * pow(10, i)) if config_initial[k] else (2 * pow(10, i))
            cat_add += toadd
            # if k.replace('use_', 'no_') in config_initial:
            #     print "{:>25s}: {:<10d} {:>25s}: {:<10d} (+{:d}) ".format(str(k), config_initial[k], k.replace('use_', 'no_'), config_initial[k.replace('use_', 'no_')], toadd)
            # else:
            #     print "{:>25s}: {:<10d} {:>25s}: {:<10s}  (+{:d})".format(str(k), config_initial[k], k.replace('use_', 'no_'), "-", toadd)
    # print cat_add
    # print '-'*10
    # return

    no_grid_cat = None
    if ('use_grid_categories' in config_initial and config_initial['use_grid_categories'] is False) or ('no_grid_categories' in config_initial.keys() and config_initial['no_grid_categories'] is True):
        no_grid_cat = True
    elif ('no_grid_categories' in config_initial and config_initial['no_grid_categories'] is False) or ('use_grid_categories' in config_initial.keys() and config_initial['use_grid_categories'] is True):
        no_grid_cat = False

    # cat_add += 0 if "use_single_categories" not in config_initial.keys() or config_initial["use_single_categories"] is None else 10 if config_initial["use_single_categories"] else 20 if config_initial["use_single_categories"]
    # cat_add += 0 if "use_grid_categories" not in config_initial.keys() or config_initial["use_grid_categories"] is None else 1 if config_initial["use_grid_categories"] else 2 if config_initial["use_grid_categories"]
    if process == 'default':
        if no_grid_cat:
            key_in = [shift, channel, cat_add]
        else:
            key_in = [shift, channel, pZeta, mt_1, btag, cat_add]

    else:
        if no_grid_cat:
            key_in = [shift, channel, process, cat_add]
        else:
            key_in = [shift, channel, process, pZeta, mt_1, btag, cat_add]

    key = convertToNumberSum(key_in)

    prt = '\n' + '=' * 20
    # prt += 'channel: %s, shifts: %s, var: %s, mask_pZetaMissVis: %s, mask_mt_1: %s, mask_btag: %s' % (channel, shift, variables, pZeta, mt_1, btag)
    # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
    # check that
    # propose_to_skip = False
    # if no_grid_cat and \
    #         key in skip_per_channel_record[channel] and \
    #         variables in skip_per_channel_record[channel][key]:
    #     propose_to_skip = True

    if key not in dict_of_categ:
        prt += '\n\t(new init)'
        if gargs.debug: print("%d: init " % idd)
        config = copy.deepcopy(config_initial)
        if gargs.year != 'default': config['era'] = gargs.year
        if channel != 'default': config['channels'] = [channel]
        if shift != 'default': config['shifts'] = [shift]
        if process != 'default': config['processes'] = [process]
        if variables != 'default': config['variables_names'] = [variables]
        config['mask_grid_categories'] = {}
        if pZeta != 'default': config['mask_grid_categories']['mask_pZetaMissVis_region'] = [pZeta]
        if mt_1 != 'default': config['mask_grid_categories']['mask_mt_1_region'] = [mt_1]
        if btag != 'default': config['mask_grid_categories']['mask_btag_region'] = [btag]
        # pp.pprint(config['single_categories'])
        if single_categories is not None: config['single_categories'] = single_categories

        if mass_susy_qqH == []:
            config['mass_susy_qqH'] = []
        elif mass_susy_qqH != 'default':
            config['mass_susy_qqH'] = [mass_susy_qqH]

        if mass_susy_ggH == []:
            config['mass_susy_ggH'] = []
        elif mass_susy_ggH != 'default':
            config['mass_susy_ggH'] = [mass_susy_ggH]

        # print config['mask_grid_categories']['mask_pZetaMissVis_region'] ; exit(1)
        # if gargs.no_grid_categories is not None: config['no_grid_categories'] = True
        # if gargs.no_single_categories is not None: config['no_single_categories'] = True
        # if gargs.use_grid_categories is not None: config['use_grid_categories'] = True
        # if gargs.use_single_categories is not None: config['use_single_categories'] = True

        # print config.keys(); exit(1)
        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
        shapes = analysis_shapes_mssm(**config)
        shapes._dry = True
        shapes._log_level = 'error'
        shapes.setup_logging(
            output_file=shapes._output_file.replace('.root', '.log'),
            level=shapes._log_level.lower(),
            logger=shapes._logger,
            danger=DANGER.enabled,
        )
        # if gargs.debug: print("%d: evaluateEra " % key)
        shapes.evaluateEra()
        # if gargs.debug: print("%d: importEstimationMethods " % key)
        shapes.importEstimationMethods()
        # if gargs.debug: print("%d: evaluateChannels " % key)
        shapes.evaluateChannels()  # after this
        shapes.evaluateSystematics()  # gives final number of shapes
        # shapes.produce()  # corrects number of shapes w/o nominals if necessary
        dict_of_categ[key] = {
            'n': shapes.getNShapes(),
            'ncategories': shapes.getNCategories(),
            'v': [idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, single_categories]
        }
        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
        # if gargs.debug: print("%d: getNShapes %d(%d)" % (key, dict_of_categ[key], shapes.getNShapes()))

    cmnd = 'python utils/produce_shapes_mssm.py --log-level info'
    cmnd = ' '.join([cmnd, '--year', gargs.year]) if gargs.year != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--channels', channel]) if channel != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--shifts', shift]) if shift != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--skip-shifts'] + skip_shifts) if skip_shifts is not None else cmnd
    cmnd = ' '.join([cmnd, '--processes', process]) if process != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--variables-names', variables]) if variables != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--mask-pZetaMissVis-region', pZeta]) if pZeta != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--mask-mt_1-region', mt_1]) if mt_1 != 'default' else cmnd
    cmnd = ' '.join([cmnd, '--mask-btag-region', btag]) if btag != 'default' else cmnd

    if mass_susy_qqH == []:
        cmnd = ' '.join([cmnd, '--mass-susy-qqH'])
    elif mass_susy_qqH != 'default':
        cmnd = ' '.join([cmnd, '--mass-susy-qqH'] + mass_susy_qqH)

    if mass_susy_ggH == []:
        cmnd = ' '.join([cmnd, '--mass-susy-ggH'])
    elif mass_susy_ggH != 'default':
        cmnd = ' '.join([cmnd, '--mass-susy-ggH'] + mass_susy_ggH)

    cmnd = ' '.join([cmnd, '--output-file-dir', gargs.output_file_dir]) if gargs.output_file_dir is not None and gargs.output_file_dir != '' else cmnd

    # cmnd = ' '.join([cmnd, '--no-grid-categories']) if gargs.no_grid_categories is not None else cmnd
    # cmnd = ' '.join([cmnd, '--no-single-categories']) if gargs.no_single_categories is not None else cmnd
    # cmnd = ' '.join([cmnd, '--use-grid-categories']) if gargs.use_grid_categories is not None else cmnd
    # cmnd = ' '.join([cmnd, '--use-single-categories']) if gargs.use_single_categories is not None else cmnd
    cmnd = ' '.join([cmnd, '--no-grid-categories']) if "no_grid_categories" in config_initial.keys() and config_initial["no_grid_categories"] is True else cmnd
    cmnd = ' '.join([cmnd, '--no-single-categories']) if "no_single_categories" in config_initial.keys() and config_initial["no_single_categories"] is True else cmnd
    cmnd = ' '.join([cmnd, '--use-grid-categories']) if "use_grid_categories" in config_initial.keys() and config_initial["use_grid_categories"] is True else cmnd
    cmnd = ' '.join([cmnd, '--use-single-categories']) if "use_single_categories" in config_initial.keys() and config_initial["use_single_categories"] is True else cmnd

    cmnd = ' '.join([cmnd, '--single-categories \\"%s\\"' % str(single_categories)]) if single_categories is not None else cmnd
    # print "'%s'" % cmnd ; exit(0)
    # Define name of the output file
    name_parts = [
        '_'.join([gargs.year]),
        '_'.join([channel]),
        '_'.join([shift]),
        # '_'.join([process]),
    ]
    if skip_shifts is not None:
        name_parts.append('_skip'.join(skip_shifts))
        print 'skip_shifts:', skip_shifts
        print 'name_parts:', name_parts
    name_parts.append('_'.join(["categ_param", str(cat_add)]))
    if process != 'default': name_parts.append('_'.join(['processes', process]))
    if variables != 'default': name_parts.append('_'.join(['variables_names', variables]))
    if pZeta != 'default': name_parts.append('_'.join(['mask_pZetaMissVis_region', pZeta]))
    if mt_1 != 'default': name_parts.append('_'.join(['mask_mt_1_region', mt_1]))
    if btag != 'default': name_parts.append('_'.join(['mask_btag_region', btag]))

    output_file_name = gargs.output_file_name + '.'.join(name_parts)

    cmnd = ' '.join([cmnd, '--output-file-name', output_file_name])

    prt += '\n\t id%d : %s\n' % (id_counter.value, cmnd) + "-" * 20
    if dict_of_categ[key]['n'] == 0:
        if gargs.debug:
            prt = '\n\t (skipping) n shapes: %d ; n categories: %d' % (dict_of_categ[key]['n'], dict_of_categ[key]['ncategories']) + prt
            # prt = ('\n\t skipping: %s \n' % key_in) + prt
            prt = prt.replace(' python ', ' SKIPPING python ')
            print(prt)
            # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
    else:
        # if gargs.debug: print("%d: not skipping " % key)
        prt = '\n\t n shapes: %d ; n categories: %d' % (dict_of_categ[key]['n'], dict_of_categ[key]['ncategories']) + prt
        print(prt)
        arguments.append(cmnd)
        # if dict_of_categ[key]['n'] == 78:
        #     print(dict_of_categ[key]['v'])
        #     print([idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, single_categories])
        #     import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
        # arguments.append(" ".join([str(id_counter.value), cmnd, "\n"]))
        id_counter.value += 1
        # if not propose_to_skip:
        #     if gargs.debug: print("%d: not skipping " % key)
        #     prt = '\n\t n categ: %d' % dict_of_categ[key] + prt
        #     print(prt)
        #     arguments.append(cmnd)
        #     # arguments.append(" ".join([str(id_counter.value), cmnd, "\n"]))
        #     id_counter.value += 1
        #     if key not in skip_per_channel_record[channel]:
        #         skip_per_channel_record[channel][key] = [variables]
        #     else:
        #         skip_per_channel_record[channel][key].append(variables)
        # else:
        #     if gargs.debug: print("%d: not skipping BUT PROPOSING TO SKIP" % key)
        #     prt = '\n\t n categ: %d' % dict_of_categ[key] + prt
        #     print(prt.replace(' python ', ' PROPOSE TO SKIP python '))
        #     arguments.append(cmnd)
        #     # arguments.append(" ".join([str(id_counter.value), cmnd, "\n"]))
        #     id_counter.value += 1


def getPrepareDirectory(args):
    # Create task dir (jobdir) and subdirectories
    args.clear = args.clear_all if args.clear_all else args.clear
    jobdir = os.path.join(args.jobdirs, args.jobdir_name)
    if os.path.exists(jobdir):
        if args.clear:
            if args.dry:
                print('Would delete jobdir %s' % jobdir)
            else:
                shutil.rmtree(jobdir)
        else:
            print(jobdir + ' exist and overriten is not set. use a different --jobdir-name')
            exit(1)

    if not args.dry:
        mkdir(jobdir)
    else:
        print('Would create jobdir %s' % jobdir)

    print("Jobdir: %s" % os.path.abspath(jobdir))
    for sd in ['out', 'log', 'err']:
        if not args.dry:
            mkdir(os.path.join(jobdir, sd))
        else:
            print('Would create jobdir subdir %s' % os.path.join(jobdir, sd))

    # create job execution file
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    job_executable_initial = os.path.join(project_dir, 'bin/batch_run.sh')
    job_executable = os.path.join(jobdir, "batch_run.sh")
    if not os.path.exists(job_executable_initial):
        print('no init batch file')
        exit(1)

    # copy with preserving the permissions
    cmnd_list = ['cp', '-p', '--preserve', job_executable_initial, job_executable]
    if not args.dry:
        p = subprocess.Popen(cmnd_list)
        p.wait()
    else:
        print('Would call: %s' % ' '.join(cmnd_list))

    # replace hardcoded location
    if args.dry:
        print('Would replace hardcoded location: \n\t %s \n\t<<%s>> to <<%s>>' % (job_executable, 'workind_dir=$(dirname "$0")/..', 'workind_dir=%s' % project_dir))
        print('Would Write jdl file\nWrite argument list')
        if args.submit: print('Would Submit jobs')
        print('done')
    else:
        for line in fileinput.input(job_executable, inplace=True):
            print line.replace('workind_dir=$(dirname "$0")/..', 'workind_dir=%s' % project_dir),

    # Clear output dir
    if os.path.exists(args.output_file_dir):
        if args.clear_all:
            if args.dry:
                print('Would delete output_file_dir %s' % args.output_file_dir)
            else:
                shutil.rmtree(args.output_file_dir)
        else:
            print(args.output_file_dir + ' exist! outputs mights get confused!')

    return jobdir


def main(args):
    # Prepare the pool
    # shared non-modified
    global dict_of_categ
    global id_counter
    global arguments
    global config_initial
    global gargs
    global skip_per_channel_record
    skip_per_channel_record = {}
    gargs = args
    # print type(args.filter_channels_grid), "'%s'" % args.filter_channels_grid ; exit(1)
    # shared modified
    manager = Manager()
    dict_of_categ = manager.dict()
    id_counter = manager.Value('i', 0)
    arguments = manager.list()
    results = []

    # Make initial conf
    # todo add the check on number of shapes that will be created
    # todo: switch between analyses
    config_initial = analysis_shapes_mssm.prepareConfig(
        analysis_shapes=analysis_shapes_mssm,
        config_file='data/mssm_legacy_mva_config.yaml',
        debug=False,
        parse_arguments=False
    )
    # This is the base case:
    # config_initial.update({'use_grid_categories': True, '_debug': False})
    config_initial['_debug'] = False
    if args.no_grid_categories is not None:
        config_initial['no_grid_categories'] = args.no_grid_categories
    if args.no_single_categories is not None:
        config_initial['no_single_categories'] = args.no_single_categories
    if args.use_grid_categories is not None:
        config_initial['use_grid_categories'] = args.use_grid_categories
    if args.use_single_categories is not None:
        config_initial['use_single_categories'] = args.use_single_categories

    if args.no_grid_categories is not None and args.use_grid_categories is not None and args.no_grid_categories and args.use_grid_categories:
        raise Exception("Contradicting parameters (grid_categories)")

    if args.no_single_categories is not None and args.use_single_categories is not None and args.no_single_categories and args.use_single_categories:
        raise Exception("Contradicting parameters (single_categories)")

    separate_singles_and_grid = True if args.use_single_categories and args.use_grid_categories else  False

    pool = Pool(processes=args.n_threads)
    if args.mass_susy_qqH == []:
        args.mass_susy_qqH = [[]]
    if args.mass_susy_ggH == []:
        args.mass_susy_ggH = [[]]

    for idd, (shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH) in enumerate(itertools.product(
            args.shifts,
            args.channels,
            args.processes,
            args.variables_names,
            args.mask_pZetaMissVis_region,
            args.mask_mt_1_region,
            args.mask_btag_region,
            args.mass_susy_qqH,
            args.mass_susy_ggH)):

        # print shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH
        # continue
        if args.filter_channels_grid is not None and channel in args.filter_channels_grid \
            and any(i in args.filter_channels_grid[channel] for i in [pZeta, mt_1, btag]):
            # if args.debug: print 'filter: %s ' % [channel, pZeta, mt_1, btag]
            continue

        if separate_singles_and_grid:

            # for drid categ
            config_initial_grid_categ = copy.deepcopy(config_initial)
            config_initial_grid_categ['no_single_categories'] = True
            config_initial_grid_categ['use_single_categories'] = False

            if args.n_threads != 1:
                results.append(pool.apply_async(prepare_command, args=(copy.deepcopy(config_initial_grid_categ), idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, args.single_categories, args.skip_shifts))) # , callback=callback
            else:
                prepare_command(copy.deepcopy(config_initial_grid_categ), idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, args.single_categories, args.skip_shifts)

            # for singles
            config_initial_single_categ = copy.deepcopy(config_initial)
            config_initial_single_categ['no_grid_categories'] = True
            config_initial_single_categ['use_grid_categories'] = False

            key_in = [shift, channel, process, variables, mass_susy_qqH, mass_susy_ggH]
            key = convertToNumberSum(key_in)
            if key not in skip_per_channel_record.keys():
                skip_per_channel_record[key] = [shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH]
                if args.n_threads != 1:
                    results.append(pool.apply_async(prepare_command, args=(copy.deepcopy(config_initial_single_categ), idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, args.single_categories, args.skip_shifts))) # , callback=callback
                else:
                    prepare_command(copy.deepcopy(config_initial_single_categ), idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, args.single_categories, args.skip_shifts)
            else:
                pass
                # if args.debug: print 'Skipping for --use-single-categories %s because added %s' % ([shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH], skip_per_channel_record[key])

        else:
            if args.n_threads != 1:
                results.append(pool.apply_async(prepare_command, args=(copy.deepcopy(config_initial), idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, args.single_categories))) # , callback=callback
            else:
                prepare_command(copy.deepcopy(config_initial), idd, shift, channel, process, variables, pZeta, mt_1, btag, mass_susy_qqH, mass_susy_ggH, args.single_categories, args.skip_shifts)

    if args.n_threads != 1:
        for result in results:
            result.get()

        pool.close()
        pool.join()
    arguments.sort()
    arguments = ['%d %s\n' % (i, v) for i, v in enumerate(arguments)]
    # print("Arguments:")
    # print(''.join(arguments))

    if len(arguments) == 0:
        print("No valid tasks to call. Exit 0.")
        return 0
    else:
        print("Number of jobs to run: %d" % len(arguments))

    jobdir = getPrepareDirectory(args)
    print('Jobdir: %s' % jobdir)

    if args.dry:
        print('Dry run done.')
        return

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

    else:
        print("cd %s ; condor_submit job.jdl" % jobdir)

    print('done')


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
