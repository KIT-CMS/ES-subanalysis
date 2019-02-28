# -*- coding: utf-8 -*-
import sys

import logging
from rootpy import log
from rootpy.logger.magic import DANGER

import yaml

import pprint
pp = pprint.PrettyPrinter(indent=4)

from shape_producer.systematics import Systematics
from channelholder import ChannelHolder
# from inidecorator import inidecorator

# TODO: wrapper for introduction of methods
# TODO: inharit from my base subprocesses class
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
                 log_level=None,
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
                 processes=None,
                 methods_collection_key='methods',
                 module=None,
                 _known_estimation_methods=None,
                 nominal_folder='nominal',
                 etau_es_shifts=None,
                 tes_sys_processes=None,
                 fes_sys_processes=None,
                 emb_sys_processes=None,
                 zpt_sys_processes=None,
                 shifts=None,
                 decay_mode=None,
                 jets_multiplicity=None,
                 indent=0,
                 ):
        # TODO: Can be commented out if @inidecorator will be used
        self._ofset = ofset
        self._directory = directory
        self._datasets = datasets
        self._binning = binning
        self._binning_key = binning_key
        self._log_level = log_level
        self._indent = indent
        self._methods_collection_key = methods_collection_key

        self._backend = backend
        self._channels_key = channels
        self._debug = debug
        self._dry = dry
        self._era_name = era
        self._et_friend_directory = et_friend_directory
        self._mt_friend_directory = mt_friend_directory
        self._tt_friend_directory = tt_friend_directory
        self._fake_factor_friend_directory = fake_factor_friend_directory
        self._gof_channel = gof_channel
        self._gof_variable = gof_variable
        self._num_threads = num_threads
        self._skip_systematic_variations = skip_systematic_variations
        self._tag = tag
        self._output_file = output_file
        self._context_analysis = context_analysis
        self._variables_names = variables_names
        self._processes = processes
        self._module = module
        self._known_estimation_methods = _known_estimation_methods
        self._nominal_folder = nominal_folder
        self._tes_sys_processes = tes_sys_processes
        self._etau_es_shifts = etau_es_shifts
        self._fes_sys_processes = fes_sys_processes
        self._emb_sys_processes = emb_sys_processes
        self._zpt_sys_processes = zpt_sys_processes
        self._shifts = shifts
        self._decay_mode = decay_mode
        self._jets_multiplicity = jets_multiplicity

        assert type(self._directory) is not None, "Shapes::directory not set"
        assert type(self._datasets) is not None, "Shapes::datasets not set"
        assert type(self._binning) is not None, "Shapes::binning not set"
        print "self._binning:", self._binning

        self._binning = yaml.load(open(self._binning))
        self._known_processes = yaml.load(open('data/known_processes.yaml'))
        self._renaming = yaml.load(open('data/renaming.yaml'))

        self._known_cuts = yaml.load(open('data/known_cuts.yaml'))
        for i in self._decay_mode:
            if i not in self._known_cuts['decay_mode'].keys():
                print 'no dm:', i, 'in known_cuts.yaml'
                exit(1)
        for i in self._jets_multiplicity:
            if i not in self._known_cuts['jets_multiplicity'].keys():
                print 'no jet multiplicity:', i, 'in known_cuts.yaml'
                exit(1)

        self._logger = logging.getLogger(__name__)
        self._channels = {}

        if self._output_file == '':
            self._output_file = "{}.root".format(self._context_analysis)
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

    @classmethod
    def prepareConfig(cls, analysis_shapes, config_file, debug=False):
        '''Read config and update to prompt'''
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '
        if debug:
            print '\n', self_name

        config = analysis_shapes.readConfig(config_file)

        prompt_args = analysis_shapes.parse_arguments(include_defaults=False)

        config.update(prompt_args)

        if debug:
            print 'config:'
            pp.pprint(config)

        return config

    # TODO: cleanup
    @classmethod
    def parse_arguments(cls, include_defaults=True, debug=False):
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '
        if debug:
            print '\n', self_name

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
        parser.add_argument("--processes", nargs='+', type=str, help="Processes from the standart map of processes")  # TODO: enable passing via syntax <name>:<class name>
        parser.add_argument("--methods-collection-key", nargs=1, type=str, help="Methods collection key")
        parser.add_argument("--module", nargs=1, type=str, help="Module to import where estimation methods are defined")  # TODO: enable passing via syntax <name>:<class name>
        parser.add_argument("--num-threads", type=int, help="Number of threads to be used.")
        parser.add_argument("--backend", choices=["classic", "tdf"], type=str, help="Backend. Use classic or tdf.")
        parser.add_argument("--tag", type=str, help="Tag of output files.")
        parser.add_argument("--output-file", type=str, help="Output file name for file with final shapes that enter datacards. If none is given context_analysis is used as a root for this name")
        parser.add_argument("--skip-systematic-variations", type=str, help="Do not produce the systematic variations.")
        parser.add_argument("--tes-sys-processes", nargs='+', type=str, help="Typical processes affected by systematic variation")
        parser.add_argument("--fes-sys-processes", nargs='+', type=str, help="Typical processes affected by systematic variation")
        parser.add_argument("--emb-sys-processes", nargs='+', type=str, help="Typical processes affected by systematic variation")
        parser.add_argument("--shifts", nargs='+', type=str, help="Pipelines, uncertainties variations, shifts : processed is the intersection of this list with list from _known_estimation_methods")
        parser.add_argument("--decay-mode", nargs='+', type=str, help="Needed for categorisation. Choices: all, dm0, dm1, dm10")
        parser.add_argument("--jets-multiplicity", nargs='+', type=str, help="Needed for categorisation. Choices: njetN, njet0")
        parser.add_argument("--binning-key", type=str, help="Used only to pick the binning! example: gof, control")
        parser.add_argument("--log-level", type=str, help="Log level")

        defaultArguments['channels'] = []
        defaultArguments['processes'] = []
        defaultArguments['methods_collection_key'] = 'methods'
        defaultArguments['module'] = None
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
        defaultArguments['shifts'] = ['nominal', 'TES', 'EMB', 'FES_shifts', 'TES_shifts']
        defaultArguments['decay_mode'] = ['all', 'dm0', 'dm1', 'dm10']
        defaultArguments['jets_multiplicity'] = ['njetN', 'njet0']
        defaultArguments['binning_key'] = 'control'
        defaultArguments['log_level'] = 'info'

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

    # TODO: separate from class, call in scope of each module
    @classmethod
    def setup_logging(cls, output_file, logger, level='DEBUG', danger=False, debug=False):
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '
        if debug:
            print '\n', self_name

        if level.lower() == 'debug':
            print self_name, 'DEBUG'
            # log.setLevel(log.DEBUG)
            level = log.DEBUG
        elif level.lower() == 'info':
            print self_name, 'INFO'
            # log.setLevel(log.INFO)
            level = log.INFO
        elif level.lower() == 'warning':
            print self_name, 'WARNING'
            # log.setLevel(log.INFO)
            level = log.WARNING
        else:
            print cls.__name__ + '::' + sys._getframe().f_code.co_name + ' : unknown leve'
            raise

        DANGER.enabled = danger

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

    @classmethod
    def readConfig(cls, config_file=None, debug=False):
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '
        if debug:
            print '\n', self_name

        assert isinstance(config_file, basestring), self_name + 'config obj of unset type'
        assert config_file.endswith('.yaml') or config_file.endswith('.yml'), self_name + 'config path is not yaml format'
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
                print self_name + 'yaml config couldn\' be loaded:\n', config_file, '\n', exc
                raise

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

    def getModule(self, era=None, context=None):
        if era is None:
            era = self._era_name
        era = str(era)
        if context is None:
            context = self._context_analysis

        if self._module is None:
            return self._known_estimation_methods[era][context]['module']
        else:
            return self._module

    def getMethodsDict(self, channel_name, era=None, context=None):
        # TODO: make initialisation universal
        if era is None:
            era = self._era_name
        era = str(era)
        if context is None:
            context = self._context_analysis
        # print self._known_processes.keys()

        if len(self._processes) == 0:
            try:
                return self._known_estimation_methods[era][context][channel_name][self._methods_collection_key]
            except:
                self._logger.error(' '.join("Couldn't find the method for era:", era, 'context:', context, 'channel_name:', channel_name))
                self._logger.error('Possible _known_estimation_methods:')
                pp.pprint(self._known_estimation_methods[era][context][channel_name])
        else:
            d = {}
            for i in self._processes:
                if i in d.keys():
                    raise ValueError(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name + ': repeating process: ' + i)
                d[i] = self._known_processes[i]
            return d

    def getChannelSystematics(self, channel_holder):
        """
        Setting systematics to associated INDIVIDUAL channel
        """
        self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)
        self._logger.warning('Not implemented!')
        pass

    def produceShapes():
        pass


if __name__ == '__main__':
    args = Shapes.parse_arguments()
    shapes = Shapes(**args)
    print shapes
