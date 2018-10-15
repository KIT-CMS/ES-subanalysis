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
    print "Start"

    config = prepareConfig()

    shapes = etau_fes.ETauFES(**config)
    shapes.setup_logging(output_file="{}_etau_fes.log".format(shapes.tag), level=logging.INFO, logger=shapes.logger)

    systematics = Systematics(
        "{}_shapes.root".format(shapes.tag),
        num_threads=shapes.num_threads,
        skip_systematic_variations=shapes.skip_systematic_variations
    )

    shapes.evaluateEra()

    # shapes.run()


if __name__ == '__main__':
    main()
