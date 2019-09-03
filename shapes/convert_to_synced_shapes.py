#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 python convert_to_synced_shapes.py --input etFes_2017_all_shapes.root --output converted_shapes
 python shapes/convert_to_synced_shapes.py --input /ceph/ohlushch/shapes/FES/shapes/etFes_Legacy_FES_with_EMB_QCDSStoOS.root --output /ceph/ohlushch/shapes/FES/converted_shapes/converted_shapes --variables m_vis
 # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
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

fes_shifts_indicators = {
    'TauEsInclusiveShift_13TeV_': 'alldm',
    'TauEsOneProngShift_13TeV_': 'dm0',
    'TauEsOneProngPiZerosShift_13TeV_': 'dm1',
    'TauEsThreeProngShift_13TeV_': 'dm10',
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

    parser.add_argument('--input-file', '-i', type=str, nargs=1, help='Path to single input ROOT file.')
    parser.add_argument('--output-dir', default="", type=str, help='Output directory')
    parser.add_argument('--variables', '-v', type=str, nargs='*', default=['m_vis', 'njets_mvis', 'dm_mvis'], help='variables.')
    parser.add_argument('--debug', default=0, action="store_const", const=1, help="Debug option [Default: %(default)s]")

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


def constructMap(hist_map, variables, input_file, debug=0):
    """
    Read name and extract shape properties
    """
    for key in input_file.GetListOfKeys():
        name = key.GetName()
        if key.GetClassName() == 'TTree':
            continue
        properties = [x for x in name.split("#") if not x == ""]

        if properties[5] not in variables:
            logger.debug('skip variable: %s' % properties[5])
            continue

        # Extract properties from name
        category = properties[1][3:]  # remove ${CHANNEL}_ from it)
        channel = properties[0]
        process = properties[2]

        # Check that in the mapping of the names the channel and category is present
        hist_map[channel] = {} if channel not in hist_map else hist_map[channel]
        hist_map[channel][category] = {} if category not in hist_map[channel] else hist_map[channel][category]

        # Push name of a histogram to the dict
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

    if debug > 1:
        print 'categories in the root file: '
        pp.pprint(hist_map)


# import pdb; pdb.set_trace()  # \!import code; code.interact(local=vars())
# input_path=args.input[0], output_dir=args.output, debug=args.debug, variables=args.variables)
def convertToSynced(variables, input_path, output_dir='', debug=False):
    # Open input ROOT file and output ROOT file
    if len(input_path) > 5 and input_path.endswith('.root'):
            pass
    else:
        input_path = "{}.root".format(input_path)

    logger.info('Input file: %s' % input_path)
    input_file = ROOT.TFile(input_path, 'read')

    # Loop over shapes of input ROOT file and create map of input/output names
    hist_map = {}
    constructMap(hist_map=hist_map, input_file=input_file, debug=debug, variables=variables)
    if hist_map == {}:
        return None
    # if debug: checkDM(hist_map)

    check_if_missing = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT"]
    # Each channel belongs to a different output file
    for channel in hist_map:
        logger.debug('channel: %s' % channel)

        if output_dir == "":
            if not os.path.isdir("converted_shapes"):
                os.makedirs("converted_shapes")
            output_dir = os.path.join(os.getcwd(), "converted_shapes", input_path.split('/')[-1].split('.root')[0])
        # TODO: check if now made it encode the input file name properly
        output_file_name = os.path.join(output_dir, input_path.split('/')[-1].split('.root')[0] + '_{CHANNEL}_converted.root'.format(CHANNEL=channel))
        logger.info('output: %s' % output_file_name)

        if not os.path.exists(output_dir):
            if os.pardir not in output_dir:
                os.makedirs(output_dir)
            else:
                try:
                    os.mkdir(output_dir)
                except:
                    raise Exception("Couldn't create output dir for the converted shapes %s. Try removing '..' from the path." % output_dir)

        output_file = ROOT.TFile(output_file_name, "RECREATE")

        for category in hist_map[channel].keys():
            logger.debug('category: %s ...' % category)

            if category.endswith("_ss") or category.endswith("_B") or category.endswith('_for_wjets_mc'):
                logger.warning('\t skipped as bg est.')
                continue

            # Each channel*category belongs to a different dir
            output_file.cd()
            dir_name = "{CHANNEL}_{CATEGORY}".format(CHANNEL=channel, CATEGORY=category)
            output_file.mkdir(dir_name)
            output_file.cd(dir_name)

            for name in hist_map[channel][category]:
                logger.debug('name: %s ...' % name)
                name_output = hist_map[channel][category][name]
                name_output = 'QCD' if name_output.startswith('QCD') else name_output
                name_output = 'W' if name_output.startswith('W') else name_output

                # Check the expected mapping of pipelines and categories
                if '_fes_' in name_output and not any(lambda f, v: v in category and f in name_output for f, v in fes_shifts_indicators.iteritems()):
                    logger.debug('Skipping FES shifts that should not belong to the limited dm/njets category: %s' % name_output)
                    # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                    continue
                elif '_fes_' in name_output:
                    new_name = name_output
                    for f in fes_shifts_indicators:
                        if f in new_name:
                            new_name = new_name.split(f)[-1]
                            break
                    logger.debug('Replacing when converting: %s -> %s' % (name_output, new_name))
                    name_output = new_name
                else:
                    logger.debug('Replacing when converting: %s -> %s' % (name_output, name_output.replace(category, '')))
                    name_output = name_output.replace(category, '')

                if name_output in check_if_missing:
                    check_if_missing.remove(name_output)

                # the nominal ZL should be treated as ZL_0
                if 'ZL' == name_output:
                    name_output += '_0'

                if 'ZL_' in name_output:
                    name_output = name_output.replace('_neg', '_-')
                    name_output = name_output.replace('0p', '0.')
                    name_output = name_output.replace('1p', '1.')
                    name_output = name_output.replace('2p', '2.')
                    name_output = name_output.replace('3p', '3.')

                logger.debug(name_output)

                # Store the histogram in the root file
                hist = input_file.Get(name)
                hist.SetTitle(name_output)
                hist.SetName(name_output)
                hist.Write()

            logger.warning("Standart processes that were not found:" + " ".join(check_if_missing))

        output_file.Close()

    input_file.Close()
    logger.info('Done convertion')
    return output_file_name


if __name__ == "__main__":
    args = parse_arguments()
    if args.debug:
        setup_logging("convert_synced_shapes.log", logging.DEBUG)
    else:
        setup_logging("convert_synced_shapes.log", logging.INFO)
    logger.debug('Converted variables: ' + ' '.join(args.variables))
    print "Converted shapes:", convertToSynced(
        input_path=args.input_file[0],
        output_dir=args.output_dir,
        debug=args.debug,
        variables=args.variables
    )
