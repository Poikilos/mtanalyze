#!/usr/bin/env python
from __future__ import print_function

# mtanalyze: module for using minetest data
# Copyright (C) 2018 Jake Gustafson

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

import os
import sys
from datetime import datetime
import platform
import json
import from minetestsettings import MinetestSettings
'''
import from minetestassumptions import (
    default_after_broken,
)
'''

settings = MinetestSettings()


def error(*args):
    if len(args) > 1:
        raise NotImplementedError("multiple args in error function")
    elif len(args) > 0:
        sys.stderr.write("{}\n".format(args[0]))
    else:
        sys.stderr.write("\n")
    sys.stderr.flush()


myPath = os.path.realpath(__file__)
myPackage = os.path.split(myPath)[0]
myRepo = os.path.split(myPackage)[0]
repos = os.path.split(myRepo)[0]
me = '__init__.py'

if not os.path.isfile(os.path.join(myPackage, me)):
    raise RuntimeError('{} is not in package {}.'.format(me, myPackage))

try:
    input = raw_input
except NameError:
    pass

UPM = 10.0  # (unused, for reference) Engine units per Minetest meter

# TODO: crafts (scrape list of ingredients to remove from inventory)

loaded_mod_list = []

prepackaged_game_mod_list = []
prepackaged_gameid = None
new_mod_list = []

user_excluded_mod_count = 0

profile_path = None
appdata_path = None
if "windows" in platform.system().lower():
    if 'USERPROFILE' in os.environ:
        profile_path = os.environ['USERPROFILE']
        appdatas_path = os.path.join(profile_path, "AppData")
        appdata_path = os.path.join(appdatas_path, "Local")
    else:
        raise ValueError("ERROR: The USERPROFILE variable is missing"
                         " though platform.system() is {}."
                         "".format(platform.system()))
else:
    if 'HOME' in os.environ:
        profile_path = os.environ['HOME']
        appdata_path = os.path.join(profile_path, ".config")
    else:
        raise ValueError("ERROR: The HOME variable is missing"
                         " though the platform {} is not Windows."
                         "".format(platform.system()))


configs_path = os.path.join(appdata_path, "enlivenminetest")
# conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                          "minetestmeta.yml")
_OLD_yaml_path = os.path.join(myPackage, "minetestmeta.yml")
# ^ formerly _OLD_conf_path formerly conf_path (or _OLD_json_path?)
_OLD_json_path = os.path.join(appdata_path, "minetestmeta.json")
# ^ formerly config_path

def irr_to_mt(irr_pos):
    '''
    Convert from engine units to Minetest meters.
    '''
    c = None
    try:
        c = len(irr_pos)
    except TypeError:
        # if isinstance(irr_pos, int):
        #     return irr_pos / 10.0
        return irr_pos / 10.0
    if c == 3:
        return (irr_pos[0] / 10.0, irr_pos[1] / 10.0, irr_pos[2] / 10.0)
    elif c == 2:
        return (irr_pos[0] / 10.0, irr_pos[1] / 10.0)
    elif c == 1:
        return (irr_pos[0] / 10.0,)
    else:
        raise ValueError("Converting Irrlicht tuples of this size is"
                         " not implemented.")
    return None


def irr_to_mt_s(irr_pos):
    '''
    Convert from engine units to Minetest meters then to a string.
    '''
    return ','.join(irr_to_mt(irr_pos))


def mt_to_irr(mt_pos):
    '''
    Convert from Minetest meters to engine units.
    '''
    c = None
    try:
        c = len(mt_pos)
    except TypeError:
        # if isinstance(mt_pos, int):
        #     return float(mt_pos) * 10.0
        return mt_pos * 10.0
    if c == 3:
        return (mt_pos[0] * 10.0, mt_pos[1] * 10.0, mt_pos[2] * 10.0)
    elif c == 2:
        return (mt_pos[0] * 10.0, mt_pos[1] * 10.0)
    elif c == 1:
        return (mt_pos[0] * 10.0,)
    else:
        raise ValueError("Converting Minetest tuples of this size is"
                         " not implemented.")
    return None


def deprecate_minetestinfo():
    '''
    This is called instead of init_minetestinfo to ensure that the old
    config is ignored since it is entirely irrelevant.
    '''
    if os.path.isfile(_OLD_yaml_path):
        print("{} is deprecated and will be ignored."
              "".format(_OLD_yaml_path))
    if os.path.isfile(_OLD_json_path):
        print("{} is deprecated and will be ignored."
              "".format(_OLD_json_path))


# init_minetestinfo()
deprecate_minetestinfo()


if __name__ == '__main__':
    error()
    error("Import this into your py file via"
          " `import mtanalyze.minetestinfo` ")
