import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging

from rootpy import log

# logging.basicConfig(level=log.INFO)
# log.setLevel(log.INFO)
# from rootpy.logger.magic import DANGER
# DANGER.enabled = False

from shapes import styled
from shapes.tes.tesshapes import TESShapes as analysis_shapes
from shape_producer.systematics import Systematics
from shapes.convert_to_shapes import convertToShapes


def produce_shapes_variables(config):

    logging.info(styled.HEADER('# 1 - init TESShapes'))
    shapes = analysis_shapes(**config)

    logging.info(styled.HEADER('# 2 - setup_logging'))
    shapes.setup_logging(
        output_file="{}_tesshapes.log".format(shapes._tag),
        level=config['log_level'],
        logger=shapes._logger,
        danger=False,
    )

    # Disabling some printouts
    logging.getLogger('shape_producer').setLevel(log.INFO)
    # print 'loggerDict:'; pp.pprint(logging.Logger.manager.loggerDict) ; exit(1)

    logging.info(styled.HEADER('# 3 - era evaluation'))
    shapes.evaluateEra()
    # shapes._nominal_folder = 'eleTauEsOneProngPiZerosShift_0'
    logging.info(styled.HEADER('# 4 - import necessary estimation methods'))
    shapes.importEstimationMethods()

    logging.info(styled.HEADER('# 5 - evaluating channels (processes, variables,cattegories)'))
    shapes.evaluateChannels()

    logging.info(styled.HEADER('# 6 - add systematics'))
    shapes.evaluateSystematics()

    logging.info(styled.HEADER('# 7 - produce shapes'))
    shapes.produce()

    logging.info(styled.HEADER('# 8 - convert to synched shapes'))

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    output_file_name = convertToShapes(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
        channels=['mt'],
        context='_tes',
    )

    # logging.info(styled.HEADER( t '\n # 9 - implement the nominal ploting if you want'))

    logging.info(styled.UNDERLINE(styled.HEADER('Output shapes:')))
    logging.info(styled.BOLD(styled.HEADER(output_file_name)))


def main():
    debug = False
    logging.info(styled.HEADER('Start'))
    # styled.HEADER('Start')

    logging.info(styled.HEADER('# 0 - prepareConfig'))
    config = analysis_shapes.prepareConfig(
        analysis_shapes=analysis_shapes,
        config_file='data/tes_config.yaml',
        debug=debug
    )

    produce_shapes_variables(config=config)

    logging.info(styled.HEADER('End'))


if __name__ == '__main__':
    main()
