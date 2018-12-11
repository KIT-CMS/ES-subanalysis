#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import ROOT
import numpy
import copy
from array import array
from multiprocessing import Pool

import argparse
import logging
logger = logging.getLogger()

import pprint
pp = pprint.PrettyPrinter(indent=4)


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
        description="Calculate fake factors and create friend trees.")
    parser.add_argument(
        "--directory",
        required=True,
        type=str,
        help="Directory with Artus outputs.")
    parser.add_argument(
        "--outputdir",
        type=str,
        help="Directory where ff will be stored.")
    parser.add_argument(
        "--et-friend-directory",
        default=[],
        type=str,
        help="Directory arranged as Artus output and containing a friend tree for et."
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=str,
        help="Key of desired config in yaml config file.")
    parser.add_argument(
        "--et-fake-factor-directory",
        required=True,
        type=str,
        help="Directory containing et fake factor inputs.")
    parser.add_argument(
        "--era", type=str, required=True, help="Experiment era.")
    parser.add_argument(
        "--num-threads",
        default=32,
        type=int,
        help="Number of threads to be used."
    )
    parser.add_argument(
        "--category-mode",
        type=str,
        help="Category mode. If 'inclusive' fake factors are calculated inclusively, otherwise depending on NN categories"
    )
    parser.add_argument(
        "--categories",
        nargs='*', type=str,
        help="Category mode. If 'inclusive' fake factors are calculated inclusively, otherwise depending on NN categories"
    )

    parser.add_argument(
        "--ff-yields",
        type=str,
        default="2017_ff_yields.root",
        help="Category mode. If 'inclusive' fake factors are calculated inclusively, otherwise depending on NN categories"
    )
    parser.add_argument('--apply-ff-per-category', action='store_true', default=False,
        help='use apply_fake_factors_per_category instead of apply_fake_factors')
    parser.add_argument('--test', action='store_true', default=False,
        help='changes the output path')
    parser.add_argument('--dm-splitting', action='store_true', default=False,
        help='if the dm is done for ff')
    parser.add_argument('--no-syst-shifts', action='store_true', default=False,
        help='disable syst shifts')
    return parser.parse_args()


