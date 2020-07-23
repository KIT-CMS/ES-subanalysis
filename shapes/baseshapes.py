# -*- coding: utf-8 -*-
import os
import ast
import six
import sys
import importlib
import copy
import logging
import copy
import ROOT
from itertools import product
from rootpy import log
from rootpy.logger.magic import DANGER

ROOT.gSystem.Load('libGenVector')

from guppy import hpy
import yaml

import pprint
pp = pprint.PrettyPrinter(indent=4)

from shape_producer.systematics import Systematics
from shape_producer.categories import Category  # move to ChannelsHolder
from channelholder import ChannelHolder
from shape_producer.process import Process  # move to ChannelsHolder
from shape_producer.variable import Variable  # move to ChannelsHolder
from shape_producer.binning import VariableBinning  # move to ChannelsHolder
from shape_producer.cutstring import Cut, Cuts, Weight
# from inidecorator import inidecorator

# TODO: wrapper for introduction of methods
# TODO: inharit from my base subprocesses class
class Shapes(object):
    # _complexEstimationMethods = ['WEstimationWithQCD', 'QCDEstimationWithW', 'NewFakeEstimationLT', 'NewFakeEstimationTT']

    @staticmethod
    def intersection(x, y):
        return list(set(x) & set(y))

    @staticmethod
    def myeval(s):
        s1 = copy.deepcopy(s).replace('&&', ' and ').replace('||', ' or ')
        try:
            return eval(s1)
        except NameError:
            return False
        except:
            raise

    @staticmethod
    def myevalast(s):
        s1 = copy.deepcopy(s).replace('&&', ' and ').replace('||', ' or ')
        try:
            import ast
            # print s, 'eval:', ast.literal_eval(s1)
            return ast.literal_eval(s1)
        except ValueError:
            return False
        except:
            raise

    _known_svfit_variables = [
        'm_fastmtt_puppi', 'pt_fastmtt_puppi', 'eta_fastmtt_puppi', 'phi_fastmtt_puppi',
        'm_sv_puppi', 'pt_sv_puppi', 'eta_sv_puppi', 'phi_sv_puppi',
        'm_fastmtt', 'pt_fastmtt', 'eta_fastmtt', 'phi_fastmtt',
        'm_sv', 'pt_sv', 'eta_sv', 'phi_sv',
    ]

    channel_minplotlev_cuts = [
        'et_minplotlev_cuts', 'mt_minplotlev_cuts',
        'tt_minplotlev_cuts', 'em_minplotlev_cuts',
        'channel_specific',  # 'year_specific'
    ]
    cuts_manipulations = [
        'fes_extra_cuts', 'force_cuts', 'extra_cuts',
        'grid_categories', 'single_categories',
    ]

    # todo: move to config
    em_closureweight = {
        '2016': 1.0,
        '2017': 1.0,
        '2018': 1.0,
        # '2016': 1.2,
        # '2017': 1.1,
        # '2018': 1.2,
    }
    # from SM, nbtag=0
    qcd_aisoiso_string = {
        '2016': "*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.889611*(pt_1>=0.0&&pt_1<20.0&&pt_2>=20.0&&pt_2<25.0)+0.906323*(pt_1>=0.0&&pt_1<20.0&&pt_2>=25.0&&pt_2<30.0)+0.838287*(pt_1>=0.0&&pt_1<20.0&&pt_2>=30.0&&pt_2<150.0)+0.900872*(pt_1>=20.0&&pt_1<25.0&&pt_2>=0.0&&pt_2<20.0)+0.918876*(pt_1>=20.0&&pt_1<25.0&&pt_2>=20.0&&pt_2<25.0)+0.857904*(pt_1>=20.0&&pt_1<25.0&&pt_2>=25.0&&pt_2<30.0)+0.833439*(pt_1>=20.0&&pt_1<25.0&&pt_2>=30.0&&pt_2<150.0)+0.956127*(pt_1>=25.0&&pt_1<30.0&&pt_2>=0.0&&pt_2<20.0)+0.863690*(pt_1>=25.0&&pt_1<30.0&&pt_2>=20.0&&pt_2<25.0)+1.060816*(pt_1>=25.0&&pt_1<30.0&&pt_2>=25.0&&pt_2<30.0)+0.938181*(pt_1>=25.0&&pt_1<30.0&&pt_2>=30.0&&pt_2<150.0)+0.993274*(pt_1>=30.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<20.0)+0.936018*(pt_1>=30.0&&pt_1<150.0&&pt_2>=20.0&&pt_2<25.0)+0.864106*(pt_1>=30.0&&pt_1<150.0&&pt_2>=25.0&&pt_2<30.0)+0.954102*(pt_1>=30.0&&pt_1<150.0&&pt_2>=30.0&&pt_2<150.0))",
        '2017': "*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.878304*(pt_1>=0.0&&pt_1<20.0&&pt_2>=20.0&&pt_2<25.0)+0.916277*(pt_1>=0.0&&pt_1<20.0&&pt_2>=25.0&&pt_2<30.0)+0.853211*(pt_1>=0.0&&pt_1<20.0&&pt_2>=30.0&&pt_2<150.0)+0.920458*(pt_1>=20.0&&pt_1<25.0&&pt_2>=0.0&&pt_2<20.0)+0.872271*(pt_1>=20.0&&pt_1<25.0&&pt_2>=20.0&&pt_2<25.0)+0.957983*(pt_1>=20.0&&pt_1<25.0&&pt_2>=25.0&&pt_2<30.0)+0.910988*(pt_1>=20.0&&pt_1<25.0&&pt_2>=30.0&&pt_2<150.0)+0.935900*(pt_1>=25.0&&pt_1<30.0&&pt_2>=0.0&&pt_2<20.0)+0.903964*(pt_1>=25.0&&pt_1<30.0&&pt_2>=20.0&&pt_2<25.0)+0.888112*(pt_1>=25.0&&pt_1<30.0&&pt_2>=25.0&&pt_2<30.0)+0.872235*(pt_1>=25.0&&pt_1<30.0&&pt_2>=30.0&&pt_2<150.0)+0.927075*(pt_1>=30.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<20.0)+0.983504*(pt_1>=30.0&&pt_1<150.0&&pt_2>=20.0&&pt_2<25.0)+0.921924*(pt_1>=30.0&&pt_1<150.0&&pt_2>=25.0&&pt_2<30.0)+0.881401*(pt_1>=30.0&&pt_1<150.0&&pt_2>=30.0&&pt_2<150.0))",
        '2018': "*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.847702*(pt_1>=0.0&&pt_1<20.0&&pt_2>=20.0&&pt_2<25.0)+0.878120*(pt_1>=0.0&&pt_1<20.0&&pt_2>=25.0&&pt_2<30.0)+0.887496*(pt_1>=0.0&&pt_1<20.0&&pt_2>=30.0&&pt_2<150.0)+0.874935*(pt_1>=20.0&&pt_1<25.0&&pt_2>=0.0&&pt_2<20.0)+0.829801*(pt_1>=20.0&&pt_1<25.0&&pt_2>=20.0&&pt_2<25.0)+0.922954*(pt_1>=20.0&&pt_1<25.0&&pt_2>=25.0&&pt_2<30.0)+0.954270*(pt_1>=20.0&&pt_1<25.0&&pt_2>=30.0&&pt_2<150.0)+0.935953*(pt_1>=25.0&&pt_1<30.0&&pt_2>=0.0&&pt_2<20.0)+0.908383*(pt_1>=25.0&&pt_1<30.0&&pt_2>=20.0&&pt_2<25.0)+0.927804*(pt_1>=25.0&&pt_1<30.0&&pt_2>=25.0&&pt_2<30.0)+0.917511*(pt_1>=25.0&&pt_1<30.0&&pt_2>=30.0&&pt_2<150.0)+0.983508*(pt_1>=30.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<20.0)+0.952974*(pt_1>=30.0&&pt_1<150.0&&pt_2>=20.0&&pt_2<25.0)+0.945860*(pt_1>=30.0&&pt_1<150.0&&pt_2>=25.0&&pt_2<30.0)+0.858417*(pt_1>=30.0&&pt_1<150.0&&pt_2>=30.0&&pt_2<150.0))",
    }
    qcd_weight_string = {
        '2016': "((-0.1138*(njets==0)+(-0.07938)*(njets==1)+(-0.02602)*(njets>=2))*((DiTauDeltaR-3.0)**2.0-3.0)+(-0.2287*(njets==0)+(-0.3251)*(njets==1)+(-0.2802)*(njets>=2))*(DiTauDeltaR-3.0)+(1.956*(njets==0)+(1.890)*(njets==1)+(1.753)*(njets>=2)))*(1.0*(pt_1>=150.0||pt_2>=150.0)+1.132149*(pt_1>=0.0&&pt_1<24.0&&pt_2>=24.0&&pt_2<30.0)+1.118163*(pt_1>=0.0&&pt_1<24.0&&pt_2>=30.0&&pt_2<40.0)+1.142240*(pt_1>=0.0&&pt_1<24.0&&pt_2>=40.0&&pt_2<150.0)+1.004560*(pt_1>=24.0&&pt_1<30.0&&pt_2>=0.0&&pt_2<24.0)+1.055802*(pt_1>=24.0&&pt_1<30.0&&pt_2>=24.0&&pt_2<30.0)+1.171731*(pt_1>=24.0&&pt_1<30.0&&pt_2>=30.0&&pt_2<40.0)+1.351143*(pt_1>=24.0&&pt_1<30.0&&pt_2>=40.0&&pt_2<150.0)+0.921943*(pt_1>=30.0&&pt_1<40.0&&pt_2>=0.0&&pt_2<24.0)+1.078412*(pt_1>=30.0&&pt_1<40.0&&pt_2>=24.0&&pt_2<30.0)+1.096989*(pt_1>=30.0&&pt_1<40.0&&pt_2>=30.0&&pt_2<40.0)+1.222142*(pt_1>=30.0&&pt_1<40.0&&pt_2>=40.0&&pt_2<150.0)+0.848351*(pt_1>=40.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<24.0)+0.852887*(pt_1>=40.0&&pt_1<150.0&&pt_2>=24.0&&pt_2<30.0)+0.891202*(pt_1>=40.0&&pt_1<150.0&&pt_2>=30.0&&pt_2<40.0)+0.913323*(pt_1>=40.0&&pt_1<150.0&&pt_2>=40.0&&pt_2<150.0))%s" % qcd_aisoiso_string['2016'],
        '2017': "((-0.1430*(njets==0)+(-0.05544)*(njets==1)+(0.03128)*(njets>=2))*((DiTauDeltaR-3.0)**2.0-3.0)+(-0.1949*(njets==0)+(-0.3685)*(njets==1)+(-0.3531)*(njets>=2))*(DiTauDeltaR-3.0)+(1.928*(njets==0)+(2.020)*(njets==1)+(1.855)*(njets>=2)))*(1.0*(pt_1>=150.0||pt_2>=150.0)+1.155767*(pt_1>=0.0&&pt_1<24.0&&pt_2>=24.0&&pt_2<30.0)+1.136188*(pt_1>=0.0&&pt_1<24.0&&pt_2>=30.0&&pt_2<40.0)+1.163907*(pt_1>=0.0&&pt_1<24.0&&pt_2>=40.0&&pt_2<150.0)+0.988366*(pt_1>=24.0&&pt_1<30.0&&pt_2>=0.0&&pt_2<24.0)+1.198820*(pt_1>=24.0&&pt_1<30.0&&pt_2>=24.0&&pt_2<30.0)+1.134818*(pt_1>=24.0&&pt_1<30.0&&pt_2>=30.0&&pt_2<40.0)+1.051062*(pt_1>=24.0&&pt_1<30.0&&pt_2>=40.0&&pt_2<150.0)+0.917948*(pt_1>=30.0&&pt_1<40.0&&pt_2>=0.0&&pt_2<24.0)+1.042672*(pt_1>=30.0&&pt_1<40.0&&pt_2>=24.0&&pt_2<30.0)+0.973973*(pt_1>=30.0&&pt_1<40.0&&pt_2>=30.0&&pt_2<40.0)+1.143160*(pt_1>=30.0&&pt_1<40.0&&pt_2>=40.0&&pt_2<150.0)+0.845711*(pt_1>=40.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<24.0)+0.853038*(pt_1>=40.0&&pt_1<150.0&&pt_2>=24.0&&pt_2<30.0)+0.890487*(pt_1>=40.0&&pt_1<150.0&&pt_2>=30.0&&pt_2<40.0)+1.037247*(pt_1>=40.0&&pt_1<150.0&&pt_2>=40.0&&pt_2<150.0))%s" % qcd_aisoiso_string['2017'],
        '2018': "((-0.1249*(njets==0)+(-0.04374)*(njets==1)+(-0.00606)*(njets>=2))*((DiTauDeltaR-3.0)**2.0-3.0)+(-0.1644*(njets==0)+(-0.3172)*(njets==1)+(-0.3627)*(njets>=2))*(DiTauDeltaR-3.0)+(1.963*(njets==0)+(2.014)*(njets==1)+(1.757)*(njets>=2)))*(1.0*(pt_1>=150.0||pt_2>=150.0)+1.163939*(pt_1>=0.0&&pt_1<24.0&&pt_2>=24.0&&pt_2<30.0)+1.128795*(pt_1>=0.0&&pt_1<24.0&&pt_2>=30.0&&pt_2<40.0)+1.083493*(pt_1>=0.0&&pt_1<24.0&&pt_2>=40.0&&pt_2<150.0)+1.006878*(pt_1>=24.0&&pt_1<30.0&&pt_2>=0.0&&pt_2<24.0)+1.078046*(pt_1>=24.0&&pt_1<30.0&&pt_2>=24.0&&pt_2<30.0)+1.080539*(pt_1>=24.0&&pt_1<30.0&&pt_2>=30.0&&pt_2<40.0)+1.080385*(pt_1>=24.0&&pt_1<30.0&&pt_2>=40.0&&pt_2<150.0)+0.930821*(pt_1>=30.0&&pt_1<40.0&&pt_2>=0.0&&pt_2<24.0)+1.077226*(pt_1>=30.0&&pt_1<40.0&&pt_2>=24.0&&pt_2<30.0)+1.030334*(pt_1>=30.0&&pt_1<40.0&&pt_2>=30.0&&pt_2<40.0)+0.940508*(pt_1>=30.0&&pt_1<40.0&&pt_2>=40.0&&pt_2<150.0)+0.836243*(pt_1>=40.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<24.0)+0.878972*(pt_1>=40.0&&pt_1<150.0&&pt_2>=24.0&&pt_2<30.0)+0.867798*(pt_1>=40.0&&pt_1<150.0&&pt_2>=30.0&&pt_2<40.0)+0.910642*(pt_1>=40.0&&pt_1<150.0&&pt_2>=40.0&&pt_2<150.0))%s" % qcd_aisoiso_string['2018'],
    }
    # QCD for em parabolas parameters
    # constant parameter
    p0_ = {
        "2016": {
            "0j": {"nom": "1.956", "Up": "2.018", "Down": "1.894"},
            "1j": {"nom": "1.890", "Up": "1.930", "Down": "1.850"},
            "2j": {"nom": "1.753", "Up": "1.814", "Down": "1.692"},
        },
        "2017": {
            "0j": {"nom": "1.928", "Up": "1.993", "Down": "1.863"},
            "1j": {"nom": "2.020", "Up": "2.060", "Down": "1.980"},
            "2j": {"nom": "1.855", "Up": "1.914", "Down": "1.796"},
        },
        "2018": {
            "0j": {"nom": "1.963", "Up": "2.010", "Down": "1.916"},
            "1j": {"nom": "2.014", "Up": "2.045", "Down": "1.983"},
            "2j": {"nom": "1.757", "Up": "1.794", "Down": "1.720"},
        }
    }
    # linear parameter
    p1_ = {
        "2016": {
            "0j": {"nom": "-0.2287", "Up": "-0.1954", "Down": "-0.2620"},
            "1j": {"nom": "-0.3251", "Up": "-0.2972", "Down": "-0.3530"},
            "2j": {"nom": "-0.2802", "Up": "-0.2402", "Down": "-0.3202"},
        },
        "2017": {
            "0j": {"nom": "-0.1949", "Up": "-0.1617", "Down": "-0.2281"},
            "1j": {"nom": "-0.3685", "Up": "-0.3445", "Down": "-0.3925"},
            "2j": {"nom": "-0.3531", "Up": "-0.3154", "Down": "-0.3908"},
        },
        "2018": {
            "0j": {"nom": "-0.1644", "Up": "-0.1402", "Down": "-0.1886"},
            "1j": {"nom": "-0.3172", "Up": "-0.2977", "Down": "-0.3367"},
            "2j": {"nom": "-0.3627", "Up": "-0.3389", "Down": "-0.3865"},
        }
    }
    # quadratic parameter
    p2_ = {
        "2016": {
            "0j": {"nom": "-0.11380", "Up": "-0.09220", "Down": "-0.13540"},
            "1j": {"nom": "-0.07938", "Up": "-0.06242", "Down": "-0.09634"},
            "2j": {"nom": "-0.02602", "Up": "-0.00307", "Down": "-0.04897"},
        },
        "2017": {
            "0j": {"nom": "-0.14300", "Up": "-0.12000", "Down": "-0.16600"},
            "1j": {"nom": "-0.05544", "Up": "-0.03986", "Down": "-0.07102"},
            "2j": {"nom": "0.031280", "Up": "0.054090", "Down": "0.008470"},
        },
        "2018": {
            "0j": {"nom": "-0.12490", "Up": "-0.10830", "Down": "-0.141500"},
            "1j": {"nom": "-0.04374", "Up": "-0.03139", "Down": "-0.056090"},
            "2j": {"nom": "-0.00606", "Up": "0.005143", "Down": "-0.024355"},
        }
    }

    # # from SM, nbtag=1
    # qcd_aisoiso_string = {
    #     '2016': "*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.767421*(pt_1>=0.0&&pt_1<20.0&&pt_2>=20.0&&pt_2<150.0)+0.968708*(pt_1>=20.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<20.0)+0.848641*(pt_1>=20.0&&pt_1<150.0&&pt_2>=20.0&&pt_2<150.0))",
    #     '2017': "*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.883249*(pt_1>=0.0&&pt_1<20.0&&pt_2>=20.0&&pt_2<150.0)+0.925161*(pt_1>=20.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<20.0)+0.997453*(pt_1>=20.0&&pt_1<150.0&&pt_2>=20.0&&pt_2<150.0))",
    #     '2018': "*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.960198*(pt_1>=0.0&&pt_1<20.0&&pt_2>=20.0&&pt_2<150.0)+0.987588*(pt_1>=20.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<20.0)+0.729727*(pt_1>=20.0&&pt_1<150.0&&pt_2>=20.0&&pt_2<150.0))",
    # }
    # qcd_weight_string = {
    #     '2016': "((-0.06938*(njets==0)+(-0.01966)*(njets==1)+(-0.09821)*(njets>=2))*((DiTauDeltaR-3.0)**2.0-3.0)+(-0.113*(njets==0)+(-0.2715)*(njets==1)+(-0.397)*(njets>=2))*(DiTauDeltaR-3.0)+(1.361*(njets==0)+(1.645)*(njets==1)+(1.432)*(njets>=2)))*(1.0*(pt_1>=150.0||pt_2>=150.0)+0.913392*(pt_1>=0.0&&pt_1<24.0&&pt_2>=24.0&&pt_2<150.0)+0.992858*(pt_1>=24.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<24.0)+1.119160*(pt_1>=24.0&&pt_1<150.0&&pt_2>=24.0&&pt_2<150.0))%s" % qcd_aisoiso_string['2016'],
    #     '2017': "((-0.1209*(njets==0)+(-0.04244)*(njets==1)+(-0.0268)*(njets>=2))*((DiTauDeltaR-3.0)**2.0-3.0)+(-0.142*(njets==0)+(-0.2626)*(njets==1)+(-0.3231)*(njets>=2))*(DiTauDeltaR-3.0)+(1.518*(njets==0)+(1.577)*(njets==1)+(1.559)*(njets>=2)))*(1.0*(pt_1>=150.0||pt_2>=150.0)+1.053479*(pt_1>=0.0&&pt_1<24.0&&pt_2>=24.0&&pt_2<150.0)+0.961059*(pt_1>=24.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<24.0)+1.063705*(pt_1>=24.0&&pt_1<150.0&&pt_2>=24.0&&pt_2<150.0))%s" % qcd_aisoiso_string['2017'],
    #     '2018': "((-0.07762*(njets==0)+(-0.00639)*(njets==1)+(-0.0429)*(njets>=2))*((DiTauDeltaR-3.0)**2.0-3.0)+(-0.1623*(njets==0)+(-0.2799)*(njets==1)+(-0.3575)*(njets>=2))*(DiTauDeltaR-3.0)+(1.372*(njets==0)+(1.538)*(njets==1)+(1.4)*(njets>=2)))*(1.0*(pt_1>=150.0||pt_2>=150.0)+1.013320*(pt_1>=0.0&&pt_1<24.0&&pt_2>=24.0&&pt_2<150.0)+0.941853*(pt_1>=24.0&&pt_1<150.0&&pt_2>=0.0&&pt_2<24.0)+1.129069*(pt_1>=24.0&&pt_1<150.0&&pt_2>=24.0&&pt_2<150.0))%s" % qcd_aisoiso_string['2018'],
    # }

    # # QCD for em parabolas parameters
    # # constant parameter
    # p0_ = {
    #     "2016": {
    #         "0j": {"nom": "1.361", "Up": "1.498", "Down": "1.224"},
    #         "1j": {"nom": "1.645", "Up": "1.741", "Down": "1.549"},
    #         "2j": {"nom": "1.432", "Up": "1.498", "Down": "1.366"},
    #     },
    #     "2017": {
    #         "0j": {"nom": "1.518", "Up": "1.633", "Down": "1.403"},
    #         "1j": {"nom": "1.577", "Up": "1.64", "Down": "1.514"},
    #         "2j": {"nom": "1.559", "Up": "1.627", "Down": "1.491"},
    #     },
    #     "2018": {
    #         "0j": {"nom": "1.372", "Up": "1.473", "Down": "1.271"},
    #         "1j": {"nom": "1.538", "Up": "1.593", "Down": "1.483"},
    #         "2j": {"nom": "1.4", "Up": "1.4", "Down": "1.4"},
    #     }
    # }
    # # linear parameter
    # p1_ = {
    #     "2016": {
    #         "0j": {"nom": "-0.113", "Up": "-0.029", "Down": "-0.197"},
    #         "1j": {"nom": "-0.2715", "Up": "-0.2116", "Down": "-0.3314"},
    #         "2j": {"nom": "-0.397", "Up": "-0.357", "Down": "-0.437"},
    #     },
    #     "2017": {
    #         "0j": {"nom": "-0.142", "Up": "-0.075", "Down": "-0.209"},
    #         "1j": {"nom": "-0.2626", "Up": "-0.2226", "Down": "-0.3026"},
    #         "2j": {"nom": "-0.3231", "Up": "-0.2813", "Down": "-0.3649"},
    #     },
    #     "2018": {
    #         "0j": {"nom": "-0.1623", "Up": "-0.107", "Down": "-0.2176"},
    #         "1j": {"nom": "-0.2799", "Up": "-0.2464", "Down": "-0.3134"},
    #         "2j": {"nom": "-0.3575", "Up": "-0.332", "Down": "-0.383"},
    #     }
    # }
    # # quadratic parameter
    # p2_ = {
    #     "2016": {
    #         "0j": {"nom": "-0.06938", "Up": "-0.01701", "Down": "-0.12175"},
    #         "1j": {"nom": "-0.01966", "Up": "0.01752", "Down": "-0.05684"},
    #         "2j": {"nom": "-0.09821", "Up": "-0.07059", "Down": "-0.12583"},
    #     },
    #     "2017": {
    #         "0j": {"nom": "-0.1209", "Up": "-0.0791", "Down": "-0.1627"},
    #         "1j": {"nom": "-0.04244", "Up": "-0.01763", "Down": "-0.06725"},
    #         "2j": {"nom": "-0.0268", "Up": "-0.0016", "Down": "-0.052"},
    #     },
    #     "2018": {
    #         "0j": {"nom": "-0.07762", "Up": "-0.03913", "Down": "-0.11611"},
    #         "1j": {"nom": "-0.00639", "Up": "0.01582", "Down": "-0.0286"},
    #         "2j": {"nom": "-0.0429", "Up": "-0.026", "Down": "-0.0598"},
    #     }
    # }
    # @inidecorator   # TODO: TEST
    # TODO: needs a splitting between init and setup
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
                 no_higgs=None,
                 danger=False,
                 era=None,
                 et_friend_directory=None,
                 mt_friend_directory=None,
                 tt_friend_directory=None,
                 em_friend_directory=None,
                 fake_factor_friend_directory=None,
                 fes_friend_directory=None,
                 fes_extra_cuts={},
                 force_cuts={},
                 invert_cuts=None,
                 extra_chain=None,
                 gof_channel=None,
                 gof_variable=None,
                 num_threads=None,
                 skip_systematic_variations=None,
                 skip_processes=["SUSYggH"],
                 tag=None,
                 output_file=None,
                 output_file_name=None,
                 output_file_dir=None,
                 context_analysis=None,
                 variables_names=None,  # X
                 processes=None,
                 methods_collection_key='methods',
                 module=None,
                 _known_estimation_methods=None,
                 _known_processes=None,
                 _complexEstimationMethods=None,
                 _complexEstimationMethodsRequirements=None,
                 _known_methods_collections=None,
                 _known_estimation_modules=None,
                 _renaming=None,
                 _known_cuts=None,
                 nominal_folder='nominal',
                 etau_es_shifts=None,
                 mtau_es_shifts=None,
                 shifts=None,
                 skip_shifts=None,
                 grid_categories={},
                 parser_grid_categories={},
                 mask_grid_categories={},
                 single_categories={},
                 indent=0,
                 update_process_per_category=None,
                 replace_weights={},
                 *args, **kwargs
                 ):
        self._logger = logging.getLogger(__name__)

        # TODO: Can be commented out if @inidecorator will be used
        self._ofset = ofset

        # Inputs with nominals and shifts
        if isinstance(directory, dict):
            try:
                self._directory = directory[era]
            except:
                self._logger('ntuples: directory is a dict but era "%s" is not a key:' % era)
                pp.pprint(directory)
                raise Exception
        else:
            self._directory = directory
        assert isinstance(self._directory, six.string_types), "Shapes::directory not set"

        # FES shifts
        if isinstance(etau_es_shifts, dict):
            try:
                self._etau_es_shifts = etau_es_shifts[era]
            except:
                self._logger('FES shifts: etau_es_shifts is a dict but era "%s" is not a key:' % era)
                pp.pprint(etau_es_shifts)
                raise Exception
        else:
            self._etau_es_shifts = etau_es_shifts

        # assert isinstance(self._etau_es_shifts, six.string_types), "Shapes::FES shifts not set"

        self._datasets = datasets
        assert isinstance(self._datasets, six.string_types), "Shapes::datasets not set"

        self._binning = binning
        self._binning_key = binning_key
        assert isinstance(self._binning, six.string_types), "Shapes::binning not set"
        self._binning = yaml.load(open(self._binning))

        self._log_level = log_level
        self._indent = indent

        self._methods_collection_key = methods_collection_key

        self._backend = backend
        self._channels_key = channels
        self._debug = debug
        self._dry = dry
        self._no_higgs = no_higgs
        self._danger = danger
        self._era_name = era

        self._extra_chain = extra_chain
        self._gof_channel = gof_channel
        self._gof_variable = gof_variable
        self._num_threads = num_threads
        self._skip_systematic_variations = skip_systematic_variations
        self._skip_processes = skip_processes if skip_processes is not None else []
        self._tag = tag
        self._context_analysis = context_analysis
        self._variables_names = variables_names
        self._processes = processes
        self._module = module

        self._known_estimation_methods = _known_estimation_methods
        self._known_processes = _known_processes
        self._complexEstimationMethods = _complexEstimationMethods
        self._complexEstimationMethodsRequirements = _complexEstimationMethodsRequirements
        self._known_methods_collections = _known_methods_collections
        self._known_estimation_modules = _known_estimation_modules
        self._renaming = _renaming
        self._known_cuts = _known_cuts

        self._nominal_folder = nominal_folder

        self._qcdem_setup = kwargs['qcdem_setup']
        self._qcdem_manual = kwargs['qcdem_manual']
        self._fes_et_setup = kwargs['fes_et_setup']
        self._trgeff_setup = kwargs['trgeff_setup']

        self._mass_susy_ggH = kwargs['mass_susy_ggH'] if 'mass_susy_ggH' in kwargs.keys() else None
        self._mass_susy_qqH = kwargs['mass_susy_qqH'] if 'mass_susy_qqH' in kwargs.keys() else None
        if isinstance(self._mass_susy_qqH, dict):
            if era in self._mass_susy_qqH:
                self._mass_susy_qqH = self._mass_susy_qqH[era]
            elif 'default' in self._mass_susy_qqH:
                self._mass_susy_qqH = self._mass_susy_qqH['default']
            else:
                raise Exception('Couldn\'t initialize the self._mass_susy_qqH')
        if isinstance(self._mass_susy_ggH, dict):
            if era in self._mass_susy_ggH:
                self._mass_susy_ggH = self._mass_susy_ggH[era]
            elif 'default' in self._mass_susy_ggH:
                self._mass_susy_ggH = self._mass_susy_ggH['default']
            else:
                raise Exception('Couldn\'t initialize the self._mass_susy_ggH')

        self._generator_qqH = kwargs['generator_qqH'] if 'generator_qqH' in kwargs.keys() else None
        if isinstance(self._generator_qqH, list):
            if len(self._generator_qqH) == 1:
                self._generator_qqH = self._generator_qqH[0]
            elif len(self._generator_qqH) == 0:
                self._logger.info('Using default generator for qqH')
                self._generator_qqH = None
            else:
                raise Exception('self._generator_qqH is list of more than 1 length - be sure to pass only 1 argument. Was passed: %s' % self._generator_qqH)
        elif isinstance(self._generator_qqH, dict):
            if era in self._generator_qqH:
                self._generator_qqH = self._generator_qqH[era]
            elif 'default' in self._generator_qqH:
                self._generator_qqH = self._generator_qqH['default']
            else:
                raise Exception('Couldn\'t initialize the self._generator_qqH')
        # print self._mass_susy_qqH ; exit(1)

        # self._et_friend_directory = os.path.expandvars(et_friend_directory)
        # self._mt_friend_directory = os.path.expandvars(mt_friend_directory)
        # self._tt_friend_directory = os.path.expandvars(tt_friend_directory)
        # self._fake_factor_friend_directory = os.path.expandvars(fake_factor_friend_directory)
        # self._fes_friend_directory = os.path.expandvars(fes_friend_directory)

        map_friends_attr = {
            '_et_friend_directory': et_friend_directory,
            '_mt_friend_directory': mt_friend_directory,
            '_tt_friend_directory': tt_friend_directory,
            '_em_friend_directory': em_friend_directory,
            '_fake_factor_friend_directory': fake_factor_friend_directory,
            '_fes_friend_directory': fes_friend_directory,
        }

        for k, v in map_friends_attr.iteritems():
            if isinstance(v, dict):
                try:
                    setattr(self, k, [os.path.expandvars(i) for i in v[era]])
                except:
                    self._logger.critical('%s is a dict but era "%s" is not a key:' % (k, era))
                    pp.pprint(v)
                    raise Exception
            else:
                setattr(self, k, [os.path.expandvars(i) for i in v])

        self._force_cuts = force_cuts
        for year in ['2016', '2017', '2018']:
            if year in self._force_cuts.keys():
                yead_dict = self._force_cuts.pop(year)
                if year == era:
                    self._force_cuts.update(yead_dict)
        self._invert_cuts = invert_cuts
        self._update_process_per_category = update_process_per_category
        self._replace_weights = replace_weights

        # Cuts manipulations
        # defaults {}
        for base in self.channel_minplotlev_cuts:
            setattr(self,
                '_' + base,
                kwargs[base] if base in kwargs.keys() else {})

        # use_*/no_*
        for base in self.cuts_manipulations + self.channel_minplotlev_cuts:
            for p in ['use_', 'no_']:
                setattr(self,
                    '_' + p + base,
                    kwargs[p + base] if p + base in kwargs.keys() else None)
            use = getattr(self, '_use_' + base)
            nouse = getattr(self, '_no_' + base)
            use = False if nouse == use and use is None else use
            assert nouse != use, "Cant use %s and %s together" % ('use_' + base, 'no_' + base)

        if self._no_fes_extra_cuts:
            self._logger.warning("All fes_extra_cuts are dropped:" + str(self._fes_extra_cuts))
            self._fes_extra_cuts = {}

        if self._no_et_minplotlev_cuts:
            self._logger.warning("All et_minplotlev_cuts are dropped:" + str(self._et_minplotlev_cuts))
            self._et_minplotlev_cuts = {}

        if self._no_force_cuts:
            self._logger.warning("All force_cuts are dropped:" + str(self._force_cuts))
            self._force_cuts = {}

        if self._no_extra_cuts:
            self._logger.warning("All fes_extra_cuts are dropped:" + str(self._fes_extra_cuts))
            self._logger.warning("All et_minplotlev_cuts are dropped:" + str(self._et_minplotlev_cuts))
            self._logger.warning("All force_cuts are dropped:" + str(self._force_cuts))
            self._fes_extra_cuts = {}
            self._et_minplotlev_cuts = {}
            self._force_cuts = {}

        if self._no_channel_specific:
            self._logger.warning('All channel_specific categorries are ignored')
            self._channel_specific = {}
        else:
            # unpack channel_specific configs (by year)
            for channel in self._channel_specific.keys():
                for option_name in self._channel_specific[channel].keys():
                    option_dict = self._channel_specific[channel][option_name]
                    if isinstance(option_dict, dict):
                        if set(('default', era)).intersection(option_dict):
                            if era in option_dict:
                                self._channel_specific[channel][option_name] = option_dict[era]
                                self._logger.info('%s : Set by era: %s = %s' % (channel, option_name, self._channel_specific[channel][option_name]))
                            elif 'default' in option_dict:
                                self._channel_specific[channel][option_name] = option_dict['default']
                                self._logger.info('%s : Set by default: %s = %s' % (channel, option_name, self._channel_specific[channel][option_name]))
                        else:
                            self._logger.info('%s : Set as is (dict): %s =  %s' % (channel, option_name, option_dict))
                            self._channel_specific[channel][option_name] = option_dict
                    else:
                        self._logger.info('%s : Set as is: %s = %s' % (channel, option_name, option_dict))
                        self._channel_specific[channel][option_name] = option_dict

            for c in self._channel_specific.keys():
                if c not in self._channels_key:
                    del self._channel_specific[c]

            for c in self._channel_specific.keys():
                if 'grid_categories' in self._channel_specific[c].keys():
                    # TODO: for now the global switch controls also individual channels
                    if (not self._no_grid_categories and self._no_grid_categories is not None) or self._use_grid_categories:

                        # add-update categories
                        for k, v in parser_grid_categories.iteritems():
                            self._channel_specific[c]['grid_categories'][k] = copy.deepcopy(v)

                        # mask/limit categories (strict -> no categories on missing keys)
                        for k, v in mask_grid_categories.iteritems():
                            k = k.replace('mask_', '')
                            if k in self._channel_specific[c]['grid_categories'].keys():
                                self._channel_specific[c]['grid_categories'][k] = copy.deepcopy(v)
                            else:
                                # if not any(eval(self._known_cuts[k][vi], {}, collections.defaultdict(lambda : 0)) for vi in v):
                                if not any(Shapes.myeval(self._known_cuts[k][vi]) for vi in v):
                                    # if the mask-key not in the dictionary - then no category can satisfy mask requirements
                                    self._logger.warning('%s : masking didn\'t result in any category!' % c)
                                    self._channel_specific[c]['grid_categories'] = {}
                                    break
                    else:
                        self._logger.warning('All channel_specific grid categorries are ignored')
                        self._channel_specific[c]['grid_categories'] = {}

        # if self._no_year_specific:
        #     self._logger.warning('All year_specific categorries are ignored')
        #     self._year_specific = {}
        # else:
        #     for year
        sys_processes = [
            'tes_sys_processes', 'fes_sys_processes', 'emb_sys_processes',
            'zpt_sys_processes', 'qcdem_sys_processes', 'met_sys_processes',
            'ees_sys_processes', 'zl_sys_processes', 'z_recoil_sys_processes',
            'tpt_sys_processes', 'jet_to_tau_fake_sys_processes', 'tauid_sys_processes',
        ]
        for sys_process in sys_processes:
            setattr(
                self,
                '_' + sys_process,
                kwargs[sys_process] if sys_process in kwargs.keys() else None)

        self._shifts = shifts
        self._skip_shifts = skip_shifts
        if self._skip_shifts is not None and self._shifts is not None:
            self._logger.warning('shifts are remooved on request: %s' % self._skip_shifts)
            for remove_shift in self._skip_shifts:
                self._shifts.remove(remove_shift)

        # set the grid categories
        if (not self._no_grid_categories and self._no_grid_categories is not None) or self._use_grid_categories:
            self._grid_categories = grid_categories

            # add-update catogories
            for k, v in parser_grid_categories.iteritems():
                self._grid_categories[k] = copy.deepcopy(v)

            # mask/limit categories (strict -> no categories on missing keys)
            for k, v in mask_grid_categories.iteritems():
                k = k.replace('mask_', '')

                if k in self._grid_categories.keys():
                    self._grid_categories[k] = copy.deepcopy(v)
                else:
                    if not any(Shapes.myeval(self._known_cuts[k][vi]) for vi in v):
                        # if the mask-key not in the dictionary - then no category can satisfy mask requirements
                        self._logger.warning('global _grid_categories : masking didn\'t result in any category!')
                        self._grid_categories = {}
                        break
        else:
            self._logger.warning('All grid categorries are ignored')
            self._grid_categories = {}

        # set the single categories
        if (not self._no_single_categories and self._no_single_categories is not None) or self._use_single_categories:
            self._single_categories = single_categories
        else:
            self._logger.warning('All single categorries ignored')
            self._single_categories = {}
        assert isinstance(self._grid_categories, dict), "grid_categories:: should be dict"
        assert isinstance(self._single_categories, dict), "single_categories:: should be dict"

        # Setting output file attribute
        self._output_file = output_file
        self._output_file_name = output_file_name if output_file_name is not None else ''
        self._output_file_dir = output_file_dir if output_file_dir is not None and output_file_dir is not '' else os.getcwd()

        for k, v in self._grid_categories.iteritems():
            for i in v:
                assert i in self._known_cuts[k].keys(), 'no dm: %s in known_cuts.yaml' % i

        self._channels = {}

        if self._output_file is not None:
            self._output_file_name = os.path.basename(self._output_file)
            self._output_file_dir = os.path.dirname(self._output_file)

        if self._output_file_name == '':
            self._output_file_name = "{}.root".format('_'.join([self._era_name, self._context_analysis, self._methods_collection_key]))
        elif not self._output_file_name.endswith('.root'):
            self._output_file_name = "{}.root".format(self._output_file_name)

        if self._no_extra_cuts:
            self._output_file_name = 'noForceCuts_' + self._output_file_name

        # check output dir exists
        if self._output_file_dir is not None and len(self._output_file_dir) > 1 and not os.path.isdir(self._output_file_dir):
            try:
                os.makedirs(self._output_file_dir)
            except:
                raise ValueError("%s::%s: failed to create a required output directory: %s" % (self.__class__.__name__, sys._getframe().f_code.co_name, self._output_file_dir))

        # set full file path
        self._output_file = os.path.join(self._output_file_dir, self._output_file_name)

        self._logger.debug("Context analysis: %s\n methods collection key: %s\n year: %s" % (self._context_analysis, self._methods_collection_key, self._era_name))
        self._logger.info("Output file: %s" % (self._output_file))

        # Holds Systematics for all the channels. TODO: add the per-channel systematics to ChannelHolder
        self.initSystematics()

    def initSystematics(self):
        self._systematics = Systematics(
            output_file=self._output_file,
            num_threads=self._num_threads,
            skip_systematic_variations=self._skip_systematic_variations
        )

    @property
    def variables_names(self):
        if not isinstance(self._variables_names, list):
            self._variables_names = [self._variables_names]
        return self._variables_names

    @variables_names.setter
    def variables_names(self, value):
        if not isinstance(value, list):
            if isinstance(value, basestring):
                self._variables_names = [value]
            else:
                log.fatal('variables_names should be a list of string or string')
                raise
        elif all(isinstance(item, basestring) for item in value):
            self._variables_names = value
        else:
            log.fatal('variables_names list contains a non-string: [' + ', '.join(self._variables_names) + ']')
            raise

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

    def addChannel(self, name, channel_holder):
        """
        Appends to the _channels dict only the ChannelHolder items
        """
        # print "ETauFES::addChannel:", name, type(channel_holder)
        if isinstance(channel_holder, ChannelHolder):
            self._channels[name] = channel_holder
        else:
            raise 'addChannel can\'t add non-ChannelHolder objects'

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
    def prepareConfig(cls, analysis_shapes, config_file, debug=False, parse_arguments=True):
        '''Read config and update to prompt'''
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '
        if debug:
            print '\n', self_name

        config = analysis_shapes.readConfig(config_file)

        if parse_arguments:
            prompt_args = analysis_shapes.parse_arguments(include_defaults=False)

            config.update(prompt_args)

            # prompt options overrule per-year definitions in the config

            # prompt options overrule per-channel definitions in the config
            options_prompt_overrides_channels = [
                'methods_collection_key',
                'single_categories', 'grid_categories',
                'no_single_categories', 'no_grid_categories',
                'use_single_categories', 'use_grid_categories',
                'replace_weights'
            ]
            if any(i in prompt_args.keys() for i in options_prompt_overrides_channels):
                # pops the corresponding options from channels settings letting it to fall back to updated global ones
                for option in Shapes.intersection(prompt_args.keys(), options_prompt_overrides_channels):
                    logging.getLogger(__name__).warning('%s was used in terminal -> updating all channel-specific values!' % option)
                    for channel in config['channel_specific'].keys():
                        if option in config['channel_specific'][channel]:
                            config['channel_specific'][channel].pop(option)

        if debug:
            print 'config:'
            pp.pprint(config)

        return config

    # TODO: cleanup, move to separate class?
    @classmethod
    def parse_arguments(cls, include_defaults=True, debug=False):
        # Note: importance:: defaults < config < terminal
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

        # Arguments with None default
        parser.add_argument("--era", "--year", type=str, help="Experiment era.")
        parser.add_argument("--gof-variable", type=str, help="Variable for goodness of fit shapes.")
        parser.add_argument("--gof-channel", type=str, help="Channel for goodness of fit shapes.")
        parser.add_argument("--et-friend-directory", nargs='*', type=str, help="Directory containing a friend tree for et.")
        parser.add_argument("--mt-friend-directory", nargs='*', type=str, help="Directory containing a friend tree for mt.")
        parser.add_argument("--tt-friend-directory", nargs='*', type=str, help="Directory containing a friend tree for tt.")
        parser.add_argument("--em-friend-directory", nargs='*', type=str, help="Directory containing a friend tree for em.")
        parser.add_argument("--fake-factor-friend-directory", type=str, help="Directory containing friend trees to data files with FF.")
        parser.add_argument("--fes-friend-directory", type=str, help="Fes shifts.")
        parser.add_argument("--extra-chain", type=str, help="Extra pipelines")
        parser.add_argument("--context-analysis", type=str, help="Context analysis.")
        parser.add_argument("--yaml-conf", type=str, help="Context analysis.")
        parser.add_argument("--variables-names", nargs='*', type=str, help="Variable names.")
        parser.add_argument("--invert-cuts", nargs='*', type=str, help="Invert cuts by their key names.")
        # parser.add_argument("--force-cuts", action=type('', (argparse.Action, ), dict(__call__=lambda a, p, n, v, o: getattr(n, a.dest).update(dict([v.split('=')])))), default={})  # anonymously subclassing argparse.Action
        parser.add_argument('--force-cuts', type=ast.literal_eval, help="Dict of cuts to force. Format: --force-cuts=\"\{'cut_key': 'cut_exp', 'cut_key': 'cut_exp'\}\"")
        # TODO!! this is just  a hack
        parser.add_argument('--single-categories', type=ast.literal_eval, help="Dict of cuts to force. Format: --single-categories=\"\{'cut_key': 'cut_exp', 'cut_key': 'cut_exp'\}\"")
        parser.add_argument('--replace-weights', type=ast.literal_eval, help="Dict of replace weights. Format: --replace-weights=\"\{'cut_key': 'cut_exp', 'cut_key': 'cut_exp'\}\"")

        parser.add_argument("--etau-es-shifts", nargs='*', type=float, help="etau_es_shifts")
        parser.add_argument("--mtau-es-shifts", nargs='*', type=float, help="mtau_es_shifts")

        # Arguments with defaults that might be changed in the config file.
        parser.add_argument("--channels", nargs='+', type=str, help="Channels to be considered.")
        parser.add_argument("--processes", nargs='+', type=str, help="Processes from the standart map of processes")  # TODO: enable passing via syntax <name>:<class name>
        parser.add_argument("--methods-collection-key", type=str, help="Methods collection key")
        parser.add_argument("--module", nargs=1, type=str, help="Module to import where estimation methods are defined")  # TODO: enable passing via syntax <name>:<class name>
        parser.add_argument('-n', "--num-threads", type=int, help="Number of threads to be used.")
        parser.add_argument("--backend", choices=["classic", "tdf"], type=str, help="Backend. Use classic or tdf.")
        parser.add_argument("--tag", type=str, help="Tag of output files.")
        parser.add_argument("--output-file", type=str, help="Output file  for file with final shapes that enter datacards. Invalidates output-file-name and output-file-dir")
        parser.add_argument("--output-file-name", type=str, help="Output file name for file with final shapes that enter datacards. If none is given context_analysis is used as a root for this name")
        parser.add_argument("--output-file-dir", type=str, help="Output file directory")
        parser.add_argument("--skip-systematic-variations", type=str, help="Do not produce the systematic variations.")
        parser.add_argument("--skip-processes", nargs='+', type=str, help="Do not produce the process.")

        # parser.add_argument("--tes-sys-processes", nargs='+', type=str, help="Typical processes affected by systematic variation")
        # parser.add_argument("--fes-sys-processes", nargs='+', type=str, help="Typical processes affected by systematic variation")
        # parser.add_argument("--emb-sys-processes", nargs='+', type=str, help="Typical processes affected by systematic variation")

        parser.add_argument("--shifts", nargs='+', type=str, help="Pipelines, uncertainties variations, shifts : processed is the intersection of this list with list from _known_estimation_methods")
        parser.add_argument("--skip-shifts", nargs='+', type=str, help="Pipelines, uncertainties variations, shifts : processed is the intersection of this list with list from _known_estimation_methods")
        parser.add_argument("--binning-key", type=str, help="Used only to pick the binning! example: gof, control")
        parser.add_argument("--log-level", type=str, help="Log level")
        parser.add_argument("--mass-susy-ggH", default=None, nargs='*', type=int, help="SUSY ggH masspoints")
        parser.add_argument("--mass-susy-qqH", default=None, nargs='*', type=int, help="SUSY bbH masspoints")
        parser.add_argument("--generator-qqH", default=None, nargs='*', type=str, help="SUSY bbH generator (leave blank to use whatever is defined in shapes-producer)")

        # Updating if the cuts grooup is already in defined grid-categories and adds it otherwise
        parser.add_argument("--eta-1-region", nargs='+', type=str, help="Needed for categorisation. Choices: eta_1_barel, eta_1_endcap, eta_1_endcap_real")
        parser.add_argument("--decay-mode", nargs='+', type=str, help="Needed for categorisation. Choices: all, dm0, dm1, dm10")
        parser.add_argument("--jets-multiplicity", nargs='+', type=str, help="Needed for categorisation. Choices: njetN, njet0")
        parser.add_argument("--pZetaMissVis-region", nargs='+', type=str, help="Needed for categorisation. Choices: dzeta_low, dzeta_medium, dzeta_high")
        parser.add_argument("--mt_1-region", nargs='+', type=str, help="Needed for categorisation. Choices: mt_1_tight, mt_1_loose")
        parser.add_argument("--btag-region", nargs='+', type=str, help="Needed for categorisation. Choices: nbtag_zero, nbtag_nonzero")

        # Updating if the cuts group is already in defined grid-categories but does NOT add it if it's not
        parser.add_argument("--mask-eta-1-region", nargs='+', type=str, help="Masks the grid categorries such that only mentioned cuts stay")
        parser.add_argument("--mask-decay-mode", nargs='+', type=str, help="Masks the grid categorries such that only mentioned cuts stay")
        parser.add_argument("--mask-jets-multiplicity", nargs='+', type=str, help="Masks the grid categorries such that only mentioned cuts stay")
        parser.add_argument("--mask-pZetaMissVis-region", nargs='+', type=str, help="Masks the grid categorries such that only mentioned cuts stay")
        parser.add_argument("--mask-mt_1-region", nargs='+', type=str, help="Masks the grid categorries such that only mentioned cuts stay")
        parser.add_argument("--mask-btag-region", nargs='+', type=str, help="Masks the grid categorries such that only mentioned cuts stay")

        parser.add_argument('--no-fes-extra-cuts', action='store_true', default=None, help='drop extra cuts. Note: will add a prefix to the output file')
        parser.add_argument('--no-et-minplotlev-cuts', action='store_true', default=None, help='drop et minplotlev cuts')
        parser.add_argument('--no-mt-minplotlev-cuts', action='store_true', default=None, help='drop mt minplotlev cuts')
        parser.add_argument('--no-force-cuts', action='store_true', default=None, help='drop extra cuts')
        parser.add_argument('--no-extra-cuts', action='store_true', default=None, help='drop extra cuts')
        parser.add_argument('--no-grid-categories', action='store_true', default=None, help='drop categorisation defined by grid_categories config.')
        parser.add_argument('--no-single-categories', action='store_true', default=None, help='drop categorisation defined by single_categories config.')
        parser.add_argument('--use-fes-extra-cuts', action='store_true', default=None, help='use extra cuts. Note: will add a prefix to the output file')
        parser.add_argument('--use-et-minplotlev-cuts', action='store_true', default=None, help='use et minplotlev cuts')
        parser.add_argument('--use-mt-minplotlev-cuts', action='store_true', default=None, help='use mt minplotlev cuts')
        parser.add_argument('--use-force-cuts', action='store_true', default=None, help='use extra cuts')
        parser.add_argument('--use-extra-cuts', action='store_true', default=None, help='use extra cuts')
        parser.add_argument('--use-grid-categories', action='store_true', default=None, help='use categorisation defined by grid_categories config.')
        parser.add_argument('--use-single-categories', action='store_true', default=None, help='use categorisation defined by single_categories config.')
        parser.add_argument('--use-channel-specific', action='store_true', default=None, help='use categorisation defined separately for channels.')
        parser.add_argument('--no-channel-specific', action='store_true', default=None, help='use categorisation defined separately for channels.')

        parser.add_argument('--use-year-specific', action='store_true', default=None, help='use categorisation defined separately for channels.')
        parser.add_argument('--no-year-specific', action='store_true', default=None, help='use categorisation defined separately for channels.')

        parser.add_argument('--update-process-per-category', action='store_true', default=None, help='Used to update extrapolation factors for the QCD estimation methods if they are provided')

        defaultArguments['channels'] = []
        defaultArguments['processes'] = []
        defaultArguments['methods_collection_key'] = 'methods'
        defaultArguments['module'] = None
        defaultArguments['num_threads'] = 32
        defaultArguments['backend'] = 'classic'
        defaultArguments['tag'] = 'ERA_CHANNEL'
        defaultArguments['output_file'] = None
        defaultArguments['output_file_name'] = ''
        defaultArguments['output_file_dir'] = ''
        defaultArguments['skip_systematic_variations'] = False
        defaultArguments['skip_processes'] = ['SUSYggH']
        defaultArguments['context_analysis'] = 'etFes'
        defaultArguments['yaml_conf'] = 'data/et_fes_legacy2017_config.yaml'

        # defaultArguments['tes_sys_processes'] = ["ZTT", "TTT", "TTL", "VVT", "EWKT", "VVL", "EMB", "DYJetsToLL"]
        # defaultArguments['fes_sys_processes'] = ['ZL', 'DYJetsToLL', 'EMB']
        # defaultArguments['emb_sys_processes'] = ['EMB']
        # defaultArguments['zpt_sys_processes'] = ['ZTT', 'ZL', 'ZJ']
        # defaultArguments['qcdem_sys_processes'] = ['QCD', 'QCDSStoOS', 'QCDSStoOSEMB', 'QCDEMB']
        # defaultArguments['met_sys_processes'] = ["TTL", "VVL"]
        # defaultArguments['ees_sys_processes'] = ["EMB"]
        # defaultArguments['zl_sys_processes'] = ["ZL"]
        # defaultArguments['tpt_sys_processes'] = ["TTT", "TTL", "TTJ", "TT"]

        defaultArguments['shifts'] = ['nominal', 'TES', 'EMB', 'FES_shifts', 'TES_shifts']
        defaultArguments['binning_key'] = 'control'
        defaultArguments['log_level'] = 'info'

        defaultArguments['mass_susy_ggH'] = [100, 110, 120, 130, 140, 180, 200, 250, 300, 350, 400, 450, 600, 700, 800, 900, 1200, 1400, 1500, 1600, 1800, 2000, 2300, 2600, 2900, 3200]
        defaultArguments['mass_susy_qqH'] = [90, 110, 120, 125, 130, 140, 160, 180, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1800, 2000, 2300, 2600, 3200]

        defaultArguments['decay_mode'] = ['all', 'dm0', 'dm1', 'dm10']
        defaultArguments['jets_multiplicity'] = ['njetN', 'njet0']
        defaultArguments['eta_1_region'] = ['inc_eta_1', 'eta_1_barel', 'eta_1_endcap', 'eta_1_barel_real', 'eta_1_endcap_real']
        defaultArguments['pZetaMissVis_region'] = ['dzeta_low', 'dzeta_medium', 'dzeta_high']
        defaultArguments['mt_1_region'] = ['mt_1_tight', 'mt_1_loose']
        defaultArguments['btag_region'] = ['nbtag_zero', 'nbtag_nonzero']

        defaultArguments['mask_decay_mode'] = ['all', 'dm0', 'dm1', 'dm10']
        defaultArguments['mask_jets_multiplicity'] = ['njetN', 'njet0']
        defaultArguments['mask_eta_1_region'] = ['inc_eta_1', 'eta_1_barel', 'eta_1_endcap', 'eta_1_barel_real', 'eta_1_endcap_real']
        defaultArguments['mask_pZetaMissVis_region'] = ['dzeta_low', 'dzeta_medium', 'dzeta_high']
        defaultArguments['mask_mt_1_region'] = ['mt_1_tight', 'mt_1_loose']
        defaultArguments['mask_btag_region'] = ['nbtag_zero', 'nbtag_nonzero']

        for base in cls.cuts_manipulations + cls.channel_minplotlev_cuts:
            for p in ['use_', 'no_']:
                defaultArguments[p + base] = False

        defaultArguments['no_fes_extra_cuts'] = False
        defaultArguments['no_et_minplotlev_cuts'] = False
        defaultArguments['no_mt_minplotlev_cuts'] = False
        defaultArguments['no_force_cuts'] = False
        defaultArguments['no_extra_cuts'] = False
        defaultArguments['no_grid_categories'] = False
        defaultArguments['no_single_categories'] = False
        defaultArguments['no_channel_specific'] = False
        # defaultArguments['no_year_specific'] = False

        defaultArguments['use_fes_extra_cuts'] = False
        defaultArguments['use_et_minplotlev_cuts'] = False
        defaultArguments['use_mt_minplotlev_cuts'] = False
        defaultArguments['use_force_cuts'] = False
        defaultArguments['use_extra_cuts'] = False
        defaultArguments['use_grid_categories'] = False
        defaultArguments['use_single_categories'] = False
        defaultArguments['use_channel_specific'] = False
        # defaultArguments['use_year_specific'] = False

        defaultArguments['update_process_per_category'] = False

        # Arguments with defaults that can NOT be changed in the config file
        parser.add_argument('--dry', action='store_true', default=False, help='dry run')
        parser.add_argument('--no-higgs', action='store_true', default=False, help='no higgs samples')
        parser.add_argument('--danger', action='store_true', default=False, help='danger level, to raise on root errors')

        parser.add_argument('--debug', action='store_true', default=False, help='cherry-debug')

        args = parser.parse_args()
        configuration = dict((k, v) for k, v in vars(args).iteritems() if v is not None)

        if include_defaults:
            for argument, default in defaultArguments.iteritems():
                if argument not in configuration:
                    configuration[argument] = default

        for base in ['fes_extra_cuts', 'et_minplotlev_cuts', 'mt_minplotlev_cuts', 'force_cuts',
                     'extra_cuts', 'grid_categories', 'single_categories', 'channel_specific',
                     # 'year_specific',
                     ]:
            use = 'use_' + base
            nouse = 'no_' + base
            assert not (use in configuration.keys() and nouse in configuration.keys()), "%s and %s can't be set at the same time" % (use, nouse)
            if use in configuration.keys():
                print 'called --%s' % use, 'setting --%s=' % nouse, not configuration[use]
                configuration[nouse] = not configuration[use]
            elif nouse in configuration.keys():
                print 'called --%s' % nouse, 'setting --%s=' % use, not configuration[nouse]
                configuration[use] = not configuration[nouse]

        # keys intended solely for usage with terminal command eg not defined in config
        configuration['parser_grid_categories'] = {}
        for k in ['decay_mode', 'jets_multiplicity', 'eta_1_region',
                  'pZetaMissVis_region', 'mt_1_region', 'btag_region']:
            if k in configuration.keys():
                configuration['parser_grid_categories'][k] = configuration.pop(k)

        configuration['mask_grid_categories'] = {}
        for k in ['mask_decay_mode', 'mask_jets_multiplicity', 'mask_eta_1_region',
                  'mask_pZetaMissVis_region', 'mask_mt_1_region', 'mask_btag_region']:
            if k in configuration.keys():
                configuration['mask_grid_categories'][k] = configuration.pop(k)

        # import pdb; pdb.set_trace()  # \!import code; code.interact(local=vars())
        return configuration

    @classmethod
    def get_rootpy_log(cls, level, logger=logging.getLogger(__name__), debug=False):
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '

        logger.info(self_name + level.upper())

        try:
            return getattr(log, level.upper())
        except:
            logger.fatal(self_name + ' unknown level ' + level)
            raise

    # TODO: separate from class? have a standalone class and inherit from it?
    @classmethod
    def setup_logging(
        cls,
        output_file,
        logger,
        level='DEBUG',
        danger=False,
        debug=False,
        add_stream_handler=False,
        add_file_handler=False,
        str_formatter=logging.BASIC_FORMAT,  # "%(name)s - %(levelname)s - %(message)s",
    ):
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name
        logger.info(self_name)

        level = cls.get_rootpy_log(level=level, logger=logger, debug=debug)
        DANGER.enabled = danger

        logger.setLevel(level)

        formatter = logging.Formatter(str_formatter)

        handler, file_handler = None, None
        if add_stream_handler and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # TODO: solve duplicated output / empty file
        if add_file_handler and not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            file_handler = logging.FileHandler(output_file, "w")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return handler, file_handler

    @staticmethod
    def getHostKey():
        import socket
        hostname = socket.gethostname()
        known_hosts = ['naf', 'cern', 'ekp', 'rwth', 'bms1', 'bms2', 'bms3', 'bird']
        for host in known_hosts:
            if host in hostname:
                return host if 'bms' not in host else 'bms'

        return 'unknown_host'

    @classmethod
    def readConfig(cls, config_file=None, debug=False):
        logger = logging.getLogger(__name__)
        self_name = cls.__name__ + '::' + sys._getframe().f_code.co_name + ': '
        if debug:
            print '\n', self_name

        common_config = {}
        with open('data/known_processes.yaml', 'r') as f:
            file_known_processes = yaml.load(f)
            for k in file_known_processes.keys():
                common_config[k] = file_known_processes[k]

        with open('data/known_estimation_methods.yaml', 'r') as f:
            file_known_estimation_methods = yaml.load(f)
            common_config['_known_methods_collections'] = file_known_estimation_methods['_known_methods_collections']
            common_config['_known_estimation_modules'] = file_known_estimation_methods['_known_estimation_modules']
            common_config['processes'] = file_known_estimation_methods['processes']

        with open('data/renaming.yaml', 'r') as f:
            common_config['_renaming'] = yaml.load(f)

        with open('data/known_cuts.yaml', 'r') as f:
            common_config['_known_cuts'] = yaml.load(f)

        assert isinstance(config_file, basestring), self_name + 'config obj of unset type'
        assert config_file.endswith('.yaml') or config_file.endswith('.yml'), self_name + 'config path is not yaml format'

        with open(config_file, 'r') as stream:
            try:
                import getpass
                username = getpass.getuser()
                hostname = Shapes.getHostKey()

                config = yaml.load(stream)

                # unpack user_specific configs (by host and year)
                for option_name in config['user_specific'].keys():
                    option_dict = config['user_specific'][option_name]
                    try:
                        config[option_name] = option_dict[username][hostname]
                        logger.info('Set by host/username: %s = %s' % (option_name, config[option_name]))
                    except:
                        try:
                            config[option_name] = option_dict['byhost'][hostname]
                            logger.info('Set by host: %s = %s' % (option_name, config[option_name]))
                        except:
                            config[option_name] = option_dict['byhost']['default']
                            logger.info('Set to default: %s = %s' % (option_name, config[option_name]))

                del config['user_specific']

                # return config

            except yaml.YAMLError as exc:
                logger.critical("%s yaml config couldn\' be loaded:\n%s\n%s" % (self_name, config_file, exc))
                # logger.critical(self_name + 'yaml config couldn\' be loaded:\n' +  config_file + '\n' + exc)
                raise

        # import pdb; pdb.set_trace()  # \!import code; code.interact(local=vars())
        common_config.update(config)
        return common_config

    # TODO: needs to belong to ChannelHolder
    def getVariables(self, channel_obj, variable_names, binning):
        """
        Returns dict of Variables for Channel
        """
        self._logger.debug(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)

        variables = {}

        for key in variable_names:
            # if channel_obj.name == 'em' and key in self._known_svfit_variables:
            #     self._logger.warning('Skippong variable %s for em channel' % key)
            #     continue
            variables[key] = Variable(
                key,
                VariableBinning(binning[key]["bins"]),
                expression=binning[key]["expression"],
            )

        return variables

    def evaluateChannel(self, channel):
        pass  # self._channels.add()

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

    def __getattr__(self, key):
        """
        Syntactic sugar to return a getEstimationMethod object defined by *key* in case no other attribute
        was resolved.
        """
        if key == '_estimation_methods':
            raise KeyError("The initialised value wasn't found or self._estimation_methods was tried to be accessed before initialization")
        self._logger.debug("__getattr__::%s" % key)
        return self.getEstimationMethod(key)

    def getEstimationMethod(self, key):
        """
        Returns class that corresponds to the requested estimation method
        """
        self._logger.debug("getEstimationMethod::%s" % key)
        if key != '_estimation_methods' and key in self._estimation_methods:
            return self._estimation_methods[key]
        else:
            raise KeyError("unknown getEstimationMethod key:" + key)

    def importEstimationMethods(self, module, *methods):  # TODO: add arguments validity
        """
        Manual importing of module
        """
        for method in methods:
                if method in self._estimation_methods:
                    self._logger.warning('Warning: Estimation method %s already defined - skipped redefinition' % method)
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
            for combine_name, method in self.getMethodsDict(
                    era=era,
                    context=context_analysis,
                    channel_name=channel_name).iteritems():
                if method in self._estimation_methods:
                    self._logger.warning('Warning: Estimation method %s already defined - skipped redefinition' % method)
                # print 'module:', self._estimation_methods, method
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

            subkey_names = [key]

            if estimation_method not in self._estimation_methods.keys():
                raise KeyError("Unknown estimation method: " + estimation_method)

            if key in processes.keys():  # TODO: add the check of the config
                print "Key added in list of processes twice. channel: " + channel_name + "; key:" + key
                continue

            if key in self._skip_processes:
                self._logger.warning("Skipping on request: %s" % key)
                continue

            if estimation_method in ['WEstimationWithQCD', 'QCDEstimationWithW']:
                bg_processes = {}
                bg_processes = [processes[process] for process in self._complexEstimationMethodsRequirements[key][estimation_method]]  # ["EMB", "ZL", "ZJ", "TTL", "TTJ", "VVL", "VVJ"]]
                # if "EMB" in key:
                #     bg_processes = [processes[process] for process in ["EMB", "ZL", "ZJ", "TTL", "TTJ", "VVL", "VVJ"]]
                #     # former with: "EWKL", "EWKJ"
                # else:
                #     bg_processes = [processes[process] for process in ["ZTT", "ZL", "ZJ", "TT", "VV"]]
                #     # alternative: ["DYJetsToLL", "TT", "VV"]]
                #     # former with "EWK"
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
                qcdsstoos_parameters_list['extrapolation_factor'] = 1.00  # 1.00  # QCD extrapolation_factor 1.17 for mt et 2016

                if 'em' in channel_obj.name:
                    qcdsstoos_parameters_list['extrapolation_factor'] = 1.00
                    if self._qcdem_setup == 2020:
                        # latest sm-htt
                        # year = copy.deepcopy(self.era.name).replace('Run', '')
                        if self._era_name not in self.em_closureweight.keys():
                            raise Exception("self.em_closureweight not set for '%s' year" % self._era_name)
                        if self._qcdem_manual:

                            ROOT.v5.TFormula.SetMaxima(3000)
                            qcdsstoos_parameters_list['qcd_weight'] = Weight(self.qcd_weight_string[self._era_name], "qcd_weight")
                        else:
                            qcdsstoos_parameters_list['qcd_weight'] = Weight("{closureweight}*em_qcd_osss_binned_Weight".format(closureweight=self.em_closureweight[self._era_name]), "qcd_weight")
                    else:
                        qcdsstoos_parameters_list['qcd_weight'] = Weight("em_qcd_extrap_up_Weight", "qcd_weight")
                elif ('et' in channel_obj.name or 'mt' in channel_obj.name) and self._era_name == '2016':
                    qcdsstoos_parameters_list['extrapolation_factor'] = 1.17  # 1.00  # QCD extrapolation_factor 1.17 for mt et 2016

                try:
                    qcdsstoos_parameters_list['data_process'] = processes['data_obs']
                except:
                    try:
                        qcdsstoos_parameters_list['data_process'] = processes['data']
                    except:
                        raise Exception("couldn't access processes['data_obs'] of data object")

                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**qcdsstoos_parameters_list))

            elif 'QCDABCD' in key:
                qcdabcd_parameters_list = copy.deepcopy(parameters_list)

                qcdabcd_parameters_list['bg_processes'] = [processes[process] for process in self._complexEstimationMethodsRequirements[key][estimation_method]]

                try:
                    qcdabcd_parameters_list['data_process'] = processes['data_obs']
                except:
                    try:
                        qcdabcd_parameters_list['data_process'] = processes['data']
                    except:
                        raise Exception("couldn't access processes neither ['data_obs'] not ['data'] of data object")

                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**qcdabcd_parameters_list))

            elif 'jetFakes' in key:
                ff_parameters_list = copy.deepcopy(parameters_list)
                ff_parameters_list['friend_directory'].extend(self._fake_factor_friend_directory)

                # import pdb; pdb.set_trace()
                if estimation_method in ['NewFakeEstimationLT', 'NewFakeEstimationTT']:
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
                else:
                    raise Exception("The jetFakes is not associated a propper method in the known_processes files. The passed method: %s " % estimation_method)

                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**ff_parameters_list))

            elif 'ZTTpTTTauTau' in key:
                ZTTpTTTauTau_parameters_list = copy.deepcopy(parameters_list)
                ZTTpTTTauTau_parameters_list['name'] = 'AddHistogram'
                ZTTpTTTauTau_parameters_list['add_processes'] = [processes[process] for process in self._complexEstimationMethodsRequirements[key][estimation_method]]
                if key.lower().endswith('up'):
                    ZTTpTTTauTau_parameters_list['add_weights'] = [1.0, 0.1]
                elif key.lower().endswith('down'):
                    ZTTpTTTauTau_parameters_list['add_weights'] = [1.0, -0.1]
                else:
                    raise Exception("couldn't identify shift direction for key: %s" % key)

                try:
                    ZTTpTTTauTau_parameters_list['data_process'] = processes['data_obs']
                except:
                    try:
                        ZTTpTTTauTau_parameters_list['data_process'] = processes['data']
                    except:
                        raise Exception("couldn't access processes['data'] or data_obs object")

                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**ZTTpTTTauTau_parameters_list))

            elif estimation_method in ['SUSYggHEstimation', 'SUSYbbHEstimation'] and not self._no_higgs:
                if key == "SUSYggH":
                    subkey_names = []
                    contributions = [
                        "ggH_t", "ggH_b", "ggH_i",
                        "ggA_i", "ggA_t", "ggA_b",
                        "ggh_i", "ggh_t", "ggh_b",
                        "ggH"
                    ]
                    for contribution in contributions:
                        for mass in self._mass_susy_ggH:
                            susy_parameters_list = copy.deepcopy(parameters_list)
                            susy_parameters_list['mass'] = str(mass)
                            susy_parameters_list['contribution'] = contribution.replace('gg', '')
                            subkey_name = "SUSYgg%s_%s" % (susy_parameters_list['contribution'], susy_parameters_list['mass'])
                            if subkey_name in self._skip_processes:
                                self._logger.warning("Skipping on request: %s" % subkey_name)
                                continue
                            subkey_names.append(subkey_name)

                            processes[subkey_name] = Process(subkey_name, self._estimation_methods[estimation_method](**susy_parameters_list))

                elif any([i in key for i in ["SUSYggH_", "SUSYggA_", "SUSYggh_"]]):
                    subkey_names = []

                    masses = copy.deepcopy(self._mass_susy_ggH)
                    if len(key.split('_')) == 3:
                        masses = [key.split('_')[-1]]

                    for mass in masses:
                        susy_parameters_list = copy.deepcopy(parameters_list)
                        susy_parameters_list['mass'] = str(mass)
                        susy_parameters_list['contribution'] = '_'.join(copy.deepcopy(key).replace('SUSYgg', '').split('_')[:2])
                        subkey_name = "SUSYgg%s_%s" % (susy_parameters_list['contribution'], susy_parameters_list['mass'])
                        if subkey_name in self._skip_processes:
                            self._logger.warning("Skipping on request: %s" % subkey_name)
                            continue
                        subkey_names.append(subkey_name)

                        processes[subkey_name] = Process(subkey_name, self._estimation_methods[estimation_method](**susy_parameters_list))

                elif "SUSYbbH" in key:
                    subkey_names = []

                    masses = copy.deepcopy(self._mass_susy_qqH)
                    if 'SUSYbbH_' in key:
                        masses = [key.split('_')[-1]]

                    for mass in masses:
                        susy_parameters_list = copy.deepcopy(parameters_list)
                        susy_parameters_list['mass'] = str(mass)
                        subkey_name = "SUSYbbH_%s" % susy_parameters_list['mass']
                        if subkey_name in self._skip_processes:
                            self._logger.warning("Skipping on request: %s" % subkey_name)
                            continue
                        subkey_names.append(subkey_name)

                        processes[subkey_name] = Process(subkey_name, self._estimation_methods[estimation_method](**susy_parameters_list))

                        if self._generator_qqH is not None:
                            # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                            # new_weights
                            processes[subkey_name]._estimation_method.queries[0]['generator'] = self._generator_qqH
                            # print processes[subkey_name]._estimation_method.get_files()
                            # exit(1)
                # not tested
                else:
                    self._logger.critical("NOT TESTED SETUP FOR SUSY")
                    susy_parameters_list = copy.deepcopy(parameters_list)
                    susy_parameters_list['mass'] = key.split('_')[-1]
                    if key in self._skip_processes:
                        self._logger.warning("Skipping on request: %s" % key)
                        continue
                    processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**susy_parameters_list))

            elif estimation_method in ['ggHEstimation', 'qqHEstimation'] and not self._no_higgs:
                HEstimation_parameters_list = copy.deepcopy(parameters_list)
                HEstimation_parameters_list['name'] = 'ggH125' if 'ggH' in estimation_method else 'qqH125'
                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**HEstimation_parameters_list))

            else:
                if self._no_higgs and 'H' in key:
                    self._logger.warning("Higgs process ignored on request: %s" % key)
                    continue
                # if key == 'ZL': print '-->getProcesses::', key, parameters_list
                processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**parameters_list))
                # try:
                #     import pdb; pdb.set_trace()  # !
                #     processes[key] = Process(combine_name, self._estimation_methods[estimation_method](**parameters_list))
                # except:
                #     import inspect

                #     # signature = inspect.signature(self._estimation_methods[estimation_method].__init__)
                #     # for name, parameter in signature.items():
                #     #     print(name, parameter.default, parameter.annotation, parameter.kind)

                #     import pdb; pdb.set_trace()  # !
                #     import code; code.interact(local=vars())

            # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
            if channel_name in self._channel_specific.keys() and 'replace_weights' in self._channel_specific[channel_name].keys():
                replace_weights = self._channel_specific[channel_name]['replace_weights']
                self._logger.info("replace_weights in channel %s [channel specific]" % (channel_name))
            else:
                replace_weights = self._replace_weights
                self._logger.info("replace_weights key in channel %s [global]" % (channel_name))

            for key_i in subkey_names:
                for replace_weights_key, replace_weights_value in replace_weights.iteritems():
                    try:
                        if "data" in key_i:
                            self._logger.warning('DO NOT REMOVE from estimetion method %s weight associated to %s' % (key_i, replace_weights_key))
                            continue
                        self._logger.warning('Removing from estimetion method %s weight associated to %s' % (key_i, replace_weights_key))
                        self._logger.debug('... old weights:%s\n%s' % (processes[key_i]._estimation_method.get_weights, str(processes[key_i]._estimation_method.get_weights())))
                        new_weights = copy.deepcopy(processes[key_i]._estimation_method.get_weights())

                        action = 'REPLACING'
                        if replace_weights_key in new_weights.names:
                            new_weights.remove(replace_weights_key)
                        else:
                            action = 'ADDING'
                            # self._logger.warning('\t\t ... nothing to remove. weight will be just added.')

                        if isinstance(replace_weights_value, six.string_types):
                            self._logger.warning('\t\t ... %s weight {%s : %s}' % (action, replace_weights_key, replace_weights_value))
                            new_weights.add(Weight(replace_weights_value, replace_weights_key))
                        elif replace_weights_value is not None:
                            raise Exception('Undefined manipulation with weights during EstimationMethods initialization. replace_weights_value: %s' % replace_weights_value)

                        self._logger.debug('\t\t ... old_weights address:%s' % (hex(id(processes[key_i]._estimation_method.get_weights))))
                        self._logger.debug('\t\t ... new_weights address:%s' % (hex(id(new_weights))))

                        processes[key_i]._estimation_method.get_weights = Shapes.make_get_weights_fun(new_weights)  #lambda: copy.deepcopy(new_weights)
                        self._logger.debug('... new assigned weights: %s\n%s' % (processes[key_i]._estimation_method.get_weights, str(processes[key_i]._estimation_method.get_weights())))
                        self._logger.debug('\t\t ... address:%s' % (hex(id(processes[key_i]._estimation_method.get_weights))))

                    except NotImplementedError:
                        self._logger.warning("The get_weights() wasn't implemented in estimation_methods: " + key_i + "\n \t replace_weights_key: " + replace_weights_key + "\n\t replace_weights_value" + replace_weights_value + "\n " + processes[key_i]._estimation_method.__str__())
                        # if 'QCDSStoOS' in key_i:
                        #     self._logger.warning("For QCDSStoOS the get_weights() wasn't implemented therefore the bg processes get replaced weights.")
                        #     self._bg_processes
                        # else:
                        #     pass

                    except Exception:
                        import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                        exit(1)
                        raise Exception('Undefined manipulation with weights during EstimationMethods initialization. \n replace_weights_key: %s \n replace_weights_value: %s\n ... old weights:%s\n%s' % (replace_weights_key, replace_weights_value, processes[key_i]._estimation_method.get_weights, str(processes[key_i]._estimation_method.get_weights())))

        return processes

    @staticmethod
    def make_get_weights_fun(r):
        new_weights = copy.deepcopy(r)
        return lambda: new_weights

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

        try:
            module = self._known_estimation_modules[era][context]['module']
            self._logger.info("Module by era '%s' context '%s': %s" % (era, context, module))
        except:
            try:
                module = self._known_estimation_modules[era]['module']
                self._logger.info("Module by era '%s': %s" % (era, module))
            except:
                module = self._known_estimation_modules['default']['module']
                self._logger.info("Default modulte: %s" % (module))

        return module

    def getMethodsDict(self, channel_name, era=None, context=None):
        # TODO: make initialisation universal

        # if self._channel_specific is not None and
        if channel_name in self._channel_specific.keys() and 'methods_collection_key' in self._channel_specific[channel_name].keys():
            methods_collection_key = self._channel_specific[channel_name]['methods_collection_key']

            self._logger.info("Methods key in channel %s : %s" % (channel_name, methods_collection_key))
        else:
            methods_collection_key = self._methods_collection_key
            self._logger.info("Methods key in channel %s [global]: %s" % (channel_name, methods_collection_key))

        if era is None:
            era = self._era_name
        era = str(era)
        if context is None:
            context = self._context_analysis

        if len(self._processes) == 0:
            try:
                return self._known_methods_collections[methods_collection_key]
            except Exception:
                self._logger.critical(' '.join(["Couldn't find the method for era:", era, 'context:', context, 'channel_name:', channel_name, 'methods_collection_key:', methods_collection_key]))
                self._logger.critical('Possible _known_estimation_methods:')
                pp.pprint(self._known_estimation_methods[era][context][channel_name])
                raise Exception
        else:
            d = {}
            for i in self._processes:
                if i in d.keys():
                    raise ValueError(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name + ': repeating process: ' + i)

                try:
                    d[i] = self._known_processes[i]
                except Exception:
                    if i.startswith('SUSYgg'):
                        d[i] = copy.deepcopy(self._known_processes['SUSYggH'])
                    elif i.startswith('SUSYbb'):
                        d[i] = copy.deepcopy(self._known_processes['SUSYbbH'])
                    else:
                        raise Exception
                        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
            return d

    # TODO: needs to belong to ChannelHolder ;
    def getCategorries(self, channel_holder, cuts=None,
            grid_categories=None,
            single_categories=None,
            channel_specific=None):
        """
        Returns dict of Cattegories for Channel
        """
        self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)

        grid_categories = self._grid_categories if grid_categories is None else grid_categories
        single_categories = self._single_categories if single_categories is None else single_categories
        channel_specific = self._channel_specific if channel_specific is None else channel_specific
        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
        categories = []
        intersection = lambda x, y: list(set(x) & set(y))
        channel_name = channel_holder._channel_obj.name
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

            # grid categories
            if not channel_specific \
               or channel_name not in channel_specific.keys() \
               or 'grid_categories' not in channel_specific[channel_name].keys():
                categories_by_space = [grid_categories[k] for k in grid_categories.keys()]
                if len(categories_by_space) > 0:
                    for category_space_cuts in product(*categories_by_space):
                        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
                        category_name = '_'.join(category_space_cuts)
                        self._logger.info('%s : ..adding grid category %s: {%s}', sys._getframe().f_code.co_name, category_name, ' && '.join(category_space_cuts))
                        categories.append(
                            Category(
                                name=category_name,
                                channel=channel_holder._channel_obj,
                                cuts=cuts,
                                variable=var)
                        )
                        # Remove cuts introduced in categorysation for the plots of isolation
                        if name == "iso_1" or name == "iso_2":
                            categories[-1].cuts.remove("ele_iso")
                            categories[-1].cuts.remove("tau_iso")

                        for cuts_class in self._known_cuts.keys():
                            # Add the $cuts_class splitting cattegorization
                            if cuts_class in grid_categories.keys():
                                cut_class_key = intersection(category_space_cuts, self._known_cuts[cuts_class].keys())
                                if len(cut_class_key) > 1:
                                    raise Exception("Too many %s values to unfold: [%s]" % (cuts_class, ', '.join(cut_class_key)))
                                else:
                                    cut_class_key = cut_class_key[0]
                                    self._logger.debug("Add the %s splitting: {%s: %s}" % (cuts_class, cut_class_key, self._known_cuts[cuts_class][cut_class_key]))
                                    categories[-1].cuts.add(Cut(self._known_cuts[cuts_class][cut_class_key], cut_class_key))

            # single categories
            if not channel_specific \
               or channel_name not in channel_specific.keys() \
               or 'single_categories' not in channel_specific[channel_name].keys():
                for category_name, category_cuts in single_categories.iteritems():
                    self._logger.info('%s : ..adding single category %s' % (sys._getframe().f_code.co_name, category_name))
                    categories.append(
                        Category(
                            name=category_name,
                            channel=channel_holder._channel_obj,
                            cuts=cuts,
                            variable=var)
                    )
                    # Remove cuts introduced in categorysation for the plots of isolation
                    if name == "iso_1" or name == "iso_2":
                        categories[-1].cuts.remove("ele_iso")
                        categories[-1].cuts.remove("tau_iso")

                    for cut_key, cut_expression in category_cuts.iteritems():
                        categories[-1].cuts.remove(cut_key)
                        if cut_expression is not None:
                            categories[-1].cuts.add(Cut(cut_expression, cut_key))
                        self._logger.debug('\t appending category cut: {"%s": "%s"}' % (cut_key, cut_expression))

            # categories specific for the channel
            if channel_name in channel_specific.keys():
                ch = channel_specific[channel_name]

                assert not('no_grid_categories' in ch and 'use_grid_categories' in ch and cd['no_grid_categories'] and ch['use_grid_categories']), "Contradicting parameters for grid_categories"
                assert not('no_single_categories' in ch and 'use_single_categories' in ch and cd['no_single_categories'] and ch['use_single_categories']), "Contradicting parameters for single_categories"

                gr_c = ch['grid_categories'] if 'grid_categories' in ch.keys() else {}
                sg_c = ch['single_categories'] if 'single_categories' in ch.keys() else {}

                if 'no_grid_categories' in ch or 'use_grid_categories' in ch:
                    if ('no_grid_categories' in ch and ch['no_grid_categories']) or ('use_grid_categories' in ch and ch['use_grid_categories'] is False):
                        gr_c = {}
                elif (not self._use_grid_categories and self._use_grid_categories is not None) or self._no_grid_categories:
                    gr_c = {}

                if 'no_single_categories' in ch or 'use_single_categories' in ch:
                    if ('no_single_categories' in ch and ch['no_single_categories']) or ('use_single_categories' in ch and ch['use_single_categories'] is False):
                        sg_c = {}
                elif (not self._use_single_categories and self._use_single_categories is not None) or self._no_single_categories:
                    sg_c = {}

                categories += self.getCategorries(
                    channel_holder=channel_holder,
                    grid_categories=gr_c,  # TODO: 'and use_grid_categories': testing
                    single_categories=sg_c,  # TODO: 'and use_single_categories': testing
                    channel_specific={},
                )

        log_categories = '\tCattegories:\n'
        for category in categories:
            log_categories += ''.join(['\t' * 2, category.name, '_:', category.cuts.__str__(indent=3 + self._indent) + '\n'])

        self._logger.info(log_categories)
        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())

        return categories

    def getChannelSystematics(self, channel_holder):
        """
        Setting systematics to associated INDIVIDUAL channel
        """
        self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)
        self._logger.warning('Not implemented!')
        pass

    def getNCategories(self):
        n = 0
        for channel_name, channel_holder in self._channels.iteritems():
            self._logger.info("Number of categories in channel %s : %d" % (channel_name, len(channel_holder._categorries)))
            n += len(channel_holder._categorries)
        self._logger.info("Number of categories in all channels: %d" % n)
        return n

    def getNShapes(self):
        return len(self._systematics._systematics)

    def produce(self):
        self._logger.info(self.__class__.__name__ + '::' + sys._getframe().f_code.co_name)
        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
        self._logger.debug(self._systematics)
        # import pdb; pdb.set_trace() # !import code; code.interact(local=vars())
        # # !import code; code.interact(local=vars())

        if 'nominal' not in self._shifts:
            self._logger.warning("Nominal shapes will not be produced")
            # import pdb; pdb.set_trace() # !import code; code.interact(local=vars())
            self._systematics._systematics = [i for i in self._systematics._systematics if i._variation._name != 'Nominal']
        shapes_to_prod = '\n'
        shapes_to_prod_debug = '\n'
        log_d = {}
        for i in self._systematics._systematics:
            ch = i._process._estimation_method._channel.name
            variation = i._variation.name
            variable = i._category._variable.name
            cat = i._category._name
            if ch not in log_d.keys():
                log_d[ch] = {'n': 0, 'variation': {}}
            if variation not in log_d[ch]['variation'].keys():
                log_d[ch]['variation'][variation] = {'n': 0, 'categ': {}}
            if cat not in log_d[ch]['variation'][variation]['categ'].keys():
                log_d[ch]['variation'][variation]['categ'][cat] = 0
            log_d[ch]['variation'][variation]['categ'][cat] += 1
            # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())
            proc_name = i._process._name
            if any(i._process._estimation_method._name.startswith(j) for j in ['bbH_', 'ggH_', 'ggA_', 'ggh_', ]):
                proc_name = i._process._estimation_method._name
            shapes_to_prod += "{:>60s} {:<10s}  {:<30s} {:<2} {:<8}\n".format(variation, proc_name, cat, ch, variable)
            # TODO : this try/except might be necessary to add on replacing weights functionality
            try:
                shapes_to_prod_debug += "{:>60s} {:<10s}  {:<30s} {:<2} {:<8}\n {:s}".format(variation, proc_name, cat, ch, variable, i._process._estimation_method.get_weights().__str__)
            except NotImplementedError:
                self._logger.warning("The get_weights() wasn't implemented inf estimation_methods: " + i._process._estimation_method.__str__())
                shapes_to_prod_debug += "{:>60s} {:<10s}  {:<30s} {:<2} {:<8} {:s}\n".format(variation, proc_name, cat, ch, variable, " WARNING: get_weights() not implemented!")

        for ch in log_d.keys():
            n1 = 0
            for v in log_d[ch]['variation'].keys():
                n = 0
                for c in log_d[ch]['variation'][v]['categ'].keys():
                    n += log_d[ch]['variation'][v]['categ'][c]
                log_d[ch]['variation'][v]['n'] = n
                n1 += n
            log_d[ch]['n'] = n1

        if self._log_level.lower() != 'debug':
            self._logger.info("Starting to produce following shapes: " + shapes_to_prod)
        else:
            self._logger.info("Starting to produce following shapes [debug]: " + shapes_to_prod_debug)
        pp.pprint(log_d)
        # print 'name:', self._systematics._systematics[0]._variation._name, self._systematics._systematics[0]._process._name, self._systematics._systematics[0]._category._name
        # import pdb; pdb.set_trace()  # !import code; code.interact(local=vars())

        if not self._dry:
            if self.getNShapes() == 0:
                self._logger.critical("Nothing to produce! Switching to dry mode.")
                self._dry = True
                return
            self._systematics.produce()
        else:
            self._logger.info("Dry run, stopping. Nshapes: %d" % len(self._systematics._systematics))


if __name__ == '__main__':
    args = Shapes.parse_arguments()
    shapes = Shapes(**args)
    print shapes
