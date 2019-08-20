import sys
import importlib
import logging
import copy

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


class ETauFES(Shapes):
    def __init__(self, **kvargs):
        logging.getLogger(__name__).info("Init " + self.__class__.__name__)
        super(ETauFES, self).__init__(**kvargs)

        self._logger = logging.getLogger(__name__)

        self._variables = []
        self._estimation_methods = {}

        self._etau_es_shifts = self._known_estimation_methods[self._era_name][self._context_analysis]['etau_es_shifts']

    def evaluateEra(self):
        """
        "Era selection"
        """
        from shape_producer.era import Run2016 as Run2016
        from shape_producer.era import Run2018 as Run2018
        from shape_producer.era import Run2017 as Run2017

        if "2017" in self._era_name:
            # self.importEstimationMethods(era=self._era_name, context_analysis=self._context_analysis)
            self.era = Run2017(self._datasets)  # self.lazy("Run2017")() #
        elif "2018" in self._era_name:
            self.era = Run2018(self._datasets)
        elif "2016" in self._era_name:
            self.era = Run2016(self._datasets)
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
        # print "ETauFES::getProcesses"
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
                bg_processes = [processes[process] for process in self._complexEstimationMethodsRequirements[key][estimation_method]]  # ["EMB", "ZL", "ZJ", "TTL", "TTJ", "VVL", "VVJ"]]
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

            elif 'QCDSStoOS' in key:  # key == 'QCDEstimation_SStoOS_MTETEM':
                qcdsstoos_parameters_list = copy.deepcopy(parameters_list)

                qcdsstoos_parameters_list['bg_processes'] = [processes[process] for process in self._complexEstimationMethodsRequirements[key][estimation_method]]
                qcdsstoos_parameters_list['extrapolation_factor'] = 1.00  # 1.17?
                try:
                    qcdsstoos_parameters_list['data_process'] = processes['data_obs']
                except:
                    try:
                        qcdsstoos_parameters_list['data_process'] = processes['data']
                    except:
                        raise Exception("couldn't access processes['data_obs'] of data object")

                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**qcdsstoos_parameters_list))

            elif 'jetFakes' in key:
                ff_parameters_list = copy.deepcopy(parameters_list)
                ff_parameters_list['friend_directory'].extend(self._fake_factor_friend_directory)

                # import pdb; pdb.set_trace()
                if estimation_method == 'NewFakeEstimationLT':
                    # ? also TTT and VVT for no EMB case?
                    # nofake_processes = ["EMB", "ZL", "TTL", "VVL"] if "EMB" in key else ["ZTT", "ZL", "TTL", "VVL"]
                    # ff_parameters_list['nofake_processes'] = [processes[process] for process in nofake_processes]
                    ff_parameters_list['nofake_processes'] = [processes[process] for process in self._complexEstimationMethodsRequirements[key][estimation_method]]
                    try:
                        ff_parameters_list['data_process'] = processes['data_obs']
                    except:
                        try:
                            ff_parameters_list['data_process'] = processes['data']
                        except:
                            raise Exception("couldn't access processes['data'] or data_obs object")

                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**ff_parameters_list))

            else:
                # if key == 'ZL': print '-->getProcesses::', key, parameters_list
                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**parameters_list))

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
        # self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)
        categories = []
        for name, var in channel_holder._variables.iteritems():
            # Cuts common for all categories
            cuts = Cuts()
            # if name != "mt_1":
            #     if 'm_t' in channel_holder._channel_obj.cuts.names:
            #         self._logger.warning('Removing the existing cut m_t in category: ' +
            #             channel_holder._channel_obj.cuts.get('m_t')._weightstring +
            #             ' --> mt_1 < 70'
            #         )
            #         channel_holder._channel_obj.cuts.remove("m_t")

            for njet in self._jets_multiplicity:
                for dm in self._decay_mode:
                    self._logger.info('%s : ..adding category {%s && %s}', sys._getframe().f_code.co_name, njet, dm)
                    categories.append(
                        Category(
                            name=njet + '_' + dm,
                            channel=channel_holder._channel_obj,
                            cuts=cuts,
                            variable=var)
                    )

                    # Add the DM splitting
                    self._logger.debug("Add the dm splitting: %s, %s" % (self._known_cuts['decay_mode'][dm], dm))
                    categories[-1].cuts.add(Cut(self._known_cuts['decay_mode'][dm], dm))

                    # Add the njets splitting:
                    self._logger.debug("Add the njets splitting: %s, %s" % (str(self._known_cuts['jets_multiplicity'][njet]), str(njet)))
                    categories[-1].cuts.add(Cut(str(self._known_cuts['jets_multiplicity'][njet]), str(njet)))

                    # Remove cuts introduced in categorysation for the plots of isolation
                    if name == "iso_1" or name == "iso_2":
                        categories[-1].cuts.remove("ele_iso")
                        categories[-1].cuts.remove("tau_iso")

        log_categories = '\t', 'Cattegories:\n'
        for category in categories:
            log_categories += '\t' * 2, category.name, '_:', category.cuts.__str__(indent=3 + self._indent) + '\n'
        self._logger.info(log_categories)

        return categories

    def getEvaluatedChannel(self, channel, variables):
        """
        Creates and returns channel_holder for requested channel
        """
        if channel == 'et' and self._context_analysis == 'etFes' and self._era_name == '2017':
            from shape_producer.channel import ETSM2017  # TODO: make this globally configurable

            channel_holder = ChannelHolder(
                ofset=self._ofset + 1,
                logger=self._logger,
                debug=self._debug,
                channel_obj=ETSM2017(),
                friend_directory=self._et_friend_directory,
            )

            # channel_holder._channel_obj.cuts.remove("tau_iso")
            # channel_holder._channel_obj.cuts.add(Cut('byLooseIsolationMVArun2017v2DBoldDMwLT2017_2 > 0.5', "tau_iso"))

            for k, v in self._force_cuts.iteritems():
                channel_holder._channel_obj.cuts.remove(k)
                if v is not None:
                    channel_holder._channel_obj.cuts.add(Cut(v, k))
                self._logger.warning('global cut value forced: {"%s": "%s"}' % (k, v))

            self._logger.info('...getProcesses')
            channel_holder._processes = self.getProcesses(
                channel_obj=channel_holder._channel_obj,
                friend_directory=self._et_friend_directory
            )
            self._logger.info('...getVariables')
            channel_holder._variables = self.getVariables(
                channel_obj=channel_holder._channel_obj,
                variable_names=variables,
                binning=self.binning[self._binning_key][channel_holder._channel_obj._name]
            )
            self._logger.info('...getCategorries')
            channel_holder._categorries = self.getCategorries(
                channel_holder=channel_holder
            )
            self._logger.info('...getChannelSystematics')
            channel_holder._systematics = self.getChannelSystematics(  # NOTE: for a single channel
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

    # TODO: split to call corresponding functions instead of passing list of strings
    def evaluateSystematics(self, *argv):
        self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)
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

            if 'TES' in self._shifts:
                print '\n\nTES...'
                tau_es_3prong_variations = create_systematic_variations(name="CMS_scale_t_3prong_13TeV", property_name="tauEsThreeProng", systematic_variation=DifferentPipeline)
                tau_es_1prong_variations = create_systematic_variations(name="CMS_scale_t_1prong_13TeV", property_name="tauEsOneProng", systematic_variation=DifferentPipeline)
                tau_es_1prong1pizero_variations = create_systematic_variations(name="CMS_scale_t_1prong1pizero_13TeV", property_name="tauEsOneProngOnePiZero", systematic_variation=DifferentPipeline)

                for variation in tau_es_3prong_variations + tau_es_1prong_variations + tau_es_1prong1pizero_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    proc_intersection = list(set(self._tes_sys_processes) & set(channel_holder._processes.keys()))
                    print '\nvariation name:', variation.name, '\nintersection self._tes_sys_processes:', proc_intersection
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            if 'EMB' in self._shifts:
                print '\n\nEMB shifts...'
                decayMode_variations = []
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_3ProngEff_13TeV", "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effUp_pi0Nom", "decayMode_SF"),
                        "Up"))
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_3ProngEff_13TeV", "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effDown_pi0Nom", "decayMode_SF"),
                        "Down"))
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effNom_pi0Up", "decayMode_SF"),
                        "Up"))
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_1ProngPi0Eff_13TeV", "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effNom_pi0Down", "decayMode_SF"),
                        "Down"))
                for variation in decayMode_variations:
                    proc_intersection = list(set(self._emb_sys_processes) & set(channel_holder._processes.keys()))
                    print '\nvariation name:', variation.name, '\nintersection self._emb_sys_processes:', proc_intersection
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            if 'Zpt' in self._shifts:
                print '\n\nZ pt reweighting'
                zpt_variations = create_systematic_variations(name="CMS_htt_dyShape_13TeV", property_name="zPtReweightWeight", systematic_variation=SquareAndRemoveWeight)
                for variation in zpt_variations:
                    for process_nick in self.intersection(self.zpt_sys_processes, channel_holder._processes.keys()):
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            if 'FES_shifts' in self._shifts:
                print '\n\nFES_shifts...'
                # Pipelines for producing shapes for calculating the TauElectronFakeEnergyCorrection*
                root_str = lambda x: str(x).replace("-", "neg").replace(".", "p")
                for es in self._etau_es_shifts:
                    shift_str = root_str(es)
                    for pipeline in ["eleTauEsOneProngShift_", "eleTauEsOneProngPiZerosShift_", "eleTauEsThreeProngShift_"]:  # TODO: add inclusive
                        variation = DifferentPipeline(name='CMS_fes_' + pipeline + '13TeV_', pipeline=pipeline, direction=shift_str)
                        proc_intersection = list(set(self._fes_sys_processes) & set(channel_holder._processes.keys()))
                        print '\nvariation name:', variation.name, '\nintersection self._fes_sys_processes:', proc_intersection
                        for process_nick in proc_intersection:
                            self._systematics.add_systematic_variation(
                                variation=variation,
                                process=channel_holder._processes[process_nick],
                                channel=channel_holder._channel_obj,
                                era=self.era
                            )
                            for cut_key, cut_expression in self._fes_extra_cuts.iteritems():
                                self._systematics._systematics[-1].category.cuts.add(Cut(cut_expression, cut_key))
                            self._systematics._systematics[-1]._process._estimation_method._directory=self._fes_friend_directory[0]
            if 'FF' in self._shifts:
                print '\n\n FF related uncertainties ...'
                fake_factor_variations_et = []

                for systematic_shift in [
                        "ff_qcd{ch}_syst_13TeV{shift}",
                        "ff_qcd_dm0_njet0{ch}_stat_13TeV{shift}",
                        "ff_qcd_dm0_njet1{ch}_stat_13TeV{shift}",
                        "ff_w_syst_13TeV{shift}",
                        "ff_w_dm0_njet0{ch}_stat_13TeV{shift}",
                        "ff_w_dm0_njet1{ch}_stat_13TeV{shift}",
                        "ff_tt_syst_13TeV{shift}",
                        "ff_tt_dm0_njet0_stat_13TeV{shift}",
                        "ff_tt_dm0_njet1_stat_13TeV{shift}",
                ]:
                    for shift_direction in ["Up", "Down"]:
                        fake_factor_variations_et.append(
                            ReplaceWeight(
                                "CMS_%s" % (systematic_shift.format(ch='_et', shift="")),
                                "fake_factor",
                                Weight(
                                    "ff2_{syst}".format(
                                        syst=systematic_shift.format(
                                            ch="", shift="_%s" % shift_direction.lower()
                                        ).replace("_13TeV", "")),
                                    "fake_factor"
                                ),
                                shift_direction
                            )
                        )

                for k in [k for k in channel_holder._processes.keys() if 'jetFakes' in k]:
                    for variation in fake_factor_variations_et:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[k],
                            channel=channel_holder._channel_obj,
                            era=self.era)

    def produce(self):
        print self._systematics
        self._systematics.produce()


if __name__ == '__main__':
    args = ETauFES.parse_arguments()
    etau_fes = ETauFES(**args)
    print etau_fes