def determine_fractions(args, categories, debug=False):
    # Input shapes
    hist_file = ROOT.TFile(args.ff_yields)

    era_labels = {
        "2016": "Run2016",
        "2017": "Run2017ReReco31Mar"
    }

    composition = {
        "et": {
            "data": ["data_obs"],
            "W": ["W", "VVJ", "ZJ"],
            "TT": ["TTJ"],
            "QCD": ["QCD"],
            "real": ["ZTT", "ZL", "TTT", "TTL", "VVT", "VVL"]
        },
    }

    fractions = {}
    fractions_float = {}
    for channel in categories.keys():
        if debug:
            print "\t channel:", channel
        subdict = {}
        subdict_float = {}

        for category in categories[channel]:
            if debug:
                print "\t\t category:", category
            subsubdict = {}
            subsubdict_float = {}

            # Preper empty histogram for each data/mc compatible with data
            for process_group in composition[channel].keys():
                hist_name = "#{ch}#{ch}_{cat}#data_obs#smhtt#{era}#{expr}#125#".format(
                    ch=channel,
                    cat=category,
                    era=era_labels[args.era],
                    expr=args.config,
                )
                # if debug:
                #     print '\t'*3, 'hist_name:', hist_name

                subsubdict[process_group] = copy.deepcopy(hist_file.Get(hist_name))
                subsubdict[process_group].Reset()
                subsubdict_float[process_group] = [0.0] * (hist_file.Get(hist_name).GetNbinsX() + 2)

            # For all but QCD read their shapes
            # For QCD assighn a shape that is = data_obs - other_proc
            if debug:
                print "\n\t\t For all but QCD read their shapes:"
            for process_group in composition[channel].keys():
                if process_group == "QCD":
                    continue

                if debug:
                    print "\n\t\t\t process_group:", process_group

                for process in composition[channel][process_group]:
                    hist_name = "#{ch}#{ch}_{cat}#{proc}#smhtt#{era}#{expr}#125#".format(
                        ch=channel,
                        cat=category,
                        proc=process,
                        era=era_labels[args.era],
                        expr=args.config
                    )
                    if debug:
                        print "\t" * 4, "hist_name:", hist_name

                    subsubdict[process_group].Add(hist_file.Get(hist_name))
                    for i in range(hist_file.Get(hist_name).GetNbinsX() + 2):
                        if debug: print "\t" * 5, i, '/', hist_file.Get(hist_name).GetNbinsX() + 2, ')', subsubdict_float[process_group][i], '+', hist_file.Get(hist_name).GetBinContent(i), '=',
                        subsubdict_float[process_group][i] += hist_file.Get(hist_name).GetBinContent(i)
                        if debug: print subsubdict_float[process_group][i], '?=', subsubdict[process_group].GetBinContent(i)

                if process_group == "data":
                    if debug:
                        print "\t\t\t QCD += datd "
                    subsubdict["QCD"].Add(subsubdict[process_group], 1.0)
                    for i in range(len(subsubdict_float[process_group])):
                        if debug:
                            print "\t" * 4, i, '/', len(subsubdict_float[process_group]), ')', subsubdict_float["QCD"][i], '+', subsubdict_float[process_group][i], '=',

                        subsubdict_float["QCD"][i] += subsubdict_float[process_group][i]

                        if debug:
                            print subsubdict_float["QCD"][i], '?=', subsubdict["QCD"].GetBinContent(i)
                else:
                    if debug:
                        print "\t\t\t QCD -= ", process_group
                    subsubdict["QCD"].Add(subsubdict[process_group], -1.0)
                    # print 'range:', len(subsubdict_float[process_group])
                    for i in range(len(subsubdict_float[process_group])):
                        if debug:
                            print "\t" * 4, i, '/', len(subsubdict_float[process_group]), ')', subsubdict_float["QCD"][i], '-', subsubdict_float[process_group][i], '=',
                        subsubdict_float["QCD"][i] -= subsubdict_float[process_group][i]
                        if debug:
                            print subsubdict_float["QCD"][i], '?=', subsubdict["QCD"].GetBinContent(i)

            # Normalize all shapes to data eg get fractions of proc wrt data
            if debug:
                print "\n\t\t Normalizing shapes on data"
            denominator_hist = copy.deepcopy(subsubdict["data"])
            data_copy = copy.deepcopy(subsubdict_float['data'])
            for process_group in composition[channel].keys():
                subsubdict[process_group].Divide(denominator_hist)
                if debug:
                    print "\t" * 3, process_group,'...'

                for i in range(len(subsubdict_float[process_group])):
                    if debug: print "\t" * 4, i, '/', len(subsubdict_float[process_group]), ')', subsubdict_float[process_group][i], '/', data_copy[i], '=',
                    if data_copy[i] != 0:
                        subsubdict_float[process_group][i] = subsubdict_float[process_group][i] / data_copy[i]
                    else:
                        subsubdict_float[process_group][i] = 0.0
                    if debug: print subsubdict_float[process_group][i], '?=', subsubdict[process_group].GetBinContent(i)

            # Where QCD bins are negative (i.e. data < MC), scale up other processes
            if debug:
                print "\n\t\t Where QCD bins are negative (i.e. data < MC), scale up other processes"
            for i in range(subsubdict["QCD"].GetNbinsX() + 2):
                qcd_fraction = subsubdict["QCD"].GetBinContent(i)
                qcd_fraction_float = subsubdict_float['QCD'][i]
                print 'Check:', qcd_fraction, '?=', qcd_fraction_float

                if qcd_fraction < 0.0:
                    logger.info(
                        "Found bin with negative QCD process_group (%s, %s, index %i). "
                        "Set QCD process_group to zero and rescale other MC's process_groups up "
                        "so their sum would match data in that bin." % (channel, category, i)
                    )

                    subsubdict["QCD"].SetBinContent(i, 0)
                    subsubdict_float['QCD'][i] = 0
                    for process_group in composition[channel].keys():
                        if not process_group == "data":
                            subsubdict[process_group].SetBinContent(
                                i,
                                subsubdict[process_group].GetBinContent(i) / (1.0 - qcd_fraction)
                            )
                            subsubdict_float[process_group][i] = subsubdict_float[process_group][i] / (1.0 - qcd_fraction_float)
                            logger.debug("Rescaled %s process_group to %f" % (process_group, subsubdict[process_group].GetBinContent(i)))
            subdict[category] = subsubdict
            subdict_float[category] = subsubdict_float

        fractions[channel] = subdict
        fractions_float[channel] = subdict_float

    hist_file.Close()
    return fractions


