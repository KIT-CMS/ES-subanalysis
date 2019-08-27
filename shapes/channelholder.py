# -*- coding: utf-8 -*-

import logging
"""
"""
import argparse
import yaml

"""Script to copy files after the skim from * to nfs."""
# import os
# import subprocess
import pprint
pp = pprint.PrettyPrinter(indent=4)
# import tempfile
# import hashlib

from shape_producer.channel import Channel
from shape_producer.process import Process
from shape_producer.cutstring import Cut

# class ChannelsDict(object):
#     """ChannelsDict"""

#     def __init__(self, value):
#         self.value = value

#     def __get__(self, instance, owner):
#         return self.value

#     def __set__(self, instance, value):
#         self.value = float(value)


class ChannelHolder(object):

    printable_attributes = [
        '_channel_obj', '_name', '_cuts', '_processes',
        '_variables', '_categorries', '_systematics',
        '_friend_directory',
    ]

    printable_cattegory_attributes = ['_channel', '_cuts', '_name', '_variable']

    def __init__(self,
                 ofset=0,
                 logger=None,
                 debug=None,
                 channel_obj=None,
                 name=None,
                 cuts=None,
                 processes=None,
                 variables=None,
                 categorries=None,
                 systematics=None,
                 friend_directory=None,
                 year=None,
                 nnominals=None,
                 ):
        self._ofset = ofset
        self._logger = logger
        self._debug = debug

        self._channel_obj = channel_obj  # channel instance from shape-producer
        self._name = name
        self._cuts = cuts  # only channel-defining cuts, not the categories
        self._processes = processes  # dict of process instances from shape-producer
        self._variables = variables
        self._categorries = categorries  # linked to all needed for channel-category cuts
        self._systematics = systematics
        self._friend_directory = friend_directory
        self._nnominals = nnominals

        try:
            self._year = ''.join(c for c in self._channel_obj.__class__.__name__ if c.isdigit())
        except:
            self._logger.warning('ChannelHolder initialized, but channel_obj might be not valid: %s' % str(channel_obj))
        if year != self._year:
            self._logger.warning('ChannelHolder extracted %s as a reference year but overriten by passed value %s' % (str(self._year), str(year)))
            self._year = year

        self._logger.debug('ChannelHolder initialized with year %s' % str(self._year))
        # assert type(self._cuts) is not None, "ChannelHolder::_cuts not set"
        # assert type(self._processes) is not None, "ChannelHolder::_processes not set"
        # assert type(self._categorries) is not None, "ChannelHolder::_categorries not set"

        if self._logger is None:
            self._logger = logging.getLogger(__name__)

    @property
    def cuts(self):
        return self._cuts

    @cuts.setter
    def cuts(self, value):
        from shape_producer.era import Era
        if isinstance(value, Era):
            self._cuts = value
        else:
            raise ValueError('Shapes::era: tried to set era not to type Era')

    @classmethod
    def pop_cut(cls, cuts, cut_name):
        try:
            cut = cuts.get(cut_name)
        except:
            print 'Couldn\'t extract cut:', cut_name
            print 'from list of cuts:', cuts
            raise

        cuts.remove(cut_name)

        return cut

    @classmethod
    def remove_cut(cls, cuts, cut_name):
        try:
            cuts.remove(cut_name)
        except:
            print 'Couldn\'t remove cut:', cut_name
            print 'from list of cuts:', cuts
            raise

        return 0

    def remove_category_cuts(self, cut_name):
        for category in self._categorries:
            if cut_name in category.cuts.names:
                self.remove_cut(category.cuts, cut_name)
                self._logger.debug("From category " + category.name + ' removed ' + cut_name)

    def remove_all_cuts(self, cut_name):
        if self._cuts is not None:
            self.remove_cut(self._cuts, cut_name)
        self.remove_category_cuts(cut_name)

    @classmethod
    def replace_cut(cls, cuts, cut_name, cut_value):
        if cut_name not in cuts.names:
            print 'Couldn\'t replace cut', cut_name, 'that is not in the list of cuts:', cuts
            return 1

        cls.remove_cut(cuts, cut_name)

        try:
            cuts.add(Cut(cut_value, cut_name))
        except:
            print 'Couldn\'t add the updated cut', cut_name, ' : ', cut_value, 'to the cuts of category'
            raise

        return 0

    def replace_category_cuts(self, cut_name, cut_value):
        for category in self._categorries:
            if cut_name in category.cuts.names:
                self.replace_cut(category.cuts, cut_name, cut_value)
                self._logger.debug(' '.join(["In category", category.name, 'set', cut_name, 'to', cut_value]))

    def replace_all_cuts(self, name, value):
        if self._cuts is not None:
            self.replace_cut(self._cuts, name, value)
        self.replace_category_cuts(name, value)

    def invert_cut(self):
        print 'Cut inversion is not implemented'
        return 1

    def __str__(self, sort_categories_cuts=False):
        self._logger.debug("ChannelHolder ofset:" + str(self._ofset))
        ind = self._ofset * '\t'
        print_str = ind + ' ChannelHolder(' + '\n'

        for attribute_name in self.printable_attributes:
            a = getattr(self, attribute_name)
            print_str += ind + '   ' + attribute_name + ' : ' + str(a) + '\n'

            if attribute_name == '_categorries':
                count = 0

                for category in a:
                    print_str += '\n' + ind + "   cat:" + str(count) + ':\n'

                    for category_attribute_name in self.printable_cattegory_attributes:
                        category_attribute = getattr(category, category_attribute_name)

                        cat_str = ''
                        if category_attribute_name == '_cuts':
                            cat_str = category_attribute.__str__(indent=self._ofset + 2).split('\n')
                            if sort_categories_cuts: cat_str.sort()
                            cat_str = '\n'.join(cat_str) + '\n'
                        elif category_attribute_name == '_variable':
                            cat_str = ' { name : ' + category_attribute.name + '; expression : ' + category_attribute.expression + '}\n'
                        else:
                            cat_str = str(category_attribute) + '\n'

                        print_str += ind + '     ' + category_attribute_name + ': ' + cat_str

                    count += 1

        return print_str


if __name__ == '__main__':
    channel_holder = ChannelHolder()
