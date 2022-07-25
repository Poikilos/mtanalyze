#!/usr/bin/env python
'''
Analyze the Minetest installation and data. The only maintained parts of
this module cover installation and other processes done while Minetest
is not running such as processing colors.txt and old flat files of
players. For features regarding configuration and runtime
data, see <https://github.com/poikilos/voxboxor>.
'''
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
import pathlib

# from voxboxor.settings import Settings
'''
import from minetestassumptions import (
    default_after_broken,
)

try:
    input = raw_input
except NameError:
    pass

'''
PYTHON_MR = sys.version_info.major

# mtanalyze was formerly mtanalyze.minetestinfo
mti = {}  # mostly deprecated
default_license_string = "CC BY-SA 3.0"
try_shared_minetest_path = os.path.join(os.getcwd(), "games")
if os.path.isdir(try_shared_minetest_path):
    mti['shared_minetest_path'] = try_shared_minetest_path

verbosity = 0
key = None
for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
    if key is not None:
        mti[key] = arg
        key = None
    elif arg == "--verbose":
        verbosity = 2
    elif arg == "--debug":
        verbosity = 2
    elif arg.startswith("--"):
        key = arg[2:]


def get_required(key):
    if key is None:
        raise KeyError("key is None")
    elif len(key.strip()) == 0:
        raise KeyError("key is blank")
    value = mti.get(key)
    if value is not None:
        value = value.strip()
        if len(value) == 0:
            value = None
    if value is None:
        raise ValueError(
            'The "{}" setting is required for this operation.'
            ''.format(key)
        )
    return value

# region from minetestoffline formerly part of mtanalyze
FLAG_EMPTY_HEXCOLOR = "#010000"

# endregion from minetestoffline formerly part of mtanalyze

# see <https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python>
def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def echo1(*args, **kwargs):
    if verbosity < 1:
        return
    print(*args, file=sys.stderr, **kwargs)

def echo2(*args, **kwargs):
    if verbosity < 2:
        return
    print(*args, file=sys.stderr, **kwargs)

def set_verbosity(level):
    global verbosity
    verbosity = level

def get_verbosity(level):
    return verbosity

me = '__init__.py'

MY_PATH = os.path.realpath(__file__)
MY_MODULE_PATH = os.path.split(MY_PATH)[0]
MY_REPO_PATH = os.path.split(MY_MODULE_PATH)[0]
REPOS_PATH = os.path.split(MY_REPO_PATH)[0]
PCT_REPO_PATH = os.path.join(REPOS_PATH, "pycodetool")
if not os.path.isfile(os.path.join(MY_MODULE_PATH, me)):
    raise RuntimeError('{} is not in module {}.'
                       ''.format(me, MY_MODULE_PATH))


PIL_DEP_MSG = '''
You must first install Pillow's PIL.
On Windows:
Right-click windows menu, 'Command Prompt (Admin)' then:
pip install Pillow

On *nix-like systems:
python3 -m pip install --user --upgrade pip
python3 -m pip install --user --upgrade pip wheel
#then:
sudo pip install Pillow
python3 -m pip install --user Pillow
'''

PYCODETOOL_DEP_MSG = '''
This script requires parsing from poikilos/pycodetool.
Try (in a Terminal):

git clone https://github.com/poikilos/pycodetool.git {}
'''.format(PCT_REPO_PATH)


def is_yes(s):
    '''
    This is ONLY for terminal input.
    '''
    if s.lower() == "y":
        return True
    if s.lower() == "yes":
        return True
    return False

