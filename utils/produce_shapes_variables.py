import logging
import pprint
pp = pprint.PrettyPrinter(indent=4)

from shapes.etau_fes import etau_fes
from shape_producer.systematics import Systematics


def prepareConfig(config_file='data/et_fes_config.yaml'):
    '''Read config and update to prompt'''
    config = etau_fes.ETauFES.readConfig(config_file)

    prompt_args = etau_fes.ETauFES.parse_arguments(include_defaults=False)

    config.update(prompt_args)

    return config


def main():
    print 'Start'

    print '# 1 - prepareConfig'
    config = prepareConfig()

    print '# 2 - setup_logging'
    shapes = etau_fes.ETauFES(**config)
    shapes.setup_logging(output_file="{}_etau_fes.log".format(shapes._tag), level=logging.INFO, logger=shapes._logger)

    print '# 3 - Era evaluation'
    shapes.evaluateEra()

    print '# 4 - import necessary estimation methods'
    shapes.importEstimationMethods()

    print '# 5 - evaluating channels (processes, variables,cattegories)'
    shapes.evaluateChannels()

    print '# 6 - add systematics'
    shapes.evaluateSystematics()

    print '# 7 - produce shapes'
    shapes.produce()


if __name__ == '__main__':
    main()
