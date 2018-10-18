import importlib
from shapes import Shapes

from shapes.channelholder import ChannelHolder
# TODO: needs to be moved from global imports
from shape_producer.process import Process  # move to ChannelsHolder
from shape_producer.variable import Variable  # move to ChannelsHolder
from shape_producer.binning import VariableBinning  # move to ChannelsHolder
from shape_producer.categories import Category  # move to ChannelsHolder
from shape_producer.cutstring import Cut, Cuts  # move to ChannelsHolder
from shape_producer.systematics import Systematic
from shape_producer.systematic_variations import Nominal


class ETauFES(Shapes):
    def __init__(self, **kvargs):
        print "init ETauFES"
        super(ETauFES, self).__init__(**kvargs)

        self._variables = []
        self._estimation_methods = {}

    def evaluateEra(self):
        """
        "Era selection"
        """
        if "2017" in self._era_name:
            # self.importEstimationMethods(era=self._era_name, context_analysis=self._context_analysis)
            from shape_producer.era import Run2017ReReco31Mar as Run2017
            self.era = Run2017(self._datasets)  # self.lazy("Run2017")() #
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
    def importEstimationMethods(self, era=None, context_analysis=None, channels_key=None):  # TODO: add arguments validity
        """
        Standalone importing
        """
        # print "ETauFES::Standalone importing"
        if era is None:
            era = self._era_name
        if context_analysis is None:
            context_analysis = self._context_analysis
        if channels_key is None:
            channels_key = self._channels_key
        era = str(era)
        imported_module = self._known_estimation_methods[era][context_analysis]['module']

        for channel in self._channels_key:
            # print "test:", self._known_estimation_methods[era][context_analysis]#[channel]#['methods']
            for combine_name, method in self._known_estimation_methods[era][context_analysis][channel]['methods'].iteritems():
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
        # print "ETauFES::getProcesses"
        parameters_list = {
            'era': self.era,
            'directory': self._directory,
            'channel': channel_obj,
            'friend_directory': friend_directory,
        }
        channel_name = channel_obj._name
        context = self._context_analysis
        era = self._era_name
        processes = {}
        renaming = self._known_estimation_methods[era][context][channel_name]['renaming']

        # TODO: move to config step
        # print '# Move all the complex methods to the end of the processes list'
        from collections import OrderedDict
        orderedProcesses = OrderedDict(self._known_estimation_methods[era][context][channel_name]['methods'])
        for combine_name, estimation_method in self._known_estimation_methods[era][context][channel_name]['methods'].iteritems():
            if estimation_method in self._complexEstimationMethods:
                temp = estimation_method
                del orderedProcesses[combine_name]
                orderedProcesses[combine_name] = temp

        # print 'Create all Processes'
        for combine_name, estimation_method in orderedProcesses.iteritems():
            key = combine_name if combine_name not in renaming.values() else renaming[combine_name]

            if estimation_method not in self._estimation_methods.keys():
                raise KeyError("Unknown estimation method: " + estimation_method)

            if key not in processes.keys():
                if estimation_method in ['WEstimationWithQCD', 'QCDEstimationWithW']:
                    bg_processes = {}

                    if "EMB" in key:
                        bg_processes = [processes[process] for process in ["EMB", "ZLL", "ZJ", "TTL", "TTJ", "VVL", "VVJ", "EWKL", "EWKJ"]],
                    else:
                        bg_processes = [processes[process] for process in ["ZTT", "ZLL", "ZJ", "TT", "VV", "EWK"]]  # dataDriven_QCDW_bg_processes

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
                else:
                    if key == 'ZL': print '-->getProcesses::', key, type(parameters_list['channel'])
                    processes[key] = Process(combine_name, self._estimation_methods[estimation_method](*parameters_list))
            else:  # TODO: add the check of the config
                print "Key added in list of processes twice. channel: " + channel_name + "; key:" + key

        return processes

    # TODO: needs to belong to ChannelHolder
    def getVariables(self, channel_obj, variable_names, binning):
        """
        Returns dict of Variables for Channel
        """
        # print "ETauFES::getVariables"
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
        categories = []
        for name, var in channel_holder._variables.iteritems():
            if name == "mt_1":
                cuts = Cuts(Cut("njets == 0", "nojets"))
            else:
                cuts = Cuts(Cut("mt_1 < 70", "mt"),
                    Cut("njets == 0", "nojets")
                )
            categories.append(
                Category(
                    name,
                    channel_holder._channel_obj,
                    cuts,
                    variable=var))
            if name == "iso_1" or name == "iso_2":
                categories[-1].cuts.remove("ele_iso")
                categories[-1].cuts.remove("tau_iso")

        return categories

    def getSystematics(self, channel_holder):  # NOTE: for a single channel
        """
        Setting systematics ro associated channel
        """
        pass

    def getEvaluatedChannel(self, channel, variables):
        """
        Creates and returns channel_holder for requested channel
        """
        if channel == 'et' and self._context_analysis == 'etFes' and self._era_name == '2017':
            from shape_producer.channel import ETMSSM2017  # TODO: make this globally configurable

            channel_holder = ChannelHolder(
                ofset=self._ofset + 1,
                logger=self._logger,
                debug=self._logger,
                channel_obj=ETMSSM2017(),
                friend_directory=self._et_friend_directory,
            )
            print "self._logger.debug('...getProcesses')"
            channel_holder._processes = self.getProcesses(
                channel_obj=channel_holder._channel_obj,
                friend_directory=self._et_friend_directory
            )
            print "self._logger.debug('...getVariables')"
            channel_holder._variables = self.getVariables(
                channel_obj=channel_holder._channel_obj,
                variable_names=variables,
                binning=self.binning["control"][channel_holder._channel_obj._name]
            )
            print "self._logger.debug('...getCategorries')"
            channel_holder._categorries = self.getCategorries(
                channel_holder=channel_holder
            )
            print "self._logger.debug('...getSystematics')"
            channel_holder._systematics = self.getSystematics(  # NOTE: for a single channel
                channel_holder=channel_holder
            )

            return channel_holder
        else:
            raise KeyError("getEvaluatedChannel: channel not setup. channel:" + channel +
                "; context:" + self._context_analysis + '; eta: ' + self._era_name)

    def evaluateChannels(self):
        """
        Evaluates all requested channels
        """
        # print "ETauFES::evaluateChannels"
        for channel in self._channels_key:
            self.addChannel(
                name=channel,
                channel_holder=self.getEvaluatedChannel(channel=channel, variables=self._variables_names),
            )

    def addChannel(self, name, channel_holder):
        """
        Appends to the _channels dict only the ChannelHolder items
        """
        # print "ETauFES::addChannel:", name, type(channel_holder)
        if isinstance(channel_holder, ChannelHolder):
            self._channels[name] = channel_holder
        else:
            raise 'addChannel can\'t add non-ChannelHolder objects'

    def evaluateSystematics(self):
        for channel_name, channel_holder in self._channels.iteritems():
            processes = channel_holder._processes.values()
            categories = channel_holder._categorries

            from itertools import product
            for process, category in product(processes, categories):
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

    def produce(self):
        self._systematics.produce()


if __name__ == '__main__':
    args = ETauFES.parse_arguments()
    etau_fes = ETauFES(**args)
    print etau_fes
