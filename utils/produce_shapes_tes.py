import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
log.setLevel(log.INFO)
from rootpy.logger.magic import DANGER
DANGER.enabled = False

from shapes.tes import tesshapes
from shape_producer.systematics import Systematics
from shapes.convert_to_shapes import convertToShapes


def prepareConfig(config_file='data/tes_config.yaml', debug=False):
    '''Read config and update to prompt'''
    config = tesshapes.TESShapes.readConfig(config_file)

    prompt_args = tesshapes.TESShapes.parse_arguments(include_defaults=False)

    config.update(prompt_args)

    if debug:
        print 'config:'
        pp.pprint(config)

    return config


def produce_shapes_variables(config):

    print '\n # 2 - setup_logging'
    shapes = tesshapes.TESShapes(**config)
    shapes.setup_logging(output_file="{}_tesshapes.log".format(shapes._tag), level=log.INFO, logger=shapes._logger)

    print '\n # 3 - Era evaluation'
    shapes.evaluateEra()
    # shapes._nominal_folder = 'eleTauEsOneProngPiZerosShift_0'
    print '\n # 4 - import necessary estimation methods'
    shapes.importEstimationMethods()

    print '\n # 5 - evaluating channels (processes, variables,cattegories)'
    shapes.evaluateChannels()

    print '\n # 6 - add systematics'
    shapes.evaluateSystematics()
    # return 0
    print '\n # 7 - produce shapes'
    shapes.produce()

    print '\n # 8 - convert to synched shapes'

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    output_file_name = convertToShapes(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
        channels=['mt'],
        context='_tes',
    )

    print '\n # 9 - implement the nominal ploting if you want'


def main():
    print 'Start'

    print '\n # 1 - prepareConfig'
    config = prepareConfig(debug=False)

    produce_shapes_variables(config=config)

    print 'End'


if __name__ == '__main__':
    main()