def apply_fake_factors(config):
    """Needs the nominal pipeline in the Data Artus files"""
    args = config[0]
    datafile = config[1]
    # Determine channel depending on the data file
    if "SingleElectron" in datafile:
        channel = "et"
        ff_file_directory = getattr(args, "%s_fake_factor_directory" % channel)
    else:
        logger.critical("Processing only SingleElectron data!")
        raise Exception
    fractions = config[2]
    categories = config[3][channel]

    unc_shifts = {  # documented in https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauJet2TauFakes
        "et": [
            "ff_qcd_syst",
            "ff_qcd_dm0_njet0_stat", "ff_qcd_dm0_njet1_stat",
            "ff_qcd_dm1_njet0_stat", "ff_qcd_dm1_njet1_stat",
            "ff_w_syst",
            "ff_w_dm0_njet0_stat", "ff_w_dm0_njet1_stat",
            "ff_w_dm1_njet0_stat", "ff_w_dm1_njet1_stat",
            "ff_tt_syst",
            "ff_tt_dm0_njet0_stat", "ff_tt_dm0_njet1_stat",
            "ff_tt_dm1_njet0_stat", "ff_tt_dm1_njet1_stat"
        ]
    }
    tau_indexes = {  # one fake factor per tau is needed
        "et": [2],
    }

    # Prepare Data inputs
    print "Prepare Data inputs:", os.path.join(args.directory, datafile)
    input_file = ROOT.TFile(os.path.join(args.directory, datafile), "READ")
    input_tree = input_file.Get("%s_nominal/ntuple" % channel)

    print 'load fake factors histograms...', ff_file_directory
    ff_file = ROOT.TFile.Open(ff_file_directory)
    ff = ff_file.Get('ff_comb')  # Backtrace warnings can apear because the root files were created with different gcc/cmssw

    # Prepare output directory
    print "...initialize %s" % str(os.path.join(args.output_directory, os.path.dirname(datafile)))
    subdir = os.path.join(args.output_directory, os.path.dirname(datafile))
    if not os.path.exists(subdir):
        os.mkdir(subdir)
        logger.info("Createt output sub-directory for:", str(subdir))

    # Creating output files
    output_file = ROOT.TFile(os.path.join(args.output_directory, datafile), "RECREATE")
    output_root_dir = output_file.mkdir("%s_nominal" % channel)
    output_root_dir.cd()
    output_tree = ROOT.TTree("ntuple", "ntuple")

    output_buffer = {}
    print 'Create numpy.zeros to hold nominal FF and systematics shift'
    for tau_index in tau_indexes[channel]:
        output_buffer["nom_%i" % tau_index] = numpy.zeros(1, dtype=float)
        output_tree.Branch(
            "ff%i_nom" % tau_index,
            output_buffer["nom_%i" % tau_index],
            "ff%i_nom/D" % tau_index
        )
        for syst in unc_shifts[channel]:
            for shift in ["up", "down"]:
                output_buffer["%s_%s_%i" % (syst, shift, tau_index)] = numpy.zeros(1, dtype=float)
                output_tree.Branch(
                    "ff%i_%s_%s" % (tau_index, syst, shift),
                    output_buffer["%s_%s_%i" % (syst, shift,
                    tau_index)], "ff%i_%s_%s/D" % (tau_index, syst, shift)
                )

    print 'Fill tree...'
    for event in input_tree:
        for tau_index in tau_indexes[channel]:
            inputs = []

            if args.category_mode == "inclusive":
                cat_index = -1
            else:
                cat_index = 0  # ?

            # cat_index = -1 if args.category_mode == "inclusive" else int(
            #     getattr(event, "%s_max_index" % channel) +
            #     (0.5 * len(categories) if channel == "tt" and tau_index == 2 else 0.0)
            # )

            cat_fractions = fractions[channel][categories[cat_index]]
            varvalue = 0.0

            if args.config == "njets_mvis":
                varvalue = 300.0 * min(event.njets, 2.0) + min(290.0, event.m_vis)
            else:
                varvalue = getattr(event, args.configdict[channel]["expression"])

            bin_index = cat_fractions["data"].GetXaxis().FindBin(varvalue)

            inputs = [
                event.pt_2,
                event.decayMode_2,
                event.njets,
                event.m_vis,
                event.mt_1,
                event.iso_1,
                cat_fractions["QCD"].GetBinContent(bin_index),
                cat_fractions["W"].GetBinContent(bin_index),
                cat_fractions["TT"].GetBinContent(bin_index)
            ]

            nominal_ff = ff.value(len(inputs), array('d', inputs))
            if not (nominal_ff >= 0.0 and nominal_ff <= 999.0):
                nominal_ff = 0.0
            output_buffer["nom_%i" % tau_index][0] = nominal_ff

            for syst in unc_shifts[channel]:
                for shift in ["up", "down"]:

                    shift_ff = ff.value(len(inputs), array('d', inputs), "%s_%s" % (syst, shift))
                    if not (shift_ff >= 0.0 and shift_ff <= 999.0):
                        print syst + shift, '\n', shift_ff, '\n', inputs
                        shift_ff = 0.0

                    output_buffer["%s_%s_%i" % (syst, shift, tau_index)][0] = shift_ff

        output_tree.Fill()

    # save
    output_tree.Write()
    logger.debug("Successfully finished %s" % os.path.join(
        args.output_directory, datafile))

    # clean up
    ff.Delete()
    ff_file.Close()
    # input_friend_file.Close()
    input_file.Close()


