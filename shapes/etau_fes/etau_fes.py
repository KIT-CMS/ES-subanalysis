import sys
import importlib
import logging

from shapes import Shapes

from shapes.channelholder import ChannelHolder
# TODO: needs to be moved from global imports
# from shape_producer.process import Process  # move to ChannelsHolder
# from shape_producer.variable import Variable  # move to ChannelsHolder
# from shape_producer.binning import VariableBinning  # move to ChannelsHolder
from shape_producer.cutstring import Cut, Weight  # move to ChannelsHolder
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

        # self._etau_es_shifts = self._known_estimation_methods[self._era_name][self._context_analysis]['etau_es_shifts']

    def getEvaluatedChannel(self, channel, variables):
        """
        Creates and returns channel_holder for requested channel
        """
        if channel == 'et':
            if self._era_name == '2017':
                from shape_producer.channel import ETSM2017 as channel_obj
            elif self._era_name == '2018':
                from shape_producer.channel import ETSM2018 as channel_obj
            elif self._era_name == '2016':
                from shape_producer.channel import ETSM2016 as channel_obj

            channel_holder = ChannelHolder(
                ofset=self._ofset + 1,
                logger=self._logger,
                debug=self._debug,
                channel_obj=channel_obj(),
                friend_directory=self._et_friend_directory,
            )

            # channel_holder._channel_obj.cuts.remove("tau_iso")
            # channel_holder._channel_obj.cuts.add(Cut('byLooseIsolationMVArun2017v2DBoldDMwLT2017_2 > 0.5', "tau_iso"))

            # used at 2017
            # channel_holder._channel_obj.cuts.remove("dilepton_veto")
            # channel_holder._channel_obj.cuts.remove('trg_selection')
            # channel_holder._channel_obj.cuts.add(Cut("(trg_singleelectron_27 == 1) || (trg_singleelectron_32 == 1) || (trg_singleelectron_35) || (trg_crossele_ele24tau30 == 1) || (isEmbedded && pt_1>20 && pt_1<24)", "trg_selection"))

            for k in self._invert_cuts:
                if k in channel_holder._channel_obj.cuts.names:
                    # import pdb; pdb.set_trace()
                    warning_message = "Inverting cut %s from old value [%s] " % (k, channel_holder._channel_obj.cuts.get(k))
                    channel_holder._channel_obj.cuts.get(k).invert()
                    warning_message += "to new value [%s]" % (channel_holder._channel_obj.cuts.get(k))
                    self._logger.warning(warning_message)
                else:
                    self._logger.error("Couldn't invert cut %s - not found in the original cuts: " + channel_holder)
                    # print channel_holder

            for k, v in self._force_cuts.iteritems():
                channel_holder._channel_obj.cuts.remove(k)
                if v is not None:
                    channel_holder._channel_obj.cuts.add(Cut(v, k))
                self._logger.warning('global cut value forced: {"%s": "%s"}' % (k, v))

            for k, v in self._et_minplotlev_cuts.iteritems():
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

    def getUpdateProcessPerCategory(self, process, category):
        # values calculated for MVAv2, 'dilepton_veto': Null
        # TODO: have a config for this
        if '2017' in process._estimation_method._era.__class__.__name__ and 'et' in category.name:
            if process.name == "QCDSStoOS":
                # import pdb; pdb.set_trace()
                if not any(i in category.name for i in ['dm0', 'dm1']):
                    if 'njet0' not in category.name:
                        process._estimation_method._extrapolation_factor = 1.38
                    else:
                        process._estimation_method._extrapolation_factor = 1.008
                elif 'dm0' in category.name:
                    if 'njet0' not in category.name:
                        process._estimation_method._extrapolation_factor = 1.170
                    else:
                        process._estimation_method._extrapolation_factor = 1.137
                elif 'dm1' in category.name and 'dm10' not in category.name:
                    if 'njet0' not in category.name:
                        process._estimation_method._extrapolation_factor = 0.997
                    else:
                        process._estimation_method._extrapolation_factor = 0.965
        return process

    # TODO: split to call corresponding functions instead of passing list of strings
    def evaluateSystematics(self, *argv):
        self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)
        intersection = lambda x, y: list(set(x) & set(y))

        for channel_name, channel_holder in self._channels.iteritems():
            processes = channel_holder._processes.values()
            categories = channel_holder._categorries

            if 'nominal' in self._shifts:
                print '\n nominal...'
                from itertools import product
                for process, category in product(processes, categories):
                    self._systematics.add(
                        Systematic(
                            category=category,
                            process=self.getUpdateProcessPerCategory(process, category) if self._update_process_per_category else process,
                            analysis=self._context_analysis,  # "smhtt",  # TODO : check if this is used anywhere, modify the configs sm->smhtt
                            era=self.era,
                            variation=Nominal(),
                            mass="125",  # TODO : check if this is used anywhere
                        )
                    )

            channel_holder._nnominals = len([i for i in self._systematics._systematics if i.variation.is_nominal()])
            if channel_holder._nnominals == 0:
                raise Exception("no nominals were found - yet not implemented.")

            if 'TES' in self._shifts:
                self._logger.info('\n\nTES...')
                tau_es_3prong_variations = create_systematic_variations(name="CMS_scale_t_3prong_13TeV", property_name="tauEsThreeProng", systematic_variation=DifferentPipeline)
                tau_es_1prong_variations = create_systematic_variations(name="CMS_scale_t_1prong_13TeV", property_name="tauEsOneProng", systematic_variation=DifferentPipeline)
                tau_es_1prong1pizero_variations = create_systematic_variations(name="CMS_scale_t_1prong1pizero_13TeV", property_name="tauEsOneProngOnePiZero", systematic_variation=DifferentPipeline)

                for variation in tau_es_3prong_variations + tau_es_1prong_variations + tau_es_1prong1pizero_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    proc_intersection = list(set(self._tes_sys_processes) & set(channel_holder._processes.keys()))
                    self._logger.debug('\n\nTES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            if 'EMB' in self._shifts:
                self._logger.info('\n\nEMB shifts...')
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
                    self._logger.debug('\nEMB::variation name: %s\nintersection self._emb_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            if 'Zpt' in self._shifts:
                self._logger.info('\n\nZ pt reweighting')
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
                self._logger.info('\n\nFES_shifts...')
                # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                # Pipelines for producing shapes for calculating the TauElectronFakeEnergyCorrection*
                root_str = lambda x: str(x).replace("-", "neg").replace(".", "p")
                for es in self._etau_es_shifts:
                    shift_str = root_str(es)
                    # TODO: here the pipeline WILL depend on the category per DM
                    for pipeline in ["eleTauEsInclusiveShift_", "eleTauEsOneProngShift_", "eleTauEsOneProngPiZerosShift_", "eleTauEsThreeProngShift_"]:  # TODO: add inclusive
                        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                        variation = DifferentPipeline(name='CMS_fes_' + pipeline + '13TeV_', pipeline=pipeline, direction=shift_str)
                        proc_intersection = list(set(self._fes_sys_processes) & set(channel_holder._processes.keys()))
                        self._logger.debug('\nvariation name: %s\nintersection self._fes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                        for process_nick in proc_intersection:
                            self._systematics.add_systematic_variation(
                                variation=variation,
                                process=channel_holder._processes[process_nick],
                                channel=channel_holder._channel_obj,
                                era=self.era
                            )

                            # Upplying cuts that are only for fes shifts
                            for shift_systematic in self._systematics._systematics[-len(categories):]:
                                for cut_key, cut_expression in self._fes_extra_cuts.iteritems():
                                    shift_systematic.category.cuts.add(Cut(cut_expression, cut_key))
                                shift_systematic._process._estimation_method._directory = self._fes_friend_directory[0]

                                # Removing shifts from unmatching by decay mode requirement categories
                                if ('InclusiveShift' in pipeline and len(intersection(shift_systematic.category.cuts.names, ['dm0', 'dm1', 'dm10'])) != 0) \
                                or ('OneProngShift' in pipeline and len(intersection(shift_systematic.category.cuts.names, ['alldm', 'dm1', 'dm10'])) != 0) \
                                or ('OneProngPiZerosShift' in pipeline and len(intersection(shift_systematic.category.cuts.names, ['alldm', 'dm0', 'dm10'])) != 0) \
                                or ('ThreeProngShift' in pipeline and len(intersection(shift_systematic.category.cuts.names, ['alldm', 'dm0', 'dm1'])) != 0):
                                    self._logger.debug("Removing systematic shift %s from production because of unmatching dm in categorisation" % (shift_systematic.name))
                                    self._systematics._systematics.remove(shift_systematic)
                                    # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())

                            # for cut_key, cut_expression in self._fes_extra_cuts.iteritems():
                            #     self._systematics._systematics[-1].category.cuts.add(Cut(cut_expression, cut_key))
                            # self._systematics._systematics[-1]._process._estimation_method._directory = self._fes_friend_directory[0]
                            # exit(1)
                            # for i in self._systematics._systematics: print 'name:', i._variation._name if 'Nominal' == i._variation._name else  ['pipeline:', i._variation._pipeline, i._process._estimation_method._directory]
                            # self._systematics._systematics[-1]._variation._name, self._systematics._systematics[-1]._category._name
                            # self._systematics._systematics[-1]._variation._pipeline
                            # self._systematics._systematics[-1]._process._estimation_method._directory

            if 'FF' in self._shifts:
                self._logger.info('\n\n FF related uncertainties ...')
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


if __name__ == '__main__':
    args = ETauFES.parse_arguments()
    etau_fes = ETauFES(**args)
    print etau_fes
