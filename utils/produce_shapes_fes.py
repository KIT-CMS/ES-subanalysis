import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
# log.setLevel(log.INFO)
from rootpy.logger.magic import DANGER
DANGER.enabled = False

from shapes import styled
from shapes.etau_fes import ETauFES as analysis_shapes
from shape_producer.systematics import Systematics
from shapes.convert_to_synced_shapes import convertToSynced


def produce_shapes_variables(config):

    print '\n # 2 - setup_logging'
    shapes = analysis_shapes(**config)

    shapes.setup_logging(
        output_file="{}_etau_fes.log".format(shapes._tag),
        level='debug' if shapes._log_level is None else shapes._log_level,
        logger=shapes._logger
    )

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

    import subprocess
    process = subprocess.Popen(['send', 'FES shape production finished: %s' % (shapes._output_file)], stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    if shapes._output_file_dir.endswith('/shapes'):
        converted_shapes_dir = shapes._output_file_dir[:-6] + 'converted_shapes'
    else:
        converted_shapes_dir = os.path.join(shapes._output_file_dir, 'converted_shapes')

    # import pdb; pdb.set_trace()  # \!import code; code.interact(local=vars())
    converted_shapes_file = convertToSynced(
        input_path=shapes._output_file,
        output_dir=os.path.join(converted_shapes_dir),
        variables=shapes._variables_names,
        debug=shapes._debug,
    )
    print 'converted_shapes_file:', converted_shapes_file
    # print '\n # 9 - implement the nominal ploting if you want'

    print 'done'


def main():
    styled.HEADER('Start FES shapes production')
    debug = True

    styled.HEADER('\n # 1 - prepareConfig')
    config = analysis_shapes.prepareConfig(
        analysis_shapes=analysis_shapes,
        config_file='data/et_fes_legacy2017_config.yaml',
        debug=debug
    )

    produce_shapes_variables(config=config)

    styled.HEADER('End')


if __name__ == '__main__':
    main()
