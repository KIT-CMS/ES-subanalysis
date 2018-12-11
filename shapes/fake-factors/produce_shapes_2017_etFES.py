#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser
ROOT.gErrorIgnoreLevel = ROOT.kError

from shape_producer.cutstring import Cut, Cuts
from shape_producer.systematics import Systematics, Systematic
from shape_producer.categories import Category
from shape_producer.binning import VariableBinning
from shape_producer.variable import Variable
from shape_producer.systematic_variations import Nominal
from shape_producer.process import Process
from shape_producer.channel import ETSM2017

from itertools import product
import os
import argparse
import yaml

import logging
logger = logging.getLogger()


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
        description="Produce single bin histograms to determine fake factor fractions")

    parser.add_argument(
        "--directory",
        required=True,
        type=str,
        help="Directory with Artus outputs.")
    parser.add_argument(
        "--et-friend-directory",
        default=[],
        type=str,
        help="Directory arranged as Artus output and containing a friend tree for et."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to store output shapes root-files.")

    parser.add_argument(
        "--config",
        required=True,
        type=str,
        help="Key of desired config in yaml config file.")
    parser.add_argument(
        "--datasets", required=True, type=str, help="Kappa datsets database.")
    parser.add_argument("--era", type=str, help="Experiment era.")
    parser.add_argument(
        "--num-threads",
        default=1,
        type=int,
        help="Number of threads to be used.")
    parser.add_argument(
        "--backend",
        default="classic",
        choices=["classic", "tdf"],
        type=str,
        help="Backend. Use classic or tdf.")
    parser.add_argument(
        "--tag", default="ERA_CHANNEL", type=str, help="Tag of output files.")
    parser.add_argument(
        "--decay-mode", default=None, type=str, nargs='*', help="dm for categorisation")

    return parser.parse_args()


def produce_shapes_2017_etFES(args):
    # Container for all distributions to be drawn
    logger.info("Set up shape variations.")

    # Read configs from yaml
    config = yaml.load(open("data/ff_config.yaml"))
    if args.config not in config['etau_fes'].keys():
        logger.critical("Requested config key %s not available in data/ff_config.yaml!" % args.config)
        raise Exception
    config = config['etau_fes'][args.config]

    # Read known cuts
    _known_cuts = yaml.load(open('data/known_cuts.yaml'))

    if args.decay_mode is None:
        dm_splitting = _known_cuts['decay_mode'].keys()
    else:
        dm_splitting = args.decay_mode

    # Prepare output dir
    output_dir = config['outputdir']
    if args.output_dir is not None:
        output_dir = args.output_dir
    if not os.path.exists(output_dir):
        print "Creating output directory.."
        os.makedirs(output_dir)
    output_file_path = str(os.path.join(output_dir, "{}_ff_yields.root".format(args.tag)))
    print "Output file path:", output_file_path

    systematics = Systematics(output_file_path, num_threads=args.num_threads)

    # Era selection
    if "2017" in args.era:
        from shape_producer.estimation_methods_Fall17 import (
            DataEstimation,
            # ZTTEmbeddedEstimation,
            ZTTEstimation, ZLEstimation, ZJEstimation,
            TTLEstimation, TTJEstimation, TTTEstimation,
            VVLEstimation, VVTEstimation, VVJEstimation,
            WEstimation,
        )
        from shape_producer.era import Run2017
        era = Run2017(args.datasets)
    else:
        logger.critical("Era {} is not implemented.".format(args.era))
        raise Exception

    # Channels and processes
    # yapf: disable
    directory = args.directory
    et_friend_directory = args.et_friend_directory

    et = ETSM2017()
    et.cuts.remove("tau_iso")
    et.cuts.add(Cut("(byTightIsolationMVArun2017v2DBoldDMwLT2017_2<0.5 && byVLooseIsolationMVArun2017v2DBoldDMwLT2017_2>0.5)", "tau_anti_iso"))

    # Parts necessary to correspond to the analysis
    et.cuts.add(Cut("mt_1 < 70", "mt"))
    et.cuts.remove("dilepton_veto")
    et.cuts.remove('trg_selection')
    et.cuts.add(Cut("(trg_singleelectron_27 == 1) || (trg_singleelectron_32 == 1) || (trg_singleelectron_35) || (trg_crossele_ele24tau30 == 1) || (isEmbedded && pt_1>20 && pt_1<24)", "trg_selection"))

    et_processes = {
        "data"  : Process("data_obs", DataEstimation      (era, directory, et, friend_directory=et_friend_directory)),
        "ZTT"   : Process("ZTT",      ZTTEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "ZJ"    : Process("ZJ",       ZJEstimation        (era, directory, et, friend_directory=et_friend_directory)),
        "ZL"    : Process("ZL",       ZLEstimation        (era, directory, et, friend_directory=et_friend_directory)),
        "TTT"   : Process("TTT",      TTTEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "TTJ"   : Process("TTJ",      TTJEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "TTL"   : Process("TTL",      TTLEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "VVT"   : Process("VVT",      VVTEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "VVJ"   : Process("VVJ",      VVJEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "VVL"   : Process("VVL",      VVLEstimation       (era, directory, et, friend_directory=et_friend_directory)),
        "W"     : Process("W",        WEstimation         (era, directory, et, friend_directory=et_friend_directory))
    }

    et_categories = [
        Category(
            "inclusive",
            et,
            Cuts(),
            variable=Variable(args.config, VariableBinning(config["et"]["binning"]), config["et"]["expression"])
        ),
    ]

    for njet in _known_cuts['jets_multiplicity'].keys():
        for dm in dm_splitting:
            et_categories.append(
                Category(
                    name=njet + '_' + dm,
                    channel=et,
                    cuts=Cuts(
                        Cut(_known_cuts['decay_mode'][dm], dm),
                        Cut(str(_known_cuts['jets_multiplicity'][njet]), str(njet)),
                    ),
                    variable=Variable(args.config, VariableBinning(config["et"]["binning"]), config["et"]["expression"])
                )
            )

    # et_categories = [
    #     Category(
    #         "njet0_dm1",
    #         et,
    #         Cuts(Cut('decayMode_2==1', 'dm1'), Cut('njets==0', 'njet0')),
    #         variable=Variable(args.config, VariableBinning(config["et"]["binning"]), config["et"]["expression"])
    #     ),
    # ]
    # Nominal histograms
    # yapf: enable
    for process, category in product(et_processes.values(), et_categories):
        systematics.add(
            Systematic(
                category=category,
                process=process,
                analysis="smhtt",
                era=era,
                variation=Nominal(),
                mass="125"
            )
        )

    # Produce nominal histograms
    logger.info("Start producing nominal shapes.")
    systematics.produce()
    logger.info("Done producing nominal shapes.")


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("{}_produce_shapes_etFES.log".format(args.tag), logging.INFO)
    produce_shapes_2017_etFES(args)
