#!/usr/bin/env python
'''
(deprecated) module for generating map chunks and/or player locations
for mtanalyze/web. Both this module and mtanalyze/web are deprecated
in favor of ../webapp since it is planned to run as the same user
as the user who ran minetestserver.
'''
from __future__ import print_function
from __future__ import division

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
import subprocess
import traceback
import argparse
import time
import sys
import timeit
from timeit import default_timer as best_timer
# file modified time etc:
import time
# from datetime import datetime
# copyfile etc:
import shutil
import math

loaded_mod_list = []  # TODO: (?) this is only filled in deprecated.py

MY_PATH = os.path.realpath(__file__)
MY_MODULE_PATH = os.path.split(MY_PATH)[0]
MY_REPO_PATH = os.path.split(MY_MODULE_PATH)[0]
REPOS_PATH = os.path.split(MY_REPO_PATH)[0]
try:
    import mtanalyze
except ImportError as ex:
    if (("No module named mtanalyze" in str(ex))  # Python 2
            or ("No module named 'mtanalyze'" in str(ex))):  # Python 3
        sys.path.insert(0, MY_REPO_PATH)
    else:
        raise ex

from mtanalyze import (
    mti,
    get_required,
    FLAG_EMPTY_HEXCOLOR,
    PIL_DEP_MSG,
    PYCODETOOL_DEP_MSG,
    PCT_REPO_PATH,
    echo0,
    echo1,
    echo2,
    genresult_name_end_flag,
    gen_error_name_end_flag,
    WEB_PATH,
    DONE_ARGS,
    ARG_TYPES,
    STORE_TRUE_ARGS,
    MTANALYZE_CACHE_PATH,
)
echo0('[generator] MTANALYZE_CACHE_PATH="{}"'.format(MTANALYZE_CACHE_PATH))
from mtanalyze.mtchunk import(
    MTChunk,
    MTDecaChunk,
)

try:
    import pycodetool
except ImportError as ex:
    if (("No module named pycodetool" in str(ex))  # Python 2
            or ("No module named 'pycodetool'" in str(ex))):  # Python 3
        sys.path.insert(0, PCT_REPO_PATH)
try:
    import pycodetool
except ImportError as ex:
    if (("No module named pycodetool" in str(ex))  # Python 2
            or ("No module named 'pycodetool'" in str(ex))):  # Python 3
        sys.stderr.write(PYCODETOOL_DEP_MSG+"\n")
        sys.stderr.flush()
        sys.exit(1)
    else:
        raise ex

from pycodetool.parsing import (
    get_dict_deepcopy,
    save_conf_from_dict,
    get_list_from_hex,
    InstalledFile,
    get_dict_from_conf_file,
    is_dict_subset,
)

from mtanalyze.pythoninfo import (
    python_exe_path,
)


try:
    from PIL import Image, ImageDraw, ImageFont, ImageColor
except ImportError as ex:
    print(str(ex))
    print(PIL_DEP_MSG)
    sys.exit(1)
except ModuleNotFoundError as ex:
    print(str(ex))
    print(PIL_DEP_MSG)
    sys.exit(1)

from chunkymaprenderer import ChunkymapRenderer

# mode_to_bpp dict is from Antti Haapala. <http://stackoverflow.com/
#   questions/28913988/is-there-a-way-to-measure-the-memory-consumption-
#   of-a-png-image>. 7 Mar 2015. 28 Feb 2016.
mode_to_bpp = {'1': 1, 'L': 8, 'P': 8, 'RGB': 24, 'RGBA': 32, 'CMYK': 32,
               'YCbCr': 24, 'I': 32, 'F': 32}
INTERNAL_TIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"

# best_timer = timeit.default_timer
# if sys.platform == "win32":
#     on Windows, the best timer is time.clock()
#    best_timer = time.clock
# else:
#     on most other platforms, the best timer is time.time()
#    best_timer = time.time
# REQUIRES: see README.md

# The way to do a full render is deleting all files from the world
# folder under chunkymapdata under your system's www_minetest_path such
# as /var/www/html/minetest/chunkymapdata/world

# minetestmapper-numpy.py calculates the region as follows:
# (XMIN', 'XMAX', 'ZMIN', 'ZMAX'), default=(-2000, 2000, -2000, 2000)
# sector_xmin, sector_xmax, sector_zmin, sector_zmax = \
#     numpy.array(args.region)/16
# sector_ymin = args.minheight/16
# sector_ymax = args.maxheight/16
# region server-specific options

# as per <http://interactivepython.org/runestone/static/pythonds/
#   BasicDS/ImplementingaQueueinPython.html>
# class SimpleQueue:
#    def __init__(self):
#        self.items = []

#    def isEmpty(self):
#        return self.items == []

#    def enqueue(self, item):
#        self.items.insert(0, item)

#    def dequeue(self):
#        return self.items.pop()

#    def size(self):
#        return len(self.items)


