#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 python convert_to_synced_shapes.py \
    --input etFes_2017_all_shapes.root \
    --output converted_shapes

 python shapes/convert_to_synced_shapes.py \
    --input   /ceph/ohlushch/shapes/FES/ET/v3_noele27/shapes/2017_etFes_Legacy_FES_noupdate_QCDSStoOS_woFR.root \
    --output /ceph/ohlushch/shapes/FES/ET/v3_noele27/sconverted_shapes \
    --variables m_vis --debug

 python shapes/convert_to_synced_shapes.py \
    --input /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/all_categories/htcondor/all_categories_ff_2/shapes_merged_split/htt_mt.inputs-mssm-vs-sm-2017-mt_tot_puppi.root \
    --output  /nfs/dust/cms/user/glusheno/shapes/MSSM/mva/all_categories/htcondor/all_categories_ff_2/converted_shapes_merged_split \
    --variables mt_tot_puppi --same-name # --debug


 # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
"""
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser

import argparse
import os
import pprint
pp = pprint.PrettyPrinter(indent=4)
import numpy
import logging
logger = logging.getLogger("")

intersection = lambda x, y: list(set(x) & set(y))

bins = [0.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0, 160.0, 165.0, 170.0, 175.0, 180.0, 185.0, 190.0, 195.0, 200.0, 205.0, 210.0, 215.0, 220.0, 225.0, 230.0, 235.0, 240.0, 245.0, 250.0, 260.0, 270.0, 280.0, 290.0, 300.0, 310.0, 320.0, 330.0, 340.0, 350.0, 360.0, 370.0, 380.0, 390.0, 400.0, 410.0, 420.0, 430.0, 440.0, 450.0, 460.0, 470.0, 480.0, 490.0, 500.0, 525.0, 550.0, 575.0, 600.0, 625.0, 650.0, 675.0, 700.0, 725.0, 750.0, 775.0, 800.0, 825.0, 850.0, 875.0, 900.0, 925.0, 950.0, 975.0, 1000.0, 1050.0, 1100.0, 1150.0, 1200.0, 1250.0, 1300.0, 1350.0, 1400.0, 1450.0, 1500.0, 1550.0, 1600.0, 1650.0, 1700.0, 1750.0, 1800.0, 1850.0, 1900.0, 1950.0, 2000.0, 2100.0, 2200.0, 2300.0, 2400.0, 2500.0, 2600.0, 2700.0, 2800.0, 2900.0, 3000.0, 3100.0, 3200.0, 3300.0, 3400.0, 3500.0, 3600.0, 3700.0, 3800.0, 3900.0, 4000.0, 4100.0, 4200.0, 4300.0, 4400.0, 4500.0, 4600.0, 4700.0, 4800.0, 4900.0, 5000]
x = numpy.array(bins)

dict_replace_proc = {
    'SUSY': '',
    'Run': '',
    'QCDEM': 'QCD',
    'jetFakesLT': 'jetFakes',
    'jetFakesTT': 'jetFakes',
    'CMS_prefiring_Run2016': 'CMS_prefiring',
    'CMS_prefiring_Run2017': 'CMS_prefiring',
    'CMS_prefiring_Run2018': 'CMS_prefiring',
    'CMS_eff_trigger_mt_Run': 'CMS_eff_trigger_mt_',
    'CMS_eff_xtrigger_mt_Run': 'CMS_eff_xtrigger_mt_',
    'CMS_eff_trigger_et_Run': 'CMS_eff_trigger_et_',
    'CMS_eff_xtrigger_et_Run': 'CMS_eff_xtrigger_et_',
    'CMS_htt_eff_b_Run': "CMS_htt_eff_b_",
    'CMS_htt_mistag_b_Run': 'CMS_htt_mistag_b_',
    'CMS_scale_t_1prong_Run': 'CMS_scale_t_1prong_',
    'CMS_scale_t_1prong1pizero_Run': 'CMS_scale_t_1prong1pizero_',
    'CMS_scale_t_3prong_Run': 'CMS_scale_t_3prong_',
    'CMS_htt_boson_reso_met': 'CMS_htt_boson_res_met',  # comm
    'CMS_scale_mc_e': 'CMS_scale_e',
    'CMS_reso_mc_e': 'CMS_res_e',

    "CMS_ff_tt_njet1_stat_et_": "CMS_ff_tt_njet1_stat_",
    "CMS_ff_tt_njet1_stat_mt_": "CMS_ff_tt_njet1_stat_",
    # "CMS_ff_w_syst_et": "CMS_ff_w_syst",
    # "CMS_ff_w_syst_mt": "CMS_ff_w_syst",
    # "CMS_ff_tt_syst_et": "CMS_ff_tt_syst",
    # "CMS_ff_tt_syst_mt": "CMS_ff_tt_syst",

}

dict_replace_dirs = {
    'wjets_control_1': 'wjets_control',
    'mt_1_tight_nbtag_zero': 'nobtag_tightmt',
    'mt_1_loose_nbtag_zero': 'nobtag_loosemt',
    'mt_1_tight_nbtag_nonzero': 'btag_tightmt',
    'mt_1_loose_nbtag_nonzero': 'btag_loosemt',
    # # em
    'ttbar_control_2': 'ttbar_control',  # (pZetaMissVis<=-50)'
    # 'ttbar_control_1': 'ttbar_control',  # (pZetaMissVis<=-35)'
    'dzeta_high_nbtag_zero': 'nobtag_highdzeta',
    'dzeta_high_nbtag_nonzero': 'btag_highdzeta',
    'dzeta_medium_nbtag_zero': 'nobtag_mediumdzeta',
    'dzeta_medium_nbtag_nonzero': 'btag_mediumdzeta',
    'dzeta_low_nbtag_zero': 'nobtag_lowdzeta',
    'dzeta_low_nbtag_nonzero': 'btag_lowdzeta',
    'btag': 'nbtag_nonzero',
    'nobtag': 'nbtag_zero',
}

# wrt the collection after the replacement
dict_copy_proc = {
    'CMS_htt_dyShape_2017': ['CMS_htt_dyShape'],
    'CMS_htt_dyShape_2018': ['CMS_htt_dyShape'],
}
bases = [
    'CMS_ff_qcd_syst',
    'CMS_ff_tt_njet1_stat',
    'CMS_ff_w_syst',
    'CMS_ff_tt_syst',
]

for base in bases:
    for year in ['2016', '2017', '2018']:
        for channel in ['et', 'mt', 'tt']:
            dict_copy_proc["{SYST}_{CH}_{ERA}".format(SYST=base, CH=channel, ERA=year)] = [
                "{SYST}_{CH}".format(SYST=base, CH=channel),
                "{SYST}_{ERA}".format(SYST=base, ERA=year),
                "{SYST}".format(SYST=base),
            ]
# temp : create copies of shapes for combine
basestemp = [
    'CMS_ff_qcd',
    # 'CMS_ff_tt_njet1_stat',
    'CMS_ff_w',
    'CMS_ff_tt',
]
for base in basestemp:
    for year in ['2016', '2017', '2018']:
        for channel in ['tt']:
            dict_copy_proc["{SYST}_{CH}_syst_{ERA}".format(SYST=base, CH=channel, ERA=year)] = [
                "{SYST}_syst_{CH}_{ERA}".format(SYST=base, CH=channel, ERA=year),
                "{SYST}_syst_{CH}".format(SYST=base, CH=channel),
                "{SYST}_syst_{ERA}".format(SYST=base, ERA=year),
                "{SYST}_syst".format(SYST=base),
            ]
for base in ['CMS_ff_tt_njet1', 'CMS_ff_qcd_njet0', 'CMS_ff_qcd_njet1']:
    for year in ['2016', '2017', '2018']:
        for channel in ['tt']:
            dict_copy_proc["{SYST}_{CH}_stat_{ERA}".format(SYST=base, CH=channel, ERA=year)] = [
                "{SYST}_stat_{CH}_{ERA}".format(SYST=base, CH=channel, ERA=year),
                "{SYST}_stat_{CH}".format(SYST=base, CH=channel),
                "{SYST}_stat_{ERA}".format(SYST=base, ERA=year),
                "{SYST}_stat".format(SYST=base),
            ]
for base in ['CMS_scale_met_unclustered',
             'CMS_scale_t_1prong', 'CMS_scale_t_1prong1pizero', 'CMS_scale_t_3prong']:
    for year in ['2016', '2017', '2018']:
        dict_copy_proc["{SYST}_{ERA}".format(SYST=base, ERA=year)] = [
            "{SYST}".format(SYST=base),
        ]




fes_shifts_indicators = {
    'TauEsInclusiveShift': 'alldm',
    'TauEsOneProngShift': 'dm0',
    'TauEsOneProngPiZerosShift': 'dm1',
    'TauEsThreeProngShift': 'dm10',
}


# fes_shifts_indicators = {
#     'TauEsInclusiveShift_13TeV_': 'alldm',
#     'TauEsOneProngShift_13TeV_': 'dm0',
#     'TauEsOneProngPiZerosShift_13TeV_': 'dm1',
#     'TauEsThreeProngShift_13TeV_': 'dm10',
# }


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # file_handler = logging.FileHandler(output_file, "w")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert shapes from the shape producer to the sync format."
    )

    parser.add_argument('--input-file', '-i', type=str, nargs=1, help='Path to single input ROOT file.')
    parser.add_argument('--output-dir', default="", type=str, help='Output directory')
    # parser.add_argument('--variables', '-v', type=str, nargs='*', default=['m_vis', 'njets_mvis', 'dm_mvis'], help='variables.')
    parser.add_argument('--variables', '-v', type=str, nargs='*', default=None, help='variables.')
    parser.add_argument('--debug', default=0, action="store_const", const=1, help="Debug option [Default: %(default)s]")
    parser.add_argument('--same-name', default=False, action="store_true", help="Store ander the same name [Default: %(default)s]")
    parser.add_argument('--var-in-name', default=False, action="store_true", help="Store ander the same name [Default: %(default)s]")

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
    found_variables = set() if variables is None else set(variables)

    for key in input_file.GetListOfKeys():
        name = key.GetName()
        if key.GetClassName() == 'TTree':
            continue


        properties = [x for x in name.split("#") if not x == ""]

        if variables is None:
            found_variables.add(properties[5])
        elif properties[5] not in variables:
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

    return found_variables


# import pdb; pdb.set_trace()  # \!import code; code.interact(local=vars())
# input_path=args.input[0], output_dir=args.output, debug=args.debug, variables=args.variables)
def convertToSynced(variables, input_path, output_dir='', debug=False, same_name=False, var_in_name=False):
    # Open input ROOT file and output ROOT file
    if len(input_path) > 5 and input_path.endswith('.root'):
        pass
    else:
        input_path = "{}.root".format(input_path)

    logger.info('Input file: %s' % input_path)
    input_file = ROOT.TFile(input_path, 'read')

    # Loop over shapes of input ROOT file and create map of input/output names
    hist_map = {}
    found_variables = constructMap(hist_map=hist_map, input_file=input_file, debug=debug, variables=variables)

    if variables is None:
        logger.info('Found variables: %s' % list(found_variables))

    if hist_map == {}:
        return None
    # if debug: checkDM(hist_map)

    # Each channel belongs to a different output file
    for channel in hist_map:
        logger.info('channel: %s' % channel)
        if channel == 'et':
            check_if_missing = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT", "jetFakesLT"]
        elif channel == 'mt':
            check_if_missing = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT", "jetFakesLT"]
        elif channel == 'tt':
            check_if_missing = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT", "jetFakesTT"]
        elif channel == 'em':
            check_if_missing = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT"]
        else:
            check_if_missing = ["W", "QCD", "ZJ", "TTT", "TTJ", "VVT", "VVJ", "ZTT", "jetFakesLT", "jetFakesTT"]

        if output_dir == "":
            if not os.path.isdir("converted_shapes"):
                os.makedirs("converted_shapes")
            output_dir = os.path.join(os.getcwd(), "converted_shapes", input_path.split('/')[-1].split('.root')[0])
        # TODO: check if now made it encode the input file name properly
        output_file_name = os.path.join(output_dir, input_path.split('/')[-1].split('.root')[0] + '{CONVERTED}.root'.format(CHANNEL=channel, CONVERTED='' if same_name else '_%s_converted' % ('_'.join([channel] + args.variables) if var_in_name else channel)))
        if os.path.normpath(os.path.dirname(input_path)) == os.path.normpath(output_dir):
            if same_name:
                raise Exception("Converted files are required to have same name but input and output deirectories are the same: %s" % output_dir)
            else:
                logger.critical("The converted and unconvertd shapes land in the same directory!")
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
            if category.endswith("_ss") or category.endswith("_B") or category.endswith('_for_wjets_mc'):
                if debug:
                    print
                logger.debug('Category: %s ...\t skipped as the shape belongs to bg est.' % category)
                continue
            print
            logger.info('Category: %s' % category if category not in dict_replace_dirs.keys() else "%s -> %s" % (category, dict_replace_dirs[category]))

            # Each channel*category belongs to a different dir
            output_file.cd()
            dir_name = "{CHANNEL}_{CATEGORY}".format(CHANNEL=channel, CATEGORY=category if category not in dict_replace_dirs.keys() else dict_replace_dirs[category])
            output_file.mkdir(dir_name)
            output_file.cd(dir_name)

            output_names = []
            for name in hist_map[channel][category]:
                logger.debug('name: %s ...' % name)
                hist = input_file.Get(name)

                name_output = hist_map[channel][category][name]
                name_output = name_output.replace('QCDSStoOS', 'QCD')

                # Check the expected mapping of pipelines and categories
                if '_fes_' in name_output and not any(lambda f, v: v in category and f in name_output for f, v in fes_shifts_indicators.iteritems()):
                    logger.debug('Skipping FES shifts that should not belong to the limited dm/njets category: %s' % name_output)
                    # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                    continue

                elif '_fes_' in name_output:
                    if 'Run2016' in name_output:
                        year = 'Run2016_'
                    elif 'Run2017' in name_output:
                        year = 'Run2017_'
                    elif 'Run2018' in name_output:
                        year = 'Run2018_'
                    else:
                        year = '13TeV_'

                    new_name = name_output
                    for f in fes_shifts_indicators:
                        if f in new_name:
                            new_name = '_'.join([new_name.split('_')[0], new_name.split('_'.join([f, year]))[-1]])
                            break
                    logger.debug('Replacing when converting: %s -> %s' % (name_output, new_name))
                    name_output = new_name

                else:
                    logger.debug('Replacing when converting: %s -> %s' % (hist_map[channel][category][name], name_output.replace(category, '')))
                    name_output = name_output.replace(category, '')

                if name_output in check_if_missing:
                    check_if_missing.remove(name_output)

                # only for FES
                # # the nominal ZL should be treated as ZL_0
                # if 'ZL' == name_output:
                #     name_output += '_0'

                if 'ZL_' in name_output and not name_output.endswith('Up') and not name_output.endswith('Down'):
                    old_name_output = name_output
                    name_output = name_output.replace('_neg', '_-')
                    for i in range(0, 10):
                        if 'p' not in name_output and '.' not in name_output and name_output != 'ZL_0':
                            logger.warning('\t name %s adding p0' % (name_output))
                            name_output += 'p0'
                        name_output = name_output.replace(str(i) + 'p', str(i) + '.')
                    logger.debug('FES:Replacing when converting: %s -> %s' % (old_name_output, name_output))

                # rename the processes as expected by combine
                for a, b in dict_replace_proc.iteritems():
                    if a in name_output:
                        old_name_output = name_output
                        name_output = name_output.replace(a, b)
                        logger.debug('Replacing when converting: %s -> %s' % (old_name_output, name_output))

                # copy histograms for decorrelations in combine
                nonshifted_name_output = name_output.replace('Up', '').replace('Down', '')
                for a, b1 in dict_copy_proc.iteritems():
                    if a in nonshifted_name_output:
                        for b in b1:
                            extra_name_output = name_output.replace(a, b)
                            logger.debug('Extra histogram when converting: %s -> %s' % (name_output, extra_name_output))

                            output_names.append(extra_name_output)
                            # Store the histogram in the root file
                            if '#mt_tot#' in name or '#mt_tot_puppi#' in name:
                                tmp = hist.Rebin(len(bins) - 1, extra_name_output, x)
                            else:
                                tmp = hist
                            tmp.SetTitle(extra_name_output)
                            tmp.SetName(extra_name_output)
                            tmp.Write()
                output_names.append(name_output)

                # Store the histogram in the root file
                if '#mt_tot#' in name or '#mt_tot_puppi#' in name:
                    tmp = hist.Rebin(len(bins) - 1, name_output, x)
                else:
                    tmp = hist
                tmp.SetTitle(name_output)
                tmp.SetName(name_output)
                tmp.Write()

            output_names.sort()
            logger.debug('names: [%s]' % ', '.join(output_names))
            logger.warning("Standart processes that were not found: " + " ".join(check_if_missing))

        output_file.Close()

    input_file.Close()
    logger.info('Done convertion')
    return output_file_name


if __name__ == "__main__":
    import logging
    from rootpy import log
    # log.setLevel(log.INFO)
    from rootpy.logger.magic import DANGER
    DANGER.enabled = True  # set True to raise exceptions

    args = parse_arguments()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        # setup_logging("convert_synced_shapes.log", logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        # setup_logging("convert_synced_shapes.log", logging.INFO)
    if args.variables is not None:
        logger.debug('Converted variables: ' + ' '.join(args.variables))
    else:
        logger.warning('Converting all found variables.')
    print "Converted shapes:", convertToSynced(
        input_path=args.input_file[0],
        output_dir=args.output_dir,
        debug=args.debug,
        variables=args.variables,
        same_name=args.same_name,
        var_in_name=args.var_in_name,
    )
