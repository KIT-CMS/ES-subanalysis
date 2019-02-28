import importlib
from shapes import Shapes

from shapes.channelholder import ChannelHolder
# TODO: needs to be moved from global imports
from shape_producer.process import Process  # move to ChannelsHolder
from shape_producer.variable import Variable  # move to ChannelsHolder
from shape_producer.binning import VariableBinning  # move to ChannelsHolder
from shape_producer.categories import Category  # move to ChannelsHolder
from shape_producer.cutstring import Cut, Cuts, Weight  # move to ChannelsHolder
from shape_producer.systematics import Systematic
from shape_producer.systematic_variations import Nominal, DifferentPipeline, create_systematic_variations, \
    ReplaceWeight, SquareAndRemoveWeight
from shapes.introduce import introduce_function
import sys
from IPython.core import ultratb
sys.excepthook = ultratb.FormattedTB(mode='Verbose', color_scheme='Linux', call_pdb=False)

# @introduce_all_class_methods
class TESShapes(Shapes):

    def __init__(self, **kvargs):
        print "init", self.__class__.__name__
        super(TESShapes, self).__init__(**kvargs)

        self._variables = []
        self._estimation_methods = {}

        self._tau_es_point   = self._known_estimation_methods[self._era_name][self._context_analysis]['tau_es_point']
        self._tau_es_charged = self._known_estimation_methods[self._era_name][self._context_analysis]['tau_es_charged']
        self._tau_es_neutral = self._known_estimation_methods[self._era_name][self._context_analysis]['tau_es_neutral']

    def evaluateEra(self):
        """
        "Era selection"
        """
        if "2017" in self._era_name:
            from shape_producer.era import Run2017ReReco31Mar as Run2017
            self.era = Run2017(self._datasets)
        else:
            self.logger.critical("Era {} is not implemented.".format(self.era))
            raise Exception

    def getEstimationMethod(self, key):
        """
        Returns class that corresponds to the requested estimation method
        """
        print "getEstimationMethod::key", key
        if key in self._estimation_methods:
            return self._estimation_methods[key]
        else:
            raise KeyError("unknown getEstimationMethod key:" + key)

    def __getattr__(self, key):
        """
        Syntactic sugar to return a getEstimationMethod object defined by *key* in case no other attribute
        was resolved.
        """
        print "__getattr__::key", key
        return self.getEstimationMethod(key)

    def importEstimationMethods(self, module, *methods):  # TODO: add arguments validity
        """
        Manual importing of module
        """
        for method in methods:
                if method in self._estimation_methods:
                    print 'Warning: Estimation method', method, 'already defined - skipped redefinition'
                    continue
                self._estimation_methods[method] = getattr(importlib.import_module(module), method)

    # TODO: add wraper to set initial parameters to self.*
    # TODO: add arguments validity
    def importEstimationMethods(self, era=None, context_analysis=None, channels_key=None):
        """
        Standalone importing
        """
        # print "TESShapes::Standalone importing"
        if channels_key is None:
            channels_key = self._channels_key

        imported_module = self.getModule()
        for channel_name in channels_key:
            # print "test:", self._known_estimation_methods[era][context_analysis]#[channel_name]#['methods']
            for combine_name, method in self.getMethodsDict(era=era, context=context_analysis, channel_name=channel_name).iteritems():
                if method in self._estimation_methods:
                    print 'Warning: Estimation method', method, 'already defined - skipped redefinition'
                # print 'module:', self._estimation_methods
                self._estimation_methods[method] = getattr(importlib.import_module(imported_module), method)

    # TODO: needs to belong to ChannelHolder
    # TODO:reimplement the function to take parameters_list as input argument
    def getProcesses(self, channel_obj, friend_directory):  # TODO: use a set of parameters; TODO: add a fn to re-set the QCD estimation method
        """
        Returns dict of Processes for Channel
        """
        print '  ' + self.__class__.__name__ + "::getProcesses"
        parameters_list = {
            'era': self.era,
            'directory': self._directory,
            'channel': channel_obj,
            'friend_directory': friend_directory,
            'folder': self._nominal_folder,
        }
        channel_name = channel_obj._name
        context = self._context_analysis
        era = self._era_name
        processes = {}
        renaming = self._renaming

        # TODO: move to config step
        # Move all the complex methods to the end of the processes list
        from collections import OrderedDict
        orderedProcesses = OrderedDict(self.getMethodsDict(era=era, context=context, channel_name=channel_name))
        for combine_name, estimation_method in self.getMethodsDict(era=era, context=context, channel_name=channel_name).iteritems():
            if estimation_method in self._complexEstimationMethods:
                temp = estimation_method
                del orderedProcesses[combine_name]
                orderedProcesses[combine_name] = temp

        # print 'Create all Processes'
        for combine_name, estimation_method in orderedProcesses.iteritems():
            key = combine_name if combine_name not in renaming.keys() else renaming[combine_name]

            if estimation_method not in self._estimation_methods.keys():
                raise KeyError("Unknown estimation method: " + estimation_method)

            if key in processes.keys():  # TODO: add the check of the config
                print "Key added in list of processes twice. channel: " + channel_name + "; key:" + key
                continue

            if estimation_method in ['WEstimationWithQCD', 'QCDEstimationWithW']:
                bg_processes = {}
                if "EMB" in key:
                    bg_processes = [processes[process] for process in ["EMB", "ZL", "ZJ", "TTL", "TTJ", "VVL", "VVJ"]]
                    # former with: "EWKL", "EWKJ"
                else:
                    bg_processes = [processes[process] for process in ["ZTT", "ZL", "ZJ", "TT", "VV"]]
                    # alternative: ["DYJetsToLL", "TT", "VV"]]
                    # former with "EWK"
                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](
                    era=self.era,
                    directory=self._directory,
                    channel=channel_obj,
                    bg_processes=bg_processes,
                    data_process=processes["data_obs"],
                    w_process=processes["WMC"],
                    friend_directory=[],
                    qcd_ss_to_os_extrapolation_factor=1.09,
                ))
            elif key == 'QCDEstimation_SStoOS_MTETEM':
                print 'QCDEstimation_SStoOS_MTETEM is not yet setup'
                exit(1)
            elif key == 'jetFakes':
                import copy
                ff_parameters_list = copy.deepcopy(parameters_list)
                ff_parameters_list['friend_directory'].append(self._fake_factor_friend_directory)
                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**ff_parameters_list))
            else:
                # if key == 'ZL': print '-->getProcesses::', key, parameters_list
                processes[key] = Process(
                    combine_name,
                    self._estimation_methods[estimation_method](**parameters_list))

        return processes

    # TODO: needs to belong to ChannelHolder
    def getVariables(self, channel_obj, variable_names, binning):
        """
        Returns dict of Variables for Channel
        """
        print '  ' + self.__class__.__name__ + "::getVariables"
        variables = {}

        for key in variable_names:
            variables[key] = Variable(
                key,
                VariableBinning(binning[key]["bins"]),
                expression=binning[key]["expression"],
            )

        return variables

    # TODO: needs to belong to ChannelHolder ;
    # TODO: need to generalise - living dummy argument
    def getCategorries(self, channel_holder, cuts=None):
        """
        Returns dict of Cattegories for Channel
        """
        print '  ' + self.__class__.__name__ + "::getCategorries"
        categories = []
        for name, var in channel_holder._variables.iteritems():
            # Cuts common for all categories
            cuts = Cuts()
            if name != "mt_1":
                cuts.add(Cut("mt_1 < 70", "mt"))
            # Cut('mt_tot<70', 'mttot_cur'), TODO: check

            for njet in self._jets_multiplicity:
                for dm in self._decay_mode:
                    categories.append(
                        Category(
                            name=njet + '_' + dm,
                            channel=channel_holder._channel_obj,
                            cuts=cuts,
                            variable=var)
                    )
                    # Add the DM splitting
                    categories[-1].cuts.add(Cut(self._known_cuts['decay_mode'][dm], dm))

                    # Add the njets splitting:
                    categories[-1].cuts.add(Cut(str(self._known_cuts['jets_multiplicity'][njet]), str(njet)))

                    # Remove cuts introduced in categorysation
                    if name == "iso_1" or name == "iso_2":
                        categories[-1].cuts.remove("ele_iso")
                        categories[-1].cuts.remove("tau_iso")

        print '\t', 'Cattegories:'
        for category in categories:
            print '\t' * 2, category.name, "_:", category.cuts.__str__(indent=3)

        return categories

    @introduce_function
    def getEvaluatedChannel(self, channel, variables):
        """
        Creates and returns channel_holder for requested channel
        """
        print '  ' + self.__class__.__name__ + "::getEvaluatedChannel"
        if self._context_analysis == 'mtTES' and self._era_name == '2017':
            if channel == 'mt':
                from shape_producer.channel import MTSM2017 as CHANNEL  # TODO: make this globally configurable
            elif channel == 'et':
                from shape_producer.channel import ETSM2017 as CHANNEL  # TODO: make this globally configurable
            elif channel == 'tt':
                from shape_producer.channel import TTSM2017 as CHANNEL  # TODO: make this globally configurable
            else:
                raise KeyError("getEvaluatedChannel: channel not setup. channel:" + channel)

            channel_holder = ChannelHolder(
                ofset=self._ofset + 1,
                logger=self._logger,
                debug=self._logger,
                channel_obj=CHANNEL(),
                friend_directory=self._et_friend_directory,
            )

            # print "self._logger.debug('...getProcesses')"
            channel_holder._processes = self.getProcesses(
                channel_obj=channel_holder._channel_obj,
                friend_directory=self._et_friend_directory
            )
            # print "self._logger.debug('...getVariables')"
            channel_holder._variables = self.getVariables(
                channel_obj=channel_holder._channel_obj,
                variable_names=variables,
                binning=self.binning[self._binning_key][channel_holder._channel_obj._name]
            )
            # print "self._logger.debug('...getCategorries')"
            channel_holder._categorries = self.getCategorries(
                channel_holder=channel_holder
            )
            # print "self._logger.debug('...getChannelSystematics')"
            channel_holder._systematics = self.getChannelSystematics(  # NOTE: for a single channel
                channel_holder=channel_holder
            )

            return channel_holder
        else:
            raise KeyError("getEvaluatedChannel: context/era not setup:" + self._context_analysis + '; era: ' + self._era_name)

    # @self.introducing
    def evaluateChannels(self):
        """
        Evaluates all requested channels
        """
        # print "TESShapes::evaluateChannels"
        print '  ' + self.__class__.__name__ + "::evaluateChannels"
        for channel in self._channels_key:
            self.addChannel(
                name=channel,
                channel_holder=self.getEvaluatedChannel(channel=channel, variables=self._variables_names),
            )

    def addChannel(self, name, channel_holder):
        """
        Appends to the _channels dict only the ChannelHolder items
        """
        # print "TESShapes::addChannel:", name, type(channel_holder)
        print '  ' + self.__class__.__name__ + "::addChannel"
        if isinstance(channel_holder, ChannelHolder):
            self._channels[name] = channel_holder
        else:
            raise 'addChannel can\'t add non-ChannelHolder objects'

    # TODO: split to call corresponding functions instead of passing list of strings
    # TODO: put to a different class and inherit from it.
    def evaluateSystematics(self, *argv):
        print "evaluateSystematics"
        for channel_name, channel_holder in self._channels.iteritems():
            processes = channel_holder._processes.values()
            categories = channel_holder._categorries

            if 'nominal' in self._shifts:
                print '\n nominal...'
                from itertools import product
                for process, category in product(processes, categories):
                    # print process._estimation_method._friend_directories
                    self._systematics.add(
                        Systematic(
                            category=category,
                            process=process,
                            analysis=self._context_analysis,  # "smhtt",  # TODO : check if this is used anywhere, modify the configs sm->smhtt
                            era=self.era,
                            variation=Nominal(),
                            mass="125",  # TODO : check if this is used anywhere
                        )
                    )
                    # print "\tnew sys:", self._systematics._systematics[-1].name, len(self._systematics._systematics), self._systematics._systematics[-1]._process.estimation_method._friend_directories

            if 'TES_shifts' in self._shifts:
                print '\n\n TES_shifts...'
                root_str = lambda x: str(x).replace("-", "neg").replace(".", "p")
                shifts = []
                if self._tau_es_point is not None:
                    shifts = ['ch' + root_str(self._tau_es_point[0]) + '_nt' + root_str(self._tau_es_point[1])]
                for c in self._tau_es_charged:
                    for n in self._tau_es_neutral:
                        shift_str = 'ch' + root_str(c) + '_nt' + root_str(n)
                        shifts.append(shift_str)

                for shift_str in shifts:
                    for pipeline in ["tauTauEsOneProngPiZerosShift_"]:
                        variation = DifferentPipeline(name='CMS_tes_' + pipeline + '13TeV_', pipeline=pipeline, direction=shift_str)
                        proc_intersection = list(set(self._tes_sys_processes) & set(channel_holder._processes.keys()))
                        print '\n variation name:', variation.name, '\nintersection self._fes_sys_processes:', proc_intersection
                        for process_nick in proc_intersection:
                            self._systematics.add_systematic_variation(
                                variation=variation,
                                process=channel_holder._processes[process_nick],
                                channel=channel_holder._channel_obj,
                                era=self.era)

    def produce(self):
        print self._systematics
        self._systematics.produce()


if __name__ == '__main__':
    args = TESShapes.parse_arguments()
    etau_fes = TESShapes(**args)
    print etau_fes
