import os
from six import string_types

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging

from rootpy import log

# logging.basicConfig(level=log.INFO)
# log.setLevel(log.INFO)
# from rootpy.logger.magic import DANGER
# DANGER.enabled = False

from shapes import styled
from shapes.control.controlshapes import ControlShapes as analysis_shapes
from shape_producer.systematics import Systematics
from shapes.convert_to_shapes import convertToShapes

# import shape_producer.systematics
# shape_producer.systematics.logger = log


def produce_shapes_variables(config):

    logging.info(styled.HEADER('# 1 - init ControlShapes'))
    shapes = analysis_shapes(**config)

    logging.info(styled.HEADER('# 2 - setup_logging'))

    handler, file_handler = shapes.setup_logging(
        output_file="{}_controlshapes.log".format(shapes._tag),
        level=config['log_level'],
        logger=logging.getLogger(),  # shapes._logger,
        danger=False,
        add_file_handler=False,
        add_stream_handler=False,
    )

    # Disabling some printouts
    # logging.getLogger('shape_producer').setLevel(log.INFO)
    # logging.getLogger('shape_producer.systematics').setLevel(log.INFO)
    # logging.getLogger('shape_producer.histogram').setLevel(log.INFO)
    logging.getLogger('shape_producer.histogram').setLevel(log.DEBUG)

    if handler is not None:
        handler.setLevel(log.INFO)
        # logging.getLogger('shape_producer.histogram').addHandler(handler)

    if file_handler is not None:
        file_handler.setLevel(log.DEBUG)

    logging.info(styled.HEADER('# 3 - era evaluation'))
    shapes.evaluateEra()

    logging.info(styled.HEADER('# 4 - import necessary estimation methods'))
    shapes.importEstimationMethods()

    logging.info(styled.HEADER('# 5 - evaluating channels (processes, variables,cattegories)'))
    shapes.evaluateChannels()

    logging.info(styled.HEADER('# 6 - add systematics'))
    shapes.evaluateSystematics()

    logging.info(styled.HEADER('# 7 - produce shapes'))
    shapes.produce()
    # TODO: close the output file properly

    logging.info(styled.HEADER('# 8 - convert to synched shapes'))

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    output_file_name = convertToShapes(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
        channels=['mt'],
        variables=shapes.variables_names,
        context='_control',
        use_number_coding=False,
    )

    # logging.info(styled.HEADER( t '\n # 9 - implement the nominal ploting if you want'))

    logging.info(styled.UNDERLINE(styled.HEADER('Output shapes:')))

    if isinstance(output_file_name, string_types):
        output_file_name = [output_file_name]
    for o in output_file_name:
        logging.info(styled.BOLD(styled.HEADER(o)))


def main():
    debug = False
    logging.info(styled.HEADER('Start'))
    # styled.HEADER('Start')

    logging.info(styled.HEADER('# 0 - prepareConfig'))
    config = analysis_shapes.prepareConfig(
        analysis_shapes=analysis_shapes,
        config_file='data/control_config.yaml',
        debug=debug
    )

    produce_shapes_variables(config=config)

    logging.info(styled.HEADER('End'))


if __name__ == '__main__':
    main()
