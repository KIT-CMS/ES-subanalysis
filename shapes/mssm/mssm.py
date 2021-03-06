import sys
import importlib
import itertools
import logging
from collections import OrderedDict

from shapes import Shapes

from shapes.channelholder import ChannelHolder
# TODO: needs to be moved from global imports
# from shape_producer.process import Process  # move to ChannelsHolder
# from shape_producer.variable import Variable  # move to ChannelsHolder
# from shape_producer.binning import VariableBinning  # move to ChannelsHolder
from shape_producer.cutstring import Cut, Weight  # move to ChannelsHolder
from shape_producer.systematics import Systematic
from shape_producer.systematic_variations import Nominal, DifferentPipeline, create_systematic_variations, \
    ReplaceWeight, SquareAndRemoveWeight, AddWeight, Relabel, ReplaceExpressions


class MSSM(Shapes):
    def __init__(self, **kvargs):
        logging.getLogger(__name__).info("Init " + self.__class__.__name__)
        super(MSSM, self).__init__(**kvargs)

        self._logger = logging.getLogger(__name__)

        self._variables = []
        self._estimation_methods = {}

    def getEvaluatedChannel(self, channel, variables):
        """
        Creates and returns channel_holder for requested channel
        """
        if channel in ['et', 'mt', 'tt', 'em']:
            self._logger.info('getEvaluatedChannel: %s' % channel)
            if channel == 'et':
                minplotlevel_cuts = self._et_minplotlev_cuts
                friend_directory = self._et_friend_directory
                if self._era_name == '2017':
                    from shape_producer.channel import ETMSSM2017 as channel_obj
                elif self._era_name == '2018':
                    from shape_producer.channel import ETMSSM2018 as channel_obj
                elif self._era_name == '2016':
                    from shape_producer.channel import ETMSSM2016 as channel_obj
            elif channel == 'mt':
                minplotlevel_cuts = self._mt_minplotlev_cuts
                friend_directory = self._mt_friend_directory
                if self._era_name == '2017':
                    from shape_producer.channel import MTMSSM2017 as channel_obj
                elif self._era_name == '2018':
                    from shape_producer.channel import MTMSSM2018 as channel_obj
                elif self._era_name == '2016':
                    from shape_producer.channel import MTMSSM2016 as channel_obj
            elif channel == 'tt':
                minplotlevel_cuts = self._tt_minplotlev_cuts
                friend_directory = self._tt_friend_directory
                if self._era_name == '2017':
                    from shape_producer.channel import TTMSSM2017 as channel_obj
                elif self._era_name == '2018':
                    from shape_producer.channel import TTMSSM2018 as channel_obj
                elif self._era_name == '2016':
                    from shape_producer.channel import TTMSSM2016 as channel_obj
            elif channel == 'em':
                minplotlevel_cuts = self._em_minplotlev_cuts
                friend_directory = self._em_friend_directory
                if self._era_name == '2017':
                    from shape_producer.channel import EMMSSM2017 as channel_obj
                elif self._era_name == '2018':
                    from shape_producer.channel import EMMSSM2018 as channel_obj
                elif self._era_name == '2016':
                    from shape_producer.channel import EMMSSM2016 as channel_obj

            # init channelholder for specific channel
            channel_holder = ChannelHolder(
                ofset=self._ofset + 1,
                logger=self._logger,
                debug=self._debug,
                channel_obj=channel_obj(),
                friend_directory=friend_directory,
            )

            # inverting cuts
            for k in self._invert_cuts:
                if k in channel_holder._channel_obj.cuts.names:
                    warning_message = "Inverting cut %s from old value [%s] " % (k, channel_holder._channel_obj.cuts.get(k))
                    channel_holder._channel_obj.cuts.get(k).invert()
                    warning_message += "to new value [%s]" % (channel_holder._channel_obj.cuts.get(k))
                    self._logger.warning(warning_message)
                else:
                    self._logger.error("Couldn't invert cut %s - not found in the original cuts: %s" % (k, channel_holder))

            # forcing cuts
            for k, v in self._force_cuts.iteritems():
                channel_holder._channel_obj.cuts.remove(k)
                if v is not None:
                    channel_holder._channel_obj.cuts.add(Cut(v, k))
                self._logger.warning('global cut value forced: {"%s": "%s"}' % (k, v))

            # miplotlevel cuts
            for k, v in minplotlevel_cuts.iteritems():
                channel_holder._channel_obj.cuts.remove(k)
                if v is not None:
                    channel_holder._channel_obj.cuts.add(Cut(v, k))
                self._logger.warning('global cut value forced: {"%s": "%s"}' % (k, v))

            # get respective processes, variables, binning
            self._logger.info('...getProcesses')

            channel_holder._processes = self.getProcesses(
                channel_obj=channel_holder._channel_obj,
                friend_directory=friend_directory
            )
            self._logger.info('...getVariables')
            self._logger.info('...binning')
            if channel_holder._channel_obj._name not in self.binning[self._binning_key]:
                raise Exception("Binning for %s undefined" % channel_holder._channel_obj._name)
            channel_holder._variables = self.getVariables(
                channel_obj=channel_holder._channel_obj,
                variable_names=variables,
                binning=self.binning[self._binning_key][channel_holder._channel_obj._name]
            )
            self._logger.info('...getCategorries')
            channel_holder._categorries = self.getCategorries(
                channel_holder=channel_holder
            )
            # import pdb; pdb.set_trace()

            self._logger.info('...getChannelSystematics')
            channel_holder._systematics = self.getChannelSystematics(
                channel_holder=channel_holder
            )

            return channel_holder
        else:
            raise KeyError("getEvaluatedChannel: channel not setup. channel:" + channel +
                "; context:" + self._context_analysis + '; eta: ' + self._era_name)

    def getUpdateExtrapFactorProcessPerCategory(self, process, category):
        # values calculated for MVAv2, 'dilepton_veto': Null
        # TODO: have a config for this
        # DT
        DT = {
            '2016': {
                "et_inc_eta_2_njetN_alldm": 1.22,  # +-?0.05
                "et_inc_eta_2_njetN_dm0": 1.244,  # 0.18
                "et_inc_eta_2_njetN_dm1": 1.23,  # 0.08
                "et_eta_2_barel_njetN_alldm": 1.24,  # 0.05
                "et_eta_2_barel_njetN_dm0": 1.2, #1.23,  # 0.18
                "et_eta_2_barel_njetN_dm1": 1.22,  # 0.08
                "et_eta_2_endcap_njetN_alldm": 1.15,  # +-0.1
                "et_eta_2_endcap_njetN_dm0": 1.28,  # +- 0.2
                "et_eta_2_endcap_njetN_dm1": 1.26,  # +-0.15
            },
            '2017': {
                "et_inc_eta_2_njetN_alldm": 1.05,  # 0.05
                "et_inc_eta_2_njetN_dm0": 1.122,  # 0.15
                "et_inc_eta_2_njetN_dm1": 1.075,  # 0.05
                "et_eta_2_barel_njetN_alldm": 1.069,  # 0.05
                "et_eta_2_barel_njetN_dm0": 1.19,  # 0.15
                "et_eta_2_barel_njetN_dm1": 1.07,  # 0.08
                "et_eta_2_endcap_njetN_alldm": 1.001,  # 1.15
                "et_eta_2_endcap_njetN_dm0": 1.018,  # 0.2
                "et_eta_2_endcap_njetN_dm1": 1.08,  # 0.15
            },
            '2018': {
                "et_inc_eta_2_njetN_alldm": 1.17,  # 0.05
                "et_inc_eta_2_njetN_dm0": 1.101,  # 0.1
                "et_inc_eta_2_njetN_dm1": 1.2,  # 0.5
                "et_eta_2_barel_njetN_alldm": 1.19,  # 0.04
                "et_eta_2_barel_njetN_dm0": 1.09,  # 0.1
                "et_eta_2_barel_njetN_dm1": 1.24,  # 0.05
                "et_eta_2_endcap_njetN_alldm": 1.12,  # 0.08
                "et_eta_2_endcap_njetN_dm0": 1.115,  # 0.2
                "et_eta_2_endcap_njetN_dm1": 1.04,  # 0.1
            },
        }
        if process.name == "QCDSStoOS":
            if '2016' in process._estimation_method._era.__class__.__name__ and 'et' in category.name:
                process._estimation_method._extrapolation_factor = DT['2016'][category.name]
            elif '2017' in process._estimation_method._era.__class__.__name__ and 'et' in category.name:
                process._estimation_method._extrapolation_factor = DT['2017'][category.name]
            else:
                process._estimation_method._extrapolation_factor = DT['2018'][category.name]

        # MVA
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
            # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())

            # active MC processes in groups
            mc_processes = set([key for key in channel_holder._processes.keys() if 'data' not in key and 'EMB' not in key and "jetFakes" not in key])

            # signals (as for MSSM)
            signal_processes = set([key for key in channel_holder._processes.keys() if 'SUSY' in channel_holder._processes[key].name])

            sm_vh_processes = set([key for key in channel_holder._processes.keys() if any(p in key for p in ["WH125", "ZH125", "VH125", "ttH125"])])

            sm_gghww_processes = set([key for key in channel_holder._processes.keys() if any(p in key for p in ["ggHWW125"])])
            sm_qqhww_processes = set([key for key in channel_holder._processes.keys() if any(p in key for p in ["qqHWW125"])])
            sm_vvhww_processes = set([key for key in channel_holder._processes.keys() if any(p in key for p in ['WHWW125', 'ZHWW125'])])
            sm_hww_processes = sm_gghww_processes | sm_qqhww_processes | sm_vvhww_processes

            sm_ggh_processes = set([key for key in channel_holder._processes.keys() if any(p in key and 'SUSY' not in key for p in ["ggH125"])])
            # print "sm_ggh_processes:", sm_ggh_processes
            sm_qqh_processes = set([key for key in channel_holder._processes.keys() if any(p in key and 'SUSY' not in key for p in ["qqH125"])])
            # print "sm_qqh_processes:", sm_qqh_processes
            sm_h_processes = sm_qqh_processes | sm_ggh_processes

            sm_h_processes = sm_vh_processes | sm_hww_processes | sm_h_processes
            # sm_htt_signals_nicks = [ggH_htxs for ggH_htxs in ggHEstimation.htxs_dict] + [qqH_htxs for qqH_htxs in qqHEstimation.htxs_dict]

            # sm_ggH_processes = [key for key in channel_holder._processes.keys() if any(x in key for x in ["ggH125", "ggH_GG2H", "ggHToWW"])]
            # sm_qqH_processes = [key for key in channel_holder._processes.keys() if any(x in key for x in ["qqH125", "qqH_GG2H", "qqHToWW"])]
            # sm_VH_processes = [key for key in channel_holder._processes.keys() if any(x in key for x in ["WH125", "ZH125", "ttH125"])]
            # mssm_ggH_signals = {"ggh_t", "ggh_b", "ggh_i", "ggH_t", "ggH_b", "ggH_i", "ggA_t", "ggA_b", "ggA_i"};
            # mssm_bbH_signals = {"bbA", "bbH", "bbh"};

            # print '\n nominal...'
            self._logger.info('\n\nNominal...')
            from itertools import product
            for process, category in product(processes, categories):
                self._systematics.add(
                    Systematic(
                        category=category,
                        process=self.getUpdateExtrapFactorProcessPerCategory(process, category) if self._update_process_per_category else process,
                        analysis=self._context_analysis,  # "smhtt",  # TODO : check if this is used anywhere, modify the configs sm->smhtt
                        era=self.era,
                        variation=Nominal(),
                        mass="125",  # TODO : check if this is used anywhere
                    )
                )

            # TODO: decorrelate emb{emb,ff}, mc
            # Tau energy scale (general, MC-specific & EMB-specific), it is mt, et & tt specific
            # note: "CMS_scale_emb_t_3prong_Run{era}" I call like "CMS_scale_t_3prong_Run{era}"
            if 'TES' in self._shifts and channel_name in ['mt', 'et', 'tt']:
                self._logger.info('\n\nTES...')
                tau_es_3prong_variations = create_systematic_variations(name="CMS_scale_t_3prong_Run%s" % channel_holder._year, property_name="tauEsThreeProng", systematic_variation=DifferentPipeline)
                tau_es_1prong_variations = create_systematic_variations(name="CMS_scale_t_1prong_Run%s" % channel_holder._year, property_name="tauEsOneProng", systematic_variation=DifferentPipeline)
                tau_es_1prong1pizero_variations = create_systematic_variations(name="CMS_scale_t_1prong1pizero_Run%s" % channel_holder._year, property_name="tauEsOneProngOnePiZero", systematic_variation=DifferentPipeline)

                for variation in tau_es_3prong_variations + tau_es_1prong_variations + tau_es_1prong1pizero_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    proc_intersection = set(self._tes_sys_processes) & set(channel_holder._processes.keys())
                    self._logger.debug('\n\nTES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in signal_processes | sm_h_processes | proc_intersection:
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
                #     tau_es_3prong_variations = create_systematic_variations(name="CMS_scale%s_t_3prong_Run%s" % (key, channel_holder._year), property_name="tauEsThreeProng", systematic_variation=DifferentPipeline)
                #     tau_es_1prong_variations = create_systematic_variations(name="CMS_scale%s_t_1prong_Run%s" % (key, channel_holder._year), property_name="tauEsOneProng", systematic_variation=DifferentPipeline)
                #     tau_es_1prong1pizero_variations = create_systematic_variations(name="CMS_scale%s_t_1prong1pizero_Run%s" % (key, channel_holder._year), property_name="tauEsOneProngOnePiZero", systematic_variation=DifferentPipeline)

                #     for variation in tau_es_3prong_variations + tau_es_1prong_variations + tau_es_1prong1pizero_variations:
                #         # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                #         proc_intersection = set(decorr_proc) & set(channel_holder._processes.keys())
                #         self._logger.debug('\n\nTES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                #         for process_nick in signal_processes | proc_intersection:
                #             self._systematics.add_systematic_variation(
                #                 variation=variation,
                #                 process=channel_holder._processes[process_nick],
                #                 channel=channel_holder._channel_obj,
                #                 era=self.era
                #             )

            # Tau ID: TODO: NOT DEBUGED
            if 'TauID' in self._shifts and channel_name in ['mt', 'et', 'tt']:
                self._logger.info('\n\nTauID...')
                tau_id_variations = []
                tau_id_variations_emb = []
                if channel_name == 'tt':
                    for idd, (shift, dm) in enumerate(itertools.product(['Up', 'Down'], [0, 1, 10])):
                        # weightstr = "(((decayMode_1=={dm})*tauIDScaleFactorWeight{shift}_tight_MVAoldDM2017v2_1)+((decayMode_1!={dm})*tauIDScaleFactorWeight_tight_MVAoldDM2017v2_1)*((decayMode_2=={dm})*tauIDScaleFactorWeight{shift}_tight_MVAoldDM2017v2_2)+((decayMode_2!={dm})*tauIDScaleFactorWeight_tight_MVAoldDM2017v2_2))".format(dm=dm, shift=shift)
                        weightstr = "(((decayMode_1=={dm})*tauIDScaleFactorWeight{shift}_tight_MVAoldDM2017v2_1+ (decayMode_1!={dm})*tauIDScaleFactorWeight_tight_MVAoldDM2017v2_1)*((decayMode_2=={dm})*tauIDScaleFactorWeight{shift}_tight_MVAoldDM2017v2_2+(decayMode_2!={dm})*tauIDScaleFactorWeight_tight_MVAoldDM2017v2_2))".format(dm=dm, shift=shift)
                        tau_id_variations.append(ReplaceWeight("CMS_eff_t_dm%d_Run%s" % (dm, channel_holder._year), "taubyIsoIdWeight", Weight(weightstr, "taubyIsoIdWeight"), shift))
                        tau_id_variations_emb.append(ReplaceWeight("CMS_emb_eff_t_dm%d_Run%s" % (dm, channel_holder._year), "taubyIsoIdWeight", Weight(weightstr, "taubyIsoIdWeight"), shift))
                else:
                    pt_ranges = [30, 35, 40, 500, 1000, "inf"]
                    pt_bins = [((i), (i + 1)) for i in range(len(pt_ranges) - 1)]
                    for idd, (shift, (bin_low, bin_high)) in enumerate(itertools.product(['Up', 'Down'], pt_bins)):
                        weightstr = "(((pt_2 >= {bin_low} && pt_2 <= {bin_high})*tauIDScaleFactorWeight{shift}_tight_MVAoldDM2017v2_2)+((pt_2 < {bin_low} || pt_2 > {bin_high})*tauIDScaleFactorWeight_tight_MVAoldDM2017v2_2))".format(
                            bin_low=pt_ranges[bin_low],
                            bin_high=pt_ranges[bin_high],
                            shift=shift).replace(' && pt_2 <= inf', '').replace(' || pt_2 > inf', '')
                        tau_id_variations.append(ReplaceWeight("CMS_eff_t_%s-%s_Run%s" % (pt_ranges[bin_low], pt_ranges[bin_high], channel_holder._year), "taubyIsoIdWeight", Weight(weightstr, "taubyIsoIdWeight"), shift))
                        tau_id_variations_emb.append(ReplaceWeight("CMS_eff_emb_t_%s-%s_Run%s" % (pt_ranges[bin_low], pt_ranges[bin_high], channel_holder._year), "taubyIsoIdWeight", Weight(weightstr, "taubyIsoIdWeight"), shift))
                        # tau_id_variations.append(ReplaceWeight("CMS_eff_t_%d-%d_Run%s" % (bin_low, bin_high, channel_holder._year), "taubyIsoIdWeight", Weight(weightstr, "taubyIsoIdWeight"), shift))
                        # tau_id_variations_emb.append(ReplaceWeight("CMS_eff_emb_t_%d-%d_Run%s" % (bin_low, bin_high, channel_holder._year), "taubyIsoIdWeight", Weight(weightstr, "taubyIsoIdWeight"), shift))

                if 'EMB' in channel_holder._processes.keys():
                    self._logger.debug('\n\nTauID::variation name: %s\nintersection self._tauid_sys_processes: [EMB]' % (variation.name))
                    for variation in tau_id_variations_emb:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes['EMB'],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

                for variation in tau_id_variations:
                    proc_intersection = set(self._tauid_sys_processes) & set(channel_holder._processes.keys())
                    self._logger.debug('\n\nTauID::variation name: %s\nintersection self._tauid_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in signal_processes | sm_h_processes | proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # EMB charged track correction uncertainty (DM-dependent): Ele energy scale : not applied to signals
            if 'EMB' in self._shifts and channel_name in ['mt', 'et', 'tt']:
                self._logger.info('\n\n EMB shifts...')
                decayMode_variations = []
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_3ProngEff_Run%s" % channel_holder._year, "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effUp_pi0Nom", "decayMode_SF"),
                        "Up"))
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_3ProngEff_Run%s" % channel_holder._year, "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effDown_pi0Nom", "decayMode_SF"),
                        "Down"))
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_1ProngPi0Eff_Run%s" % channel_holder._year, "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effNom_pi0Up", "decayMode_SF"),
                        "Up"))
                decayMode_variations.append(
                    ReplaceWeight(
                        "CMS_1ProngPi0Eff_Run%s" % channel_holder._year, "decayMode_SF",
                        Weight("embeddedDecayModeWeight_effNom_pi0Down", "decayMode_SF"),
                        "Down"))

                for variation in decayMode_variations:
                    proc_intersection = set(self._emb_sys_processes) & set(channel_holder._processes.keys())
                    self._logger.debug('\nEMB::variation name: %s\nintersection self._emb_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # EMB : not applied to signals
            # 10% removed events in ttbar simulation (ttbar -> real tau tau events) added/subtracted to EMB shape to use as systematic.
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
                            variation=Relabel("CMS_htt_emb_ttbar_Run%s" % channel_holder._year, shift),
                            mass="125"))

            # TODO: check if in the loop there is only 1 year per loop iter
            if 'prefiring' in self._shifts and channel_holder._year != '2018':
                self._logger.info('\n\n prefiring shifts...')

                prefiring_variations = []
                # for process, category in product(processes, categories):
                #     if '2017' not in process._estimation_method._era.__class__.__name__:
                #     continue
                # print "categories:", categories, categories[0].name
                # print "processes:", processes, [p.name for p in processes]
                for updownvar in ['Up', 'Down']:
                    prefiring_variations.append(
                        ReplaceWeight(
                            # "CMS_prefiring_Run%s" % channel_holder._year,
                            "CMS_prefiring",
                            "prefireWeight",
                            Weight(
                                "prefiringweight%s" % updownvar.lower(),
                                "prefireWeight"),
                            updownvar))

                # # import pdb; pdb.set_trace()
                # print "bef:", len(self._systematics._systematics)
                # for variation in prefiring_variations:
                #     for process_nick in mc_processes:
                #         print process_nick, variation

                # print "aft:"
                for variation in prefiring_variations:
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )
                # print "aft:", len(self._systematics._systematics)
                # exit(0)

            # Z pt reweighting : not applied to signals
            if 'Zpt' in self._shifts:
                self._logger.info('\n\n Z pt reweighting')
                zpt_variations = create_systematic_variations(
                    name="CMS_htt_dyShape_Run%s" % channel_holder._year if channel_holder._year != '2018' else "CMS_htt_dyShape",
                    property_name="zPtReweightWeight",
                    systematic_variation=SquareAndRemoveWeight,
                )

                for variation in zpt_variations:
                    for process_nick in MSSM.intersection(self._zpt_sys_processes, channel_holder._processes.keys()):
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # top pt reweighting : not applied to signals
            if 'Tpt' in self._shifts:
                self._logger.info('\n\ntop pt reweighting')
                tpt_variations = create_systematic_variations(name="CMS_htt_ttbarShape", property_name="topPtReweightWeightRun1", systematic_variation=SquareAndRemoveWeight,)

                for variation in tpt_variations:
                    for process_nick in MSSM.intersection(self._tpt_sys_processes, channel_holder._processes.keys()):
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # jetfakes : not applied to signals
            if 'FF' in self._shifts and channel_name in ['mt', 'et', 'tt']:
                self._logger.info('\n\n FF related uncertainties ...')
                fake_factor_variations = []

                if channel_name in ['mt', 'et']:
                    for systematic_shift in [
                            "ff_qcd_syst{ch}{runyear}{shift}",
                            "ff_qcd_dm0_njet0_stat{ch}{runyear}{shift}",
                            "ff_qcd_dm0_njet1_stat{ch}{runyear}{shift}",
                            "ff_w_syst{ch}{runyear}{shift}",
                            "ff_w_dm0_njet0_stat{ch}{runyear}{shift}",
                            "ff_w_dm0_njet1_stat{ch}{runyear}{shift}",
                            "ff_tt_syst{ch}{runyear}{shift}",
                            "ff_tt_dm0_njet0_stat{ch}{runyear}{shift}",
                            "ff_tt_dm0_njet1_stat{ch}{runyear}{shift}",
                    ]:
                        for shift_direction in ["Up", "Down"]:
                            fake_factor_variations.append(
                                ReplaceWeight(
                                    "CMS_%s" % (systematic_shift.format(
                                        ch='_' + channel_name,
                                        shift="",
                                        runyear="_%s" % channel_holder._year).replace("_dm0", "")),
                                    "fake_factor",
                                    Weight(
                                        "ff2_{syst}".format(
                                            syst=systematic_shift.format(
                                                ch="",
                                                shift="_%s" % shift_direction.lower(),
                                                runyear='').replace("_Run%s" % channel_holder._year, "")),
                                        "fake_factor"),
                                    shift_direction))

                elif channel_name == 'tt':
                    # todo: rename
                    for systematic_shift in [
                            "ff_qcd_syst{ch}{runyear}{shift}",
                            "ff_qcd_dm0_njet0_stat{ch}{runyear}{shift}",
                            "ff_qcd_dm0_njet1_stat{ch}{runyear}{shift}",
                            "ff_w_syst{ch}{runyear}{shift}",
                            "ff_tt_syst{ch}{runyear}{shift}",
                            "ff_w_frac_syst{ch}{runyear}{shift}",
                            "ff_tt_frac_syst{ch}{runyear}{shift}"
                    ]:
                        for shift_direction in ["Up", "Down"]:
                            fake_factor_variations.append(
                                ReplaceWeight(
                                    "CMS_%s" % (systematic_shift.format(
                                        ch='_' + channel_name,
                                        shift="",
                                        runyear="_%s" % channel_holder._year).replace("_dm0", "")),
                                    "fake_factor",
                                    Weight(
                                        "(0.5*ff1_{syst}*(byTightIsolationMVArun2017v2DBoldDMwLT2017_1<0.5)+0.5*ff2_{syst}*(byTightIsolationMVArun2017v2DBoldDMwLT2017_2<0.5))".format(
                                            syst=systematic_shift.format(
                                                ch="",
                                                shift="_%s" % shift_direction.lower(),
                                                runyear='').replace("_Run%s" % channel_holder._year, "")),
                                        "fake_factor"),
                                    shift_direction))

                for k in [k for k in channel_holder._processes.keys() if 'jetFakes' in k]:
                    for variation in fake_factor_variations:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[k],
                            channel=channel_holder._channel_obj,
                            era=self.era)

            # QCD for em : not applied to signals
            if 'QCDem' in self._shifts and channel_name == 'em':
                qcd_variations = []
                for shift in ['Up', 'Down']:
                    if self._qcdem_setup == 2020:
                        if self._qcdem_manual:
                            # rate
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p0_[channel_holder._year]["0j"]["nom"], self.p0_[channel_holder._year]["0j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p0_[channel_holder._year]["1j"]["nom"], self.p0_[channel_holder._year]["1j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p0_[channel_holder._year]["2j"]["nom"], self.p0_[channel_holder._year]["2j"][shift]), "qcd_weight"), shift))

                            # shape
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p1_[channel_holder._year]["0j"]["nom"], self.p1_[channel_holder._year]["0j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_shape2_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p2_[channel_holder._year]["0j"]["nom"], self.p2_[channel_holder._year]["0j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p1_[channel_holder._year]["1j"]["nom"], self.p1_[channel_holder._year]["1j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_shape2_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p2_[channel_holder._year]["1j"]["nom"], self.p2_[channel_holder._year]["1j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p1_[channel_holder._year]["2j"]["nom"], self.p1_[channel_holder._year]["2j"][shift]), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_shape2_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight(self.qcd_weight_string[self._era_name].replace(self.p2_[channel_holder._year]["2j"]["nom"], self.p2_[channel_holder._year]["2j"][shift]), "qcd_weight"), shift))
                        else:
                            # rate
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_0jet_rate%s_Weight" % shift.lower(), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_1jet_rate%s_Weight" % shift.lower(), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_2jet_rate%s_Weight" % shift.lower(), "qcd_weight"), shift))

                            # shape
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_0jet_shape%s_Weight" % shift.lower(), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_1jet_shape%s_Weight" % shift.lower(), "qcd_weight"), shift))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_2jet_shape%s_Weight" % shift.lower(), "qcd_weight"), shift))

                    else:
                        # rate
                        qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_0jet_rate%s_Weight*em_qcd_extrap_uncert_Weight" % shift.lower(), "qcd_weight"), shift))
                        qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_1jet_rate%s_Weight*em_qcd_extrap_uncert_Weight" % shift.lower(), "qcd_weight"), shift))
                        # qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_rate_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_2jet_rate%s_Weight*em_qcd_extrap_uncert_Weight" % shift.lower(), "qcd_weight"), shift))

                        # shape
                        qcd_variations.append(ReplaceWeight("CMS_htt_qcd_0jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_0jet_shape%s_Weight*em_qcd_extrap_uncert_Weight" % shift.lower(), "qcd_weight"), shift))
                        qcd_variations.append(ReplaceWeight("CMS_htt_qcd_1jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_1jet_shape%s_Weight*em_qcd_extrap_uncert_Weight" % shift.lower(), "qcd_weight"), shift))
                        # qcd_variations.append(ReplaceWeight("CMS_htt_qcd_2jet_shape_Run{year}".format(year=channel_holder._year), "qcd_weight", Weight("em_qcd_osss_2jet_shape%s_Weight*em_qcd_extrap_uncert_Weight" % shift.lower(), "qcd_weight"), shift))

                for year_correlation in ['', '_Run{year}'.format(year=channel_holder._year)]:
                    if self._qcdem_setup == 2020:
                        if self._qcdem_manual:
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s" % year_correlation, "qcd_weight", Weight(self.qcd_weight_string[channel_holder._year].replace(self.qcd_aisoiso_string[channel_holder._year], self.qcd_aisoiso_string[channel_holder._year] + "**2"), "qcd_weight"), "Up"))
                            qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s" % year_correlation, "qcd_weight", Weight(self.qcd_weight_string[channel_holder._year].replace(self.qcd_aisoiso_string[channel_holder._year], ""), "qcd_weight"), "Down"))
                        else:
                            for shift_direction in ["up", "down"]:
                                qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s" % year_correlation, "qcd_weight", Weight("em_qcd_extrap_" + shift_direction + "_Weight", "qcd_weight"), shift_direction.capitalize()))
                    else:
                        qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s" % year_correlation, "qcd_weight", Weight("em_qcd_extrap_up_Weight*em_qcd_extrap_uncert_Weight", "qcd_weight"), "Up"))
                        qcd_variations.append(ReplaceWeight("CMS_htt_qcd_iso%s" % year_correlation, "qcd_weight", Weight("em_qcd_osss_binned_Weight", "qcd_weight"), "Down"))

                for variation in qcd_variations:
                    # proc_intersection = MSSM.intersection(self._qcdem_sys_processes, channel_holder._processes.keys())
                    proc_intersection = [pr for pr in channel_holder._processes.keys() if 'QCD' in pr]
                    self._logger.debug('\n QCDem::variation name: %s\nintersection self._qcdem_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era)

            # JetToTauFake : not applied to signals
            if 'JetToTauFake' in self._shifts and channel_name != 'em':
                self._logger.info('\n\n JetToTauFake (jet->tau fake efficiency)')
                jet_to_tau_fake_variations = [
                    AddWeight("CMS_htt_jetToTauFake_Run{year}".format(year=channel_holder._year), "jetToTauFake_weight", Weight("max(1.0-pt_2*0.002, 0.6)", "jetToTauFake_weight"), "Up"),
                    AddWeight("CMS_htt_jetToTauFake_Run{year}".format(year=channel_holder._year), "jetToTauFake_weight", Weight("min(1.0+pt_2*0.002, 1.4)", "jetToTauFake_weight"), "Down"),
                ]
                for variation in jet_to_tau_fake_variations:
                    # self._logger.debug('\n\n JetToTauFake::variation name: %s\n intersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in MSSM.intersection(self._jet_to_tau_fake_sys_processes, channel_holder._processes.keys()):
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # WG1 uncertainty scheme, for sm signals (Uncertainty: Theory uncertainties) : TODO
            if 'WG1' in self._shifts:

                # Gluon-fusion
                ggh_variations = []
                THU_ggH_unc = [
                    "THU_ggH_Mig01", "THU_ggH_Mig12", "THU_ggH_Mu", "THU_ggH_PT120",
                    "THU_ggH_PT60", "THU_ggH_Res", "THU_ggH_VBF2j", "THU_ggH_VBF3j",
                    "THU_ggH_qmtop",
                ]
                for unc in THU_ggH_unc:
                    ggh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("({})".format(unc), "{}_weight".format(unc)), "Up"))
                    # ggh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("(1.0/{})".format(unc), "{}_weight".format(unc)), "Down"))
                    ggh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("(2.0-{})".format(unc), "{}_weight".format(unc)), "Down"))

                for process_nick, variation in product(sm_ggh_processes, ggh_variations):  # if "ggH" in nick and "HWW" not in nick
                    self._systematics.add_systematic_variation(
                        variation=variation,
                        process=channel_holder._processes[process_nick],
                        channel=channel_holder._channel_obj,
                        era=self.era
                    )

                # VBF uncertainties
                qqh_variations = []
                THU_qqH_unc = [
                    "THU_qqH_25", "THU_qqH_JET01", "THU_qqH_Mjj1000", "THU_qqH_Mjj120",
                    "THU_qqH_Mjj1500", "THU_qqH_Mjj350", "THU_qqH_Mjj60", "THU_qqH_Mjj700",
                    "THU_qqH_PTH200", "THU_qqH_TOT",
                ]
                for unc in THU_qqH_unc:
                    qqh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("({})".format(unc), "{}_weight".format(unc)), "Up"))
                    qqh_variations.append(AddWeight(unc, "{}_weight".format(unc), Weight("(2.0-{})".format(unc), "{}_weight".format(unc)), "Down"))

                for process_nick, variation in product(sm_qqh_processes, qqh_variations):  # if "qqH" in nick and "qqHWW" not in nick
                    self._systematics.add_systematic_variation(
                        variation=variation,
                        process=channel_holder._processes[process_nick],
                        channel=channel_holder._channel_obj,
                        era=self.era
                    )

            # TODO: refactor the emb part
            # Lepton trigger efficiency; the same values for (MC & EMB) and (mt & et)
            if 'TrgEff' in self._shifts and channel_name in ["mt", "et"]:
                self._logger.info('\n\n Lepton trigger efficiency uncertainties (same for [MC & EMB], [mt & et])')
                lep_trigger_eff_variations = []

                l_eff_cut = {
                    "mt": "25",
                    "et": "25",
                }
                if self._trgeff_setup == 2020:
                    if channel_holder._year in ["2017", "2018"]:
                        l_eff_cut = {
                            "mt": "25",
                            "et": "28",
                        }
                    elif channel_holder._year == "2016":
                        l_eff_cut = {
                            "mt": "23",
                            "et": "28",
                        }

                # MC
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_trigger_%s_Run%s" % (channel_name, channel_holder._year),
                        "trg_%s_eff_weight" % channel_name,
                        Weight("(1.0*(pt_1<={ptcut})+1.02*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "trg_%s_eff_weight" % channel_name),
                        "Up"))
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_trigger_%s_Run%s" % (channel_name, channel_holder._year),
                        "trg_%s_eff_weight" % channel_name,
                        Weight("(1.0*(pt_1<={ptcut})+0.98*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "trg_%s_eff_weight" % channel_name),
                        "Down"))
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_xtrigger_%s_Run%s" % (channel_name, channel_holder._year),
                        "xtrg_%s_eff_weight" % channel_name,
                        Weight("(1.054*(pt_1<={ptcut})+1.0*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "xtrg_%s_eff_weight" % channel_name),
                        "Up"))
                lep_trigger_eff_variations.append(
                    AddWeight(
                        "CMS_eff_xtrigger_%s_Run%s" % (channel_name, channel_holder._year),
                        "xtrg_%s_eff_weight" % channel_name,
                        Weight("(0.946*(pt_1<={ptcut})+1.0*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "xtrg_%s_eff_weight" % channel_name),
                        "Down"))

                for variation in lep_trigger_eff_variations:
                    # self._logger.debug('\n\n TrgEff::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

                if 'EMB' in channel_holder._processes.keys():
                    lep_trigger_eff_variations_emb = []
                    lep_trigger_eff_variations_emb.append(
                        AddWeight(
                            "CMS_eff_trigger_emb_%s_Run%s" % (channel_name, channel_holder._year),
                            "trg_%s_eff_weight" % channel_name,
                            Weight("(1.0*(pt_1<={ptcut})+1.02*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "trg_%s_eff_weight" % channel_name),
                            "Up"))
                    lep_trigger_eff_variations_emb.append(
                        AddWeight(
                            "CMS_eff_trigger_emb_%s_Run%s" % (channel_name, channel_holder._year),
                            "trg_%s_eff_weight" % channel_name,
                            Weight("(1.0*(pt_1<={ptcut})+0.98*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "trg_%s_eff_weight" % channel_name),
                            "Down"))
                    lep_trigger_eff_variations_emb.append(
                        AddWeight(
                            "CMS_eff_xtrigger_emb_%s_Run%s" % (channel_name, channel_holder._year),
                            "xtrg_%s_eff_weight" % channel_name,
                            Weight("(1.054*(pt_1<={ptcut})+1.0*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "xtrg_%s_eff_weight" % channel_name),
                            "Up"))
                    lep_trigger_eff_variations_emb.append(
                        AddWeight(
                            "CMS_eff_xtrigger_emb_%s_Run%s" % (channel_name, channel_holder._year),
                            "xtrg_%s_eff_weight" % channel_name,
                            Weight("(0.946*(pt_1<={ptcut})+1.0*(pt_1>{ptcut}))".format(ptcut=l_eff_cut[channel_name]), "xtrg_%s_eff_weight" % channel_name),
                            "Down"))
                    for variation in lep_trigger_eff_variations_emb:
                        # self._logger.debug('\n\n TrgEff::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes['EMB'],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # Splitted JES shapes
            if 'JES' in self._shifts:
                self._logger.info('\n\n JES reweighting')
                # jet_es_variations = create_systematic_variations(name="CMS_scale_j_eta0to3_Run%s" % channel_holder._year, property_name="jecUncEta0to3", systematic_variation=DifferentPipeline)
                # jet_es_variations += create_systematic_variations(name="CMS_scale_j_eta0to5_Run%s" % channel_holder._year, property_name="jecUncEta0to5", systematic_variation=DifferentPipeline)
                # jet_es_variations += create_systematic_variations(name="CMS_scale_j_eta3to5_Run%s" % channel_holder._year, property_name="jecUncEta3to5", systematic_variation=DifferentPipeline)
                # jet_es_variations += create_systematic_variations(name="CMS_scale_j_RelativeBal_Run%s" % channel_holder._year, property_name="jecUncRelativeBal", systematic_variation=DifferentPipeline)
                # jet_es_variations += create_systematic_variations(name="CMS_scale_j_RelativeSample_Run%s" % channel_holder._year, property_name="jecUncRelativeSample", systematic_variation=DifferentPipeline)

                jet_es_variations = create_systematic_variations(name="CMS_scale_j_Absolute", property_name="jecUncAbsolute", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_Absolute_Run%s" % channel_holder._year, property_name="jecUncAbsoluteYear", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_BBEC1", property_name="jecUncBBEC1", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_BBEC1_Run%s" % channel_holder._year, property_name="jecUncBBEC1Year", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_EC2", property_name="jecUncEC2", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_EC2_Run%s" % channel_holder._year, property_name="jecUncEC2Year", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_FlavorQCD", property_name="jecUncFlavorQCD", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_HF", property_name="jecUncHF", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_HF_Run%s" % channel_holder._year, property_name="jecUncHFYear", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_RelativeBal", property_name="jecUncRelativeBal", systematic_variation=DifferentPipeline)
                jet_es_variations += create_systematic_variations(name="CMS_scale_j_RelativeSample_Run%s" % channel_holder._year, property_name="jecUncRelativeSampleYear", systematic_variation=DifferentPipeline)

                # jet_es_variations += create_systematic_variations(name="CMS_res_j_%s" % channel_holder._year, property_name="jerUnc", systematic_variation=DifferentPipeline)

                for variation in jet_es_variations:
                    # TODO: + signal_nicks:; keep a list of affected shapes in a separate config file
                    # proc_intersection = set(self._jes_sys_processes) & set(channel_holder._processes.keys())
                    # self._logger.debug('\n\n JES::variation name: %s\nintersection self._tes_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )
            if 'JER' in self._shifts:
                self._logger.info('\n\n JER reweighting')

                jet_es_variations = create_systematic_variations(name="CMS_res_j_%s" % channel_holder._year, property_name="jerUnc", systematic_variation=DifferentPipeline)

                for variation in jet_es_variations:
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # B-tagging
            if 'BTag' in self._shifts:
                self._logger.info('\n\n BTag reweighting')
                btag_eff_variations = create_systematic_variations("CMS_htt_eff_b_Run%s" % channel_holder._year, "btagEff", DifferentPipeline)
                mistag_eff_variations = create_systematic_variations("CMS_htt_mistag_b_Run%s" % channel_holder._year, "btagMistag", DifferentPipeline)

                for variation in btag_eff_variations + mistag_eff_variations:
                    # proc_intersection = MSSM.intersection(channel_holder._processes.keys(), mc_processes)
                    # self._logger.debug('\n\n BTag::variation name: %s\nintersection mc_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in mc_processes:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # MET energy scale. Note: only those variations for non-resonant processes are used in the stat. inference
            # are used in the stat. inference, uncorrelated across the years, see https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETRun2Corrections#Uncertainty_correlations_among_y
            if 'METES' in self._shifts:
                self._logger.info('\n\n METES reweighting')
                met_unclustered_variations = create_systematic_variations("CMS_scale_met_unclustered_Run%s" % channel_holder._year, "metUnclusteredEn", DifferentPipeline)

                # proc_intersection = set(self._met_sys_processes) & set(channel_holder._processes.keys())
                # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                for variation in met_unclustered_variations:
                    # self._logger.debug('\n\n METES::variation name: %s\nintersection self._met_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in mc_processes:  # proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # Ele energy scale (EMB-specific),  it is et & em specific
            # todo: one of them should affect the data too
            # Ele energy scale & smear uncertainties (MC-specific), it is et & em specific
            if 'EES' in self._shifts and channel_name in ["et", "em"]:
                self._logger.info('\n\n EES reweighting')

                if 'EMB' in channel_holder._processes.keys():
                    ele_es_emb_variations = create_systematic_variations("CMS_scale_emb_e", "eleEs", DifferentPipeline)  # Run%s" % (channel_name, channel_holder._year)
                    # for process_nick in [x for x in channel_holder._processes.keys() if 'EMB' in x and 'QCDSStoOS' not in x and 'jetFakes' not in x]:
                    self._systematics.add_systematic_variation(
                        variation=ele_es_emb_variations,
                        process=channel_holder._processes['EMB'],
                        channel=channel_holder._channel_obj,
                        era=self.era
                    )

                ele_es_variations = create_systematic_variations("CMS_scale_mc_e", "eleScale", DifferentPipeline) # Run%s" % (channel_name, channel_holder._year)
                ele_es_variations += create_systematic_variations("CMS_reso_mc_e", "eleSmear", DifferentPipeline) # Run%s" % (channel_name, channel_holder._year)
                for variation in ele_es_variations:
                    # TODO: check all proc are needed here
                    # proc_intersection = set(self._ees_sys_processes) & set(channel_holder._processes.keys())
                    # self._logger.debug('\n\n EES::variation name: %s\nintersection self._ees_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    # for process_nick in [x for x in channel_holder._processes.keys() if 'EMB' not in x and 'data' not in x and 'QCDSStoOS' not in x]:
                    # for process_nick in [x for x in channel_holder._processes.keys() if 'EMB' not in x and 'data' not in x]:
                    # for process_nick in proc_intersection - set('EMB'):
                    for process_nick in mc_processes:
                        # print 'process_nick:', process_nick, variation
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # Zll reweighting !!! replaced by log normal uncertainties:
            # CMS_eFakeTau_Run2018 16%; CMS_mFakeTau_Run2018 26%

            # ZL fakes energy scale (e->t, m->t) : not applied to signals
            if 'ZES' in self._shifts and channel_name in ["et", "mt"]:
                self._logger.info('\n\n ZES reweighting')

                if channel_name == 'mt' or self._fes_et_setup != 2020:
                    fakelep_dict = {"et": "Ele", "mt": "Mu"}
                    lep_fake_es_variations = create_systematic_variations("CMS_ZLShape_%s_1prong_Run%s" % (channel_name, channel_holder._year), "tau%sFakeEsOneProng" % fakelep_dict[channel_name], DifferentPipeline)
                    lep_fake_es_variations += create_systematic_variations("CMS_ZLShape_%s_1prong1pizero_Run%s" % (channel_name, channel_holder._year), "tau%sFakeEsOneProngPiZeros" % fakelep_dict[channel_name], DifferentPipeline)
                else:
                    lep_fake_es_variations = create_systematic_variations("CMS_ZLShape_et_1prong_barrel_Run%s" % channel_holder._year, "tauEleFakeEsOneProngBarrel", DifferentPipeline)
                    lep_fake_es_variations += create_systematic_variations("CMS_ZLShape_et_1prong_endcap_Run%s" % channel_holder._year, "tauEleFakeEsOneProngEndcap", DifferentPipeline)
                    lep_fake_es_variations += create_systematic_variations("CMS_ZLShape_et_1prong1pizero_barrel_Run%s" % channel_holder._year, "tauEleFakeEsOneProngPiZerosBarrel", DifferentPipeline)
                    lep_fake_es_variations += create_systematic_variations("CMS_ZLShape_et_1prong1pizero_endcap_Run%s" % channel_holder._year, "tauEleFakeEsOneProngPiZerosEndcap", DifferentPipeline)

                proc_intersection = MSSM.intersection(self._zl_sys_processes, channel_holder._processes.keys())
                for variation in lep_fake_es_variations:
                    self._logger.debug('\n\n ZES::variation name: %s\n intersection self._zl_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # only for the e->tau
            if 'ZFR' in self._shifts and channel_name in ["et"]:
                self._logger.info('\n\n ZFR reweighting')

                # Zll l to tau fake uncertainties:
                # wd: v4_noele27_rebinning5GeVbelow110GeV_15GeVabove110GeV_5_bin
                efake_dict = {
                    "2016": {
                        "BA_dm0": "0.1005*(decayMode_2==0)*(abs(eta_2)<1.448)",
                        "BA_dm1": "0.1175*(decayMode_2==1)*(abs(eta_2)<1.448)",
                        "EC_dm0": "0.1950*(decayMode_2==0)*(abs(eta_2)>1.448)",
                        "EC_dm1": "0.2040*(decayMode_2==1)*(abs(eta_2)>1.448)"
                    },
                    "2017": {
                        "BA_dm0": "0.1175*(decayMode_2==0)*(abs(eta_2)<1.448)",
                        "BA_dm1": "0.0910*(decayMode_2==1)*(abs(eta_2)<1.448)",
                        "EC_dm0": "0.1845*(decayMode_2==0)*(abs(eta_2)>1.448)",
                        "EC_dm1": "0.1735*(decayMode_2==1)*(abs(eta_2)>1.448)"
                    },
                    "2018": {
                        "BA_dm0": "0.1155*(decayMode_2==0)*(abs(eta_2)<1.448)",
                        "BA_dm1": "0.0840*(decayMode_2==1)*(abs(eta_2)<1.448)",
                        "EC_dm0": "0.1405*(decayMode_2==0)*(abs(eta_2)>1.448)",
                        "EC_dm1": "0.1405*(decayMode_2==1)*(abs(eta_2)>1.448)"
                    }
                }
                lep_fake_rate_variations = []
                for eta_region, weight in efake_dict[channel_holder._year].items():
                    lep_fake_rate_variations.append(AddWeight(name="CMS_fake_e_%s_Run%s" % (eta_region, channel_holder._year,), weight_name="eFakeTau_reweight", new_weight=Weight("(1.0+%s)" % weight, "eFakeTau_reweight"), direction="Up"))
                    lep_fake_rate_variations.append(AddWeight(name="CMS_fake_e_%s_Run%s" % (eta_region, channel_holder._year,), weight_name="eFakeTau_reweight", new_weight=Weight("(1.0-%s)" % weight, "eFakeTau_reweight"), direction="Down"))
                proc_intersection = MSSM.intersection(self._zl_sys_processes, channel_holder._processes.keys())
                for variation in lep_fake_rate_variations:
                    self._logger.debug('\n\n ZFR::variation name: %s\n intersection self._zl_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

            # Recoil correction unc, for resonant processes
            if 'Recoil' in self._shifts:
                self._logger.info('\n\n recoil reweighting')

                recoil_variations = create_systematic_variations("CMS_htt_boson_reso_met_Run%s" % channel_holder._year, "metRecoilResolution", DifferentPipeline)
                recoil_variations += create_systematic_variations("CMS_htt_boson_scale_met_Run%s" % channel_holder._year, "metRecoilResponse", DifferentPipeline)

                # sm_ggH_processes ggH qqH, {"ZTT", "ZL", "ZJ", "W", H125, bbH, bbA etc.
                # signals, mssm_signals, signals_ggHToWW, signals_qqHToWW,{"ZTT", "ZL", "ZJ", "W"}
                proc_intersection = set(self._z_recoil_sys_processes) & set(channel_holder._processes.keys())
                for variation in recoil_variations:
                    self._logger.debug('\n\n Recoil::variation name: %s\nintersection self._z_recoil_sys_processes: [%s]' % (variation.name, ', '.join(proc_intersection)))
                    for process_nick in signal_processes | sm_h_processes | proc_intersection:
                        self._systematics.add_systematic_variation(
                            variation=variation,
                            process=channel_holder._processes[process_nick],
                            channel=channel_holder._channel_obj,
                            era=self.era
                        )

        if 'nominal' not in self._shifts:
            self._logger.warning("Nominal shapes will not be produced")
            # import pdb; pdb.set_trace() # !import code; code.interact(local=vars())
            self._systematics._systematics = [i for i in self._systematics._systematics if i._variation._name != 'Nominal']

    def upplyFesCuts(self, pipeline, depth):
        '''
        Upplying cuts that are only for fes shifts
        '''
        for shift_systematic in self._systematics._systematics[-len(depth):]:
            for cut_key, cut_expression in self._fes_extra_cuts.iteritems():
                shift_systematic.category.cuts.add(Cut(cut_expression, cut_key))

            shift_systematic._process._estimation_method._directory = self._fes_friend_directory[0]

            # Removing shifts from unmatching by decay mode requirement/cuts categories
            if ('InclusiveShift' in pipeline and len(MSSM.intersection(shift_systematic.category.cuts.names, ['dm0', 'dm1', 'dm10'])) != 0) \
            or ('OneProngShift' in pipeline and len(MSSM.intersection(shift_systematic.category.cuts.names, ['alldm', 'dm1', 'dm10'])) != 0) \
            or ('OneProngPiZerosShift' in pipeline and len(MSSM.intersection(shift_systematic.category.cuts.names, ['alldm', 'dm0', 'dm10'])) != 0) \
            or ('ThreeProngShift' in pipeline and len(MSSM.intersection(shift_systematic.category.cuts.names, ['alldm', 'dm0', 'dm1'])) != 0):
                self._logger.debug("Removing systematic shift %s from production because of unmatching dm in categorisation" % (shift_systematic.name))
                self._systematics._systematics.remove(shift_systematic)


if __name__ == '__main__':
    args = MSSM.parse_arguments()
    mssm = MSSM(**args)
    print mssm
