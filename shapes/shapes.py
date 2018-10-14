# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
"""
"""
import argparse

"""Script to copy files after the skim from * to nfs."""
# import os
# import subprocess
import pprint
pp = pprint.PrettyPrinter(indent=4)
# import tempfile
# import hashlib


class Shapes(object):
    def __init__(self,
                 ofset=0,
                 directory=None,
                 datasets=None,
                 binning=None,
                 backend=None,
                 channels=None,
                 debug=None,
                 dry=None,
                 era=None,
                 et_friend_directory=None,
                 fake_factor_friend_directory=None,
                 gof_channel=None,
                 gof_variable=None,
                 mt_friend_directory=None,
                 num_threads=None,
                 skip_systematic_variations=None,
                 tag=None,
                 tt_friend_directory=None,
                 **kwargs):
        self.ofset = ofset
        self.directory = directory
        self.datasets = datasets
        self.binning = binning
        self.backend = backend
        self.channels = channels
        self.debug = debug
        self.dry = dry
        self.era = era
        self.et_friend_directory = et_friend_directory
        self.fake_factor_friend_directory = fake_factor_friend_directory
        self.gof_channel = gof_channel
        self.gof_variable = gof_variable
        self.mt_friend_directory = mt_friend_directory
        self.num_threads = num_threads
        self.skip_systematic_variations = skip_systematic_variations
        self.tag = tag
        self.tt_friend_directory = tt_friend_directory

        self.__dict__.update(kwargs)

        assert type(directory) is None, "Shapes::directory not set"
        assert type(datasets) is None, "Shapes::datasets not set"
        assert type(binning) is None, "Shapes::binning not set"

    def __str__(self):
        logger.debug("Shapes ofset:", self.ofset)
        print "ofset", self.ofset
        output = (
            self.ofset * "\t" + " Shapes(" + "\n" +
            self.ofset * "\t" + "    debug = " + str(self.debug) + "\n" +
            self.ofset * "\t" + " )"
        )
        return output

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description='shapes.py parser')
        parser.add_argument("--directory", required=True, type=str, help="Directory with Artus outputs.")
        parser.add_argument("--datasets", required=True, type=str, help="Kappa datsets database.")
        parser.add_argument("--binning", required=True, type=str, help="Binning configuration.")

        parser.add_argument("--channels", default=[], nargs='+', type=str, help="Channels to be considered.")
        parser.add_argument("--era", type=str, help="Experiment era.")
        parser.add_argument("--gof-channel", default=None, type=str, help="Channel for goodness of fit shapes.")
        parser.add_argument("--gof-variable", type=str, help="Variable for goodness of fit shapes.")
        parser.add_argument("--num-threads", default=32, type=int, help="Number of threads to be used.")
        parser.add_argument("--backend", default="classic", choices=["classic", "tdf"], type=str, help="Backend. Use classic or tdf.")
        parser.add_argument("--tag", default="ERA_CHANNEL", type=str, help="Tag of output files.")
        parser.add_argument("--skip-systematic-variations", default=False, type=str, help="Do not produce the systematic variations.")

        parser.add_argument("--et-friend-directory", default=None, type=str, help="Directory containing a friend tree for et.")
        parser.add_argument("--mt-friend-directory", default=None, type=str, help="Directory containing a friend tree for mt.")
        parser.add_argument("--tt-friend-directory", default=None, type=str, help="Directory containing a friend tree for tt.")
        parser.add_argument("--fake-factor-friend-directory", default=None, type=str, help="Directory containing friend trees to data files with FF.")

        parser.add_argument('--dry', action='store_true', default=False, help='dry run')
        parser.add_argument('--debug', action='store_true', default=False, help='cherry-debug')

        args = parser.parse_args()
        return vars(args)

    @staticmethod
    def setup_logging(output_file, level=logging.DEBUG):
        logger.setLevel(level)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        file_handler = logging.FileHandler(output_file, "w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def run(self):
        pass


if __name__ == '__main__':
    args = Shapes.parse_arguments()
    shapes = Shapes(**args)
    print shapes
    shapes.run()
