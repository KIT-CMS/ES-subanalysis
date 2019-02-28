import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
log.setLevel(log.INFO)
from rootpy.logger.magic import DANGER
DANGER.enabled = False

from shapes.etau_fes import etau_fes
from shape_producer.systematics import Systematics
from shapes.convert_to_synced_shapes import convertToSynced


def prepareConfig(config_file='data/et_fes_config.yaml', debug=False):
    '''Read config and update to prompt'''
    config = etau_fes.ETauFES.readConfig(config_file)

    prompt_args = etau_fes.ETauFES.parse_arguments(include_defaults=False)

    config.update(prompt_args)

    if debug:
        print 'config:'
        pp.pprint(config)

    return config


def produce_shapes_variables(config):

    print '\n # 2 - setup_logging'
    shapes = etau_fes.ETauFES(**config)
    shapes.setup_logging(output_file="{}_etau_fes.log".format(shapes._tag), level=log.INFO, logger=shapes._logger)

    print '\n # 3 - Era evaluation'
    shapes.evaluateEra()
    # shapes._nominal_folder = 'eleTauEsOneProngPiZerosShift_0'
    print '\n # 4 - import necessary estimation methods'
    shapes.importEstimationMethods()

    print '\n # 5 - evaluating channels (processes, variables,cattegories)'
    shapes.evaluateChannels()

    print '\n # 6 - add systematics'
    shapes.evaluateSystematics()

    print '\n # 7 - produce shapes'
    shapes.produce()

    print '\n # 8 - convert to synched shapes'

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    convertToSynced(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
    )

    # print '\n # 9 - implement the nominal ploting if you want'

    print 'done'


def main():
    print 'Start'

    print '\n # 1 - prepareConfig'
    config = prepareConfig(debug=False)

    produce_shapes_variables(config=config)

    print 'End'


if __name__ == '__main__':
    main()
