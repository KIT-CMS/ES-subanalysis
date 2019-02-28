import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
# log.setLevel(log.INFO)
# from rootpy.logger.magic import DANGER
# DANGER.enabled = False

from shapes.tes import tesshapes
from shape_producer.systematics import Systematics
from shapes.convert_to_shapes import convertToShapes


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def prepareConfig(config_file='data/tes_config.yaml', debug=False):
    '''Read config and update to prompt'''
    config = tesshapes.TESShapes.readConfig(config_file)

    prompt_args = tesshapes.TESShapes.parse_arguments(include_defaults=False)

    config.update(prompt_args)

    if debug:
        print 'config:'
        pp.pprint(config)
    pp.pprint(config)
    exit(1)
    return config


def produce_shapes_variables(config):

    print bcolors.HEADER, '\n # 1 - init TESShapes', bcolors.ENDC
    shapes = tesshapes.TESShapes(**config)

    print bcolors.HEADER, '\n # 2 - setup_logging', bcolors.ENDC
    shapes.setup_logging(output_file="{}_tesshapes.log".format(shapes._tag), level=config['log_level'], logger=shapes._logger)

    print bcolors.HEADER, '\n # 3 - era evaluation', bcolors.ENDC
    shapes.evaluateEra()
    # shapes._nominal_folder = 'eleTauEsOneProngPiZerosShift_0'
    print bcolors.HEADER, '\n # 4 - import necessary estimation methods', bcolors.ENDC
    shapes.importEstimationMethods()

    print bcolors.HEADER, '\n # 5 - evaluating channels (processes, variables,cattegories)', bcolors.ENDC
    shapes.evaluateChannels()

    print bcolors.HEADER, '\n # 6 - add systematics', bcolors.ENDC
    shapes.evaluateSystematics()
    # return 0
    print bcolors.HEADER, '\n # 7 - produce shapes', bcolors.ENDC
    shapes.produce()

    print bcolors.HEADER, '\n # 8 - convert to synched shapes', bcolors.ENDC

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    output_file_name = convertToShapes(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
        channels=['mt'],
        context='_tes',
    )

    # prinbcolors.HEADER, t '\n # 9 - implement the nominal ploting if you want', bcolors.ENDC

    print bcolors.HEADER, 'Output shapes:', output_file_name


def main():
    print bcolors.HEADER, 'Start', bcolors.ENDC

    print bcolors.HEADER, '\n # 0 - prepareConfig', bcolors.ENDC
    config = prepareConfig(debug=False)

    produce_shapes_variables(config=config)

    print bcolors.HEADER, 'End', bcolors.ENDC


if __name__ == '__main__':
    main()
