"""
Creates plots for comparison of individual shapes in the isolated versus anti-isolated regions
"""
import os
import copy
import ROOT
import pprint
pp = pprint.PrettyPrinter(indent=4)
import functools

from shapes.convert_to_synced_shapes import convertToSynced

from python_wrappers.subprocessHandler import SubprocessHandler
from python_wrappers.myBase import MyBase
from python_wrappers.harryHolder import HarryHolder

'''
[[ ":$PYTHONPATH:" != *"/afs/desy.de/user/g/glusheno/RWTH/KIT/Shapes/ES-subanalysis/:"* ]] && PYTHONPATH="/afs/desy.de/user/g/glusheno/RWTH/KIT/Shapes/ES-subanalysis/:${PYTHONPATH}"
[[ ":$PYTHONPATH:" != *"$DIR_PRIVATESETTINGS:"* ]] && PYTHONPATH="$DIR_PRIVATESETTINGS:${PYTHONPATH}"
export PYTHONPATH
source /cvmfs/sft.cern.ch/lcg/views/LCG_94/x86_64-slc6-gcc62-opt/setup.sh
'''


class CompareShapes(MyBase):

    def __init__(self, **kvargs):
        if kvargs['debug']:
            print "CompareShapes::__init__"

        super(CompareShapes, self).__init__(**kvargs)

        self.commands = []
        self.commands_dicts = []

        self.dprint("CompareShapes::__init__ ... done")

    def run(self):
        self.category = 'njet0_dm1'
        # ff_shapes = '/afs/desy.de/user/g/glusheno/RWTH/KIT/Shapes/ES-subanalysis/fake-factors/2017_ff_yields.root'
        # ff_shapes_conv = '/nfs/dust/cms/user/glusheno/afs/RWTH/KIT/Shapes/ES-subanalysis/converted_shapes/2017_ff_yields/htt_et.inputs-etFes.root'
        # ff_shapes = '/afs/desy.de/user/g/glusheno/RWTH/KIT/Shapes/ES-subanalysis/fake-factors-test/2017_ff_yields.root'
        # ff_shapes_conv = '/nfs/dust/cms/user/glusheno/afs/RWTH/KIT/Shapes/ES-subanalysis/converted_shapes/2017_ff_yields/htt_et.inputs-etFes.root'
        # a_shapes_conv = '/nfs/dust/cms/user/glusheno/afs/RWTH/KIT/Shapes/ES-subanalysis/converted_shapes/A5_etauFES_bin5GeV_ff_njet0_dm1/htt_et.inputs-etFes.root'
        a_shapes_conv = self.args.a_shapes_conv
        ff_shapes = self.args.ff_shapes
        ff_shapes_conv = self.args.ff_shapes_conv

        # FF shapes from root-file convert to datacards format
        if self.args.reconvert_ff_shapes or ff_shapes_conv is None:
            if not os.path.isfile(os.path.join(ff_shapes)):
                print 'not a file:', os.path.join(ff_shapes)
                exit(1)
            ff_shapes_conv = convertToSynced(
                input_path=ff_shapes,
                output_dir=str(os.path.join('/nfs/dust/cms/user/glusheno/afs/RWTH/KIT/Shapes/ES-subanalysis/converted_shapes/', ff_shapes.split('/')[-2])),
            )
        self.dprint('ff_shapes_conv:', ff_shapes_conv)
        if not os.path.isfile(os.path.join(a_shapes_conv)):
            print 'not a file:', os.path.join(a_shapes_conv)
            exit(1)
        if not os.path.isfile(os.path.join(ff_shapes_conv)):
            print 'not a file:', os.path.join(ff_shapes_conv)
            exit(1)

        # Prepare the list of histograms that are in both files to be compared
        self.hist_map_ff = HarryHolder.prepareHistMap(file=ff_shapes_conv, debug=False)
        self.hist_map_a = HarryHolder.prepareHistMap(file=a_shapes_conv, debug=False)
        self.hist_map = MyBase.dictIntersection(self.hist_map_ff, self.hist_map_a, debug=False)
        print 'self.hist_map:'
        MyBase.dpprint(self.hist_map, debug=True)

        # For each plot construct a hp call
        commands_dicts = HarryHolder.getPlotsCommands(
            plottingpath=os.path.join(self.args.produce_plots_path, 'plots'),
            title='FF fine categ.',
            labels=['anti-iso', 'iso,tight'],
            files=[ff_shapes_conv, a_shapes_conv],
            files_nicks=['ff', 'a'],
            # root_file_dirs='et_' + self.category,
            # x_expressions=None,
            hist_map=self.hist_map,
            dry=self.args.dry,
            debug=False,
            xlable='m_{vis}',
        )
        self.commands_dicts.extend(copy.deepcopy(commands_dicts))

        # Fix the spaces passing in the passed parameters, ratio arguments
        for cd in self.commands_dicts:

            # Use escape symbol to pass parameters with spaces
            for single_str in ['--title', '--x-label']:
                if single_str in cd.keys():
                    cd[single_str] = '\"' + cd[single_str] + '\"'

            # Add the ratio plot settings
            if self.args.ratio:
                extra_dict = {
                    '--analysis-modules': ['Ratio'],
                    '--ratio-numerator-nicks': ['ff', 'a'],
                    '--ratio-denominator-nicks': ['a', 'a'],
                    '--ratio-result-nicks': ['ratio', 'ratio_unity'],
                    '--colors': ["kRed", "kBlack"],
                }
                if '--analysis-modules' in cd:
                    extra_dict['--analysis-modules'].extend(cd['--analysis-modules'])
                cd.update(extra_dict)

        # Construct a single HP call in form of string
        self.commands_s = map(lambda x: HarryHolder.dictToStr(x, s='higgsplot.py '), self.commands_dicts)
        pp.pprint(self.commands_s)

        # Start execution of HP calls
        subprocessHandler = SubprocessHandler(
            commands=self.commands_s,
            dry=self.args.dry,
            debug=self.args.debug,
            n_threads=self.args.n_threads,
            yes_on_command=self.args.yes_on_command,
            silent=self.args.silent,
        )
        subprocessHandler.run()

        print "done"

    def setup_parser(self):
        self.dprint('CompareShapes::setup_parser')
        super(CompareShapes, self).setup_parser()

        # self.subparser = self.subparsers.add_parser('CompareShapes', help='Script to compare shapes that are used for ff ratio calculation with analysis shapes')
        self.subparser = self.parser.add_argument_group("Script to compare shapes that are used for ff ratio calculation with analysis shapes")

        self.subparser.add_argument(
            '--reconvert-ff-shapes',
            default=False, action="store_true",
            help='Reconvert ff shapes',
        )

        self.subparser.add_argument(
            '--ratio',
            default=False, action="store_true",
            help='Reconvert ff shapes',
        )

        self.subparser.add_argument(
            "-i", "--input-files",
            nargs='*', default=[],
            help="Input dirs preferable /merged/. number should correspond to output files!")
        self.subparser.add_argument(
            "--output-dir",
            nargs='*', default=["et_nominal", ],
            help="Output directory")
        self.subparser.add_argument(
            "-c", "--channels",
            nargs='*', default=["et_nominal", ],
            help="Channels (eg mother directory) to look for btag num and denum")  # "mt_nominal", "tt_nominal", "mm_nominal", "em_nominal"

        self.subparser.add_argument(
            "--input-dirs",
            nargs='*', default=[],
            help="input dirs preferable /merged/ ")
        self.subparser.add_argument(
            '--produce-plots-path',
            default="/nfs/dust/cms/user/glusheno/FF/glusheno/fake_factor_friends/new_ff_weights/fake_factor_friends/",
            help="Produce plots path will work around all root files in the path [Default: %(default)s]")

        self.subparser.add_argument(
            '--variables',
            nargs='*',
            default=[
                'ff2_nom', 'ff2_ff_qcd_syst_up', 'ff2_ff_qcd_syst_down',
                'ff2_ff_qcd_dm0_njet0_stat_up', 'ff2_ff_qcd_dm0_njet0_stat_down',
                'ff2_ff_qcd_dm0_njet1_stat_up', 'ff2_ff_qcd_dm0_njet1_stat_down',
                'ff2_ff_w_syst_up', 'ff2_ff_w_syst_down', 'ff2_ff_w_dm0_njet0_stat_up',
                'ff2_ff_w_dm0_njet0_stat_down', 'ff2_ff_w_dm0_njet1_stat_up',
                'ff2_ff_w_dm0_njet1_stat_down', 'ff2_ff_tt_syst_up',
                'ff2_ff_tt_syst_down', 'ff2_ff_tt_dm0_njet0_stat_up',
                'ff2_ff_tt_dm0_njet0_stat_down', 'ff2_ff_tt_dm0_njet1_stat_up',
                'ff2_ff_tt_dm0_njet1_stat_down'
            ],
            help="Variables to compare [Default: %(default)s]")

        self.subparser.add_argument(
            "--a-shapes-conv",
            type=str, default='/nfs/dust/cms/user/glusheno/afs/RWTH/KIT/Shapes/ES-subanalysis/converted_shapes/test_A5_ZL_njets0_dm1_withFF/htt_et.inputs-etFes.root',
            help="a_shapes_conv: the shapes are taken for the isolated region")
        self.subparser.add_argument(
            "--ff-shapes-conv",
            type=str, default=None,
            help="ff_shapes_conv: the shapes are taken for the anti-isolated region")
        self.subparser.add_argument(
            "--ff-shapes",
            type=str, default=None,
            help="ff_shapes")

        self.dprint('CompareShapes::setup_parser ... done')


if __name__ == "__main__":
    c = CompareShapes(debug=False)
    c.dprint("Obtaining parsers")
    print c.parse_args()
    c.setDebugLevel(c.args.debug)

    c.run()
    # setup_logging("{}_compare_ff_shapes_etFES.log".format(args.tag), logging.INFO)
