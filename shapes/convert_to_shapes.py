#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 python convert_to_synced_shapes.py --input etFes_2017_all_shapes.root --output converted_shapes

"""
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser

import argparse
import os
from six import string_types
import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
logger = logging.getLogger(__name__)
from rootpy import log
from rootpy.logger.magic import DANGER

intersection = lambda x, y: list(set(x) & set(y))

trimmed = [
    'CMS_tes_gamma_nominal_13TeV_',  # keeping it out to have both options in converted file
    'CMS_tes_tauTauEsOneProngPiZerosShift_13TeV_',
    'CMS_fes_eleTauEsInclusiveShift_13TeV_',
    'CMS_fes_eleTauEsOneProngShift_13TeV_',
    'CMS_fes_eleTauEsOneProngPiZerosShift_13TeV_',
    'CMS_fes_eleTauEsThreeProngShift_13TeV_',
]
# TODO: generalise?
map_pipes = {
    '0jet_alldm': 'CMS_fes_eleTauEsInclusiveShift_13TeV_',
    '0jet_dm0': 'CMS_fes_eleTauEsOneProngShift_13TeV_',
    '0jet_dm1': 'CMS_fes_eleTauEsOneProngPiZerosShift_13TeV_',
    '0jet_dm10': 'CMS_fes_eleTauEsThreeProngShift_13TeV_',

    'njet0_alldm': 'CMS_fes_eleTauEsInclusiveShift_13TeV_',
    'njet0_dm0': 'CMS_fes_eleTauEsOneProngShift_13TeV_',
    'njet0_dm1': 'CMS_fes_eleTauEsOneProngPiZerosShift_13TeV_',
    'njet0_dm10': 'CMS_fes_eleTauEsThreeProngShift_13TeV_',

    'njetN_alldm': 'CMS_fes_eleTauEsInclusiveShift_13TeV_',
    'njetN_dm0': 'CMS_fes_eleTauEsOneProngShift_13TeV_',
    'njetN_dm1': 'CMS_fes_eleTauEsOneProngPiZerosShift_13TeV_',
    'njetN_dm10': 'CMS_fes_eleTauEsThreeProngShift_13TeV_',

    'inclusive': 'CMS_fes_eleTauEsInclusiveShift_13TeV_',

    'jeta_1': 'jeta_1',
    'jeta_2': 'jeta_2',
    'm_vis': 'm_vis',
}


def drange(start, stop, step, include_last=False):
    rounding_to = str(step).split('.')
    if len(rounding_to) == 1:
        rounding_to = 0
    else:
        rounding_to = len(rounding_to[1])

    l = []
    while round(start, rounding_to) < round(stop + step * include_last, rounding_to):
        l.append(round(start, rounding_to))
        start += step

    return l


charged_points = drange(-4.0, 4.0, 0.2, include_last=True)
neutral_points = drange(-2.0, 2.0, 0.2, include_last=True)
root_str = lambda x: str(x).replace("-", "neg").replace(".", "p")
print neutral_points
tes_gamma_bins = {}
for cp in charged_points:
    for nn in neutral_points:
        if nn == 0: nn = 0.0
        if cp == 0: cp = 0.0
        key = 'ch' + root_str(cp) + '_nt' + root_str(nn)
        binn = int((cp + 10) * 10 * 1000 + (nn + 10) * 10)
        tes_gamma_bins[key] = binn
        # if key =="chneg3p8_ntneg0p0":
        #     print cp, nn, key, binn; exit(1)
# pp.pprint(tes_gamma_bins); exit(1)
if len(set(tes_gamma_bins.values())) != len(tes_gamma_bins):
    print 'binning in tes_gamma_bins is not uniq! tes_gamma_bins:'
    pp.pprint(tes_gamma_bins)
    raise


def printConvertToShapesCommand(input_path, output_dir, debug, variables, channels, context):
    if isinstance(variables, string_types):
        variables = [variables]
    if isinstance(channels, string_types):
        channels = [channels]
    logger.info('\nTerminal command:\n   python %s -i %s -o %s -v %s -c %s --context %s %s \n' % (
        __file__,
        input_path,
        output_dir,
        ' '.join(variables),
        ' '.join(channels),
        context,
        '-d' if debug else '',
    ))


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert shapes from the shape producer to the sync format."
    )

    parser.add_argument('-o', '--output-dir', default="", type=str,
                        help='Output directory')
    parser.add_argument('-i', '--input', type=str, nargs=1,
                        help='Path to single input ROOT file.')
    parser.add_argument('-v', '--variables', type=str, nargs='*', default=None,
                        help='variables.')
    parser.add_argument('-c', '--channels', type=str, nargs='*', default=['mt'],
                        help='channels.')
    parser.add_argument('--debug', default=False, action="store_true",
                        help="Debug option [Default: %(default)s]")
    parser.add_argument('--context', type=str, default='',
                        help='context.')
    parser.add_argument('--use-number-coding', default=False, action="store_true",
                        help="Use number coding for gamma TES [Default: %(default)s]")

    return parser.parse_args()


def checkDM(hist_map):
    filtered_catDM0_ZL_DM0_remove = {k: v for k, v in hist_map['et']['0jet_dm0'].iteritems() if '#ZL#' in k and '_fes_eleTauEsOneProng_' in k}
    filtered_catDM0_ZL_DM0 = {k: v for k, v in hist_map['et']['0jet_dm0'].iteritems() if '#ZL#' in k and '_fes_eleTauEsOneProngShift_' in k}
    filtered_catDM0_ZL_DM1 = {k: v for k, v in hist_map['et']['0jet_dm0'].iteritems() if '#ZL#' in k and '_fes_eleTauEsOneProngPiZerosShift_' in k}
    filtered_catDM0_ZL_DM10 = {k: v for k, v in hist_map['et']['0jet_dm0'].iteritems() if '#ZL#' in k and '_fes_eleTauEsThreeProngShift_' in k}
    filtered_catDM0_ZL_ALLDM = {k: v for k, v in hist_map['et']['0jet_dm0'].iteritems() if '#ZL#' in k}

    print 'filtered catDM0_ZL:'
    print '\tDM0:'
    pp.pprint(filtered_catDM0_ZL_DM0)
    print '\tDM1:'
    pp.pprint(filtered_catDM0_ZL_DM1)
    print '\tDM10:'
    pp.pprint(filtered_catDM0_ZL_DM10)
    for k in filtered_catDM0_ZL_ALLDM.keys():
        if k not in filtered_catDM0_ZL_DM0_remove.keys() + filtered_catDM0_ZL_DM0.keys() + filtered_catDM0_ZL_DM1.keys() + filtered_catDM0_ZL_DM10.keys():
            print 'nominal:', k


def constructMap(hist_map, input_file, debug=0, variables=None):
    # pp.pprint(sorted(input_file.GetListOfKeys())); exit(1)
    if variables is None:
        print "convertToShapes::constructMap : no desired variables were asked to be updated."
        return

    # Read name and extract shape properties
    for key in input_file.GetListOfKeys():
        name = key.GetName()

        properties = [x for x in name.split("#") if not x == ""]
        if len(properties) not in [7, 8]:
            logger.critical("Shape {} has an unexpected number of properties.".format(name))
            raise Exception

        # Get other properties
        # ex.: ['mt', 'mt_njetN_dm1', 'ZTT', 'mtTES', 'Run2017ReReco31Mar', 'm_vis', '125', 'CMS_fes_eleTauEsInclusiveShift_13TeV_']
        channel = properties[0]
        category = properties[1][3:]  # remove the trailing channel from category name)
        process = properties[2]
        analysis = properties[3]
        period = properties[4]
        variable = properties[5]
        mass = properties[6]
        systematic = ''
        if len(properties) == 8:
            systematic = properties[7]

        if variable not in variables:
            log.debug('skip variable: ' + variable)
            continue

        # Add new channel and/or category to the map if needed
        if channel not in hist_map:
            hist_map[channel] = {}
        if category not in hist_map[channel]:
            hist_map[channel][category] = {}
        if name in hist_map[channel][category].keys():
            continue

        name_output = "{PROCESS}{SYSTEMATIC}".format(PROCESS=process, SYSTEMATIC=systematic)
        hist_map[channel][category][name] = name_output

        if debug > 1:
            print 'name:', name, '\n\t properties:',
            pp.pprint(properties)
            print '\t channel:', channel
            print '\t category:', category
            print '\t process:', process
            print '\t analysis:', analysis
            print '\t period:', period
            print '\t variable:', variable
            print '\t mass:', mass
            print '\t name_output:', name_output
            print '\t hist_map[et]:', hist_map[channel]
            exit(1)

    print 'hist_map: '
    pp.pprint(hist_map)
    print 'categories in the root file: '
    pp.pprint(hist_map[channel].keys())


# TODO: class-based
# TODO: use also for fes
def convertToShapes(
        input_path='',
        output_dir='',
        debug=False,
        variables=['m_vis', 'njets_mvis', 'dm_mvis'],
        channels=['mt'],
        context='',
        use_number_coding=False,
):
    if len(variables) > 1:
        print('ConvertToShapes: multiple variables -> multiple output files')
        printConvertToShapesCommand(input_path, output_dir, debug, variables, channels, context)

    outputs = []
    output_dir_initial = output_dir
    for variable in variables:
        if len(variables) > 1:
            output_dir = '_'.join([output_dir_initial.rstrip('.root'), variable])
            logger.warning('new output dir:' + output_dir)

        outputs.append(
            convertToShapesSingleVariable(
                input_path=input_path,
                output_dir=output_dir,
                debug=debug,
                variables=variable,
                channels=channels,
                context=context,
                use_number_coding=use_number_coding,
            )
        )

    return outputs


def convertToShapesSingleVariable(
        input_path='',
        output_dir='',
        debug=False,
        variables='m_vis',
        channels=['mt'],
        context='',
        use_number_coding=False,
):
    print('ConvertToShapes: single variable')
    printConvertToShapesCommand(input_path, output_dir, debug, variables, channels, context)

    # Open input ROOT file and output ROOT file
    if not input_path.endswith('.root'):
        input_path = "{}.root".format(input_path)
    if not os.path.isfile(input_path):
        raise Exception('Input file not found:' + input_path)
    print 'Input file:', input_path
    input_file = ROOT.TFile(input_path, 'read')

    # Loop over shapes of input ROOT file and create map of input/output names
    hist_map = {}
    constructMap(hist_map=hist_map, input_file=input_file, debug=debug, variables=variables)

    # if debug and '_fes_' in name_output:
    #     checkDM(hist_map)

    check_processes = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT"]

    known_categories = map_pipes.keys()

    for channel in hist_map:
        print '-' * 10, '\n Channel:', channel

        # Prepare output file
        if output_dir == '':
            output_dir = os.path.join(os.getcwd(), "converted_shapes", input_path.split('/')[-1].split('.root')[0])
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        output_file_name = os.path.join(output_dir, "htt_{CHANNEL}.inputs{CONTEXT}.root").format(CHANNEL=channel, CONTEXT=context)
        print 'Output file:', output_file_name
        output_file = ROOT.TFile(output_file_name, "RECREATE")

        if len(intersection(known_categories, hist_map[channel].keys())) == 0:
            print 'No registered as known categories are found in hist_map. Known are:'
            pp.pprint(known_categories)
            print "But found:"
            pp.pprint(hist_map[channel].keys())
        else:
            print "Intersection:", intersection(known_categories, hist_map[channel].keys())

        for category in intersection(known_categories, hist_map[channel].keys()):
            ztt_tes_bins = []
            print '\t category:', category, '...'
            # if category == '0jet_alldm':
            #         print 'add after next skimm'
            #         continue

            if category.endswith("_ss") or category.endswith("_B") or category.endswith('_for_wjets_mc'):
                print '\t skipped'
                continue

            output_file.cd()
            dir_name = "{CHANNEL}_{CATEGORY}".format(CHANNEL=channel, CATEGORY=category)
            output_file.mkdir(dir_name)
            output_file.cd(dir_name)

            for name in hist_map[channel][category]:
                print 'name:', name, '...',
                name_output = hist_map[channel][category][name]

                if category in map_pipes.keys():
                    if '_fes_' in name_output and map_pipes[category] not in name_output:
                        # print '\t dropping', name_output
                        continue
                    else:
                        name_output = name_output.replace(map_pipes[category], '')
                else:
                    print 'unknown category to drop unnessesary pipelines:', category
                    exit(1)
                for t in trimmed:
                    name_output = name_output.replace(t, '')

                if '_fes_' in context:
                    if name_output in check_processes:
                        check_processes.remove(name_output)

                    if 'ZL' == name_output:
                        name_output += '_0'
                    name_output = name_output.replace('_neg', '_-')
                    name_output = name_output.replace('0p', '0.')
                    name_output = name_output.replace('1p', '1.')
                    name_output = name_output.replace('2p', '2.')
                    name_output = name_output.replace('3p', '3.')
                    name_output = name_output.replace('4p', '4.')

                if 'tes' in context:
                    if 'ZTT' == name_output:  # this is already in the list with shifts notation
                        pass
                        # continue
                    elif use_number_coding and 'ZTT' in name_output:
                        replaced = False
                        for k in tes_gamma_bins.keys():
                            if k in name_output:
                                name_output = name_output.replace(k, '_' + str(tes_gamma_bins[k]))
                                replaced = True
                                ztt_tes_bins.append(str(tes_gamma_bins[k]))
                                break
                        if not replaced:
                            print '\n Could not assign a tes_gamma bin for:', name_output
                            raise

                if category == '0jet_dm0' and 'ZL' in name_output:
                    print '\t ', name_output
                print name_output
                hist = input_file.Get(name)
                hist.SetTitle(name_output)
                hist.SetName(name_output)
                hist.Write()

            if '_fes_' in context:
                print "check_processes:", check_processes

        if 'tes' in context:
            print '\t ZTT bins:', ztt_tes_bins
        output_file.Close()

    # Clean-up
    input_file.Close()
    print 'done'
    return output_file_name


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # file_handler = logging.FileHandler(output_file, "w")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)


if __name__ == "__main__":
    args = parse_arguments()

    print args.variables
    output_file_name = convertToShapes(
        input_path=args.input[0],
        output_dir=args.output_dir,
        debug=args.debug,
        variables=args.variables,
        channels=args.channels,
        context=args.context,
        use_number_coding=args.use_number_coding,
    )

    if isinstance(output_file_name, string_types):
        output_file_name = [output_file_name]
    for o in output_file_name:
        logging.info(o)

    # TODO: fix
    # pp.pprint(logging.Logger.manager.loggerDict)
    # setup_logging("convert_synced_shapes.log", log.DEBUG)
    # # doesn't change logging.Logger.manager.loggerDict
    # pp.pprint(logging.Logger.manager.loggerDict)