def apply_fake_factors_per_category(config):
    """Needs the nominal pipeline in the Data Artus files"""
    args = config[0]
    datafile = config[1]
    # Determine channel depending on the data file
    if "SingleElectron" in datafile:
        channel = "et"
        ff_file_directory = getattr(args, "%s_fake_factor_directory" % channel)
    else:
        logger.critical("Processing only SingleElectron data!")
        raise Exception
    fractions = config[2]
    category = config[3]
    cat_fractions = fractions[channel][category]

    # documented in https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsToTauTauJet2TauFakes
    if args.dm_splitting:
        unc_shifts = {
            "et": [
                "ff_qcd_syst",
                "ff_qcd_dm0_njet0_stat", "ff_qcd_dm0_njet1_stat",
                "ff_qcd_dm1_njet0_stat", "ff_qcd_dm1_njet1_stat",
                "ff_w_syst",
                "ff_w_dm0_njet0_stat", "ff_w_dm0_njet1_stat",
                "ff_w_dm1_njet0_stat", "ff_w_dm1_njet1_stat",
                "ff_tt_syst",
                "ff_tt_dm0_njet0_stat", "ff_tt_dm0_njet1_stat",
                "ff_tt_dm1_njet0_stat", "ff_tt_dm1_njet1_stat"
            ]
        }
    else:
        unc_shifts = {
            "et": [
                "ff_qcd_syst",
                "ff_qcd_dm0_njet0_stat", "ff_qcd_dm0_njet1_stat",
                "ff_w_syst",
                "ff_w_dm0_njet0_stat", "ff_w_dm0_njet1_stat",
                "ff_tt_syst",
                "ff_tt_dm0_njet0_stat", "ff_tt_dm0_njet1_stat",
            ]
        }
    if args.no_syst_shifts:
        unc_shifts = {"et":[]}

    # Prepare Data inputs
    print "Prepare Data inputs:", os.path.join(args.directory, datafile)
    input_file = ROOT.TFile(os.path.join(args.directory, datafile), "READ")
    input_tree = input_file.Get("%s_nominal/ntuple" % channel)

    print 'load fake factors histograms...', ff_file_directory
    ff_file = ROOT.TFile.Open(ff_file_directory)
    ff = ff_file.Get('ff_comb')  # Backtrace warnings can apear because the root files were created with different gcc/cmssw

    # Prepare output
    print "...initialize %s" % str(os.path.join(args.output_directory, category, os.path.dirname(datafile)))
    subdir = os.path.join(args.output_directory, category, os.path.dirname(datafile))

    if not os.path.exists(subdir):
        os.makedirs(subdir)
        print "Created output sub-directory for:", subdir

    # Creating output files
    output_file = ROOT.TFile(os.path.join(args.output_directory, category, datafile), "RECREATE")
    output_root_dir = output_file.mkdir("%s_nominal" % channel)
    output_root_dir.cd()
    output_tree = ROOT.TTree("ntuple", "ntuple")

    tau_indexes = {  # one fake factor per tau is needed
        "et": [2],
    }
    output_buffer = {}
    print 'Create numpy.zeros to hold nominal FF and systematics shift'
    for tau_index in tau_indexes[channel]:
        output_buffer["nom_%i" % tau_index] = numpy.zeros(1, dtype=float)
        output_tree.Branch(
            "ff%i_nom" % tau_index,
            output_buffer["nom_%i" % tau_index],
            "ff%i_nom/D" % tau_index
        )
        for syst in unc_shifts[channel]:
            for shift in ["up", "down"]:
                output_buffer["%s_%s_%i" % (syst, shift, tau_index)] = numpy.zeros(1, dtype=float)
                output_tree.Branch(
                    "ff%i_%s_%s" % (tau_index, syst, shift),
                    output_buffer["%s_%s_%i" % (syst, shift,
                    tau_index)], "ff%i_%s_%s/D" % (tau_index, syst, shift)
                )

    print 'Fill tree...'
    # count = 0
    for event in input_tree:
        # count += 1
        # if count == 100: break
        for tau_index in tau_indexes[channel]:
            inputs = []

            varvalue = 0.0
            if args.config == "njets_mvis":
                varvalue = 300.0 * min(event.njets, 2.0) + min(290.0, event.m_vis)
            elif args.config == "dm_mvis":
                varvalue = 300.0 * min(event.decayMode_2, 3.0) + min(290.0, event.m_vis)
            else:
                varvalue = getattr(event, args.configdict[channel]["expression"])

            bin_index = cat_fractions["data"].GetXaxis().FindBin(varvalue)

            inputs = [
                event.pt_2,
                event.decayMode_2,
                event.njets,
                event.m_vis,
                event.mt_1,
                event.iso_1,
                cat_fractions["QCD"].GetBinContent(bin_index),
                cat_fractions["W"].GetBinContent(bin_index),
                cat_fractions["TT"].GetBinContent(bin_index)
            ]

            nominal_ff = ff.value(len(inputs), array('d', inputs))
            if not (nominal_ff >= 0.0 and nominal_ff <= 999.0):
                nominal_ff = 0.0
            output_buffer["nom_%i" % tau_index][0] = nominal_ff

            for syst in unc_shifts[channel]:
                for shift in ["up", "down"]:
                    shift_ff = ff.value(len(inputs), array('d', inputs), "%s_%s" % (syst, shift))
                    if not (shift_ff >= 0.0 and shift_ff <= 999.0):
                        print syst + shift, '\n', shift_ff, '\n', inputs
                        shift_ff = 0.0

                    output_buffer["%s_%s_%i" % (syst, shift, tau_index)][0] = shift_ff

        output_tree.Fill()

    # save
    output_tree.Write()
    logger.debug("Successfully finished %s" % os.path.join(
        args.output_directory, datafile))

    # clean up
    ff.Delete()
    ff_file.Close()
    # input_friend_file.Close()
    input_file.Close()


