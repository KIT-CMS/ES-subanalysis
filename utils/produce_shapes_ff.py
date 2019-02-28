import os

import pprint
pp = pprint.PrettyPrinter(indent=4)

import logging
from rootpy import log
# log.setLevel(log.INFO)
# from rootpy.logger.magic import DANGER
# DANGER.enabled = False

# TODO: configurable
from shapes import styled
from shapes.tes.tesshapes import TESShapes as analysis_shapes
from shape_producer.systematics import Systematics
from shapes.convert_to_shapes import convertToShapes


def produce_shapes_variables(config):

    styled.HEADER('\n # 1 - init FF shapes production')
    shapes = analysis_shapes(**config)

    styled.HEADER('\n # 2 - setup_logging')
    shapes.setup_logging(
        output_file="{}_ff_shapes.log".format(shapes._tag),
        level=config['log_level'],
        logger=shapes._logger,
    )

    styled.HEADER('\n # 3 - era evaluation')
    shapes.evaluateEra()

    styled.HEADER('\n # 4 - import necessary estimation methods')
    shapes.importEstimationMethods()

    styled.HEADER('\n # 5 - evaluating channels (processes, variables,cattegories)')
    shapes.evaluateChannels()

    styled.HEADER('\n # 5.5 - invert isolation cuts')
    for key in shapes.channels.keys():
        shapes.channels[key].replace_all_cuts(name='tau_iso', value='byTightIsolationMVArun2017v2DBoldDMwLT2017_2<0.5')

    styled.HEADER('\n # 6 - add systematics')
    shapes.evaluateSystematics()
    # return 0
    styled.HEADER('\n # 7 - produce shapes')
    shapes.produce()

    styled.HEADER('\n # 8 - convert to synched shapes')

    shapes_dir = os.path.join('/'.join(os.path.realpath(os.path.dirname(__file__)).split('/')[:-1]), 'converted_shapes')
    output_file_name = convertToShapes(
        input_path=shapes._output_file,
        output_dir=os.path.join(shapes_dir, shapes._output_file[:-5]),
        channels=['mt'],
        context='_tes',
    )

    # styled.HEADER(, t '\n # 9 - implement the nominal ploting if you want', bcolors.ENDC

    styled.HEADER('Output shapes:\n', output_file_name)


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
    debug = True
    styled.HEADER('Start shapes for FF productions')

    styled.HEADER('\n # 0 - prepareConfig')
    config = analysis_shapes.prepareConfig(
        analysis_shapes=analysis_shapes,
        config_file='data/tes_config.yaml',
        debug=debug
    )

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

    styled.HEADER('End')


if __name__ == '__main__':
    main()
