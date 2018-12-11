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


def constructMap(hist_map, input_file, debug=0, variables=['m_vis', 'njets_mvis', 'dm_mvis']):
    # pp.pprint(sorted(input_file.GetListOfKeys())); exit(1)
    for key in input_file.GetListOfKeys():
        # Read name and extract shape properties
        name = key.GetName()
        properties = [x for x in name.split("#") if not x == ""]

        if properties[5] not in variables:
            print 'skip variable:', properties[5]
            continue

        # Get category name (and remove CHANNEL_ from category name)
        category = properties[1][3:]
        # Get other properties
        channel = properties[0]
        process = properties[2]

        # Check that in the mapping of the names the channel and category is existent
        if channel not in hist_map:
            hist_map[channel] = {}
        if category not in hist_map[channel]:
            hist_map[channel][category] = {}

        # Push name of histogram to dict
        if len(properties) not in [7, 8]:
            logger.critical("Shape {} has an unexpected number of properties.".format(name))
            raise Exception

        name_output = "{PROCESS}".format(PROCESS=process)
        if len(properties) == 8:
            systematic = properties[7]
            name_output += "_" + systematic

        if name in hist_map[channel][category].keys():
            continue

        hist_map[channel][category][name] = name_output

        if debug > 1:
            print 'name:', name, '\n\tproperties:',
            pp.pprint(properties)
            print '\tchannel:', channel
            print '\tcategory:', category
            print '\tprocess:', process
            print '\tanalysis:', properties[3]
            print '\tperiod:', properties[4]
            print '\tvariable:', properties[5]
            print '\tmass:', properties[6]
            print '\tname_output:', name_output
            print '\thist_map[et]:', hist_map['et']
            exit(1)

    print 'categories in the root file: ', hist_map,
    pp.pprint(hist_map['et'].keys())

    # if debug:
    #     print '0jet_dm0_for_wjets_mc'
    #     pp.pprint(hist_map['et']['0jet_dm0_for_wjets_mc'])
    #     print '0jet_dm0_ss_for_qcd'
    #     pp.pprint(hist_map['et']['0jet_dm0_ss_for_qcd'])
    #     print '0jet_dm0'
    #     pp.pprint(hist_map['et']['0jet_dm0'])


def convertToSynced(input_path='', output_dir='', debug=False):
    # Open input ROOT file and output ROOT file
    if len(input_path) > 5 and input_path[-5:] == '.root':
            pass
    else:
        input_path = "{}.root".format(input_path)

    print 'Input:', input_path
    input_file = ROOT.TFile(input_path, 'read')

    # Loop over shapes of input ROOT file and create map of input/output names
    hist_map = {}
    constructMap(hist_map=hist_map, input_file=input_file, debug=debug)

    # if debug:
    #     checkDM(hist_map)

    check = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT"]
    known_categories = map_pipes.keys()
    for channel in hist_map:
        print 'channel:', channel
        if output_dir == "":
            output_dir = os.path.join(os.getcwd(), "converted_shapes", input_path.split('/')[-1].split('.root')[0])
        output_file_name = os.path.join(output_dir, "htt_{CHANNEL}.inputs-etFes.root").format(CHANNEL=channel)
        print 'output:', output_file_name

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        output_file = ROOT.TFile(output_file_name, "RECREATE")

        if len(intersection(known_categories, hist_map[channel].keys())) == 0:
            print 'No registered as known categories are found. Known:'
            pp.pprint(known_categories)
            print "found:"
            pp.pprint(hist_map[channel])
        else:
            print "Intersection:", intersection(known_categories, hist_map[channel].keys())

        for category in intersection(known_categories, hist_map[channel].keys()):
            print 'category:', category, '...'
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

                if name_output in check:
                    check.remove(name_output)

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

            print "check:", check

        output_file.Close()

    # Clean-up
    input_file.Close()
    print 'done'
    return output_file_name


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("convert_synced_shapes.log", logging.DEBUG)
    convertToSynced(input_path=args.input[0], output_dir=args.output, debug=args.debug, variables=args.variables)
