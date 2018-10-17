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

# class ChannelsDict(object):
#     """ChannelsDict"""

#     def __init__(self, value):
#         self.value = value

#     def __get__(self, instance, owner):
#         return self.value

#     def __set__(self, instance, value):
#         self.value = float(value)


class ChannelHolder(object):
    def __init__(self,
                 ofset=0,
                 logger=None,
                 debug=None,
                 channel_obj=None,
                 name=None,
                 cuts=None,
                 processes=None,
                 categorries=None,
                 friend_directory=None,
                 ):
        self._ofset = ofset
        self._logger = logger
        self._debug = debug

        self._channel_obj = channel_obj
        self._name = name
        self._cuts = cuts  # Channel()._cuts
        self._processes = processes
        self._categorries = categorries
        self._friend_directory = friend_directory

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

    def __str__(self):
        self._logger.debug("ChannelHolder ofset:", self._ofset)
        print "ofset", self._ofset
        output = (
            self._ofset * "\t" + " ChannelHolder(" + "\n" +
            self._ofset * "\t" + "    name = " + str(self._name) + "\n" +
            self._ofset * "\t" + "    debug = " + str(self._debug) + "\n" +
            self._ofset * "\t" + " )"
        )
        return output


if __name__ == '__main__':
    channel_holder = ChannelHolder()
