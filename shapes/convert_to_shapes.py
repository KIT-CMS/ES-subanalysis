#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 python convert_to_synced_shapes.py --input etFes_2017_all_shapes.root --output converted_shapes

"""
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser

import argparse
import os
import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
logger = logging.getLogger("")

intersection = lambda x, y: list(set(x) & set(y))

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


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert shapes from the shape producer to the sync format."
    )

    parser.add_argument('--output', '-o', default="", type=str,
                        help='Output directory')
    parser.add_argument('--input', '-i', type=str, nargs=1,
                        help='Path to single input ROOT file.')
    parser.add_argument('--variables', type=str, nargs='*', default=None,
                        help='variables.')
    parser.add_argument('--channels', type=str, nargs='*', default=['mt'],
                        help='channels.')
    parser.add_argument('--debug', default=False, action="store_true",
                        help="Debug option [Default: %(default)s]")

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
            print 'skip variable:', variable
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

    print 'categories in the root file: ', hist_map,
    pp.pprint(hist_map[channel].keys())


# TODO: class-based
# TODO: use also for fes
def convertToShapes(input_path='', output_dir='', debug=False,
        variables=['m_vis', 'njets_mvis', 'dm_mvis'], channels=['mt'],
        context='',
):
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

    # if debug:
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

                if name_output in check_processes:
                    check_processes.remove(name_output)

                if 'ZL' == name_output:
                    name_output += '_0'

                if 'ZL_' in name_output:
                    name_output = name_output.replace('_neg', '_-')
                    name_output = name_output.replace('0p', '0.')
                    name_output = name_output.replace('1p', '1.')
                    name_output = name_output.replace('2p', '2.')
                    name_output = name_output.replace('3p', '3.')

                if category == '0jet_dm0' and 'ZL' in name_output:
                    print '\t ', name_output
                print name_output
                hist = input_file.Get(name)
                hist.SetTitle(name_output)
                hist.SetName(name_output)
                hist.Write()

            print "check_processes:", check_processes

        output_file.Close()

    # Clean-up
    input_file.Close()
    print 'done'
    return output_file_name


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("convert_synced_shapes.log", logging.DEBUG)
    print args.variables
    convertToShapes(input_path=args.input[0], output_dir=args.output, debug=args.debug, variables=args.variables, channels=args.channels)
