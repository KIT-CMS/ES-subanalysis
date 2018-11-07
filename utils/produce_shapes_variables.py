import logging
import pprint
pp = pprint.PrettyPrinter(indent=4)

from shapes.etau_fes import etau_fes
from shape_producer.systematics import Systematics


def prepareConfig(config_file='data/et_fes_config.yaml', debug=False):
    '''Read config and update to prompt'''
    config = etau_fes.ETauFES.readConfig(config_file)

    prompt_args = etau_fes.ETauFES.parse_arguments(include_defaults=False)

    config.update(prompt_args)

    if debug:
        print 'config:'
        pp.pprint(config)

    return config


def main():
    print 'Start'

    print '\n# 1 - prepareConfig'
    config = prepareConfig(debug=False)

    print '\n# 2 - setup_logging'
    shapes = etau_fes.ETauFES(**config)
    shapes.setup_logging(output_file="{}_etau_fes.log".format(shapes._tag), level=logging.INFO, logger=shapes._logger)

    print '\n# 3 - Era evaluation'
    shapes.evaluateEra()
    # shapes._nominal_folder = 'eleTauEsOneProngPiZerosShift_0'
    print '\n# 4 - import necessary estimation methods'
    shapes.importEstimationMethods()

    print '\n# 5 - evaluating channels (processes, variables,cattegories)'
    shapes.evaluateChannels()

    print '\n# 6 - add systematics'
    shapes.evaluateSystematics(
        'nominal',
        'TES',
        'FES_shifts',
    )

    print '# 7 - produce shapes'
    shapes.produce()

    print 'End'


if __name__ == '__main__':
    main()