class MTChunks(ChunkymapRenderer):
    first_mtime_string = None
    chunkymap_data_path = None
    chunkymapdata_worlds_path = None
    is_save_output_ok = None

    def __init__(self, world_path):  # formerly checkpaths() in global scope
        # self.python_exe_path = None
        # ^ instead, use global from EnlivenMinetest pythoninfo module
        self.players = None
        # ^ dict with playerid as subscript,
        #   each containing a player metadata dict.
        # self.force_rerender_decachunks_enable = None
        self.mydir = os.path.dirname(os.path.abspath(__file__))
        self.backend_string = None
        self.chunkymap_players_name = None
        self.chunkymap_players_path = None
        self.data_16px_path = None
        self.data_160px_path = None
        self.grPrefix = "chunk_"  # genresult name opener string
        self.plSec = None  # last_players_refresh_second
        self.mapSec = None  # last_map_refresh_second
        self.last_player_move_mtime_string = None

        # self.force_rerender_decachunks_enable = True
        self.FLAG_COLORS_LIST = list()
        self.FLAG_COLOR_CHANNELS = get_list_from_hex(
            FLAG_EMPTY_HEXCOLOR
        )
        self.FLAG_COLORS_LIST.append(self.FLAG_COLOR_CHANNELS)
        self.FLAG_COLORS_LIST.append((255, 255, 255))
        # ^ for compatibility w/ maps generated by earlier versions ONLY
        self.FLAG_COLORS_LIST.append((0, 0, 0))
        # ^ for compatibility w/ maps generated by earlier versions ONLY
        min_indent = "  "
        self.decachunks = {}
        self.rendered_this_session_count = 0
        self.is_backend_detected = False
        self.mapvars = {}
        self.mapvars["total_generated_count"] = 0
        self.rendered_count = 0
        self.preload_all_enable = True
        self.todo_index = -1
        self.todo_positions = []
        # ^ list of tuples (locations) to render next (simulate recurse)
        self.run_count = 0
        self.verbose_enable = True
        self.is_verbose_explicit = False
        self.loop_enable = True
        self.refresh_map_enable = True
        self.refresh_players_enable = True
        self.chunks = {}

        self.mapDelay = 30  # refresh_map seconds
        # ^ does one chunk at a time so as not to interrupt player
        #   updates too often
        self.players_delay = 5  # refresh_players seconds
        self.confPrefix = "chunk_"  # chunk yaml name opener_string
        self.confDotExt = ".yml"  # chunk yaml name dotext string
        # self.region_separators = [" ", " ", " "]
        self.mtm_bin_enable = False
        # ^ mtm_bin_enable will be set below automatically if present.

        input_string = ""
        w_path = world_path
        self.world_path = world_path
        if self.world_path is not None:
            if os.path.isdir(w_path):
                print("Using world path '{}'".format(w_path))
            else:
                raise ValueError("Missing world path '{}'".format(w_path))
        else:
            raise ValueError("world is not set.")

        # if not os.path.isdir(w_path):
        #     print("(ERROR: missing, so please close immediately and"
        #           " update primary_world_path in '"
        #           + mti._config_path + "' before next run)")
        # print("")

        worldmt_path = os.path.join(w_path, "world.mt")
        self.backend_string = "sqlite3"
        if (os.path.isfile(worldmt_path)):
            ins = open(worldmt_path, 'r')
            line = True
            while line:
                line = ins.readline()
                if line:
                    line_strip = line.strip()
                    if len(line_strip) > 0 and line_strip[0] != "#":
                        if line_strip[:7] == "backend":
                            ao_index = line_strip.find("=")
                            if ao_index > -1:
                                self.backend_string = \
                                    line_strip[ao_index+1:].strip()
                                self.is_backend_detected = True
                                break
            ins.close()
        else:
            print("ERROR: failed to read '" + worldmt_path + "'")
        self.is_save_output_ok = False
        # ^ Keeping output after analyzing it is no longer necessary
        #   since results are saved to YAML, but keeping output provides
        #   debug info since is the output of minetestmapper-numpy.py
        if self.is_backend_detected:
            print("Detected backend '" + self.backend_string
                  + "' from '" + worldmt_path + "'")
        else:
            print("WARNING: Database backend cannot be detected (unable"
                  " to ensure image generator script will render map)")

        self.prepare_env()  # from super
        print('www_minetest_path={}'
              ''.format(get_required("www_minetest_path",
                                     caller_name="MTChunks")))

        self.chunkymap_data_path = os.path.join(
            get_required("www_minetest_path",
                         caller_name="MTChunks"),
            "chunkymapdata"
        )
        self.chunkymapdata_worlds_path = os.path.join(
            self.chunkymap_data_path,
            "worlds"
        )
        print("Using chunkymap_data_path '" + self.chunkymap_data_path
              + "'")
        # if not os.path.isdir(self.chunkymap_data_path):
        #     os.mkdir(self.chunkymap_data_path)
        htaccess_path = os.path.join(self.chunkymap_data_path,
                                     ".htaccess")
        if not os.path.isdir(self.chunkymap_data_path):
            os.makedirs(self.chunkymap_data_path)
            print("Created '"+self.chunkymap_data_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymap_data_path)
            print("  (created .htaccess)")

        htaccess_path = os.path.join(self.chunkymapdata_worlds_path,
                                     ".htaccess")
        if not os.path.isdir(self.chunkymapdata_worlds_path):
            os.makedirs(self.chunkymapdata_worlds_path)
            print("Created '"+self.chunkymapdata_worlds_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymapdata_worlds_path)
            print("  (created .htaccess)")
        # TODO: consider using world_name from minetestoffline.py
        self.world_name = os.path.basename(w_path)
        self.chunkymap_thisworld_data_path = os.path.join(
            self.chunkymapdata_worlds_path,
            self.world_name
        )
        if not os.path.isdir(self.chunkymap_thisworld_data_path):
            os.makedirs(self.chunkymap_thisworld_data_path)
            print("Created '"+self.chunkymap_thisworld_data_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymap_thisworld_data_path)
            print("  (created .htaccess)")

        self.data_16px_path = os.path.join(
            self.chunkymap_thisworld_data_path,
            "16px"
        )
        if not os.path.isdir(self.data_16px_path):
            os.makedirs(self.data_16px_path)
            print("Created '"+self.data_16px_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.data_16px_path)
            print("  (created .htaccess)")

        self.data_160px_path = os.path.join(
            self.chunkymap_thisworld_data_path,
            "160px"
        )
        if not os.path.isdir(self.data_160px_path):
            os.makedirs(self.data_160px_path)
            print("Created '"+self.data_160px_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.data_160px_path)
            print("  (created .htaccess)")

        # TODO: deny recursively under these folders? doesn't seem that
        #   important for security so maybe not (no player info is
        #   there)

        self.install_default_world_data()

        self.chunkymap_players_name = "players"
        self.chunkymap_players_path = os.path.join(
            self.chunkymap_thisworld_data_path,
            self.chunkymap_players_name
        )
        htaccess_path = os.path.join(self.chunkymap_players_path,
                                     ".htaccess")
        if not os.path.isdir(self.chunkymap_players_path):
            os.makedirs(self.chunkymap_players_path)
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymap_players_path)

        self.yaml_name = "generated.yml"
        self.world_yaml_path = os.path.join(
            self.chunkymap_thisworld_data_path,
            self.yaml_name
        )

        self.mapvars["min_chunkx"] = 0
        self.mapvars["min_chunkz"] = 0
        self.mapvars["max_chunkx"] = 0
        self.mapvars["max_chunkz"] = 0
        self.mapvars["chunk_size"] = 16
        self.mapvars["maxheight"] = 96
        self.mapvars["minheight"] = -32
        self.mapvars["pixelspernode"] = 1
        self.saved_mapvars = get_dict_from_conf_file(
            self.world_yaml_path,
            ":"
        )
        is_mapvars_changed = False
        if self.saved_mapvars is None:
            is_mapvars_changed = True
            # self.save_mapvars_if_changed()
        # self.mapvars = get_dict_from_conf_file(self.world_yaml_path,
        #                                        ":")
        # NOTE: do not save or load self.mapvars yet, because if world
        #   name is different than saved, chunks must all be redone
        sm = self.saved_mapvars
        if self.saved_mapvars is not None:
            if "min_chunkx" in sm.keys():
                self.mapvars["min_chunkx"] = sm["min_chunkx"]
            if "max_chunkx" in sm.keys():
                self.mapvars["max_chunkx"] = sm["max_chunkx"]
            if "min_chunkz" in sm.keys():
                self.mapvars["min_chunkz"] = sm["min_chunkz"]
            if "max_chunkz" in sm.keys():
                self.mapvars["max_chunkz"] = sm["max_chunkz"]

        if self.mapvars is not None:
            self.enforce_ints(["min_chunkx", "max_chunkx", "min_chunkz",
                               "max_chunkz"])
        if is_mapvars_changed:
            self.save_mapvars_if_changed()
        if not self.refresh_map_enable:
            print("refresh_map_enable has been turned off by default"
                  " since is WIP")

    # def install_default_world_data(self):
    #     source_web_path = WEB_PATH  # os.path.join(
    #     #     self.mydir,
    #     #     "web"
    #     # )
    #     dest_web_chunkymapdata_world_path = \
    #         self.chunkymap_thisworld_data_path
    #     dest_web_chunkymapdata_world_players_path = os.path.join(
    #         self.chunkymap_thisworld_data_path,
    #         "players"
    #     )
    #     install_list.append(
    #         InstalledFile("singleplayer.png",
    #                       source_chunkymapdata_players,
    #                       dest_chunkymapdata_players)
    #     )

    def enforce_ints(self, names):
        for name in names:
            try:
                v = self.mapvars[name]
                try:
                    self.mapvars[name] = int(v)
                except ValueError:
                    print("WARNING: {} was not an int so is now 0"
                          "".format(name))
                    self.mapvars[name] = 0
            except KeyError:
                print("WARNING: {} was not set so is now 0"
                      "".format(name))
                self.mapvars[name] = 0

    def echo0(self, msg):
        # def echo0(self, *args, **kwargs):
        # print(*args, file=sys.stderr, **kwargs)
        print(msg, file=sys.stderr)
        return True

    def echo1(self, msg):
        # def echo1(self, *args, **kwargs):
        if not self.verbose_enable:
            return False
        # print(*args, file=sys.stderr, **kwargs)
        print(msg, file=sys.stderr)
        return True

    def install_default_world_data(self):
        # formerly install_website
        source_web_path = WEB_PATH
        source_web_chunkymapdata_path = os.path.join(
            source_web_path,
            "chunkymapdata_default"
        )
        source_web_chunkymapdata_world_path = os.path.join(
            source_web_chunkymapdata_path,
            "world"
        )
        source_web_chunkymapdata_images_path = os.path.join(
            source_web_chunkymapdata_path,
            "images"
        )
        dest_web_path = get_required(
            "www_minetest_path",
            caller_name="install_default_world_data",
        )
        # TODO: ^ Should this be configurable separately?

        dest_web_chunkymapdata_path = os.path.join(
            get_required("www_minetest_path",
                         caller_name="install_default_world_data"),
            "chunkymapdata"
        )
        dest_web_chunkymapdata_images_path = os.path.join(
            dest_web_chunkymapdata_path,
            "images"
        )
        install_list = list()
        install_list.append(
            InstalledFile("browser.php", source_web_path, dest_web_path)
        )
        install_list.append(
            InstalledFile("chunkymap.php",
                          source_web_path, dest_web_path)
        )
        install_list.append(
            InstalledFile("viewchunkymap.php",
                          source_web_path, dest_web_path)
        )
        install_list.append(
            InstalledFile("zoom_in.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("zoom_out.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("zoom_in_disabled.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("zoom_out_disabled.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("start.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("target_start.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("compass_rose.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("loading.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("arrow_wide_up.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("arrow_wide_down.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("arrow_wide_left.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("arrow_wide_right.png",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("chunk_blank.jpg",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        install_list.append(
            InstalledFile("decachunk_blank.jpg",
                          source_web_chunkymapdata_images_path,
                          dest_web_chunkymapdata_images_path)
        )
        source_chunkymapdata_players = os.path.join(
            source_web_chunkymapdata_world_path,
            "players"
        )
        dest_chunkymapdata_players = os.path.join(
            self.chunkymap_thisworld_data_path,
            "players"
        )
        install_list.append(
            InstalledFile("singleplayer.png",
                          source_chunkymapdata_players,
                          dest_chunkymapdata_players)
        )
        source_chunkymapdata_markers = os.path.join(
            source_web_chunkymapdata_world_path,
            "markers"
        )
        dest_chunkymapdata_markers = os.path.join(
            self.chunkymap_thisworld_data_path,
            "markers"
        )
        install_list.append(
            InstalledFile("0.yml",
                          source_chunkymapdata_markers,
                          dest_chunkymapdata_markers)
        )
        for this_object in install_list:
            source_path = os.path.join(this_object.source_dir_path,
                                       this_object.file_name)
            installed_path = os.path.join(this_object.dest_dir_path,
                                          this_object.file_name)
            if os.path.isfile(source_path):
                if not os.path.isdir(this_object.dest_dir_path):
                    os.makedirs(this_object.dest_dir_path)
                if not os.path.isfile(installed_path):
                    shutil.copyfile(source_path, installed_path)
                    # ^ DOES replace destination file
                else:
                    source_mtime_seconds = time.ctime(
                        os.path.getmtime(source_path)
                    )
                    installed_mtime_seconds = time.ctime(
                        os.path.getmtime(installed_path)
                    )
                    if source_mtime_seconds > installed_mtime_seconds:
                        shutil.copyfile(source_path, installed_path)
                        # ^ DOES replace destination file
            else:
                print("WARNING: cannot update file since can't find '"
                      + source_path + "'")
                exit(1)

    def deny_http_access(self, dir_path):
        htaccess_name = ".htaccess"
        htaccess_path = os.path.join(dir_path, htaccess_name)
        outs = open(htaccess_path, 'w')
        outs.write("IndexIgnore *"+"\n")
        outs.write("<Files .htaccess>"+"\n")
        outs.write("order allow, deny"+"\n")
        outs.write("deny from all"+"\n")
        outs.write("</Files>"+"\n")
        outs.write("<Files *.php>"+"\n")
        outs.write("order allow, deny"+"\n")
        outs.write("deny from all"+"\n")
        outs.write("</Files>"+"\n")
        outs.close()

    def cLUID(self, qX, qZ):
        """get locally unique identifier (unique to world only)
        using the quantized coordinates (quantized by chunk size)"""
        return "x" + str(qX) + "z" + str(qZ)

    def dcImageNameAt(self, qX, qZ):
        return "decachunk_" + self.dcLUIDAt(qX, qZ) + ".jpg"

    def dcImageName(self, decachunky_x, decachunky_z):

        return ("decachunk_" + self.dcLUID(decachunky_x, decachunky_z)
                + ".jpg")

    def dcLUIDAt(self, qX, qZ):
        """get decachunk LUID from chunk position
        (already quantized, so only decimate and get)
        """
        decachunky_x = self.decimate(qX)
        decachunky_z = self.decimate(qZ)
        return self.cLUID(decachunky_x, decachunky_z)

    def dcLUID(self, decachunky_x, decachunky_z):
        """get decachunk LUID (locally-unique id) from decachunk"""
        return self.cLUID(decachunky_x, decachunky_z)

    def dcConfNameAt(self, qX, qZ):
        return "decachunk_" + self.dcLUIDAt(qX, qZ) + ".yml"

    def dcConfName(self, decachunky_x, decachunky_z):
        """get decachunk yaml name from decachunk"""
        return ("decachunk_" + self.dcLUID(decachunky_x, decachunky_z)
                + ".yml")

    def get_chunk_image_name(self, qX, qZ):
        return "chunk_" + self.cLUID(qX, qZ) + ".png"

    # def get_decachunk_image_tmp_path_from_decachunk(self, qX, qZ):
    #     return os.path.join(
    #         self.mydir,
    #         self.dcImageName(qX, qZ)
    #     )

    def get_chunk_image_tmp_path(self, qX, qZ):
        return os.path.join(self.mydir,
                            self.get_chunk_image_name(qX, qZ))

    def get_signal_name(self):
        return "signals.txt"

    def get_signal_path(self):
        return os.path.join(self.mydir, self.get_signal_name())

    def decimate(self, qX):
        """get decachunky coord from chunky_coord
        15 becomes 1,
        10 becomes 1,
        5 becomes 0,
        -5 becomes -1,
        -10 becomes -1,
        15 becomes -2
        """
        return int(math.floor(float(qX)/10.0))

    def undecimate(self, decachunky_x):
        """get chunky coord from decachunky coord
        1 becomes 10,
        0 becomes 0,
        1 becomes -10
        """
        return int(decachunky_x*10)

    def is_worldborder_chunk(self, qX, qZ):
        result = False
        image_path = self.cImagePath(qX, qZ)
        border_pixel_count = 0
        if os.path.isfile(image_path):
            original_im = Image.open(image_path)
            im = original_im
            bit_count = 24
            bit_count = mode_to_bpp[im.mode]
            # TODO: ? find out what exception may happen here?
            # except:
            #     print("ERROR in is_worldborder_chunk: unknown image"
            #           " mode {} so can't get bitdepth of chunk"
            #           "".format(im.mode))
            if bit_count < 24:  # if im.bits<24:
                im = original_im.convert('RGB')
            width, height = im.size
            pixel_count = width*height
            pixel_count_f = float(pixel_count)
            border_count = 0
            for FLAG_COLOR in self.FLAG_COLORS_LIST:
                if len(FLAG_COLOR) == 3 or len(FLAG_COLOR) == 4:
                    for y in range(0, height):
                        for x in range(0, width):
                            r, g, b = im.getpixel((x, y))
                            if (r == FLAG_COLOR[0] and
                                    g == FLAG_COLOR[1] and
                                    b == FLAG_COLOR[2]):
                                border_pixel_count += 1
                    if float(border_pixel_count)/pixel_count_f >= .51:
                        result = True
                        break
                else:
                    print("ERROR: FLAG_COLOR (obtained from"
                          " FLAG_EMPTY_HEXCOLOR in minetestinfo.py)"
                          " has {} element(s)"
                          " (3 or 4 expected)".format(len(FLAG_COLOR)))
                    exit(2)
        return result

    def findToDoAt(self, chunky_pos, allow_current_chunk_enable=False):
        """Get the index of the chunk on the todo list, otherwise
        return -1."""
        result = -1
        if self.todo_index > -1:
            if self.todo_index < len(self.todo_positions):
                first_index = self.todo_index + 1
                if allow_current_chunk_enable:
                    first_index = self.todo_index
                if first_index < len(self.todo_positions):
                    for index in range(first_index,
                                       len(self.todo_positions)):
                        if ivec2_equals(self.todo_positions[index],
                                        chunky_pos):
                            result = index
                            break
        return result

    def checkDCAt(self, qX, qZ):
        """check decachunk containing the chunk identified by the given
        quantized position (quantized by chunk size)"""
        min_indent = ""
        chunky_coord_list = list()
        decachunky_x = self.decimate(qX)
        decachunky_z = self.decimate(qZ)
        chunky_min_x = decachunky_x*10
        chunky_max_x = chunky_min_x + 9
        # ^ NOTE: ADD even if negative, since originally floor was
        #   used
        chunky_min_z = decachunky_z*10
        chunky_max_z = chunky_min_z + 9
        # ^ NOTE: ADD even if negative, since originally floor was
        #   used
        x_chunky_count = chunky_max_x-chunky_min_x+1
        z_chunky_count = chunky_max_z-chunky_min_z+1
        is_any_part_queued = False
        preview_strings = z_chunky_count*[None]
        queued_chunk_coords = None
        chunky_offset_z = 0
        qZ = chunky_min_z
        queued_index = None
        is_chunk_complete = False
        while qZ <= chunky_max_z:
            preview_strings[chunky_offset_z] = ""
            qX = chunky_min_x
            while qX <= chunky_max_x:
                coords = (qX, qZ)
                chunky_coord_list.append(coords)
                queued_index = self.findToDoAt(
                    coords,
                    allow_current_chunk_enable=False
                )
                is_any_part_queued = queued_index > -1
                if is_any_part_queued:
                    if queued_chunk_coords is None:
                        queued_chunk_coords = list()
                    queued_chunk_coords.append(coords)
                    break
                qX += 1
            if is_any_part_queued:
                break
            qZ += 1
            chunky_offset_z += 1
        if not is_any_part_queued:
            is_chunk_complete = True
        unfinished_chunky_coord = None
        if is_chunk_complete:
            # NOTE: a chunk is incomplete if any rendered
            # nonworldborder chunk touches a nonrendered chunk
            for chunky_pos in chunky_coord_list:
                this_chunky_x, this_chunky_z = chunky_pos
                if self.isCDeployed(this_chunky_x, this_chunky_z):
                    continue
                outline_coords_list = self.get_outline_coords_list(
                    this_chunky_x,
                    this_chunky_z,
                    True
                )
                if outline_coords_list is None:
                    print(min_indent + "ERROR in"
                          " checkDCAt: no"
                          " outline of chunks could be found"
                          " around "+str(chunky_pos))
                    continue
                for nearby_chunky_pos in outline_coords_list:
                    nearby_chunky_x, nearby_chunky_z = nearby_chunky_pos
                    nearby_chunk_luid = self.cLUID(nearby_chunky_x,
                                                   nearby_chunky_z)
                    is_c = nearby_chunk_luid in self.chunks
                    n_c = self.chunks.get(nearby_chunk_luid)
                    if n_c is None:
                        # FIXME: Is this correct?
                        n_c = MTChunk()
                        self.chunks[nearby_chunk_luid] = n_c

                    is_fresh = n_c.is_fresh
                    is_deployed = self.isCDeployed(nearby_chunky_x,
                                                   nearby_chunky_z)
                    if (is_c and is_fresh) or is_deployed:
                        is_wb = n_c.metadata.get("is_worldborder")
                        is_wbc = False  # is world border chunk
                        if (is_c and is_wb):
                            is_wbc = True
                        elif self.is_worldborder_chunk(nearby_chunky_x,
                                                       nearby_chunky_z):
                            is_wbc = True
                            self.prepareC(nearby_chunky_x,
                                          nearby_chunky_z)
                            if not is_wb:
                                n_c.metadata["is_worldborder"] = True
                                self.save_chunk_meta(
                                    nearby_chunky_x,
                                    nearby_chunky_z,
                                    min_indent=min_indent+"  ",
                                )
                        if not is_wbc:
                            # empty chunk would not touch
                            # NON-worldborder chunk if decachunk was
                            # complete
                            is_chunk_complete = False
                            unfinished_chunky_coord = (nearby_chunky_x,
                                                       nearby_chunky_z)
                            break
                if not is_chunk_complete:
                    break

        # if not is_any_part_queued:
        # if queued_chunk_coords is None:
        if is_chunk_complete and not is_any_part_queued:
            # TODO: implement verbosity level here
            print("")
            print("")
            print("    Rendering 160px decachunk {}"
                  "".format((decachunky_x, decachunky_z)))
            if self.echo1(str(chunky_coord_list)):
                self.echo1("")
            else:
                self.echo0(
                    "      USING ({}) chunks (region {}:{}, {}:{})"
                    "".format(len(chunky_coord_list), chunky_min_x,
                              chunky_max_x, chunky_min_z,
                              chunky_max_z)
                )
            decachunk_global_coords = (decachunky_x * 160,
                                       decachunky_z * 160)
            im = Image.new("RGB", (160, 160), FLAG_EMPTY_HEXCOLOR)
            decachunk_yaml_path = self.dcConfPath(decachunky_x,
                                                  decachunky_z)
            decachunk_image_path = self.dcImagePath(decachunky_x,
                                                    decachunky_z)
            combined_count = 0
            contains_chunk_luids = list()

            for coord in chunky_coord_list:
                qX, qZ = coord
                chunky_offset_x = qX - chunky_min_x
                chunky_offset_z = qZ - chunky_min_z
                chunk_image_path = self.cImagePath(qX, qZ)
                if not os.path.isfile(chunk_image_path):
                    preview_strings[chunky_offset_z] += "0"
                    continue
                preview_strings[chunky_offset_z] += "1"
                participle = "initializing"
                # participle = "opening path"
                chunk_im = Image.open(open(chunk_image_path, 'rb'))
                # double-open to make sure file is finished writing
                # NOTE: PIL automatically closes, otherwise you can
                #   do something like https://bytes.com/topic/
                #   python/answers/24308-pil-do-i-need-close
                # fp = open(file_name, "rb")
                # im = Image.open(fp) # open from file object
                # im.load() # make sure PIL has read the data
                # fp.close()
                cGCoords = qX*16, qZ*16  # global coords of chunk
                lX = cGCoords[0] - decachunk_global_coords[0]
                lZ = cGCoords[1] - decachunk_global_coords[1]
                chunk_local_coords = lX, lZ
                offset = (chunk_local_coords[0],
                          160-chunk_local_coords[1])
                # convert to inverted cartesian since that's the
                # coordinate system of images
                im.paste(chunk_im, offset)
                contains_chunk_luids.append(self.cLUID(qX, qZ))
                # except:
                #     print(min_indent + "Could not finish "
                #           + participle
                #           + " in checkDCAt:")
                #     view_traceback()
            chunky_offset_z = z_chunky_count - 1
            print(min_indent + "Decachunk available chunk mask"
                  " (height:" + str(z_chunky_count) + "):")
            while chunky_offset_z >= 0:
                if preview_strings[chunky_offset_z] is None:
                    preview_strings[chunky_offset_z] = "<None>"
                print(min_indent + "  " + str(chunky_offset_z)
                      + ":" + preview_strings[chunky_offset_z])
                chunky_offset_z -= 1
            # except:
            #     print(min_indent + "Could not finish showing mask (this"
            #           " should never happen)")
            #     print(min_indent + "  z_chunky_count:"
            #           + str(z_chunky_count))
            #     print(min_indent + "  len(preview_strings):"
            #           + str(len(preview_strings)))
            #     print(min_indent + "  chunky_min_x:"
            #           + str(chunky_min_x))
            #     print(min_indent + "  chunky_max_x:"
            #           + str(chunky_max_x))
            #     print(min_indent + "  chunky_min_z:"
            #           + str(chunky_min_z))
            #     print(min_indent + "  chunky_max_z:"
            #           + str(chunky_max_z))
            #     view_traceback()
            print("")
            decachunk_folder_path = self.dcPath(decachunky_x,
                                                decachunky_z)
            if not os.path.isdir(decachunk_folder_path):
                os.makedirs(decachunk_folder_path)
                print(min_indent + "Made folder '"
                      + decachunk_folder_path + "'")
            else:
                print(min_indent + "Found folder '"
                      + decachunk_folder_path + "'")
            print(min_indent + "Saving '" + decachunk_image_path + "'")
            im.save(decachunk_image_path)
            decachunk_luid = self.dcLUID(decachunky_x, decachunky_z)
            self.prepareDC(decachunky_x, decachunky_z)
            this_second = int(time.time())
            this_dc = self.decachunks[decachunk_luid]
            meta = this_dc.metadata
            # if int(meta["last_saved_utc_second"]) != this_second:
            meta["last_saved_utc_second"] = this_second
            # time.time() returns float even if OS doesn't give a time
            #   in increments smaller than seconds
            if len(contains_chunk_luids) > 0:
                meta["contains_chunk_luids"] = \
                    ', '.join(contains_chunk_luids)
            else:
                meta["contains_chunk_luids"] = None
            this_dc.save_yaml(decachunk_yaml_path)
        else:
            # TODO: implement verbosity level here
            if is_any_part_queued:
                print(
                    min_indent + "Not rendering decachunk {dcPos} yet"
                    " since contains queued chunk (found_index:"
                    "[{fi}]; current_index:[{ci}]; len(todo_positions"
                    "):{tpc}; chunky_position:{cp})".format(
                        dcPos=(decachunky_x, decachunky_z),
                        fi=queued_index,
                        ci=self.todo_index,
                        tpc=len(self.todo_positions),
                        cp=queued_chunk_coords
                    )
                )
            else:
                print(
                    min_indent + "Not rendering decachunk {dcPos} yet"
                    " since unfinished chunks (world border not"
                    " between empty and closed area) such as empty"
                    " chunk {ucc}".format(
                        dcPos=(decachunky_x, decachunky_z),
                        ucc=unfinished_chunky_coord
                    )
                )
            print(min_indent + "  (index:[{}]; len:{}) .".format(
                queued_index, len(self.todo_positions)
            ))
        # except:
        #     print(min_indent + "Could not finish"
        #           " checkDCAt:")
        #     view_traceback()

    def cPath(self, qX, qZ):
        """Get chunk folder path at coordinates which are
        quantized by chunk size."""
        result = None
        decachunky_x = self.decimate(qX)
        decachunky_z = self.decimate(qZ)
        result = os.path.join(self.data_16px_path, str(decachunky_x),
                              str(decachunky_z))
        return result

    def dcPathAt(self, qX, qZ):
        """Get decachunk path for a chunk position"""
        result = None
        if qX is not None and qZ is not None:
            decachunk_x = self.decimate(qX)
            decachunk_z = self.decimate(qZ)
            # hectochunky_x = int(math.floor(qX/100))
            # hectochunky_z = int(math.floor(qZ/100))
            # result = os.path.join(os.path.join(self.data_160px_path,
            #                                    str(hectochunky_x)),
            #                                    str(hectochunky_x))
            result = self.dcPath(decachunk_x, decachunk_z)
        return result

    def dcPath(self, decachunky_x, decachunky_z):
        """get decachunk folder path from decimated position
        (decimated is always quantized by chunk size first)
        """
        result = None
        if decachunky_x is not None and decachunky_z is not None:
            hectochunky_x = int(math.floor(float(decachunky_x)/10.0))
            hectochunky_z = int(math.floor(float(decachunky_z)/10.0))
            result = os.path.join(
                os.path.join(self.data_160px_path, str(hectochunky_x)),
                str(hectochunky_z)
            )
        return result

    def mdForC(self, qX, qZ):
        """Create the chunk folder for the chunk identified by the given
        quantized position (quantized by chunk size)."""
        path = self.cPath(qX, qZ)
        if not os.path.isdir(path):
            os.makedirs(path)

    def dcImagePathAt(self, qX, qZ):
        """Get decachunk path for a chunk position"""
        return os.path.join(self.dcPathAt(qX, qZ),
                            self.dcImageNameAt(qX, qZ))

    def dcConfPathAt(self, qX, qZ):
        """get decachunk yaml path for the decachunk that contains
        the chunk identified by the given quantized coordinates
        (quantized by the chunk size)"""
        return os.path.join(self.dcPathAt(qX, qZ),
                            self.dcConfNameAt(qX, qZ))

    def dcImagePath(self, decachunky_x, decachunky_z):
        """Get decachunk image path from decachunk"""
        return os.path.join(self.dcPath(decachunky_x, decachunky_z),
                            self.dcImageName(decachunky_x,
                                             decachunky_z))

    def dcConfPath(self, decachunky_x, decachunky_z):
        """Get decachunk yaml path from decachunk"""
        return os.path.join(self.dcPath(decachunky_x, decachunky_z),
                            self.dcConfName(decachunky_x,
                                            decachunky_z))

    def cImagePath(self, qX, qZ):
        """
        get chunk image path at the given quantized coordinates
        (quantized by chunk size)
        """
        return os.path.join(self.cPath(qX, qZ),
                            self.get_chunk_image_name(qX, qZ))

    def grName(self, qX, qZ):
        """get chunk genresult name"""
        chunk_luid = self.cLUID(qX, qZ)
        return (self.grPrefix + chunk_luid
                + genresult_name_end_flag)

    def luidOfGRName(self, file_name):
        """get chunk luid from genresult file name"""
        ne_l = 1 * len(genresult_name_end_flag)
        # ^ genresult_name_end_flag is from minetestinfo.py
        return file_name[len(self.grPrefix):-ne_l]

    def grTempDirPath(self, qX, qZ):
        """get chunk genresult tmp folder"""
        # coords = self.coordsOfLUID(chunk_luid)
        # if coords is not None:
        #     qX, qZ = coords
        tmp_path = self.grBasePath()
        decachunky_x = self.decimate(qX)
        decachunky_z = self.decimate(qZ)
        tmp_path = os.path.join(tmp_path, str(decachunky_x),
                                str(decachunky_z))
        return tmp_path

    def grBasePath(self):
        """get chunk genresults base path"""
        # formerly get_chunk_genresults_tmp_folder(self, chunk_luid)
        # return os.path.join(
        #     os.path.join(self.mydir, "chunkymap-genresults"),
        #     self.world_name
        # )
        return os.path.join(
            MTANALYZE_CACHE_PATH,
            self.world_name,
        )


    def grTempPath(self, qX, qZ):
        """get chunk genresult tmp path"""
        return os.path.join(self.grTempDirPath(qX, qZ),
                            self.grName(qX, qZ))

    def cLUIDOfConfName(self, file_name):
        """get chunk luid from yaml file name"""
        de_l = 1 * len(self.confDotExt)
        return file_name[len(self.confPrefix):-de_l]

    def cConfName(self, qX, qZ):
        """get chunk yaml name"""
        luid = self.cLUID(qX, qZ)
        return self.confPrefix + luid + self.confDotExt

    def is_chunk_yaml_present(self, qX, qZ):
        return os.path.isfile(self.get_chunk_yaml_path(qX, qZ))

    def get_chunk_yaml_path(self, qX, qZ):
        return os.path.join(self.cPath(qX, qZ), self.cConfName(qX, qZ))

    def is_chunk_yaml_marked(self, qX, qZ):
        yaml_path = self.get_chunk_yaml_path(qX, qZ)
        result = False
        if os.path.isfile(yaml_path):
            result = True
            # ins = open(yaml_path, 'r')
            # line = True
            # while line:
            #     line = ins.readline()
            #     if line:
            #         line_strip = line.strip()
            #         if "is_empty:" in line_strip:
            #             result = True
            #             break
            # ins.close()
        return result

    def is_chunk_yaml_marked_empty(self, qX, qZ):
        result = False
        yaml_path = self.get_chunk_yaml_path(qX, qZ)
        if os.path.isfile(yaml_path):
            self.prepareC(qX, qZ)
            # ^ prepareC DOES get existing data if any file exists
            chunk_luid = self.cLUID(qX, qZ)
            if "is_empty" in self.chunks[chunk_luid].metadata.keys():
                result = self.chunks[chunk_luid].metadata["is_empty"]

        return result

    def remove_chunk_image(self, qX, qZ):
        result = False
        tmp_png_path = self.cImagePath(qX, qZ)
        if os.path.isfile(tmp_png_path):
            result = True
            os.remove(tmp_png_path)
        return result

    def remove_chunk(self, qX, qZ):
        result = False
        chunk_luid = self.cLUID(qX, qZ)
        out_path = self.grTempPath(qX, qZ)
        tmp_png_path = self.cImagePath(qX, qZ)
        yml_path = self.get_chunk_yaml_path(qX, qZ)
        if os.path.isfile(tmp_png_path):
            os.remove(tmp_png_path)
            result = True
        if os.path.isfile(yml_path):
            os.remove(yml_path)
            result = True
        if os.path.isfile(out_path):
            os.remove(out_path)
            result = True
        # TODO: if folder becomes empty, remove it
        return result

    def isCDeployed(self, qX, qZ):
        """is chunk rendered and at destination path
        (not merely rendered or saved to temporary path)"""
        # formerly is_chunk_empty_on_dest (reversed)
        is_rendered = False
        dest_png_path = self.cImagePath(qX, qZ)
        if os.path.isfile(dest_png_path):
            is_rendered = True
        return is_rendered

    def prepareDCAt(self, qX, qZ):
        """prepare decachunk meta at chunk (quantized) location"""
        chunk_luid = self.dcLUIDAt(qX, qZ)
        if chunk_luid not in self.decachunks.keys():
            self.decachunks[chunk_luid] = MTDecaChunk()
            # self.chunks[chunk_luid].luid = chunk_luid
            yaml_path = self.dcConfPathAt(qX, qZ)
            if os.path.isfile(yaml_path):
                self.decachunks[chunk_luid].load_yaml(yaml_path)

    def prepareDC(self, decachunky_x, decachunky_z):
        """prepare decachunk meta from decimated location
        (decimated locations are already quantized by chunk size before
        decimated)"""
        chunk_luid = self.dcLUID(decachunky_x, decachunky_z)
        if chunk_luid not in self.decachunks.keys():
            self.decachunks[chunk_luid] = MTDecaChunk()
            # self.chunks[chunk_luid].luid = chunk_luid
            yaml_path = self.dcConfPath(decachunky_x, decachunky_z)
            if os.path.isfile(yaml_path):
                self.decachunks[chunk_luid].load_yaml(yaml_path)

    def prepareC(self, qX, qZ):
        """
        Prepare chunk metadata at quantized coordinates
        (at coordinates quantized by chunk size).
        """
        chunk_luid = self.cLUID(qX, qZ)
        if chunk_luid not in self.chunks.keys():
            self.chunks[chunk_luid] = MTChunk()
            # self.chunks[chunk_luid].luid = chunk_luid
            yaml_path = self.get_chunk_yaml_path(qX, qZ)
            if os.path.isfile(yaml_path):
                self.chunks[chunk_luid].load_yaml(yaml_path)

    def _render_chunk(self, qX, qZ):
        """
        Normally, call checkC instead which renders chunk only if
        necessary.
        """
        mv = self.mapvars
        min_indent = "  "  # increased below
        result = False
        chunk_luid = self.cLUID(qX, qZ)
        this_chunk = self.chunks.get(chunk_luid)
        if this_chunk is None:
            # FIXME: Is this correct?
            this_chunk = MTChunk()
            self.chunks[chunk_luid] = this_chunk
        meta = this_chunk.metadata
        png_name = self.get_chunk_image_name(qX, qZ)
        tmp_png_path = self.get_chunk_image_tmp_path(qX, qZ)
        genresult_name = self.grName(qX, qZ)
        genresult_tmp_folder_path = self.grTempDirPath(qX, qZ)
        if not os.path.isdir(genresult_tmp_folder_path):
            os.makedirs(genresult_tmp_folder_path)
        genresult_path = self.grTempPath(qX, qZ)
        mvcs = self.mapvars["chunk_size"]
        min_x = qX * mvcs
        max_x = qX * mvcs + mvcs - 1
        min_z = qZ * mvcs
        max_z = qZ * mvcs + mvcs - 1

        # print(min_indent+"generating qX = " + str(min_x) + " to "
        #       + str(max_x) + " ,  qZ = " + str(min_z) + " to "
        #       + str(max_z))
        geometry_value_string = "{}:{}+{}+{}".format(
            min_x,
            min_z,
            int(max_x)-int(min_x)+1,
            int(max_z)-int(min_z)+1
        )
        # +1 since max-min is exclusive and width must be inclusive for
        # minetestmapper.py
        cmd_suffix = ""
        genresults_folder_path = os.path.join(self.mydir,
                                              "chunkymap-genresults",
                                              self.world_name)
        if not os.path.isdir(genresults_folder_path):
            os.makedirs(genresults_folder_path)
        gen_error_path = os.path.join(
            genresults_folder_path,
            "singleimage"+gen_error_name_end_flag
        )
        cmd_suffix = " 1> \""+genresult_path+"\""
        cmd_suffix += " 2> \""+gen_error_path+"\""
        # self.mapper_id = "minetestmapper-region"
        bin_string = (python_exe_path + " \""
                      + self.mtm_py_path + "\"")
        geometry_enable = False
        if not os.path.isfile(self.mtm_py_path):
            bin_string = "minetestmapper"
            geometry_enable = True
        w_path = self.world_path
        cmd_no_out_string = (bin_string + " --region " + str(min_x)
                             + " " + str(max_x) + " " + str(min_z)
                             + " " + str(max_z) + " --maxheight "
                             + str(self.mapvars["maxheight"])
                             + " --minheight "
                             + str(self.mapvars["minheight"])
                             + " --pixelspernode "
                             + str(self.mapvars["pixelspernode"])
                             + " \"" + w_path + "\" \"" + tmp_png_path
                             + "\"")
        cmd_string = cmd_no_out_string + cmd_suffix
        if self.mtm_py_path == self.mtm_custom_path:
            # if self.backend_string != "sqlite3":
            # if self.mapper_id == "minetestmapper-region":
            geometry_enable = True
        if geometry_enable:
            #  Since minetestmapper-numpy has trouble with leveldb:
            #    such as sudo minetest-mapper --input
            #      "/home/owner/.minetest/worlds/FCAGameAWorld"
            #      --geometry -32:-32+64+64 --output
            #      /var/www/html/minetest/try1.png
            #    where geometry option is like --geometry x:y+w+h
            #    mapper_id = "minetest-mapper"
            #    NOTE: minetest-mapper is part of the minetest-data
            #      package, which can be installed alongside the git
            #      version of minetestserver
            #    BUT *buntu Trusty version of it does NOT have geometry
            #      option
            #    cmd_string = ("/usr/games/minetest-mapper --input \""
            #                  + w_path + "\" --draworigin --geometry "
            #                  + geometry_value_string + " --output \""
            #                  + tmp_png_path + "\"" + cmd_suffix)
            #    such as sudo python minetestmapper --input "/home/owner
            #      /.minetest/worlds/FCAGameAWorld" --geometry
            #      -32:-32+64+64 --output
            #      /var/www/html/minetest/try1.png
            # OR try PYTHON version (looks for the Poikilos fork which
            #   has the geometry option like C++ version does):
            # script_path = ("$HOME/git/minetestmapper-python/"
            #                "minetestmapper.py")
            # region_capable_script_path = "$HOME/git/
            #  minetestmapper-python/minetestmapper.py"
            #    region_capable_script_path = os.path.join(
            #        self.mydir,
            #        "minetestmapper.py"
            #    )
            #    if os.path.isfile(region_capable_script_path):
            #        script_path=region_capable_script_path
            # if os.path.isfile(region_capable_script_path):
            #     script_path = region_capable_script_path
            # FIXME: Use geometry string from above (already done?)
            geometry_string = "{}:{}+{}+{}".format(
                min_x,
                min_z,
                int(max_x)-int(min_x)+1,
                int(max_z)-int(min_z)+1
            )
            # +1 since max-min is exclusive and width must be inclusive
            # for minetestmapper.py
            geometry_param = " --geometry " + geometry_string
            # region_string = (str(min_x) + ":" + str(max_x)
            #     + ", " + str(min_z) + ":" + str(max_z))
            # cmd_string = ("sudo python " + script_path + " --input \""
            #               + w_path + "\" --geometry "
            #               + geometry_value_string + " --output \""
            #               + tmp_png_path + "\"" + cmd_suffix)
            io_string = (" --input \"" + w_path + "\" --output \""
                         + tmp_png_path + "\"")
            # if "numpy" in self.mtm_py_path:
            #     io_string = (" \"" + w_path + "\" \"" + tmp_png_path
            #                  + "\"")
            #     geometry_param = (" --region " + str(min_x) + " "
            #                       + str(max_x) + " " + str(min_z)
            #                       + " " + str(max_z))
            cmd_no_out_string = (bin_string + " --bgcolor '"
                                 + FLAG_EMPTY_HEXCOLOR + "'"
                                 + geometry_param + io_string)
            cmd_string = cmd_no_out_string + cmd_suffix
            # sudo python /home/owner/minetest/util/minetestmapper.py
            #   --bgcolor '#010000' --input "/home/owner/
            #   .minetest/worlds/FCAGameAWorld" --output /var/www/html/
            #   minetest/chunkymapdata/entire.png > entire-mtmresult.txt
            # sudo python /home/owner/minetest/util/chunkymap/
            #    minetestmapper.py --input "/home/owner/.minetest/worlds
            #    /FCAGameAWorld" --geometry 0:0+16+16 --output
            #    /var/www/html/minetest/chunkymapdata/chunk_x0z0.png >
            #      /home/owner/minetest/util/chunkymap-genresults/
            #      chunk_x0z0_mapper_result.txt
            # sudo mv entire-mtmresult.txt /home/owner/minetest/util/
            #   chunkymap-genresults/

        dest_png_path = self.cImagePath(qX, qZ)
        # is_empty_chunk = (is_chunk_yaml_marked(qX, qZ) and
        #                   is_chunk_yaml_marked_empty(qX, qZ))
        # if self.echo1(min_indent+"Running '"+cmd_string+"'...")
        # else:
        self.echo0(min_indent+"Calling map tile renderer for: {}"
              "".format((qX, qZ)))
        min_indent += "  "
        if os.path.isfile(tmp_png_path):
            os.remove(tmp_png_path)
        subprocess.call(cmd_string, shell=True)
        # ^ TODO: remember not to allow arbitrary command execution,
        # which could happen if input contains ';' when
        # using shell=True

        # is_empty_before = True
        # is_marked_before = False
        self.prepareC(qX, qZ)  # DOES load existing yml if exists
        old_meta = get_dict_deepcopy(meta)
        is_marked_before = meta["is_marked"]
        is_empty_before = meta["is_empty"]
        # if chunk_luid in self.chunks.keys():
        #     is_marked_before = True
        #     is_empty = None
        #     if meta is not None:
        #         is_empty = meta.get("is_empty")
        #     if (is_empty is not None):
        #         is_empty_before = is_empty
        if os.path.isfile(tmp_png_path):
            result = True
            meta["is_empty"] = False
            if (os.path.isfile(dest_png_path)):
                os.remove(dest_png_path)
            self.mdForC(qX, qZ)
            shutil.move(tmp_png_path, dest_png_path)
            print(min_indent+"(moved to '"+dest_png_path+"')")
            self.rendered_this_session_count += 1
            self.prepareC(qX, qZ)
            # ^ DOES load existing yml if exists
            this_chunk.is_fresh = True
            meta["is_empty"] = False
            print(min_indent + "{rendered_this_session_count:"
                  + str(self.rendered_this_session_count) + "}")
        else:
            if self.isLUIDTraversed(chunk_luid):
                print(min_indent + "WARNING: no chunk data though"
                      " traversed by player:")
                print(min_indent + "standard output stream:")
                line_count = print_file(genresult_path,
                                        min_indent+"  ")
                if line_count > 0:
                    print(min_indent + "  #EOF: " + str(line_count)
                          + " line(s) in '" + genresult_path + "'")
                    pass
                else:
                    print(min_indent + "  #EOF: " + str(line_count)
                          + " line(s) in '" + genresult_path + "'")
                    subprocess.call(
                        (cmd_no_out_string + " 2> \""
                         + genresult_path + "\""),
                        shell=True
                    )
                    print(min_indent+"standard error stream:")
                    line_count = print_file(genresult_path,
                                            min_indent+"  ")
                    if line_count < 1:
                        print(min_indent + "  #EOF: "
                              + str(line_count) + " line(s) in '"
                              + genresult_path + "'")
                    print(min_indent + "  (done output of '"
                          + cmd_no_out_string + "')")
                    if os.path.exists(tmp_png_path):
                        shutil.move(tmp_png_path, dest_png_path)
        participle = "checking result"
        is_locked = False
        err_count = 0
        if os.path.isfile(gen_error_path):
            ins = open(gen_error_path, 'r')
            line = True
            while line:
                line = ins.readline()
                if line:
                    if len(line.strip()) > 0:
                        err_count += 1
                    line_lower = line.lower()
                    if ((" lock " in line_lower) or
                            ("/lock " in line_lower)):
                        is_locked = True
                        lock_line = line
                        result = None
                        break
            ins.close()
        if err_count < 1:
            os.remove(gen_error_path)
        if not is_locked:
            is_changed = this_chunk.set_from_genresult(
                genresult_path
            )
            if is_marked_before:
                participle = "checking for marks"
                if ((not is_empty_before) and meta["is_empty"]):
                    print("ERROR: chunk changed from nonempty"
                          " to empty (may happen if output of"
                          " mapper was not recognized)")
                elif (meta["is_empty"] and
                        os.path.isfile(dest_png_path)):
                    print("ERROR: chunk marked empty though has"
                          " data (may happen if output of"
                          " mapper was not recognized)")
            is_wbc = self.is_worldborder_chunk(qX, qZ)
            if (("is_worldborder" not in meta) or
                    is_wbc != meta["is_worldborder"]):
                meta["is_worldborder"] = is_wbc
                is_changed = True

            # chunk_yaml_path = self.get_chunk_yaml_path(qX, qZ)
            # self.mdForC(qX, qZ)
            # this_chunk.save_yaml(chunk_yaml_path)
            # if is_changed:
            participle = "accessing dict"
            # set_verbosity(1)
            if not is_dict_subset(meta, old_meta):
                participle = "saving chunk meta"
                self.save_chunk_meta(qX, qZ, min_indent=min_indent+"  ")
            # print(min_indent + "(saved yaml to '"
            #       + chunk_yaml_path + "')")
            if not self.is_save_output_ok:
                if os.path.isfile(genresult_path):
                    participle = "removing "+genresult_path
                    os.remove(genresult_path)
        else:
            print(min_indent + "database locked: " + lock_line)
        return result

    def save_chunk_meta(self, qX, qZ, min_indent=None):
        if min_indent is None:
            min_indent = ""
        chunk_yaml_path = self.get_chunk_yaml_path(qX, qZ)
        chunk_luid = self.cLUID(qX, qZ)
        if chunk_luid not in self.chunks:
            self.prepareC(qX, qZ)
        self.mdForC(qX, qZ)
        self.chunks[chunk_luid].save_yaml(chunk_yaml_path)
        print(min_indent + "(saved yaml to '" + chunk_yaml_path + "')")

    def is_used_player_index(self, index):
        result = False
        if self.players is not None:
            for this_key in self.players.keys():
                this_player = self.players[this_key]
                if "index" in this_player:
                    if int(this_player["index"]) == int(index):
                        result = True
                        break
                    # else:
                    #     self.echo1("existing " + this_player["index"]
                    #                + " is not needle " + str(index))
                # else:
                #     print("WARNING: player " + this_key + ":"
                #           + str(this_player) + " is missing index")
        return result

    def get_new_player_index(self):
        result = None
        max_player_index = None
        index = 0
        while (self.is_used_player_index(index)):
            index += 1
        result = index
        # TODO: ignore exceptions like old code?
        # except:
        #     print(min_indent+"Could not finish get_new_player_index:")
        #     view_traceback()

        return result

    def get_new_player_index_faster(self):
        result = None
        max_player_index = None
        if self.players is not None:
            for this_key in self.players.keys():
                this_player = self.players[this_key]
                if "index" in this_player:
                    if ((max_player_index is None) or
                            (int(this_player["index"]) >
                             max_player_index)):
                        max_player_index = int(this_player["index"])
                else:
                    print("WARNING: player with playerid '" + this_key
                          + "' has no public index (programmer or admin"
                          " error)")
        if max_player_index is not None:
            result = max_player_index + 1
        else:
            result = 0

        return result

    def save_player(self, playerid):
        if self.players is None:
            print("ERROR: Tried save_player but the players dict is not"
                  " ready (self.players is None)")
            return
        if playerid is None:
            print("ERROR: save_player(None) was attempted.")
        if playerid not in self.players:
            print("ERROR: tried to save nonexistant playerid '"
                  + str(playerid) + "'")
            return
        if not os.path.isdir(self.chunkymap_players_path):
            os.makedirs(self.chunkymap_players_path)
            self.deny_http_access(self.chunkymap_players_path)
        this_player = self.players[playerid]
        if "index" in this_player:
            player_path = os.path.join(self.chunkymap_players_path,
                                       this_player["index"])
            save_conf_from_dict(player_path, this_player, ":")
        else:
            print("ERROR: cannot save player since missing 'index'"
                  " ('index' is used for filename on map)")

    def check_players(self):
        if self.first_mtime_string is None:
            first_mtime = time.gmtime()
            # NOTE: time.gmtime converts long timestamp to 9-long tuple
            self.first_mtime_string = time.strftime(
                INTERNAL_TIME_FORMAT_STRING,
                first_mtime
            )
        print("PROCESSING PLAYERS")
        mvcs = self.mapvars["chunk_size"]
        player_markers_count = 0
        if self.players is None:
            self.players = {}
            if os.path.isdir(self.chunkymap_players_path):
                folder_path = self.chunkymap_players_path
                for sub_name in os.listdir(folder_path):
                    sub_path = os.path.join(folder_path, sub_name)
                    if not os.path.isfile(sub_path):
                        continue
                    if sub_name.startswith("."):
                        continue
                    if not sub_name.endswith(".yml"):
                        continue
                    player_markers_count += 1
                    player_dict = get_dict_from_conf_file(sub_path, ":")
                    if player_dict is None:
                        print("ERROR: could not read any yaml values"
                              " from '"+sub_path+"'")
                        continue
                    player_dict["index"] = int(sub_name[:-4])
                    # ^ repair the index
                    if "playerid" not in player_dict:
                        print("WARNING: dangling player marker"
                              " (no playerid) in '" + sub_path
                              + "' so cannot be updated")
                        continue
                    if ((player_dict["playerid"] is not None) and
                            (player_dict["playerid"] != "")):
                        player_dict["playerid"] = \
                            str(player_dict["playerid"])
                        # in case was detected as int, change back to
                        # string since is a name and so name string will
                        # be found as dict key when checked later
                        self.players[player_dict["playerid"]] = \
                            player_dict
                        self.echo1('Loading map entry index "{}"'
                                   ' for playerid "{}"'
                                   ''.format(player_dict["index"],
                                             player_dict["playerid"]))
                    else:
                        self.echo0("ERROR: no 'playerid' in chunkymap"
                              " player entry '"+sub_path+"'")
            else:
                os.makedirs(self.chunkymap_players_path)
                self.deny_http_access(self.chunkymap_players_path)
        self.echo1('player_markers_count: {}'
                   ''.format(player_markers_count))
            # this could be huge:
            # print("players:" + str(self.players.keys()))
        players_path = os.path.join(self.world_path, "players")
        player_count = 0
        player_written_count = 0
        players_moved_count = 0
        players_didntmove_count = 0
        players_saved_count = 0
        for base_path, dirnames, filenames in os.walk(players_path):
            for file_name in filenames:
                file_path = os.path.join(players_path, file_name)
                # print("  EXAMINING "+file_name)
                # badstart_string = "."
                player_name = None
                player_position = None
                # if (file_name[:len(badstart_string)] != \
                #     badstart_string):
                if file_name.startswith("."):
                    continue
                ins = open(file_path, 'r')
                line = True
                is_enough_data = False
                while line:
                    line = ins.readline()
                    if line:
                        ao_index = line.find("=")
                        if ao_index > 0:
                            found_name = line[:ao_index].strip()
                            found_value = line[ao_index+1:].strip()
                            if found_name == "name":
                                player_name = found_value
                            elif found_name == "position":
                                player_position = found_value
                            if ((player_name is not None) and
                                    (player_position is not None)):
                                is_enough_data = True
                                break
                ins.close()
                player_index = None
                # this_player = None
                is_changed = False
                # (mode, ino, dev, nlink, uid, gid, size, atime, mtime,
                #  ctime) = os.stat(file_path)
                moved_mtime = time.gmtime()
                # mtime = time.gmtime(os.path.getmtime(file_path))
                # NOTE: time.gmtime converts long timestamp to 9-long
                #   tuple
                this_mtime_s = time.strftime(
                    INTERNAL_TIME_FORMAT_STRING,
                    moved_mtime
                )
                # mtime = os.path.getmtime(file_path)
                # this_mtime_s = datetime.strftime(
                #     mtime,
                #     INTERNAL_TIME_FORMAT_STRING
                # )
                if file_name in self.players:
                    # this_player = self.players[file_name]
                    if ("utc_mtime" not in self.players[file_name]):
                        # or (self.players[file_name]["utc_mtime"] != \
                        #     this_mtime_s):
                        self.echo1('no modified time for player "{}"'
                                   ' so marking for resave.'
                                   ''.format(file_name))
                        self.players[file_name]["utc_mtime"] = \
                            this_mtime_s
                        is_changed = True
                        # not necessarily moved--even if resaved by
                        # server, may not have moved a whole block or at
                        # all
                    if "index" in self.players[file_name]:
                        player_index = self.players[file_name]["index"]
                    else:
                        print(min_indent + "WARNING: missing index in"
                              " yml file for playerid '" + file_name
                              + "' so making a new one.")
                        player_index = self.get_new_player_index()
                        self.players[file_name]["index"] = player_index
                        is_changed = True
                else:
                    # self.echo1(
                    #     '{} is not in {}'
                    #     ''.format(file_name, self.players.keys())
                    # )  # this could be huge
                    self.players[file_name] = {}
                    player_index = self.get_new_player_index()
                    print(min_indent + "Creating map entry "
                          + str(player_index) + " for playerid '"
                          + file_name + "'")
                    self.players[file_name]["index"] = player_index
                    self.players[file_name]["playerid"] = file_name
                    self.players[file_name]["utc_mtime"] = this_mtime_s
                    if player_name is not None:
                        self.players[file_name]["name"] = player_name
                    is_changed = True
                player_dest_path = None
                if player_index is not None:
                    player_dest_path = os.path.join(
                        self.chunkymap_players_path,
                        str(player_index)+".yml"
                    )
                else:
                    print(min_indent + "ERROR: player_index is still"
                          " None for '" + file_name
                          + "' (this should never"
                          " happen), so skipped writing map entry")
                player_x = None
                player_y = None
                player_z = None
                chunk_x = None
                chunk_y = None
                chunk_z = None
                plPos = s_to_tuple(player_position, file_name)
                # ^ s_to_tuple is from minetestoffline.py
                if plPos is not None:
                    # Divide by 10 because I don't know why (minetest
                    # issue, maybe to avoid float rounding errors upon
                    # save/load)
                    plPos = irr_to_mt(plPos)
                    player_x, player_y, player_z = plPos
                    player_x = float(player_x)
                    player_y = float(player_y)
                    player_z = float(player_z)
                    qX = player_x // mvcs
                    chunky_y = player_y // mvcs
                    qZ = player_z // mvcs
                    chunk_luid = self.cLUID(qX, qZ)
                    self.prepareC(qX, qZ)
                    # ^ DOES load existing yml if exists
                    if not meta["is_traversed"]:
                        meta = self.chunks[chunk_luid].metadata
                        meta["is_traversed"] = True
                        self.save_chunk_meta(
                            qX,
                            qZ,
                            min_indent=min_indent+"  ",
                        )

                # if is_enough_data:
                # if player_name != "singleplayer":
                # self.players[file_name] = \
                #     get_dict_from_conf_file(player_dest_path, ":")
                # map_player_position_tuple = None
                saved_player_x = None
                saved_player_y = None
                saved_player_z = None
                # map_player_position_tuple = (saved_player_x,
                #                              saved_player_y,
                #                              saved_player_z)
                is_moved = False
                if "x" in self.players[file_name].keys():
                    saved_player_x = float(self.players[file_name]["x"])
                    if int(saved_player_x) != int(player_x):
                        is_moved = True
                        self.echo1('{}x changed for playerid "{}"'
                                   ' so marking for save.'
                                   ''.format(min_indent, file_name))
                else:
                    self.players[file_name]["x"] = player_x
                    is_moved = True
                    self.echo1('{}No x for playerid "{}"'
                               ' so marking for save:'
                               ''.format(min_indent, file_name))
                    self.echo1(min_indent+str(self.players[file_name]))
                if "y" in self.players[file_name].keys():
                    saved_player_y = float(self.players[file_name]["y"])
                    if int(saved_player_y) != int(player_y):
                        is_moved = True
                        self.echo1('{}y changed for playerid "{}"'
                                   ' so marking for save.'
                                   ''.format(min_indent, file_name))
                else:
                    self.players[file_name]["y"] = player_y
                    is_moved = True
                    self.echo1('{}No y for playerid "{}"'
                               ' so marking for save.'
                               ''.format(min_indent, file_name))
                if "z" in self.players[file_name].keys():
                    saved_player_z = float(self.players[file_name]["z"])
                    if int(saved_player_z) != int(player_z):
                        is_moved = True
                        self.echo1('{}z changed for playerid "{}"'
                                   ' so marking for save.'
                                   ''.format(min_indent, file_name))
                else:
                    self.players[file_name]["z"] = player_z
                    is_moved = True
                    self.echo1('{}No z for playerid "{}"'
                               ' so marking for save.'
                               ''.format(min_indent, file_name))
                if is_moved:
                    self.echo1('{}Moved so marking as changed'
                               ''.format(min_indent))
                    is_changed = True

                # if ((self.players[file_name] is None) or
                #         not is_same_fvec3(map_player_position_tuple,
                #                           plPos)):
                # if ((self.players[file_name] is None) or
                #     (saved_player_x is None) or
                #     (saved_player_z is None) or
                #     (int(saved_player_x) != int(player_x)) or
                #     (int(saved_player_y) != int(player_y)) or
                #     (int(saved_player_z) != int(player_z))):
                if is_changed:
                    self.echo1('{}{} changed.'
                               ''.format(min_indent, player_name))
                    # don't check y since y is elevation in minetest,
                    # don't use float since subblock position doesn't
                    # matter to map
                    # if ((self.players[file_name] is not None) and
                    #         (saved_player_x is not None) and
                    #         (saved_player_y is not None) and
                    #         (saved_player_z is not None)):
                    if is_moved:
                        # print("PLAYER MOVED: " + str(player_name)
                        #       + " moved from "
                        #       + str(map_player_position_tuple)
                        #       + " to " + str(plPos))
                        self.echo1(
                            '{}PLAYER MOVED: {} moved from '
                            '{}, {}, {} to '
                            '{}, {}, {}'
                            ''.format(min_indent, player_name,
                                      saved_player_x, saved_player_y,
                                      saved_player_z,
                                      player_x, player_y, player_z)
                        )
                        self.last_player_move_mtime_string = \
                            this_mtime_s
                        players_moved_count += 1
                        self.players[file_name]["utc_mtime"] = \
                            this_mtime_s
                    else:
                        self.echo1('{}SAVING map entry for'
                                   ' player "{}"'
                                   ''.format(min_indent, player_name))
                        players_saved_count += 1

                    # set BEFORE saving to prevent unecessary resaving
                    # on successive runs:
                    self.players[file_name]["x"] = player_x
                    self.players[file_name]["y"] = player_y
                    self.players[file_name]["z"] = player_z

                    if player_dest_path is not None:
                        self.echo1('{}saving "{}"'
                                   ''.format(min_indent,
                                             player_dest_path))
                        save_conf_from_dict(player_dest_path,
                                            self.players[file_name],
                                            ":",
                                            save_nulls_enable=False)
                    else:
                        self.echo0('{}Could not save playerid "{}"'
                                   ' since generating map'
                                   ' entry path failed'
                                   ''.format(min_indent, file_name))
                    # outs = open(player_dest_path, 'w')
                    # outs.write("playerid:"+file_name)
                    # if player_name is not None:
                    #     outs.write("name:"+player_name+"\n")
                    # # python automatically uses correct newline for
                    # # your os when you put "\n"
                    # #if player_position is not None:
                    # #    outs.write("position:"+player_position+"\n")
                    # if player_x is not None:
                    #     outs.write("x:"+str(player_x)+"\n")
                    # if player_y is not None:
                    #     outs.write("y:"+str(player_y)+"\n")
                    # if player_z is not None:
                    #     outs.write("z:"+str(player_z)+"\n")
                    # outs.write("is_enough_data:"+str(is_enough_data))
                    # outs.close()
                    player_written_count += 1
                else:
                    self.echo1("DIDN'T MOVE: "+str(player_name))
                    players_didntmove_count += 1
                player_count += 1
        # if not self.verbose_enable:
        print("PLAYERS:")
        print("  saved: " + str(player_written_count) + " (moved:"
              + str(players_moved_count) + "; new:"
              + str(players_saved_count) + ")")
        last_move_msg = ""
        if (players_moved_count < 1):
            if (self.last_player_move_mtime_string is not None):
                last_move_msg = (" (last any moved: "
                                 + self.last_player_move_mtime_string
                                 + ")")
            else:
                last_move_msg = (" (none moved since started checking "
                                 + self.first_mtime_string+")")
        print("  didn't move: " + str(players_didntmove_count)
              + last_move_msg)

    def isLUIDTraversed(self, chunk_luid):
        """is chunk traversed by player"""
        result = False
        if chunk_luid in self.chunks.keys():
            result = self.chunks[chunk_luid].metadata["is_traversed"]
        return result

    def isLUIDFresh(self, chunk_luid):
        """is the chunk fresh?"""
        result = False
        if chunk_luid in self.chunks.keys():
            result = self.chunks[chunk_luid].is_fresh
        return result

    def checkC(self, qX, qZ):
        """
        Check the chunk identified by the given quauntized location
        (quauntized by chunk size).

        Returns:
        (boolean) whether the chunk image is present on dest (rendered
        now or earlier); else None if database is locked (then re-adds
        it to self.todo_positions)--only possible if there is chunk data
        at the given location
        """
        min_indent = "  "
        result = [False, ""]
        chunk_luid = self.cLUID(qX, qZ)

        # if (is_different_world):
        #     # instead, see above where all chunk
        #     # files and player files are deleted
        #     self.remove_chunk(qX, qZ)

        is_traversed_by_player = self.isLUIDTraversed(chunk_luid)
        # ^ ok if stale, since is only used for whether empty chunk
        # should be regenerated

        is_render_needed = False

        if not self.isLUIDFresh(chunk_luid):
            if is_traversed_by_player:
                if self.is_chunk_yaml_marked(qX, qZ):
                    if self.is_chunk_yaml_marked_empty(qX, qZ):
                        is_render_needed = True
                        result[1] = ("RENDERING since nonfresh empty"
                                     " traversed")
                        self.echo1('{}{}: {}'
                                   ''.format(min_indent, chunk_luid,
                                             result[1]))
                        # else:
                        #     sys.stdout.write('.')
                    else:
                        if self.isCDeployed(qX, qZ):
                            result[1] = ("SKIPPING since RENDERED"
                                         " nonfresh nonempty traversed")
                            self.echo1(
                                '{}{}: '
                                ''.format(min_indent, chunk_luid,
                                          result[1])
                            )
                        else:
                            is_render_needed = True
                            result[1] = ("RENDERING since NONRENDERED"
                                         " nonfresh nonempty traversed")
                            if self.echo1('{}{}: {}'
                                          ''.format(min_indent,
                                                    chunk_luid,
                                                    result[1])):
                                try_path = self.cImagePath(qX, qZ)
                                self.echo1('{}  (dest_png_path="{}")'
                                           ''.format(min_indent,
                                                     try_path))
                # end if marked
                else:
                    is_render_needed = True
                    result[1] = ("RENDERING since nonfresh unmarked"
                                 " traversed")
                    self.echo1('{}{}: {}'
                               ''.format(min_indent,chunk_luid,
                                         result[1]))
                    # if not self.verbose_enable:
                    #     sys.stdout.write('.')
            # end if traversed
            else:
                if (self.is_chunk_yaml_marked(qX, qZ)):
                    if (self.is_chunk_yaml_marked_empty(qX, qZ)):
                        result[1] = ("SKIPPING since nonfresh empty"
                                     " nontraversed")
                        self.echo1(min_indent+chunk_luid+": "+result[1])
                    else:
                        if (self.isCDeployed(qX, qZ)):
                            result[1] = ("SKIPPING since RENDERED"
                                         " nonfresh nonempty"
                                         " nontraversed (delete png to"
                                         " re-render)")
                            self.echo1('{}{}: {}'
                                       ''.format(min_indent, chunk_luid,
                                                 result[1]))
                        else:
                            is_render_needed = True
                            try_path = self.cImagePath(qX, qZ)
                            result[1] = ("RENDERING since NONRENDRERED"
                                         " nonfresh nonempty"
                                         " nontraversed")
                            self.echo1('{}{}: {}'
                                       ''.format(min_indent, chunk_luid,
                                                 result[1]))
                            self.echo1('{}  (dest_png_path={})'
                                       ''.format(min_indent, try_path))
                else:
                    is_render_needed = True
                    result[1] = ("RENDERING since nonfresh unmarked"
                                 " nontraversed")
                    self.echo1('{}{}: {}'
                               ''.format(min_indent, chunk_luid,
                                         result[1]))
                    # if not self.verbose_enable:
                    #     sys.stdout.write('.')
        else:
            result[1] = "SKIPPING since RENDERED fresh"
            self.echo1('{}{}: {}'
                       ' (rendered after starting "{}")'
                       ''.format(min_indent, chunk_luid, result[1],
                                 __file__))
            # if (not self.is_chunk_yaml_marked(qX, qZ)):
            #     is_render_needed = True

        # This should never happen since keeping the output of
        #   minetestmapper-numpy.py (after analyzing that output) is
        #   deprecated:
        # if (self.is_genresult_marked(chunk_luid) and
        #         not self.is_chunk_yaml_present(qX, qZ)):
        #     tmp_chunk = MTChunk()
        #     tmp_chunk.luid = chunk_luid
        #     genresult_path = self.grTempPath(qX, qZ)
        #     tmp_chunk.set_from_genresult(genresult_path)
        #     chunk_yaml_path = self.get_chunk_yaml_path(qX, qZ)
        #     self.mdForC(qX, qZ)
        #     tmp_chunk.save_yaml(chunk_yaml_path)
        #     print(min_indent+"(saved yaml to '"+chunk_yaml_path+"')")

        if is_render_needed:
            self.rendered_count += 1
            if not self.verbose_enable:
                print('{}{}: {}'
                      ''.format(min_indent,chunk_luid, result[1]))
            sub_result = self._render_chunk(qX, qZ)
            if sub_result is True:
                result[0] = True
            elif sub_result is None:
                result[0] = None
                self.todo_positions.append((qX, qZ))  # redo this one
                print("Waiting to retry...")
                time.sleep(.5)

        else:
            if self.isCDeployed(qX, qZ):
                result[0] = True
                tmp_png_path = self.cImagePath(qX, qZ)
                # NOTE: do NOT set result[1] since specific reason was
                # already set above
                self.echo1('{}{}: Skipping existing'
                           ' map tile file "{}"'
                           ' (delete it to re-render)'
                           ''.format(min_indent, chunk_luid,
                                     tmp_png_path))
            # elif is_empty_chunk:
            #     print("Skipping empty chunk " + chunk_luid)
            # else:
            #     print(min_indent+chunk_luid+": Not rendered on dest.")
        return result

    def _mapPRInto(self, qX, qZ):
        """check map pseudorecursion branchfrom"""
        chunk_luid = self.cLUID(qX, qZ)
        branched_pos = qX-1, qZ
        # Only add if not in list already, to prevent infinite
        # re-branching.
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)
        branched_pos = qX+1, qZ
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)
        branched_pos = qX, qZ-1
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)
        branched_pos = qX, qZ+1
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)

    def check_map_pseudorecursion_iterate(self):
        # , redo_empty_enable=False):
        min_indent = ""
        minQZ = self.mapvars["min_chunkz"]
        maxQZ = self.mapvars["max_chunkz"]
        minQX = self.mapvars["min_chunkx"]
        maxQX = self.mapvars["max_chunkx"]
        if self.todo_index < 0:
            self.check_map_pseudorecursion_start()
            self.echo1('{}(initialized {} branch(es))'
                       ''.format(min_indent, len(self.todo_positions)))
        if self.todo_index >= 0:
            if self.todo_index < len(self.todo_positions):
                this_pos = self.todo_positions[self.todo_index]
                qX, qZ = this_pos
                chunk_luid = self.cLUID(qX, qZ)
                prev_rendered_this_session_count = \
                    self.rendered_this_session_count
                is_present, reason_s = self.checkC(qX, qZ)

                if (is_present is None) or is_present:
                    if is_present:
                        self.mapvars["total_generated_count"] += 1
                        if qX < minQX:
                            self.mapvars["min_chunkx"] = qX
                        if qX > maxQX:
                            self.mapvars["max_chunkx"] = qX
                        if qZ < minQZ:
                            self.mapvars["min_chunkz"] = qZ
                        if qZ > maxQZ:
                            self.mapvars["max_chunkz"] = qZ
                        # end while square outline
                        # (1-chunk-thick outline)
                        # generated any png files
                        self.save_mapvars_if_changed()
                        prev_len = len(self.todo_positions)
                        self._mapPRInto(qX, qZ)
                        # must checkDCAt AFTER
                        #   _mapPRInto so
                        #   checkDCAt can see if
                        #   there are more to do before rendering
                        #   superchunk
                        # always check since already checks queue and
                        #   doesn't render decachunk on last rendered
                        #   chunk, but instead on last queued chunk in
                        #   decachunk
                        # if (self.rendered_this_session_count > \
                        #         prev_rendered_this_session_count or
                        #     self.force_rerender_decachunks_enable):

                        # Now is ok to checkDCAt,
                        # since does not count current index as
                        # unfinished (allow_current_chunk_enable=False):
                        self.checkDCAt(qX, qZ)
                        if self.verbose_enable:
                            XZ = (qX, qZ)
                            ti = self.todo_index
                            td = len(self.todo_positions) - prev_len
                            fmt = "[{}] branching from {} (added {})"
                            self.echo0(min_indent
                                       + fmt.format(ti, XZ, td))
                    # else None (db is locked; let retry happen later)
                else:
                    # Now is ok to checkDCAt,
                    # since does not count current index as unfinished
                    # (allow_current_chunk_enable=False):
                    self.checkDCAt(qX, qZ)
                    self.echo1('{}[{}] not branching from {}'
                               ''.format(min_indent, self.todo_index,
                                         (qX, qZ)))
                self.todo_index += 1
                self.checkDCAt(qX, qZ)
            if self.todo_index >= len(self.todo_positions):
                # ^ check again since may have branched,
                #   making this become untrue after the check further up
                self.save_mapvars_if_changed()
                self.todo_index = -1
                self.todo_positions = list()
                # ^ there seems to be issues where not empty due to
                #   delayed garbage collection?
                # while len(self.todo_positions) > 0:
                #     self.todo_positions.pop()
        else:
            self.echo1(min_indent+"(no branches)")

    def coordsOfLUID(self, chunk_luid):
        """get coords from luid"""
        result = None
        if chunk_luid is not None:
            xopener_index = chunk_luid.find("x")
            zopener_index = chunk_luid.find("z")
            if xopener_index >= 0 and zopener_index > xopener_index:
                x_string = chunk_luid[xopener_index+1:zopener_index]
                z_string = chunk_luid[zopener_index+1:]
                # TODO: ignore all exceptions below like old code?
                qX = int(x_string)
                qZ = int(z_string)
        return result

    def apply_auto_tags_by_worldgen_mods(self, qX, qZ):
        min_indent = ""
        chunk_luid = self.cLUID(qX, qZ)
        if chunk_luid not in self.chunks.keys():
            self.prepareC(qX, qZ)
        auto_tags_string = ""
        existing_tags_string = ""
        tags_list = None
        meta = self.chunks[chunk_luid].metadata
        if (("tags" in meta) and (meta["tags"] is not None)):
            existing_tags_string = meta["tags"]
            tags_list = existing_tags_string.split(", ")
            for index in range(0, len(tags_list)):
                tags_list[index] = tags_list[index].strip()
        else:
            tags_list = list()

        for mod_name in worldgen_mod_list:
            if mod_name in loaded_mod_list:
                if mod_name not in tags_list:
                    tags_list.append(mod_name)
                    is_changed = True

        if is_changed:
            meta["tags"] = ', '.join(tags_list)
            self.save_chunk_meta(qX, qZ, min_indent=min_indent+"  ")

    def correct_genresults_paths(self):
        count = 0
        folder_path = self.grBasePath()
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
            echo0('[generator] created "{}"'.format(folder_path))
        # for base_path, dirnames, filenames in os.walk(folder_path):
        for file_name in os.listdir(folder_path):
            # for file_name in filenames:
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                continue
            # print("  EXAMINING "+file_name)
            # badstart_string = "."
            player_name = None
            player_position = None
            if file_name.startswith("."):
                continue
            ne_l = len(genresult_name_end_flag)
            # ^ genresult_name_end_flag is from minetestinfo.py
            if len(file_name) < (len(self.grPrefix) + 4 + ne_l):
                print("WARNING: found unusable genresults file '{}' in "
                      "".format(file_name))
                continue
            chunk_luid = self.luidOfGRName(file_name)
            coords = self.coordsOfLUID(chunk_luid)
            if coords is not None:
                qX, qZ = coords
                corrected_folder_path = self.grTempDirPath(qX, qZ)
                if not os.path.isdir(corrected_folder_path):
                    print("    creating \"" + corrected_folder_path
                          + "\"")
                    os.makedirs(corrected_folder_path)
                # corrected_file_path = os.path.join(
                #     corrected_folder_path,
                #     file_name
                # )
                corrected_file_path = self.grTempPath(qX, qZ)
                if os.path.isfile(corrected_file_path):
                    os.remove(corrected_file_path)
                    shutil.move(file_path, corrected_file_path)
                count += 1

        if count > 0:
            # TODO: implement verbosity level here
            print("")
            print("MOVED {} genresult file(s)".format(count))
            print("")
            print("")

    def get_cross_coords_list(x_int, y_int,
                              enable_restrict_to_decachunk=False):
        results = None
        if x_int is not None and y_int is not None:
            tmp = list()
            # North, East, South, West (cartesian):
            tmp.append((x_int, y_int+1))
            tmp.append((x_int+1, y_int))
            tmp.append((x_int, y_int-1))
            tmp.append((x_int-1, y_int))
            if enable_restrict_to_decachunk:
                results = list()
                starting_decachunk_luid = self.dcLUIDAt(x_int, y_int)
                for result in tmp:
                    this_x, this_y = result
                    luid = self.dcLUIDAt(this_x, this_y)
                    if luid == starting_decachunk_luid:
                        results.append(result)
            else:
                results = tmp
        return results

    def get_outline_coords_list(self, x_int, y_int,
                                enable_restrict_to_decachunk=False):
        results = None
        if x_int is not None and y_int is not None:
            tmp = list()
            # North, NE, East, SE, South, SW, West, NW (cartesian):
            tmp.append((x_int, y_int+1))  # N
            tmp.append((x_int+1, y_int+1))  # NE
            tmp.append((x_int+1, y_int))  # E
            tmp.append((x_int+1, y_int-1))  # SE
            tmp.append((x_int, y_int-1))  # S
            tmp.append((x_int-1, y_int-1))  # SW
            tmp.append((x_int-1, y_int))  # W
            tmp.append((x_int-1, y_int+1))  # NW
            if enable_restrict_to_decachunk:
                results = list()
                starting_decachunk_luid = self.dcLUIDAt(x_int, y_int)
                for result in tmp:
                    this_x, this_y = result
                    luid = self.dcLUIDAt(this_x, this_y)
                    if luid == starting_decachunk_luid:
                        results.append(result)
            else:
                results = tmp
        return results

    def isMinWBRenderCount(self, chunky_coords_list, min_count):
        """is worldborder count gt or eq min_count"""
        result = False
        count = 0
        for chunky_pos in chunky_coords_list:
            if is_worldborder_chunk(chunky_pos[0], chunky_pos[1]):
                count += 1
                if count >= min_count:
                    result = True
                    break
        return result

    def isMinNWBRenderCount(self, chunky_coords_list, min_count):
        """is nonworldborder isrendered count gt or eq min_count"""
        result = False
        count = 0
        is_crod = self.isCDeployed
        is_wbc = self.is_worldborder_chunk
        if chunky_coords_list is not None:
            for chunky_pos in chunky_coords_list:
                qX, qZ = chunky_pos
                if is_crod(qX, qZ) and not is_wbc(qX, qZ):
                    count += 1
                    if count >= min_count:
                        result = True
                        break
        return result

    def _checkChunks(self, chunk_path):
        """
        Check a chunk in an z chunks path that is inside of an x path.
        """
        min_indent = ""
        # file_path = os.path.join(
        #     self.chunkymap_thisworld_data_path,
        #     file_name
        # )
        # print("  EXAMINING "+file_name)

        # TODO: optimize this (outer function can provide vars below)
        chunk_filename = os.path.split(chunk_path)
        chunk_luid = self.cLUIDOfConfName(chunk_filename)
        coords = self.coordsOfLUID(chunk_luid)

        qX, qZ = coords
        decachunk_luid = self.dcLUIDAt(qX, qZ)
        if decachunk_luid not in decachunk_luid_list:
            decachunk_luid_list.append(decachunk_luid)
        if "chunk_size" not in self.mapvars:
            print("ERROR: '" + chunk_luid + "' has missing"
                  " mapvars among {" + str(self.mapvars) + "}")
            return False
        print("Checking chunk " + str(coords) + " *"
              + str(self.mapvars["chunk_size"]) + "")
        self.prepareC(qX, qZ)
        # meta = self.chunks[chunk_luid].metadata
        # if ("tags" not in meta):
        #     meta["tags"] = "moreores, caverealms"
        #     self.save_chunk_meta(qX, qZ, min_indent=min_indent+"  ")
        #     print("  saved tags to '"+chunk_path+"'")

    def _checkZ(self, decachunk_x_path):
        """Check a z path containing x chunk paths"""
        minlen = (len(self.confPrefix) + 4 + len(self.confDotExt))
        # ^  +4 for luid, such as x1z2 (ok since just a minimum)
        for decachunk_z_name in os.listdir(decachunk_x_path):
            decachunk_z_path = os.path.join(decachunk_x_path,
                                            decachunk_z_name)
            if decachunk_z_name.startswith("."):
                continue
            if not os.path.isdir(decachunk_z_path):
                continue
            for chunk_filename in os.listdir(decachunk_z_path):
                chunk_path = os.path.join(decachunk_z_path,
                                          chunk_filename)
                if chunk_filename.startswith("."):
                    continue
                if not os.path.isfile(chunk_path):
                    continue
                if len(chunk_filename) < minlen:
                    continue
                chunk_luid = self.cLUIDOfConfName(chunk_filename)
                coords = self.coordsOfLUID(chunk_luid)
                if coords is None:
                    continue
                if not self._checkChunks(chunk_path):
                    break

    def _checkDirs(self):
        for decachunk_x_name in os.listdir(self.data_16px_path):
            decachunk_x_path = os.path.join(self.data_16px_path,
                                            decachunk_x_name)
            if decachunk_x_name.startswith("."):
                continue
            if not os.path.isdir(decachunk_x_path):
                continue
            self._checkZ(decachunk_x_path)

    def check_map_pseudorecursion_start(self):
        min_indent = ""
        if ((self.todo_positions is not None) and
                (self.todo_index >= len(self.todo_positions))):
            print("WARNING in check_map_pseudorecursion_start: todo"
                  " index was [{}] in {}-length list, so resetting todo"
                  "_list".format(self.todo_index,
                                 len(self.todo_positions)))
            self.todo_index = -1
        if self.todo_index < 0:
            print("PROCESSING MAP DATA (BRANCH PATTERN)")
            if (os.path.isfile(self.mtm_py_path) and
                    os.path.isfile(self.colors_path)):
                self.rendered_count = 0
                # self.todo_positions = list()
                # ^ there seems to be issues where not empty (due to
                #   delayed garbage collection??)
                while len(self.todo_positions) > 0:
                    self.todo_positions.pop()
                self.todo_positions.append((0, 0))
                # self.mapvars = get_dict_from_conf_file(
                #     self.world_yaml_path,
                #     ":"
                # )
                self.verify_correct_map()
                decachunk_luid_list = list()
                if self.preload_all_enable:
                    self.preload_all_enable = False
                    self.correct_genresults_paths()
                    self._checkDirs()
                    for decachunk_luid in decachunk_luid_list:
                        coords = self.coordsOfLUID(
                            decachunk_luid
                        )
                        if coords is None:
                            print("ERROR: could not get coords from"
                                  " decachunk luid " + decachunk_luid)
                            continue
                        decachunky_x, decachunky_z = coords
                        qX = self.undecimate(decachunky_x)
                        qZ = self.undecimate(decachunky_z)
                        if not os.path.isfile(self.dcImagePathAt(qX,
                                                                 qZ)):
                            print("Checking decachunk "
                                  + str(decachunky_x) + ", "
                                  + str(decachunky_z))
                            self.checkDCAt(qX, qZ)
                for chunk_luid in self.chunks.keys():
                    coords = self.coordsOfLUID(chunk_luid)
                    if coords is None:
                        print("ERROR: could not get coords from luid '"
                              + chunk_luid + "'")
                        continue
                    qX, qZ = coords
                    meta = self.chunks[chunk_luid].metadata
                    if not meta["is_traversed"]:
                        continue
                    if self.isCDeployed(qX, qZ):
                        continue
                    if meta["is_empty"]:
                        meta["is_empty"] = False
                        self.save_chunk_meta(
                            qX,
                            qZ,
                            min_indent=min_indent+"  ",
                        )
                    # if coords is not None:
                    self.todo_positions.append(coords)
                    # ins = open(file_path, 'r')
                    # line = True
                    # while line:
                    #     line = ins.readline()
                    #     if line:
                    # ins.close()
                self.todo_index = 0
                # while (todo_index<len(self.todo_positions)):
                self.verify_correct_map()

    def verify_correct_map(self):
        # NOTE: NO LONGER NEEDED since each world has its own folder in
        # chunkymapdata/worlds folder
        pass

    def save_mapvars_if_changed(self):
        is_changed = False
        # is_different_world = False
        if self.saved_mapvars is None:
            print("SAVING '" + self.world_yaml_path + "' since nothing"
                  " was loaded or it did not exist")
            is_changed = True
        else:
            for this_key in self.mapvars:
                if this_key != "total_generated_count":
                    # ^ don't care if generated count changed since may
                    #   have been regenerated
                    if (this_key not in self.saved_mapvars.keys()):
                        is_changed = True
                        print(
                            "SAVING '{}' since {} not in"
                            " saved_mapvars".format(
                                self.world_yaml_path, this_key
                            )
                        )
                        break
                    s_s_v = str(self.saved_mapvars[this_key])
                    if (s_s_v != str(self.mapvars[this_key])):
                        is_changed = True
                        print("SAVING '" + self.world_yaml_path
                              + "' since new " + this_key + " value "
                              + str(self.mapvars[this_key])
                              + " not same as saved value "
                              + s_s_v + "")
                        break
        if is_changed:
            save_conf_from_dict(self.world_yaml_path, self.mapvars, ":")
            # ^ save_conf_from_dict is from minetestinfo.py
            self.saved_mapvars = get_dict_from_conf_file(
                self.world_yaml_path,
                ":"
            )
            # self.mapvars = get_dict_from_conf_file(
            #     self.world_yaml_path,
            #     ":"
            # )
        else:
            self.echo1('  (Not saving "{}" since same value of each'
                       ' current variable is already in file as loaded)'
                       ''.format(self.world_yaml_path))

    def atH(self, qX):
        if qX == self.mapvars["min_chunkx"]:
            return True
        if qX == self.mapvars["max_chunkx"]:
            return True
        return False

    def atV(self, qZ):
        if qZ == self.mapvars["min_chunkz"]:
            return True
        if qZ == self.mapvars["max_chunkz"]:
            return True
        return False

    def check_map_inefficient_squarepattern(self):
        if (os.path.isfile(self.mtm_py_path) and
                os.path.isfile(self.colors_path)):
            self.rendered_count = 0
            self.mapvars = get_dict_from_conf_file(self.world_yaml_path,
                                                   ":")
            s_mv = self.mapvars

            self.verify_correct_map()

            s_mv["min_chunkx"] = 0
            s_mv["min_chunkz"] = 0
            s_mv["max_chunkx"] = 0
            s_mv["max_chunkz"] = 0
            if self.saved_mapvars is not None:
                if "min_chunkx" in self.saved_mapvars.keys():
                    s_mv["min_chunkx"] = \
                        self.saved_mapvars["min_chunkx"]
                if "max_chunkx" in self.saved_mapvars.keys():
                    s_mv["max_chunkx"] = \
                        self.saved_mapvars["max_chunkx"]
                if "min_chunkz" in self.saved_mapvars.keys():
                    s_mv["min_chunkz"] = \
                        self.saved_mapvars["min_chunkz"]
                if "max_chunkz" in self.saved_mapvars.keys():
                    s_mv["max_chunkz"] = \
                        self.saved_mapvars["max_chunkz"]

            s_mv["total_generated_count"] = 0

            newchunk_luid_list = list()
            this_iteration_generates_count = 1
            # if self.config["world_name"] != ...):
            #     is_different_world = True
            #     print("FULL RENDER since chosen world name '"
            #           + self.config["world_name"] + "' does not match"
            #           + " previously rendered world name '"
            #           + self.config["world_name"] + "'")
            print("PROCESSING MAP DATA (SQUARE)")
            while this_iteration_generates_count > 0:
                this_iteration_generates_count = 0
                self.read_then_remove_signals()
                if not self.refresh_map_enable:
                    break
                minQZ = s_mv["min_chunkz"]
                maxQZ = s_mv["max_chunkz"]
                for qZ in range(minQZ, s_mv["max_chunkz"]+1):
                    self.read_then_remove_signals()
                    if not self.refresh_map_enable:
                        break
                    for qX in range(s_mv["min_chunkx"],
                                    s_mv["max_chunkx"]+1):
                        self.read_then_remove_signals()
                        if not self.refresh_map_enable:
                            break
                        # python ~/minetest/util/minetestmapper-numpy.py
                        #  --region -1200 800 -1200 800 --drawscale
                        #  --maxheight 100 --minheight -50
                        #  --pixelspernode 1
                        #  ~/.minetest/worlds/FCAGameAWorld ~/map.png
                        # sudo mv ~/map.png
                        #   /var/www/html/minetest/images/map.png

                        # only generate the edges (since started with
                        # region 0 0 0 0) and expanding from there until
                        # no png is created:
                        is_outline = self.atH(qX) or self.atV(qZ)
                        if not is_outline:
                            continue
                        is_present, reason_s = self.checkC(qX, qZ)
                        if not is_present:
                            continue
                        this_iteration_generates_count += 1
                        self.mapvars["total_generated_count"] += 1
                    self.echo1("") # blank line before next qZ
                self.mapvars["min_chunkx"] -= 1
                self.mapvars["min_chunkz"] -= 1
                self.mapvars["max_chunkx"] += 1
                self.mapvars["max_chunkz"] += 1
            # ^ end while square outline (1-chunk-thick outline)
            #   generated any png files
            self.save_mapvars_if_changed()
            if not self.verbose_enable:
                self.echo0('  rendered: {}'
                           ' (only checks for new chunks)'
                           ''.format(self.rendered_count))
        else:
            self.echo0("MAP ERROR: failed since this folder must contain"
                       " colors.txt and minetestmapper-numpy.py")

    def read_then_remove_signals(self):
        signal_path = self.get_signal_path()
        if os.path.isfile(signal_path):
            signals = get_dict_from_conf_file(signal_path, ":")
            if signals is not None:
                print("ANALYZING "+str(len(signals))+" signal(s)")
                for this_key in signals.keys():
                    is_signal_ok = True
                    sig = signals[this_key]
                    if this_key == "loop_enable":
                        if not sig:
                            self.loop_enable = False
                        else:
                            is_signal_ok = False
                            print("WARNING: Got signal to change"
                                  " loop_enable to True, so doing"
                                  " nothing")
                    elif this_key == "refresh_players_enable":
                        if type(sig) is bool:
                            self.refresh_players_enable = sig
                        else:
                            is_signal_ok = False
                            print("ERROR: expected bool for "+this_key)
                    elif this_key == "mapDelay":
                        if (type(sig) is float) or (type(sig) is int):
                            if float(sig) >= 1.0:
                                self.mapDelay = float(sig)
                            else:
                                is_signal_ok = False
                                print("ERROR: expected >=1 seconds for"
                                      " mapDelay (int or float)")
                        else:
                            is_signal_ok = False
                            print("ERROR: expected int for "+this_key)
                    elif this_key == "players_delay":
                        if (type(sig) is float) or (type(sig) is int):
                            if float(sig) >= 1.0:
                                self.players_delay = float(sig)
                            else:
                                print("ERROR: expected >=1 seconds for"
                                      " players_delay (int or float)")
                        else:
                            is_signal_ok = False
                            print("ERROR: expected int for "+this_key)
                    elif this_key == "recheck_rendered":
                        if type(sig) is bool:
                            if sig:
                                for chunk_luid in self.chunks.keys():
                                    self.chunks[chunk_luid].is_fresh = \
                                        False
                        else:
                            is_signal_ok = False
                            print("ERROR: expected bool for "
                                  + this_key)
                    elif this_key == "refresh_map_enable":
                        if type(sig) is bool:
                            self.refresh_map_enable = sig
                        else:
                            is_signal_ok = False
                            print("ERROR: expected bool for "
                                  + this_key)
                    elif this_key == "verbose_enable":
                        if type(sig) is bool:
                            self.verbose_enable = sig
                            self.is_verbose_explicit = \
                                self.verbose_enable
                        else:
                            is_signal_ok = False
                            print("ERROR: expected true or false after"
                                  " colon for " + this_key)

                    else:
                        is_signal_ok = False
                        print("ERROR: unknown signal '" + this_key
                              + "'")
                    if is_signal_ok:
                        print("RECEIVED SIGNAL " + str(this_key) + ":"
                              + str(sig))
            else:
                print("WARNING: blank '" + signal_path + "'")
            try:
                os.remove(signal_path)
            except PermissionError:
                print("ERROR: " + __file__ + " must have permission"
                      " to remove '" + signal_path + "'. Commands will"
                      " be repeated unless command was loop_enable:"
                      "false.")
                # so exiting to avoid inability to avoid repeating
                # commands at next launch.")
                # self.loop_enable = False

    def run_loop(self):
        # self.last_run_second = best_timer()
        self.loop_enable = True
        if not self.is_verbose_explicit:
            self.verbose_enable = False
        is_first_iteration = True
        while self.loop_enable:
            before_second = best_timer()
            run_wait_seconds = self.mapDelay
            if self.players_delay < run_wait_seconds:
                run_wait_seconds = self.players_delay
            # TODO: Implement a verbosity setting.
            print("")
            print("Ran {} time(s) for {}".format(self.run_count,
                                                 self.world_name))
            self.read_then_remove_signals()
            late = 0.3  # map_render_latency
            pW = None
            if self.plSec is not None:
                pW = best_timer() - self.plSec
                # TODO: use `late` as below?
            if self.loop_enable:
                if self.refresh_players_enable:
                    if self.plSec is None or (pW > self.players_delay):
                        # if self.plSec is not None:
                        #     print("waited "+str(pW)+"s: move player")
                        self.plSec = best_timer()
                        self.check_players()
                    else:
                        print("waiting before doing player update")
                else:
                    print("player update is not enabled")
                if self.refresh_map_enable:
                    is_first_run = True
                    is_done_iterating = self.todo_index < 0
                    passed = None
                    if self.mapSec is not None:
                        passed = best_timer() - self.mapSec
                    if ((not is_first_iteration) or
                            (self.mapSec is None) or
                            (passed > self.mapDelay) or
                            (not is_done_iterating)):
                        pW = (best_timer() + late) - self.plSec
                        # ^ player waited
                        # mW = best_timer() - self.mapSec
                        # ^ map waited
                        while is_first_run or (pW < self.players_delay):
                            self.read_then_remove_signals()
                            if not self.refresh_map_enable:
                                break
                            is_first_run = False
                            is_first_iteration = self.todo_index < 0
                            # if ((self.mapSec is None) or
                            #     (mW > self.mapDelay)):
                            # if self.mapSec is not None:
                            #     print("waited "+str(mW)+"s to map")
                            self.mapSec = best_timer()
                            self.check_map_pseudorecursion_iterate()
                            if self.todo_index < 0:  # if done iterating
                                break
                            late = best_timer() - self.mapSec
                            # self.check_map_inefficient_squarepattern()
                            pW = (best_timer() + late) - self.plSec
                            # mW = best_timer() - self.mapSec
                    else:
                        print("waiting before doing map update")
                else:
                    print("map update is not enabled")
                run_wait_seconds -= (best_timer()-before_second)
                is_done_iterating = self.todo_index < 0
                if ((float(run_wait_seconds) > 0.0) and
                        is_done_iterating):
                    print("sleeping for "+str(run_wait_seconds)+"s")
                    time.sleep(run_wait_seconds)
                self.run_count += 1
            else:
                self.verbose_enable = True

    def run(self):
        if self.refresh_players_enable:
            self.check_players()
        if self.refresh_map_enable:
            self.check_map_inefficient_squarepattern()
            # self.check_map_pseudorecursion_iterate()


def main():
    mtchunks = MTChunks(
        get_required("world", caller_name="generator:main"),
    )
    # ^ formerly primary_world_path
    signal_path = mtchunks.get_signal_path()
    stop_line = "loop_enable:False"
    parser = argparse.ArgumentParser(
        description='Generate minetest maps.'
    )
    parser.add_argument(
        '--skip-map',
        type=bool,
        metavar=('skip_map'),
        default=False,
        help='draw map tiles & save YAML files for chunkymap.php to use'
    )
    parser.add_argument(
        '--skip-players',
        type=bool,
        metavar=('skip_players'),
        default=False,
        help='update player YAML files for chunkymap.php to use'
    )
    parser.add_argument(
        '--no-loop',
        type=bool,
        metavar=('no_loop'),
        default=False,
        help=('keep running until "' + signal_path
              + '" contains the line ' + stop_line)
    )
    for done_arg in DONE_ARGS:
        if not done_arg.startswith("-"):
            continue
        if done_arg in STORE_TRUE_ARGS:
            parser.add_argument(
                done_arg,
                # type=ARG_TYPES[done_arg],
                action='store_true',
                help=('See mtchunk mti for more information.')
            )
        else:
            parser.add_argument(
                done_arg,
                type=ARG_TYPES[done_arg],
                help=('See mtchunk mti for more information.')
            )
    args = parser.parse_args()

    if not args.skip_players:
        if not args.skip_map:
            print("Drawing players and map")
        else:
            mtchunks.refresh_map_enable = False
            print("Drawing players only")
    else:
        if not args.skip_map:
            mtchunks.refresh_players_enable = False
            print("Drawing map only")
        else:
            mtchunks.refresh_players_enable = False
            mtchunks.refresh_map_enable = False
            print("Nothing to do since " + str(args))
    if mtchunks.refresh_players_enable or mtchunks.refresh_map_enable:
        if args.no_loop:
            mtchunks.run()
        else:
            print("To stop generator.py loop, save a line '" + stop_line
                  + "' to '" + signal_path + "'")
            mtchunks.run_loop()
    return 0

if __name__ == '__main__':
    sys.exit(main())
