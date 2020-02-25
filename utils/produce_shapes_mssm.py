import os

import subprocess
import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
# log.setLevel(log.INFO)
from rootpy.logger.magic import DANGER
DANGER.enabled = True  # set True to raise exceptions

from shapes import styled
from shapes.mssm import MSSM as analysis_shapes_mssm
from shape_producer.systematics import Systematics
from shapes.convert_to_synced_shapes import convertToSynced


def produce_shapes_variables(config):

    print '\n # 2 - setup_logging'
    shapes = analysis_shapes_mssm(**config)

    # handler, file_handler = shapes.setup_logging(
    #     output_file=shapes._output_file.replace('.root', '.log'),
    #     level='debug' if shapes._log_level is None else shapes._log_level,
    #     logger=shapes._logger,  # logging.getLogger()
    #     danger=False,
    #     add_file_handler=True,
    #     add_stream_handler=False,
    # )

    if shapes._debug:
        shapes._log_level = 'debug'

    shapes.setup_logging(
        output_file=shapes._output_file.replace('.root', '.log'),
        level=shapes._log_level.lower(),
        logger=shapes._logger,
        danger=DANGER.enabled,  # shapes._danger,
    )
    # # Disabling some printouts
    # TODO - add this only to the case with higher verbosity
    if shapes._log_level == 'DEBUG':  # shapes._debug_shape_producer:  # shapes._log_level == 'debug'
        logging.getLogger('shape_producer').setLevel(log.DEBUG)
    else:
        logging.getLogger('shape_producer').setLevel(log.INFO)
    # # logging.getLogger('shape_producer.systematics').setLevel(log.INFO)
    # # logging.getLogger('shape_producer.histogram').setLevel(log.INFO)

    if shapes._log_level == 'Debug' or shapes._log_level == 'DEBUG':
        logging.getLogger('shape_producer.histogram').setLevel(log.DEBUG)
        # logging.getLogger('shape_producer.systematics').setLevel(log.DEBUG)
        # logging.getLogger('shape_producer.systematic_variations').setLevel(log.DEBUG)
    else:
        logging.getLogger('shape_producer.histogram').setLevel(log.INFO)

    # if handler is not None:
    #     handler.setLevel(log.INFO)
    #     # logging.getLogger('shape_producer.histogram').addHandler(handler)

    # if file_handler is not None:
    #     file_handler.setLevel(log.DEBUG)

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

    if not shapes._dry:
        process = subprocess.Popen(['send', '"MSSM shape production finished: %s"' % (shapes._output_file)],
            stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()

    if os.path.basename(os.path.normpath(shapes._output_file_dir)) == 'shapes':
        import copy
        converted_shapes_dir = os.path.join(os.path.dirname(os.path.normpath(shapes._output_file_dir)), 'converted_shapes')
    else:
        converted_shapes_dir = os.path.join(shapes._output_file_dir, 'converted_shapes')

    # import pdb; pdb.set_trace()  # \!import code; code.interact(local=vars())
    if not shapes._dry:
        converted_shapes_file = convertToSynced(
            input_path=shapes._output_file,
            output_dir=os.path.join(converted_shapes_dir),
            variables=shapes._variables_names,
            debug=shapes._debug,
        )
        print 'shapes:', shapes._output_file
        print 'converted_shapes_file:', converted_shapes_file
    else:
        print 'dry run - skip converting'

    # print '\n # 9 - implement the nominal ploting if you want'

    print 'done'


def main():
    styled.HEADER('Start MSSM shapes production')
    debug = False

    styled.HEADER('\n # 1 - prepareConfig')
    config = analysis_shapes_mssm.prepareConfig(
        analysis_shapes=analysis_shapes_mssm,
        config_file='data/mssm_legacy_mva_config.yaml',
        debug=debug
    )
    if 'yaml_conf' in config.keys() and config['yaml_conf'] is not None:
        config = analysis_shapes_mssm.prepareConfig(
            analysis_shapes=analysis_shapes_mt,
            config_file=config['yaml_conf'],
            debug=debug
        )

    produce_shapes_variables(config=config)

    styled.HEADER('End')


if __name__ == '__main__':
    main()
