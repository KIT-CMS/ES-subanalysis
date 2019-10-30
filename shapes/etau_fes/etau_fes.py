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
    ReplaceWeight, SquareAndRemoveWeight, AddWeight, Relabel


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
            self._logger.info('...binning')
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

            # active processes in groups
            mc_processes = [key for key in channel_holder._processes.keys() if 'data' not in key and 'EMB' not in key]
            sm_ggH_processes = [key for key in channel_holder._processes.keys() if any(x in key for x in ["ggH125", "ggH_GG2H", "ggHToWW"])]

            # print '\n nominal...'
            self._logger.info('\n\nNominal...')
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

            # TODO: decorrelate emb, mc, year
            # Tau energy scale (general, MC-specific & EMB-specific), it is mt, et & tt specific
            if 'TES' in self._shifts and channel_name in ['mt', 'et', 'tt']:
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

                # TODO -> uncorrelate
                # self._logger.info('\n\nTES...')
                # # general
                # decorr = {
                #     '': self._tes_sys_processes,
                #     '_mc': self._tes_sys_processes_mc_uncor,
                #     '_emb': self._tes_sys_processes_mc_uncor
                # }
                # for key, decorr_proc in decorr.iteritems():
                #     tau_es_3prong_variations = create_systematic_variations(name="CMS_scale%s_t_3prong_13TeV" % key, property_name="tauEsThreeProng", systematic_variation=DifferentPipeline)
                #     tau_es_1prong_variations = create_systematic_variations(name="CMS_scale%s_t_1prong_13TeV" % key, property_name="tauEsOneProng", systematic_variation=DifferentPipeline)
                #     tau_es_1prong1pizero_variations = create_systematic_variations(name="CMS_scale%s_t_1prong1pizero_13TeV" % key, property_name="tauEsOneProngOnePiZero", systematic_variation=DifferentPipeline)

                #     for variation in tau_es_3prong_variations + tau_es_1prong_variations + tau_es_1prong1pizero_variations:
                #         # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                #         proc_intersection = list(set(decorr_proc) & set(channel_holder._processes.keys()))
                #         self._logger.debug('\n\nTES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                #         for process_nick in proc_intersection:
                #             self._systematics.add_systematic_variation(
                #                 variation=variation,
                #                 process=channel_holder._processes[process_nick],
                #                 channel=channel_holder._channel_obj,
                #                 era=self.era
                #             )

            # EMB charged track correction uncertainty (DM-dependent)
            if 'EMB' in self._shifts:
                self._logger.info('\n\n EMB shifts...')
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

            # EMB?: 10% removed events in ttbar simulation (ttbar -> real tau tau events) added/subtracted to EMB shape to use as systematic.
            if 'ZTTpTT' in self._shifts:
                # ! Technical procedure different to usual systematic variations!
                self._logger.info('\n\n ZTTpTT shifts...')

                # for process_nick, category in product(proc_intersection, categories):
                for category, shift in product(categories, ["Up", "Down"]):
                    self._systematics.add(
                        Systematic(
                            category=category,
                            process=channel_holder._processes['ZTTpTTTauTau%s' % shift],
                            analysis=self._context_analysis,
                            era=self.era,
                            variation=Relabel("CMS_htt_emb_ttbar_13TeV", shift),
                            mass="125"))

            # TODO: check if in the loop there is only 1 year per loop iter
            if 'prefiring' in self._shifts:
                self._logger.info('\n\n prefiring shifts...')

                prefiring_variations = []
                for process, category in product(processes, categories):
                    if '2017' not in process._estimation_method._era.__class__.__name__:
                        continue
                    for updownvar in ['Up', 'Down']:
                        prefiring_variations.append(
                            ReplaceWeight(
                                "CMS_prefiring_13TeV",
                                "prefireWeight",
                                Weight(
                                    "prefiringweight%s" % updownvar.lower(),
                                    "prefireWeight"),
                                updownvar))

                for variation in prefiring_variations:
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # Z pt reweighting
            if 'Zpt' in self._shifts:
                self._logger.info('\n\n Z pt reweighting')
                zpt_variations = create_systematic_variations(
                    name="CMS_htt_dyShape_13TeV",
                    property_name="zPtReweightWeight",
                    systematic_variation=SquareAndRemoveWeight,
                )

                for variation in zpt_variations:
                    for process_nick in ETauFES.intersection(self._zpt_sys_processes, channel_holder._processes.keys()):
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # top pt reweighting
            if 'Tpt' in self._shifts:
                self._logger.info('\n\ntop pt reweighting')
                tpt_variations = create_systematic_variations(
                    name="CMS_htt_ttbarShape_13TeV",
                    property_name="topPtReweightWeight",
                    systematic_variation=SquareAndRemoveWeight,
                )

                for variation in tpt_variations:
                    for process_nick in ETauFES.intersection(self._tpt_sys_processes, channel_holder._processes.keys()):
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

            # jetfakes
            if 'FF' in self._shifts and channel_name in ['mt', 'et', 'tt']:
                self._logger.info('\n\n FF related uncertainties ...')
                fake_factor_variations_et = []

                if channel_name in ['mt', 'et']:
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
                                    "CMS_%s" % (systematic_shift.format(ch='_' + channel_name, shift="").replace("_dm0", "")),
                                    "fake_factor",
                                    Weight(
                                        "ff2_{syst}".format(
                                            syst=systematic_shift.format(ch="", shift="_%s" % shift_direction.lower()).replace("_13TeV", "")),
                                        "fake_factor"),
                                    shift_direction))

                elif channel_name == 'tt':
                    for systematic_shift in [
                            "ff_qcd{ch}_syst_13TeV{shift}",
                            "ff_qcd_dm0_njet0{ch}_stat_13TeV{shift}",
                            "ff_qcd_dm0_njet1{ch}_stat_13TeV{shift}",
                            "ff_w{ch}_syst_13TeV{shift}", "ff_tt{ch}_syst_13TeV{shift}",
                            "ff_w_frac{ch}_syst_13TeV{shift}",
                            "ff_tt_frac{ch}_syst_13TeV{shift}"
                    ]:
                        for shift_direction in ["Up", "Down"]:
                            fake_factor_variations_et.append(
                                ReplaceWeight(
                                    "CMS_%s" % (systematic_shift.format(ch='_' + channel_name, shift="").replace("_dm0", "")),
                                    "fake_factor",
                                    Weight(
                                        "(0.5*ff1_{syst}*(byTightIsolationMVArun2017v2DBoldDMwLT2017_1<0.5)+0.5*ff2_{syst}*(byTightIsolationMVArun2017v2DBoldDMwLT2017_2<0.5))".format(
                                            syst=systematic_shift.format(ch="", shift="_%s" % shift_direction.lower()).replace("_13TeV", "")),
                                        "fake_factor"),
                                    shift_direction))

                for k in [k for k in channel_holder._processes.keys() if 'jetFakes' in k]:
                    for variation in fake_factor_variations_et:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[k],
                            channel=channel_holder._channel_obj,
                            era=self.era)

            # QCD for em
            if 'QCDem' in self._shifts and channel_name == 'em':  # TODO: generalize?
                qcd_variations = []
                for shift in ['Up', 'Down']:
                    qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_rate_Run2017", "qcd_weight", Weight("em_qcd_osss_0jet_rate%s_Weight*em_qcd_extrap_uncert_Weight" % shift, "qcd_weight"), shift))
                    qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_shape_Run2017", "qcd_weight", Weight("em_qcd_osss_0jet_shape%s_Weight*em_qcd_extrap_uncert_Weight" % shift, "qcd_weight"), shift))
                    qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_shape_Run2017", "qcd_weight", Weight("em_qcd_osss_1jet_shape%s_Weight*em_qcd_extrap_uncert_Weight" % shift, "qcd_weight"), shift))

                for year_correlation in ['', '_Run2017']:
                    qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s", "qcd_weight", Weight("em_qcd_extrap_up_Weight*em_qcd_extrap_uncert_Weight", "qcd_weight"), updownvar))
                    qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s", "qcd_weight", Weight("em_qcd_osss_binned_Weight", "qcd_weight"), "Down"))

                for variation in qcd_variations:
                    proc_intersection = ETauFES.intersection(self._qcdem_sys_processes, channel_holder._processes.keys())
                    self._logger.debug('\n QCDem::variation name: %s\nintersection self._qcdem_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era)

            # Gluon-fusion WG1 uncertainty scheme, for sm signals (Uncertainty: Theory uncertainties)
            if 'WG1' in self._shifts:
                ggh_variations = []
                THU_unc = [
                    "THU_ggH_Mig01", "THU_ggH_Mig12", "THU_ggH_Mu", "THU_ggH_PT120",
                    "THU_ggH_PT60", "THU_ggH_Res", "THU_ggH_VBF2j", "THU_ggH_VBF3j",
                    "THU_ggH_qmtop"
                ]
                for unc in THU_unc:
                    ggh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("({})".format(unc), "{}_weight".format(unc)), "Up"))
                    ggh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("(1.0/{})".format(unc), "{}_weight".format(unc)), "Down"))

                for process_nick, variation in product(sm_ggH_processes, ggh_variations):
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # TODO: decor. emb and mc
            # Lepton trigger efficiency; the same values for (MC & EMB) and (mt & et)
            if 'TrgEff' in self._shifts and channel_name in ["mt", "et"]:
                self._logger.info('\n\n Lepton trigger efficiency uncertainties (same for [MC & EMB], [mt & et])')
                lep_trigger_eff_variations = []
                # MC
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_trigger_%s_13TeV" % (channel_name),
                        "trg_%s_eff_weight" % channel_name,
                        Weight("(1.0*(pt_1<=25)+1.02*(pt_1>25))", "trg_%s_eff_weight" % channel_name),
                        "Up"))
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_trigger_%s_13TeV" % (channel_name),
                        "trg_%s_eff_weight" % channel_name,
                        Weight("(1.0*(pt_1<=25)+0.98*(pt_1>25))", "trg_%s_eff_weight" % channel_name),
                        "Down"))
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_xtrigger_%s_13TeV" % (channel_name),
                        "xtrg_%s_eff_weight" % channel_name,
                        Weight("(1.054*(pt_1<=25)+1.0*(pt_1>25))", "xtrg_%s_eff_weight" % channel_name),
                        "Up"))
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_xtrigger_%s_13TeV" % (channel_name),
                        "xtrg_%s_eff_weight" % channel_name,
                        Weight("(0.946*(pt_1<=25)+1.0*(pt_1>25))", "xtrg_%s_eff_weight" % channel_name),
                        "Down"))

                for variation in lep_trigger_eff_variations:
                    self._logger.debug('\n\n TrgEff::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # Splitted JES shapes
            if 'JES' in self._shifts:
                self._logger.info('\n\n JES reweighting')
                jet_es_variations = create_systematic_variations(name="CMS_scale_j_eta0to3_Run2017", property_name="jecUncEta0to3", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_eta0to5_Run2017", property_name="jecUncEta0to5", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_eta3to5_Run2017", property_name="jecUncEta3to5", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_RelativeBal_Run2017", property_name="jecUncRelativeBal", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_RelativeSample_Run2017", property_name="jecUncRelativeSample", systematic_variation=DifferentPipeline)

                for variation in jet_es_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    # proc_intersection = list(set(self._jes_sys_processes) & set(channel_holder._processes.keys()))
                    # self._logger.debug('\n\n JES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process in processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=process,
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # B-tagging
            if 'BTag' in self._shifts:
                self._logger.info('\n\n BTag reweighting')
                btag_eff_variations = create_systematic_variations("CMS_htt_eff_b_Run2017", "btagEff", DifferentPipeline)
                mistag_eff_variations = create_systematic_variations("CMS_htt_mistag_b_Run2017", "btagMistag", DifferentPipeline)

                for variation in btag_eff_variations + mistag_eff_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    # proc_intersection = list(set(self._jes_sys_processes) & set(channel_holder._processes.keys()))
                    # self._logger.debug('\n\n BTag::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process in processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=process,
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # MET energy scale. Note: only those variations for non-resonant processes are used in the stat. inference
            if 'METES' in self._shifts:
                self._logger.info('\n\n METES reweighting')
                met_unclustered_variations = create_systematic_variations("CMS_scale_met_unclustered", "metUnclusteredEn", DifferentPipeline)

                proc_intersection = list(set(self._met_sys_processes) & set(channel_holder._processes.keys()))
                self._logger.debug('\n\n METES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                for process_nick in proc_intersection:
                    self._systematics.add_systematic_variation(
                        variation=met_unclustered_variations,
                        process=channel_holder._processes[process_nick],
                        channel=channel_holder._channel_obj,
                        era=self.era
                    )

            # Ele energy scale (EMB-specific),  it is et & em specific
            if 'EES' in self._shifts and channel_name in ["et", "em"]:
                self._logger.info('\n\n EES reweighting')
                ele_es_emb_variations = create_systematic_variations("CMS_scale_emb_e", "eleEs", DifferentPipeline)

                # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                proc_intersection = list(set(self._ees_sys_processes) & set(channel_holder._processes.keys()))
                # self._logger.debug('\n\n BTag::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                for process_nick in processes:
                    self._systematics.add_systematic_variation(
                        variation=ele_es_emb_variations,
                        process=channel_holder._processes[process_nick],
                        channel=channel_holder._channel_obj,
                        era=self.era
                    )

            # ZL fakes energy scale
            if 'ZES' in self._shifts and channel_name in ["et", "em"]:
                self._logger.info('\n\n ZES reweighting')
                fakelep_dict = {"et": "Ele", "mt": "Mu"}

                lep_fake_es_variations = create_systematic_variations("CMS_ZLShape_%s_1prong_Run2017" % channel_name, "tau%sFakeEsOneProng" % fakelep_dict[channel_name], DifferentPipeline)
                lep_fake_es_variations += create_systematic_variations("CMS_ZLShape_%s_1prong1pizero_Run2017" % channel_name, "tau%sFakeEsOneProngPiZeros" % fakelep_dict[channel_name], DifferentPipeline)

                for variation in lep_fake_es_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    proc_intersection = list(set(self._zl_sys_processes) & set(channel_holder._processes.keys()))
                    # self._logger.debug('\n\n BTag::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )


if __name__ == '__main__':
    args = ETauFES.parse_arguments()
    etau_fes = ETauFES(**args)
    print etau_fes
