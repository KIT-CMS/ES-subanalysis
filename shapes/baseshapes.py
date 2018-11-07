# -*- coding: utf-8 -*-

import logging
"""
"""
import yaml

"""Script to copy files after the skim from * to nfs."""
# import os
# import subprocess
import pprint
pp = pprint.PrettyPrinter(indent=4)
# import tempfile
# import hashlib

from shape_producer.systematics import Systematics
from channelholder import ChannelHolder
# from inidecorator import inidecorator


class Shapes(object):
    _complexEstimationMethods = ['WEstimationWithQCD', 'QCDEstimationWithW']

    intersection = lambda x, y: list(set(x) & set(y))

    # @inidecorator   # TODO: TEST
    def __init__(self,
                 ofset=0,
                 directory=None,
                 datasets=None,
                 binning=None,
                 binning_key=None,
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
                 output_file=None,
                 tt_friend_directory=None,
                 context_analysis=None,
                 variables_names=None,  # X
                 _known_estimation_methods=None,
                 nominal_folder='nominal',
                 etau_es_shifts=None,
                 tes_sys_processes=None,
                 fes_sys_processes=None,
                 emb_sys_processes=None,
                 zpt_sys_processes=None,
                 shifts=None,
                 decay_mode=None,
                 ):
        # TODO: Can be commented out if @inidecorator will be used
        self._ofset = ofset
        self._directory = directory
        self._datasets = datasets
        self._binning = binning
        self._binning_key = binning_key
        self._backend = backend
        self._channels_key = channels
        self._debug = debug
        self._dry = dry
        self._era_name = era
        self._et_friend_directory = et_friend_directory
        self._fake_factor_friend_directory = fake_factor_friend_directory
        self._gof_channel = gof_channel
        self._gof_variable = gof_variable
        self._mt_friend_directory = mt_friend_directory
        self._num_threads = num_threads
        self._skip_systematic_variations = skip_systematic_variations
        self._tag = tag
        self._output_file = output_file
        self._tt_friend_directory = tt_friend_directory
        self._context_analysis = context_analysis
        self._variables_names = variables_names
        self._known_estimation_methods = _known_estimation_methods
        self._nominal_folder = nominal_folder
        self._tes_sys_processes = tes_sys_processes
        self._etau_es_shifts = etau_es_shifts
        self._fes_sys_processes = fes_sys_processes
        self._emb_sys_processes = emb_sys_processes
        self._zpt_sys_processes = zpt_sys_processes
        self._shifts = shifts
        self._decay_mode = decay_mode

        assert type(self._directory) is not None, "Shapes::directory not set"
        assert type(self._datasets) is not None, "Shapes::datasets not set"
        assert type(self._binning) is not None, "Shapes::binning not set"
        print "self._binning:", self._binning

        self._binning = yaml.load(open(self._binning))

        self._logger = logging.getLogger(__name__)
        self._channels = {}

        if self._output_file == '':
            self._output_file = "{}.root".format(self._tag)
        elif len(self._output_file) > 5 and self._output_file[-5:] == '.root':
            pass
        else:
            self._output_file = "{}.root".format(self._output_file)

        # Holds Systematics for all the channels. TODO: add the per-channel systematics to ChannelHolder
        self._systematics = Systematics(
            output_file=self._output_file,
            num_threads=self._num_threads,
            skip_systematic_variations=self._skip_systematic_variations
        )

    @property
    def binning(self):
        return self._binning

    @property
    def era(self):
        return self._era

    @era.setter
    def era(self, value):
        from shape_producer.era import Era
        if isinstance(value, Era):
            self._era = value
        else:
            raise ValueError('Shapes::era: tried to set era not to type Era')

    @era.deleter
    def era(self):
        del self._era

    @property
    def channels(self):
        return self._channels

    def addChannel(self, name, cuts, processes, categorries):
        self._channels[name] = ChannelHolder(
            ofset=self._ofset + 1,
            logger=self._logger,
            debug=self._logger,
            name=name,
            cuts=cuts,
            processes=processes,
            categorries=categorries,
        )

    def __str__(self):
        self._logger.debug("Shapes ofset:", self._ofset)
        print "ofset", self._ofset
        output = (
            self._ofset * "\t" + " Shapes(" + "\n" +
            self._ofset * "\t" + "    debug = " + str(self.debug) + "\n" +
            self._ofset * "\t" + " )"
        )
        return output

    @staticmethod
    def parse_arguments(include_defaults=True):
        import argparse
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
        parser.add_argument("--context-analysis", type=str, help="Context analysis.")
        parser.add_argument("--variables-names", nargs='*', type=str, help="Variable names.")

        # Arguments with defaults that might be changed in the config file
        parser.add_argument("--channels", nargs='+', type=str, help="Channels to be considered.")
        parser.add_argument("--num-threads", type=int, help="Number of threads to be used.")
        parser.add_argument("--backend", choices=["classic", "tdf"], type=str, help="Backend. Use classic or tdf.")
        parser.add_argument("--tag", type=str, help="Tag of output files.")
        parser.add_argument("--output-file", type=str, help="Output file name.")
        parser.add_argument("--skip-systematic-variations", type=str, help="Do not produce the systematic variations.")
        parser.add_argument("--tes-sys-processes", nargs='+', type=str, help="...")
        parser.add_argument("--fes-sys-processes", nargs='+', type=str, help="...")
        parser.add_argument("--emb-sys-processes", nargs='+', type=str, help="...")
        parser.add_argument("--shifts", nargs='+', type=str, help="...")
        parser.add_argument("--decay-mode", nargs='+', type=str, help="...")
        parser.add_argument("--binning-key", choices=["gof", "control"], type=str, help="binning_key")

        defaultArguments['channels'] = []
        defaultArguments['num_threads'] = 32
        defaultArguments['backend'] = 'classic'
        defaultArguments['tag'] = 'ERA_CHANNEL'
        defaultArguments['output_file'] = ''
        defaultArguments['skip_systematic_variations'] = False
        defaultArguments['context_analysis'] = 'etFes'
        defaultArguments['tes_sys_processes'] = ["ZTT", "TTT", "TTL", "VVT", "EWKT", "VVL", "EMB", "DYJetsToLL"]
        defaultArguments['fes_sys_processes'] = ['ZL', 'DYJetsToLL', 'EMB']
        defaultArguments['emb_sys_processes'] = ['EMB']
        defaultArguments['zpt_sys_processes'] = ['ZTT', 'ZL', 'ZJ']
        defaultArguments['shifts'] = ['nominal', 'TES', 'EMB', 'FES_shifts']
        defaultArguments['decay_mode'] = ['all', 'dm0', 'dm1', 'dm10']
        defaultArguments['binning_key'] = 'control'

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
                        print('Shapes::readConfig: yaml config couldn\' be loaded:\n', config_file, '\n', exc)
            else:
                raise ValueError('Shapes::readConfig: config path is not yaml format')
        else:
            raise ValueError('Shapes::readConfig: config obj of unset type')

    def evaluateChannel(self, channel):
        pass  # self._channels.add()

    def evaluateChannels(self):
        pass

    def evaluateEra(self):
        pass

    # TODO: use a set of parameters
    # TODO: add a fn to re-set the QCD estimation method
    def getProcessesDict(self, channel_name=None):
        pass

    def produceShapes():
        pass


if __name__ == '__main__':
    args = Shapes.parse_arguments()
    shapes = Shapes(**args)
    print shapes
