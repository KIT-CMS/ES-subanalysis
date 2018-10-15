# -*- coding: utf-8 -*-

import logging
"""
"""
import argparse
import yaml

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
                 ):
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

        assert type(self.directory) is not None, "Shapes::directory not set"
        assert type(self.datasets) is not None, "Shapes::datasets not set"
        assert type(self.binning) is not None, "Shapes::binning not set"

        self.logger = logging.getLogger(__name__)

    def __str__(self):
        self.logger.debug("Shapes ofset:", self.ofset)
        print "ofset", self.ofset
        output = (
            self.ofset * "\t" + " Shapes(" + "\n" +
            self.ofset * "\t" + "    debug = " + str(self.debug) + "\n" +
            self.ofset * "\t" + " )"
        )
        return output

    @staticmethod
    def parse_arguments(include_defaults=True):
        defaultArguments = {}
        parser = argparse.ArgumentParser(description='shapes.py parser')

        # Required for every run
        parser.add_argument("--directory", type=str, help="Directory with Artus outputs.")
        parser.add_argument("--datasets", type=str, help="Kappa datsets database.")
        parser.add_argument("--binning", type=str, help="Binning configuration.")

        # Arguments with None or none default
        parser.add_argument("--era", type=str, help="Experiment era.")
        parser.add_argument("--gof-variable", type=str, help="Variable for goodness of fit shapes.")
        parser.add_argument("--gof-channel", type=str, help="Channel for goodness of fit shapes.")
        parser.add_argument("--et-friend-directory", type=str, help="Directory containing a friend tree for et.")
        parser.add_argument("--mt-friend-directory", type=str, help="Directory containing a friend tree for mt.")
        parser.add_argument("--tt-friend-directory", type=str, help="Directory containing a friend tree for tt.")
        parser.add_argument("--fake-factor-friend-directory", type=str, help="Directory containing friend trees to data files with FF.")

        # Arguments with defaults that might be changed in the config file
        parser.add_argument("--channels", nargs='+', type=str, help="Channels to be considered.")
        parser.add_argument("--num-threads", type=int, help="Number of threads to be used.")
        parser.add_argument("--backend", choices=["classic", "tdf"], type=str, help="Backend. Use classic or tdf.")
        parser.add_argument("--tag", type=str, help="Tag of output files.")
        parser.add_argument("--skip-systematic-variations", type=str, help="Do not produce the systematic variations.")

        defaultArguments['channels'] = []
        defaultArguments['num_threads'] = 32
        defaultArguments['backend'] = 'classic'
        defaultArguments['tag'] = 'ERA_CHANNEL'
        defaultArguments['skip_systematic_variations'] = False

        # Arguments with defaults that can not be changed in the config file
        parser.add_argument('--dry', action='store_true', default=False, help='dry run')
        parser.add_argument('--debug', action='store_true', default=False, help='cherry-debug')

        args = parser.parse_args()
        configuration = dict((k, v) for k, v in vars(args).iteritems() if v is not None)

        if include_defaults:
            for argument, default in defaultArguments.iteritems():
                if argument not in configuration:
                    configuration[argument] = default

        return configuration

    @staticmethod
    def setup_logging(output_file=None, level=logging.DEBUG, logger=None):
        logger.setLevel(level)
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        file_handler = logging.FileHandler(output_file, "w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    @staticmethod
    def getHostKey():
        import socket
        hostname = socket.gethostname()
        known_hosts = ['naf', 'cern', 'ekp', 'rwth']
        for host in known_hosts:
            if host in hostname:
                return host
        return 'unknown_host'

    @staticmethod
    def readConfig(config_file=None):
        if isinstance(config_file, basestring):
            if config_file[-5:] == '.yaml' or config_file[-4:] == '.yml':
                with open(config_file, 'r') as stream:
                    try:
                        import getpass
                        username = getpass.getuser()
                        hostname = Shapes.getHostKey()

                        config = yaml.load(stream)
                        for user_specific_key in config['user_specific'].keys():
                            user_specific = config['user_specific'][user_specific_key]
                            config[user_specific_key] = user_specific['default']
                            if username in user_specific and hostname in user_specific[username]:
                                config[user_specific_key] = user_specific[username][hostname]
                        del config['user_specific']

                        return config

                    except yaml.YAMLError as exc:
                        print('Shapes::readConfig: yaml config couldn\' be loaded', exc)
            else:
                raise ValueError('Shapes::readConfig: config path is not yaml format')
        else:
            raise ValueError('Shapes::readConfig: config obj of unset type')

    def run(self):
        pass


if __name__ == '__main__':
    args = Shapes.parse_arguments()
    shapes = Shapes(**args)
    print shapes
    shapes.run()