class EngineInfo:
    def __init__(self, path_user, path_share, prefix=None,
                 run_in_place=None, conf_path=None, gameid=None):
        '''
        Get various Minetest paths (sets self.meta['paths'] dict).
        To indicate RUN_IN_PLACE mode, set path_user and path_share
        to the same value. Otherwise, manually set run_in_place.

        Sequential arguments:
        path_user -- This is the path to the user-specific data.
            - If run_in_place, this should be the same as path_share.
            - If not run_in_place, path_user should usually be
              ~/.minetest

        path_share -- This contains data shared between users, such as
            the following directories: builtin, client, fonts, games,
            textures. It may also contain files such as:
            minetestmapper-colors.txt. The directory (or a "doc"
            directory under it) may contain files such as: copyright,
            README.txt, lua_api.txt, menu_lua_api.txt,
            minetest.conf.example, texture_packs.txt, world_format.txt.
            - If run_in_place, this should be the same as path_user such
              as ~/minetest.
            - If not run_in_place, path_share is the prefixed system
              path such as "/usr/share/games/minetest".

        prefix -- The preferred location of bin/minetest or
            bin/minetestserver. For example, set prefix to "/usr" or
            "/usr/local", otherwise the first minetest binaries
            occurring in the system's PATH will be used. The prefix is
            irrelevant if run_in_place.

        run_in_place -- Use the standard run-in-place locations of
            files, such as {path_share}/games and {path_share}/worlds.
            Also, the binary {path_share}/bin/minetest will be used and
            the prefix and system PATH will be ignored.

        gameid -- The engine will be set to use the gameid specified
                  but only if the gameid. The game must exist in one of
                  the standard locations. The gameid value is defined
                  by game.conf but the "_game" suffix is removed. The
                  environment variable MINETEST_SUBGAME_PATH can
                  override this behavior and use a nonstandard location.
        '''
        self.meta = {}

        self.gameid = None
        if run_in_place is None:
            run_in_place = (path_user == path_share)
        elif run_in_place is True:
            if path_user != path_share:
                echo0('WARNING: path_user "{}" and path_share "{}"'
                      ' differ but run_in_place is True, so path_share'
                      ' will be used.'.format(path_user, path_share))
        path_user = os.path.abspath(path_user)
        path_share = os.path.abspath(path_share)
        if run_in_place:
            if not os.path.isdir(path_share):
                raise ValueError("When run_in_place, the path_share"
                                 " must exist and be the location of"
                                 " all minetest subdirectories such as"
                                 " bin and builtin.")
        # if not run_in_place:
        #     raise NotImplementedError("non-run_in_place is not"
        #                               " implemented")
        paths = {}
        self.meta['paths'] = paths
        paths['RUN_IN_PLACE'] = run_in_place
        exeCount = 0
        tryExeDirsMsg = "in the system's paths"
        if conf_path is not None:
            paths['conf'] = conf_path
        if run_in_place:
            if conf_path is None:
                paths['conf'] = os.path.join(path_share,
                                                  'minetest.conf')
            paths['screenshots'] = os.getcwd()
            tryBinsPath = os.path.join(path_share, 'bin')

            paths['minetest'] = os.path.join(tryBinsPath,
                                                  'minetest')
            tryExeDirsMsg = 'in "{}"'.format(os.path.join(tryBinsPath))
            if not os.path.isfile(paths['minetest']):
                del paths['minetest']
            else:
                exeCount += 1

            tryMTS = os.path.join(tryBinsPath, 'minetestserver')
            paths['minetestserver'] = tryMTS
            if not os.path.isfile(paths['minetestserver']):
                del paths['minetestserver']
            else:
                exeCount += 1
        else:
            if conf_path is None:
                paths['conf'] = os.path.join(path_user,
                                                  'minetest.conf')
            gamesDirs = []
            sysGames = os.path.join(path_share, "games")
            myGames = os.path.join(path_user, "games")

            binNames = ['minetest', 'minetestserver']
            myPaths = sys.path
            if prefix is not None:
                tryExeDirsMsg = ('in the system PATH nor the specified '
                                 ' prefix "{}"\'s bin folder'
                                 ''.format(prefix))
                myPaths = [os.path.join(prefix, "bin")] + sys.path
            for binName in binNames:
                for tryBinsPath in myPaths:
                    tryBinPath = os.path.join(tryBinsPath, binName)
                    if os.path.isfile(tryBinPath):
                        paths[binName] = tryBinPath
                        exeCount += 1
                        break
            paths['screenshots'] = os.path.join(path_user,
                                                     "screenshots")
            tryExes = [
                '/usr/games/minetest',  # Ubuntu bionic package for MT5
            ]

        if gameid is not None:
            self.meta['gameid'] = gameid
            '''
            paths['game'] = game_path
            if not os.path.isdir(game_path):
                raise ValueError("")
            '''

        if not os.path.isfile(paths['conf']):
            echo0("WARNING: There is no \"{}\"."
                  "".format(paths['conf']))
        if exeCount < 1:
            echo0("WARNING: There was no minetest nor minetestserver"
                  " found {}.")



# HOME_PATH = expanduser("~")  # from os.path import expanduser
HOME_PATH = str(pathlib.Path.home())

APPDATA_PATH = None
if "windows" in platform.system().lower():
    if 'USERPROFILE' in os.environ:
        # HOME_PATH = os.environ['USERPROFILE']
        APPDATAS_PATH = os.path.join(HOME_PATH, "AppData")
        APPDATA_PATH = os.path.join(APPDATAS_PATH, "Local")
    else:
        raise ValueError("ERROR: The USERPROFILE variable is missing"
                         " though platform.system() is {}."
                         "".format(platform.system()))
else:
    if 'HOME' in os.environ:
        # HOME_PATH = os.environ['HOME']
        APPDATA_PATH = os.path.join(HOME_PATH, ".config")
    else:
        raise ValueError("ERROR: The HOME variable is missing"
                         " though the platform {} is not Windows."
                         "".format(platform.system()))


CONFIGS_PATH = os.path.join(APPDATA_PATH, "enlivenminetest")
# conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                          "minetestmeta.yml")
_OLD_yaml_path = os.path.join(MY_MODULE_PATH, "minetestmeta.yml")
# ^ formerly _OLD_conf_path formerly conf_path (or _OLD_json_path?)
_OLD_json_path = os.path.join(APPDATA_PATH, "minetestmeta.json")
# ^ formerly config_path


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




if __name__ == '__main__':
    # init_minetestinfo()
    deprecate_minetestinfo()
    echo0()
    echo0("This is a module not a script. In Python you can do:"
          " `import mtanalyze` ")
    # formerly " `import mtanalyze.minetestinfo` ")
