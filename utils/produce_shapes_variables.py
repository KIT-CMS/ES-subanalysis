import pprint
pp = pprint.PrettyPrinter(indent=4)

from shapes.etau_fes import etau_fes


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
    print shapes

    shapes.run()


if __name__ == '__main__':
    main()
