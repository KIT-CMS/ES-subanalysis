import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
# log.setLevel(log.INFO)
# from rootpy.logger.magic import DANGER
# DANGER.enabled = False

# TODO: configurable
from shapes.tes.tesshapes import TESShapes as analysis_shapes
from shape_producer.systematics import Systematics
from shapes.convert_to_shapes import convertToShapes


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def prepareConfig(config_file='data/tes_config.yaml', debug=False):
    '''Read config and update to prompt'''
    config = analysis_shapes.readConfig(config_file)

    prompt_args = analysis_shapes.parse_arguments(include_defaults=False)

    config.update(prompt_args)

    if debug:
        print 'config:'
        pp.pprint(config)

    return config


def str_header(*argv):
    text = bcolors.HEADER
    for txt in argv:
        text += txt
    text += bcolors.ENDC
    return text


def produce_shapes_variables(config):

    print str_header('\n # 1 - init FF shapes production')
    shapes = analysis_shapes(**config)

    print str_header('\n # 2 - setup_logging')
    shapes.setup_logging(
        output_file="{}_ff_shapes.log".format(shapes._tag),
        level=config['log_level'],
        logger=shapes._logger,
    )

    print str_header('\n # 3 - era evaluation')
    shapes.evaluateEra()

    print str_header('\n # 4 - import necessary estimation methods')
    shapes.importEstimationMethods()

    print str_header('\n # 5 - evaluating channels (processes, variables,cattegories)')
    shapes.evaluateChannels()

    print str_header('\n # 5.5 - invert isolation cuts')
    for key in shapes.channels.keys():
        shapes.channels[key].replace_all_cuts(name='tau_iso', value='byTightIsolationMVArun2017v2DBoldDMwLT2017_2<0.5')

    print str_header('\n # 6 - add systematics')
    shapes.evaluateSystematics()
    # return 0
    print str_header('\n # 7 - produce shapes')
    shapes.produce()

    print str_header('\n # 8 - convert to synched shapes')

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    output_file_name = convertToShapes(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
        channels=['mt'],
        context='_tes',
    )

    # prinbcolors.HEADER, t '\n # 9 - implement the nominal ploting if you want', bcolors.ENDC

    print str_header('Output shapes:\n', output_file_name)


def dict_replace(old, new, d):
    # Replace all keys
    if old in d:
        try:
            d[new] = d.pop(old)
        except:
            print 'dict_replace couldnt replace a key'
            raise

    # Replace all values
    for k, v in d.items():
        if isinstance(v, dict):
            dict_replace(old, new, v)
        elif v == old:
            d[k] = new


def main():
    debug = False
    print str_header('Start shapes for FF productions')

    print str_header('\n # 0 - prepareConfig')
    config = prepareConfig(debug=debug)

    if debug:
        import copy
        config_old = copy.deepcopy(config)

    # Changing the analysis config to correspond to ff shapes setup
    config['shifts'] = ['nominal']
    old_context = config['context_analysis']  # TODO: context and tags are the same
    new_context = 'ff_shapes_' + config['context_analysis']
    dict_replace(old=old_context, new=new_context, d=config)

    if debug:
        from python_wrappers.dictdiffer import DictDiffer
        print DictDiffer(
            new_dict=config,
            old_dict=config_old,
            show_none=False,
            show_unchanged=False,
        )

    # Targeted analysis class should be passed
    produce_shapes_variables(config=config)

    print str_header('End')


if __name__ == '__main__':
    main()