def calculate_fake_factors(args):
    config = yaml.load(open("data/ff_config.yaml"))
    if args.config not in config['etau_fes'].keys():
        logger.critical("Requested config key %s not available in data/ff_config.yaml!" % args.config['etau_fes'])
        raise Exception
    if args.category_mode == "inclusive":
        logger.warning("Option to calculate fake factors inclusively has been set. No categorization applied!")

    args.configdict = config['etau_fes'][args.config]

    if args.outputdir is not None:
        args.output_directory = args.outputdir
    else:
        args.output_directory = args.configdict["outputdir"]

    if args.test and args.output_directory[-4:] is not 'test':
        args.output_directory += '_test'

    categories = {
        "et": [
            'njet0_alldm',
            # 'njet0_dm10',
            # 'njet0_dm1',
            # 'njet0_dm0',

            'njetN_alldm',
            # 'njetN_dm10',
            # 'njetN_dm1',
            # 'njetN_dm0',

            # 'inclusive',

            # 'njet0',
            # "inclusive"  # always in the end of the list
        ]
    }
    # categories = {"et": ['njet0_dm1']}  # TEST
    if args.categories:
        categories['et'] = [].extend(args.categories)

    fractions = determine_fractions(args, categories, debug=True)
    pp.pprint(fractions)
    # exit(1)

    # Get paths to Data files the fake factors are appended to
    datafiles = []
    for entry in os.listdir(args.directory):
        if "Run%s" % args.era in entry and ("Single" in entry):
            path = os.path.join(entry, "%s.root" % entry)

            # check whether expected files exist
            if not os.path.isfile(os.path.join(args.directory, path)):
                logger.critical(
                    "Expected file %s does not exist. Check --directory option!"
                )
                raise Exception

            datafiles.append(path)

    # Create output directory
    if os.path.exists(args.output_directory):
        print "Removing output directory:", args.output_directory
        import shutil
        try:
            shutil.rmtree(args.output_directory)
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))
    else:
        print 'Output dir should be created..'
    print "Create output directory:", args.output_directory
    os.mkdir(args.output_directory)

    logger.info("Create friend trees...")
    if args.apply_ff_per_category:
        if args.num_threads == 1:
            pp.pprint(datafiles)
            for category in categories['et']:
                for datafile in datafiles:
                    print "Starting applying FF for:", datafile
                    apply_fake_factors_per_category([args, datafile, fractions, category])
        else:
            # from multiprocessing import Process, Queue
            # processes = []
            # queue = Queue()
            # p = Process(target=apply_fake_factors, args=(args, datafile, fractions, category))
            # p.start()
            # p.join() # this blocks until the process terminates
            # result = queue.get()
            # print result

            import itertools
            nthreads = min(args.num_threads, len(datafiles))
            pool = Pool(processes=nthreads)
            pool.map(apply_fake_factors_per_category,
                [
                    [args, datafile, fractions, category]
                    for datafile, category in list(itertools.product(datafiles, categories['et']))
                ]
            )
            pool.close()
            pool.join()
            del pool
    else:
        if args.num_threads == 1:
            pp.pprint(datafiles)
            for datafile in datafiles:
                print "Starting applying FF for:", datafile
                apply_fake_factors([args, datafile, fractions, categories])
        else:
            nthreads = min(args.num_threads, len(datafiles))
            pool = Pool(processes=nthreads)
            pool.map(apply_fake_factors, [[args, datafile, fractions, categories] for datafile in datafiles])
            pool.close()
            pool.join()
            del pool


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("{}_calculate_fake_factors.log".format(args.era), logging.INFO)
    calculate_fake_factors(args)
