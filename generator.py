#!/usr/bin/env python3

# (deprecated) module for generating map chunks and/or player locations
# for mtanalyze/web. Both this module and mtanalyze/web are deprecated
# in favor of ../webapp since it is planned to run as the same user
# as the user who ran minetestserver.
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
#file modified time etc:
import time
#from datetime import datetime
#copyfile etc:
import shutil
import math

from minetestinfo import *
from poikilos import *
#python_exe_path is from:
from pythoninfo import *

from PIL import Image, ImageDraw, ImageFont, ImageColor
#mode_to_bpp dict is from Antti Haapala. <http://stackoverflow.com/questions/28913988/is-there-a-way-to-measure-the-memory-consumption-of-a-png-image>. 7 Mar 2015. 28 Feb 2016.
mode_to_bpp = {'1':1, 'L':8, 'P':8, 'RGB':24, 'RGBA':32, 'CMYK':32, 'YCbCr':24, 'I':32, 'F':32}
INTERNAL_TIME_FORMAT_STRING="%Y-%m-%d %H:%M:%S"

#best_timer = timeit.default_timer
#if sys.platform == "win32":
    # on Windows, the best timer is time.clock()
#    best_timer = time.clock
#else:
    # on most other platforms, the best timer is time.time()
#    best_timer = time.time
# REQUIRES: see README.md

# The way to do a full render is deleting all files from the world folder under chunkymapdata under your system's www_minetest_path such as /var/www/html/minetest/chunkymapdata/world

#minetestmapper-numpy.py calculates the region as follows:
#(XMIN','XMAX','ZMIN','ZMAX'), default = (-2000,2000,-2000,2000)
#sector_xmin,sector_xmax,sector_zmin,sector_zmax = numpy.array(args.region)/16
#sector_ymin = args.minheight/16
#sector_ymax = args.maxheight/16
#region server-specific options

#as per http://interactivepython.org/runestone/static/pythonds/BasicDS/ImplementingaQueueinPython.html
#class SimpleQueue:
    #def __init__(self):
        #self.items = []

    #def isEmpty(self):
        #return self.items == []

    #def enqueue(self, item):
        #self.items.insert(0,item)

    #def dequeue(self):
        #return self.items.pop()

    #def size(self):
        #return len(self.items)



class MTChunks:
    first_mtime_string = None
    chunkymap_data_path = None
    chunkymapdata_worlds_path = None
    is_save_output_ok = None
    minetestmapper_numpy_path = None
    minetestmapper_custom_path = None
    minetestmapper_py_path = None
    colors_path = None
    python_exe_path = None
    chunks = None
    players = None  # dict with playerid as subscript, each containing player metadata dict
    decachunks = None
    rendered_this_session_count = None
    #force_rerender_decachunks_enable = None

    #region values for subprocess arguments:
    pixelspernode = 1
    refresh_map_enable = None
    refresh_players_enable = None
    refresh_map_seconds = None
    refresh_players_seconds = None
    last_players_refresh_second = None
    last_map_refresh_second = None
    #endregion values for subprocess arguments:

    loop_enable = None
    verbose_enable = None
    is_verbose_explicit = None

    run_count = None
    todo_positions = None  # list of tuples (locations) to render next (for fake recursion)
    todo_index = None
    yaml_name = None
    world_yaml_path = None
    preload_all_enable = None
    chunk_yaml_name_opener_string = None
    chunk_yaml_name_dotext_string = None
    mapvars = None
    saved_mapvars = None
    rendered_count = None
    backend_string = None
    #region_separators = None
    is_backend_detected = None
    chunkymap_players_name = None
    chunkymap_players_path = None
    data_16px_path = None
    data_160px_path = None

    FLAG_COLORS_LIST = None
    world_name = None
    chunkymap_thisworld_data_path = None
    genresult_name_opener_string = "chunk_"
    min_indent = None
    last_player_move_mtime_string = None

    def __init__(self):  #formerly checkpaths() in global scope
        #self.force_rerender_decachunks_enable = True
        self.FLAG_COLORS_LIST = list()
        self.FLAG_COLOR_CHANNELS = get_list_from_hex(FLAG_EMPTY_HEXCOLOR)
        self.FLAG_COLORS_LIST.append(self.FLAG_COLOR_CHANNELS)
        self.FLAG_COLORS_LIST.append((255,255,255))  #for compatibility with maps generated by earlier versions ONLY
        self.FLAG_COLORS_LIST.append((0,0,0))  #for compatibility with maps generated by earlier versions ONLY
        min_indent = "  "
        self.decachunks = {}
        self.rendered_this_session_count = 0
        self.is_backend_detected = False
        self.mapvars = {}
        self.mapvars["total_generated_count"] = 0
        self.rendered_count = 0
        self.preload_all_enable = True
        self.todo_index = -1
        self.todo_positions = list()
        self.run_count = 0
        self.verbose_enable = True
        self.is_verbose_explicit = False
        self.loop_enable = True
        self.refresh_map_enable = False
        self.refresh_players_enable = True
        self.chunks = {}

        self.refresh_map_seconds = 30 #does one chunk at a time so as not to interrupt player updates too often
        self.refresh_players_seconds = 5
        self.chunk_yaml_name_opener_string = "chunk_"
        self.chunk_yaml_name_dotext_string = ".yml"
        #self.region_separators = [" "," "," "]

        input_string = ""

        if minetestinfo.get_var("primary_world_path") is not None:
            if os.path.isdir(minetestinfo.get_var("primary_world_path")):
                print("Using primary_world_path '"+minetestinfo.get_var("primary_world_path")+"'")
            else:
                print("ERROR: Missing world '"+minetestinfo.get_var("primary_world_path")+"'")
                sys.exit(2)
        else:
            print("ERROR: No primary_world_path")
            sys.exit(2)

        # if not os.path.isdir(minetestinfo.get_var("primary_world_path")):
             # print("(ERROR: missing, so please close immediately and update primary_world_path in '"+minetestinfo._config_path+"' before next run)")
        #print("")

        worldmt_path = os.path.join(minetestinfo.get_var("primary_world_path"), "world.mt")
        self.backend_string="sqlite3"
        if (os.path.isfile(worldmt_path)):
            ins = open(worldmt_path, 'r')
            line = True
            while line:
                line = ins.readline()
                if line:
                    line_strip = line.strip()
                    if len(line_strip)>0 and line_strip[0]!="#":
                        if line_strip[:7]=="backend":
                            ao_index = line_strip.find("=")
                            if ao_index>-1:
                                self.backend_string = line_strip[ao_index+1:].strip()
                                self.is_backend_detected = True
                                break
            ins.close()

        else:
            print("ERROR: failed to read '"+worldmt_path+"'")
        self.is_save_output_ok = False   # Keeping output after analyzing it is no longer necessary since results are saved to YAML, but keeping output provides debug info since is the output of minetestmapper-numpy.py
        if self.is_backend_detected:
            print("Detected backend '"+self.backend_string+"' from '"+worldmt_path+"'")
        else:
            print("WARNING: Database backend cannot be detected (unable to ensure image generator script will render map)")

        #region same as singleimage.py
        #self.minetestmapper_numpy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minetestmapper-numpy.py")
        #self.minetestmapper_custom_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minetestmapper-poikilos.py")
        git_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        print("MAPPERS search path (clone minetestmapper-python folder in here): " + git_path)
        self.minetestmapper_numpy_path = os.path.join(os.path.join(git_path, "minetestmapper-python"), "minetestmapper-numpy.py")
        self.minetestmapper_custom_path = os.path.join(os.path.join(git_path, "minetestmapper-python"), "minetestmapper.py")
        self.minetestmapper_py_path = self.minetestmapper_numpy_path
        #if (self.backend_string!="sqlite3"):
            # minetestmapper-numpy had trouble with leveldb but this fork has it fixed so use numpy always always instead of running the following line
            #self.minetestmapper_py_path = self.minetestmapper_custom_path
        print("Chose image generator script: "+self.minetestmapper_py_path)
        if not os.path.isfile(self.minetestmapper_py_path):
            print("WARNING: script does not exist, so "+__file__+" cannot generate maps.")
            #sys.exit(2)
        self.colors_path = os.path.join(os.path.dirname(os.path.abspath(self.minetestmapper_py_path)), "colors.txt")
        if not os.path.isfile(self.colors_path):
            print("WARNING: missing '"+self.colors_path+"', so "+__file__+" may not generate maps properly.")
            #sys.exit(2)
        #endregion same as singleimage.py


        self.chunkymap_data_path=os.path.join(minetestinfo.get_var("www_minetest_path"),"chunkymapdata")
        self.chunkymapdata_worlds_path=os.path.join(self.chunkymap_data_path, "worlds")
        print("Using chunkymap_data_path '"+self.chunkymap_data_path+"'")
        #if not os.path.isdir(self.chunkymap_data_path):
        #    os.mkdir(self.chunkymap_data_path)
        htaccess_path = os.path.join(self.chunkymap_data_path,".htaccess")
        if not os.path.isdir(self.chunkymap_data_path):
            os.makedirs(self.chunkymap_data_path)
            print("Created '"+self.chunkymap_data_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymap_data_path)
            print("  (created .htaccess)")

        htaccess_path = os.path.join(self.chunkymapdata_worlds_path,".htaccess")
        if not os.path.isdir(self.chunkymapdata_worlds_path):
            os.makedirs(self.chunkymapdata_worlds_path)
            print("Created '"+self.chunkymapdata_worlds_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymapdata_worlds_path)
            print("  (created .htaccess)")

        self.world_name = os.path.basename(minetestinfo.get_var("primary_world_path"))
        self.chunkymap_thisworld_data_path = os.path.join(self.chunkymapdata_worlds_path, self.world_name)
        if not os.path.isdir(self.chunkymap_thisworld_data_path):
            os.makedirs(self.chunkymap_thisworld_data_path)
            print("Created '"+self.chunkymap_thisworld_data_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymap_thisworld_data_path)
            print("  (created .htaccess)")

        self.data_16px_path = os.path.join(self.chunkymap_thisworld_data_path, "16px")
        if not os.path.isdir(self.data_16px_path):
            os.makedirs(self.data_16px_path)
            print("Created '"+self.data_16px_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.data_16px_path)
            print("  (created .htaccess)")

        self.data_160px_path = os.path.join(self.chunkymap_thisworld_data_path, "160px")
        if not os.path.isdir(self.data_160px_path):
            os.makedirs(self.data_160px_path)
            print("Created '"+self.data_160px_path+"'")
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.data_160px_path)
            print("  (created .htaccess)")

        #TODO: deny recursively under these folders? doesn't seem that important for security so maybe not (no player info is there)


        self.install_default_world_data()

        self.chunkymap_players_name = "players"
        self.chunkymap_players_path = os.path.join(self.chunkymap_thisworld_data_path, self.chunkymap_players_name)
        htaccess_path = os.path.join(self.chunkymap_players_path,".htaccess")
        if not os.path.isdir(self.chunkymap_players_path):
            os.makedirs(self.chunkymap_players_path)
        if not os.path.isfile(htaccess_path):
            self.deny_http_access(self.chunkymap_players_path)


        self.yaml_name = "generated.yml"
        self.world_yaml_path = os.path.join(self.chunkymap_thisworld_data_path, self.yaml_name)

        self.mapvars["min_chunkx"] = 0
        self.mapvars["min_chunkz"] = 0
        self.mapvars["max_chunkx"] = 0
        self.mapvars["max_chunkz"] = 0
        self.mapvars["chunk_size"] = 16
        self.mapvars["maxheight"] = 96
        self.mapvars["minheight"] = -32
        self.mapvars["pixelspernode"] = 1
        self.saved_mapvars = get_dict_from_conf_file(self.world_yaml_path,":")
        is_mapvars_changed = False
        if self.saved_mapvars is None:
            is_mapvars_changed = True
            #self.save_mapvars_if_changed()
        #self.mapvars = get_dict_from_conf_file(self.world_yaml_path,":")
        #NOTE: do not save or load self.mapvars yet, because if world name is different than saved, chunks must all be redone
        if self.saved_mapvars is not None:
            if "min_chunkx" in self.saved_mapvars.keys():
                self.mapvars["min_chunkx"] = self.saved_mapvars["min_chunkx"]
            if "max_chunkx" in self.saved_mapvars.keys():
                self.mapvars["max_chunkx"] = self.saved_mapvars["max_chunkx"]
            if "min_chunkz" in self.saved_mapvars.keys():
                self.mapvars["min_chunkz"] = self.saved_mapvars["min_chunkz"]
            if "max_chunkz" in self.saved_mapvars.keys():
                self.mapvars["max_chunkz"] = self.saved_mapvars["max_chunkz"]

        if self.mapvars is not None:
            if "min_chunkx" in self.mapvars.keys():
                try:
                    self.mapvars["min_chunkx"] = int(self.mapvars["min_chunkx"])
                except:
                    print("WARNING: min_chunkx was not int so set to 0")
                    self.mapvars["min_chunkx"] = 0
            if "max_chunkx" in self.mapvars.keys():
                try:
                    self.mapvars["max_chunkx"] = int(self.mapvars["max_chunkx"])
                except:
                    print("WARNING: max_chunkx was not int so set to 0")
                    self.mapvars["max_chunkx"] = 0
            if "min_chunkz" in self.mapvars.keys():
                try:
                    self.mapvars["min_chunkz"] = int(self.mapvars["min_chunkz"])
                except:
                    print("WARNING: min_chunkz was not int so set to 0")
                    self.mapvars["min_chunkz"] = 0
            if "max_chunkz" in self.mapvars.keys():
                try:
                    self.mapvars["max_chunkz"] = int(self.mapvars["max_chunkz"])
                except:
                    print("WARNING: max_chunkz was not int so set to 0")
                    self.mapvars["max_chunkz"] = 0
        if is_mapvars_changed:
            self.save_mapvars_if_changed()
        if not self.refresh_map_enable:
            print("refresh_map_enable has been turned off by default since is WIP")

    #def install_default_world_data(self):
        #source_web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        #dest_web_chunkymapdata_world_path = self.chunkymap_thisworld_data_path
        #dest_web_chunkymapdata_world_players_path = os.path.join(self.chunkymap_thisworld_data_path, "players")
        #install_list.append(InstalledFile("singleplayer.png", source_chunkymapdata_players, dest_chunkymapdata_players))


    #formerly install_website
    def install_default_world_data(self):
        source_web_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        source_web_chunkymapdata_path = os.path.join(source_web_path, "chunkymapdata_default")
        source_web_chunkymapdata_world_path = os.path.join(source_web_chunkymapdata_path, "world")
        source_web_chunkymapdata_images_path = os.path.join(source_web_chunkymapdata_path, "images")
        dest_web_path = minetestinfo.get_var("www_minetest_path")
        dest_web_chunkymapdata_path = os.path.join(minetestinfo.get_var("www_minetest_path"),"chunkymapdata")
        dest_web_chunkymapdata_images_path = os.path.join(dest_web_chunkymapdata_path,"images")
        install_list = list()
        install_list.append(InstalledFile("browser.php",source_web_path,dest_web_path))
        install_list.append(InstalledFile("chunkymap.php",source_web_path,dest_web_path))
        install_list.append(InstalledFile("viewchunkymap.php",source_web_path,dest_web_path))
        install_list.append(InstalledFile("zoom_in.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("zoom_out.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("zoom_in_disabled.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("zoom_out_disabled.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("start.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("target_start.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("compass_rose.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("loading.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("arrow_wide_up.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("arrow_wide_down.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("arrow_wide_left.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("arrow_wide_right.png", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("chunk_blank.jpg", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        install_list.append(InstalledFile("decachunk_blank.jpg", source_web_chunkymapdata_images_path, dest_web_chunkymapdata_images_path))
        source_chunkymapdata_players = os.path.join(source_web_chunkymapdata_world_path, "players")
        dest_chunkymapdata_players = os.path.join(self.chunkymap_thisworld_data_path, "players")
        install_list.append(InstalledFile("singleplayer.png", source_chunkymapdata_players, dest_chunkymapdata_players))
        source_chunkymapdata_markers = os.path.join(source_web_chunkymapdata_world_path, "markers")
        dest_chunkymapdata_markers = os.path.join(self.chunkymap_thisworld_data_path, "markers")
        install_list.append(InstalledFile("0.yml", source_chunkymapdata_markers, dest_chunkymapdata_markers))
        for this_object in install_list:
            source_path = os.path.join(this_object.source_dir_path, this_object.file_name)
            installed_path = os.path.join(this_object.dest_dir_path, this_object.file_name)
            if os.path.isfile(source_path):
                if not os.path.isdir(this_object.dest_dir_path):
                    os.makedirs(this_object.dest_dir_path)
                if not os.path.isfile(installed_path):
                    shutil.copyfile(source_path, installed_path) # DOES replace destination file
                else:
                    source_mtime_seconds = time.ctime(os.path.getmtime(source_path))
                    installed_mtime_seconds = time.ctime(os.path.getmtime(installed_path))
                    if source_mtime_seconds>installed_mtime_seconds:
                        shutil.copyfile(source_path, installed_path) # DOES replace destination file
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
        outs.write("order allow,deny"+"\n")
        outs.write("deny from all"+"\n")
        outs.write("</Files>"+"\n")
        outs.write("<Files *.php>"+"\n")
        outs.write("order allow,deny"+"\n")
        outs.write("deny from all"+"\n")
        outs.write("</Files>"+"\n")
        outs.close()


    #locally unique identifier (unique to world only)
    def get_chunk_luid(self, chunky_x, chunky_z):
        return "x"+str(chunky_x)+"z"+str(chunky_z)

    def get_decachunk_image_name_from_chunk(self, chunky_x, chunky_z):
        return "decachunk_"+self.get_decachunk_luid_from_chunk(chunky_x, chunky_z)+".jpg"

    def get_decachunk_image_name_from_decachunk(self, decachunky_x, decachunky_z):
        return "decachunk_"+self.get_decachunk_luid_from_decachunk(decachunky_x, decachunky_z)+".jpg"

    def get_decachunk_luid_from_chunk(self, chunky_x, chunky_z):
        decachunky_x = self.get_decachunky_coord_from_chunky_coord(chunky_x)
        decachunky_z = self.get_decachunky_coord_from_chunky_coord(chunky_z)
        return self.get_chunk_luid(decachunky_x, decachunky_z)

    def get_decachunk_luid_from_decachunk(self, decachunky_x, decachunky_z):
        return self.get_chunk_luid(decachunky_x, decachunky_z)

    def get_decachunk_yaml_name_from_chunk(self, chunky_x, chunky_z):
        return "decachunk_"+self.get_decachunk_luid_from_chunk(chunky_x, chunky_z)+".yml"

    def get_decachunk_yaml_name_from_decachunk(self, decachunky_x, decachunky_z):
        return "decachunk_"+self.get_decachunk_luid_from_decachunk(decachunky_x, decachunky_z)+".yml"

    def get_chunk_image_name(self, chunky_x, chunky_z):
        return "chunk_"+self.get_chunk_luid(chunky_x, chunky_z)+".png"

    #def get_decachunk_image_tmp_path_from_decachunk(self, chunky_x, chunky_z):
        #return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.get_decachunk_image_name_from_decachunk(chunky_x, chunky_z))

    def get_chunk_image_tmp_path(self, chunky_x, chunky_z):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.get_chunk_image_name(chunky_x, chunky_z))

    def get_signal_name(self):
        return "signals.txt"

    def get_signal_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), self.get_signal_name())

    def get_decachunky_coord_from_chunky_coord(self, chunky_x):
        # 15 becomes 1
        # 10 becomes 1
        #  5 becomes 0
        # -5 becomes -1
        #-10 becomes -1
        #-15 becomes -2
        return int(math.floor(float(chunky_x)/10.0))

    def get_chunky_coord_from_decachunky_coord(self, decachunky_x):
        # 1 becomes 10
        # 0 becomes 0
        #-1 becomes -10
        return int(decachunky_x*10)



    def is_worldborder_chunk(self, chunky_x, chunky_z):
        result = False
        image_path = self.get_chunk_image_path(chunky_x, chunky_z)
        border_pixel_count = 0
        if os.path.isfile(image_path):
            original_im = Image.open(image_path)
            im = original_im
            bit_count = 24
            try:
                bit_count = mode_to_bpp[im.mode]
            except:
                print("ERROR in is_worldborder_chunk: unknown image mode "+str(im.mode)+" so can't get bitdepth of chunk")
            if bit_count<24:#if im.bits<24:
                im = original_im.convert('RGB')
            width, height = im.size
            pixel_count = width*height
            pixel_count_f = float(pixel_count)
            border_count = 0
            for FLAG_COLOR in self.FLAG_COLORS_LIST:
                if len(FLAG_COLOR)==3 or len(FLAG_COLOR)==4:
                    for y in range(0,height):
                        for x in range(0,width):
                            r, g, b = im.getpixel((x, y))
                            if r==FLAG_COLOR[0] and g==FLAG_COLOR[1] and b==FLAG_COLOR[2]:
                                border_pixel_count += 1
                    if float(border_pixel_count)/pixel_count_f >=.51:
                        result = True
                        break
                else:
                    print("ERROR: FLAG_COLOR (obtained from"
                          + " FLAG_EMPTY_HEXCOLOR in minetestinfo.py)"
                          + " has " + len(FLAG_COLOR) + " element(s)"
                          + " (3 or 4 expected)")
                    exit(2)
        return result

    def get_index_of_chunk_on_todo_list(self, chunky_pos, allow_current_chunk_enable=False):
        result = -1
        if self.todo_index > -1:
            if self.todo_index<len(self.todo_positions):
                first_index = self.todo_index + 1
                if allow_current_chunk_enable:
                    first_index = self.todo_index
                if first_index<len(self.todo_positions):
                    for index in range(first_index,len(self.todo_positions)):
                        if ivec2_equals(self.todo_positions[index], chunky_pos):
                            result = index
                            break
        return result


    def check_decachunk_containing_chunk(self, chunky_x, chunky_z):
        try:
            chunky_coord_list = list()
            decachunky_x = self.get_decachunky_coord_from_chunky_coord(chunky_x)
            decachunky_z = self.get_decachunky_coord_from_chunky_coord(chunky_z)
            chunky_min_x = decachunky_x*10
            chunky_max_x = chunky_min_x + 9  # NOTE: ADD even if negative, since originally floor was used
            chunky_min_z = decachunky_z*10
            chunky_max_z = chunky_min_z + 9  # NOTE: ADD even if negative, since originally floor was used
            x_chunky_count = chunky_max_x-chunky_min_x+1
            z_chunky_count = chunky_max_z-chunky_min_z+1
            is_any_part_queued = False
            preview_strings = z_chunky_count*[None]
            queued_chunk_coords = None
            chunky_offset_z = 0
            chunky_z = chunky_min_z
            queued_index = None
            is_chunk_complete = False
            while chunky_z <= chunky_max_z:
                preview_strings[chunky_offset_z] = ""
                chunky_x = chunky_min_x
                while chunky_x <= chunky_max_x:
                    coords = (chunky_x, chunky_z)
                    chunky_coord_list.append( coords )
                    queued_index = self.get_index_of_chunk_on_todo_list(coords, allow_current_chunk_enable=False)
                    is_any_part_queued = queued_index > -1
                    if is_any_part_queued:
                        if queued_chunk_coords is None:
                            queued_chunk_coords = list()
                        queued_chunk_coords.append(coords)
                        break
                    chunky_x += 1
                if is_any_part_queued:
                    break
                chunky_z += 1
                chunky_offset_z += 1
            if not is_any_part_queued:
                is_chunk_complete = True
            unfinished_chunky_coord = None
            if is_chunk_complete:
                ### NOTE: a chunk is incomplete if any rendered nonworldborder chunk touches a nonrendered chunk
                for chunky_pos in chunky_coord_list:
                    this_chunky_x, this_chunky_z = chunky_pos
                    if not self.is_chunk_rendered_on_dest(this_chunky_x, this_chunky_z):
                        outline_coords_list = self.get_outline_coords_list(this_chunky_x, this_chunky_z, True)
                        if outline_coords_list is not None:
                            for nearby_chunky_pos in outline_coords_list:
                                nearby_chunky_x, nearby_chunky_z = nearby_chunky_pos
                                nearby_chunk_luid = self.get_chunk_luid(nearby_chunky_x, nearby_chunky_z)
                                if (nearby_chunk_luid in self.chunks and self.chunks[nearby_chunk_luid].is_fresh) or self.is_chunk_rendered_on_dest(nearby_chunky_x, nearby_chunky_z):
                                    this_is_worldborder_chunk = False
                                    if (nearby_chunk_luid in self.chunks and "is_worldborder" in self.chunks[nearby_chunk_luid].metadata and self.chunks[nearby_chunk_luid].metadata["is_worldborder"]):
                                        this_is_worldborder_chunk = True
                                    elif self.is_worldborder_chunk(nearby_chunky_x, nearby_chunky_z):
                                        this_is_worldborder_chunk = True
                                        self.prepare_chunk_meta(nearby_chunky_x, nearby_chunky_z)
                                        if ("is_worldborder" not in self.chunks[nearby_chunk_luid].metadata) or (not self.chunks[nearby_chunk_luid].metadata["is_worldborder"]):
                                            self.chunks[nearby_chunk_luid].metadata["is_worldborder"] = True
                                            self.save_chunk_meta(nearby_chunky_x, nearby_chunky_z)
                                    if not this_is_worldborder_chunk:
                                        #empty chunk would not touch NON-worldborder chunk if decachunk was complete
                                        is_chunk_complete = False
                                        unfinished_chunky_coord = nearby_chunky_x, nearby_chunky_z
                                        break
                        else:
                            print(min_indent+"ERROR in check_decachunk_containing_chunk: no outline of chunks could be found around "+str(chunky_pos))
                    if not is_chunk_complete:
                        break

            #if not is_any_part_queued:
            #if queued_chunk_coords is None:
            if is_chunk_complete and not is_any_part_queued:
                print("")
                print("")
                print("    Rendering 160px decachunk "+str((decachunky_x, decachunky_z)))
                if self.verbose_enable:
                    print("      USING ("+str(len(chunky_coord_list))+") chunks (region "+str(chunky_min_x)+":"+str(chunky_max_x)+","+str(chunky_min_z)+":"+str(chunky_max_z)+"): "+str(chunky_coord_list))
                    print("")
                else:
                    print("      USING ("+str(len(chunky_coord_list))+") chunks (region "+str(chunky_min_x)+":"+str(chunky_max_x)+","+str(chunky_min_z)+":"+str(chunky_max_z)+")")
                decachunk_global_coords = decachunky_x*160, decachunky_z*160
                im = Image.new("RGB", (160, 160), FLAG_EMPTY_HEXCOLOR)
                decachunk_yaml_path = self.get_decachunk_yaml_path_from_decachunk(decachunky_x, decachunky_z)
                decachunk_image_path = self.get_decachunk_image_path_from_decachunk(decachunky_x, decachunky_z)
                combined_count = 0
                contains_chunk_luids = list()

                for coord in chunky_coord_list:
                    chunky_x, chunky_z = coord
                    chunky_offset_x = chunky_x - chunky_min_x
                    chunky_offset_z = chunky_z - chunky_min_z
                    chunk_image_path = self.get_chunk_image_path(chunky_x, chunky_z)
                    if os.path.isfile(chunk_image_path):
                        preview_strings[chunky_offset_z] += "1"
                        participle="initializing"
                        try:
                            participle="opening path"
                            chunk_im = Image.open(open(chunk_image_path, 'rb'))  # double-open to make sure file is finished writing
                            #NOTE: PIL automatically closes, otherwise you can do something like https://bytes.com/topic/python/answers/24308-pil-do-i-need-close
                            #fp = open(file_name, "rb")
                            #im = Image.open(fp) # open from file object
                            #im.load() # make sure PIL has read the data
                            #fp.close()
                            chunk_global_coords = chunky_x*16, chunky_z*16
                            chunk_local_coords = chunk_global_coords[0]-decachunk_global_coords[0], chunk_global_coords[1]-decachunk_global_coords[1]
                            offset = chunk_local_coords[0], 160-chunk_local_coords[1]  # convert to inverted cartesian since that's the coordinate system of images
                            im.paste(chunk_im, offset)
                            contains_chunk_luids.append(self.get_chunk_luid(chunky_x, chunky_z))
                        except:
                            print(min_indent+"Could not finish "+participle+" in check_decachunk_containing_chunk:")
                            view_traceback()
                    else:
                        preview_strings[chunky_offset_z] += "0"
                chunky_offset_z = z_chunky_count - 1
                try:
                    print(min_indent+"Decachunk available chunk mask (height:"+str(z_chunky_count)+"):")
                    while chunky_offset_z>=0:
                        if preview_strings[chunky_offset_z] is None:
                            preview_strings[chunky_offset_z] = "<None>"
                        print(min_indent+"  "+str(chunky_offset_z)+":"+preview_strings[chunky_offset_z])
                        chunky_offset_z -= 1
                except:
                    print(min_indent+"Could not finish showing mask (this should never happen)")
                    print(min_indent+"  z_chunky_count:"+str(z_chunky_count))
                    print(min_indent+"  len(preview_strings):"+str(len(preview_strings)))
                    print(min_indent+"  chunky_min_x:"+str(chunky_min_x))
                    print(min_indent+"  chunky_max_x:"+str(chunky_max_x))
                    print(min_indent+"  chunky_min_z:"+str(chunky_min_z))
                    print(min_indent+"  chunky_max_z:"+str(chunky_max_z))
                    view_traceback()
                print("")
                decachunk_folder_path = self.get_decachunk_folder_path_from_decachunk(decachunky_x, decachunky_z)
                if not os.path.isdir(decachunk_folder_path):
                    os.makedirs(decachunk_folder_path)
                    print(min_indent+"Made folder '"+decachunk_folder_path+"'")
                else:
                    print(min_indent+"Found folder '"+decachunk_folder_path+"'")
                print(min_indent+"Saving '"+decachunk_image_path+"'")
                im.save(decachunk_image_path)
                decachunk_luid = self.get_decachunk_luid_from_decachunk(decachunky_x, decachunky_z)
                self.prepare_decachunk_meta_from_decachunk(decachunky_x, decachunky_z)
                this_second = int(time.time())
                #if int(self.decachunks[decachunk_luid].metadata["last_saved_utc_second"]) != this_second:
                self.decachunks[decachunk_luid].metadata["last_saved_utc_second"] = this_second  # time.time() returns float even if OS doesn't give a time in increments smaller than seconds
                if len(contains_chunk_luids)>0:
                    self.decachunks[decachunk_luid].metadata["contains_chunk_luids"] = ','.join(contains_chunk_luids)
                else:
                    self.decachunks[decachunk_luid].metadata["contains_chunk_luids"] = None
                self.decachunks[decachunk_luid].save_yaml(decachunk_yaml_path)
            else:
                if is_any_part_queued:
                    print(min_indent+"Not rendering decachunk "+str((decachunky_x,decachunky_z))+" yet since contains queued chunk {found_index:["+str(queued_index)+"]; current_index:["+str(self.todo_index)+"]; len(todo_positions):"+str(len(self.todo_positions))+"; chunky_position:"+str(queued_chunk_coords)+"}")
                else:
                    print(min_indent+"Not rendering decachunk "+str((decachunky_x,decachunky_z))+" yet since unfinished chunks (world border not between empty and closed area) such as empty chunk "+str(unfinished_chunky_coord))
                print(min_indent+"  (index:["+str(queued_index)+"]; len:"+str(len(self.todo_positions))+") .")
        except:
            print(min_indent+"Could not finish check_decachunk_containing_chunk:")
            view_traceback()

    def get_chunk_folder_path(self, chunky_x, chunky_z):
        result = None
        decachunky_x = self.get_decachunky_coord_from_chunky_coord(chunky_x)
        decachunky_z = self.get_decachunky_coord_from_chunky_coord(chunky_z)
        result = os.path.join( os.path.join(self.data_16px_path, str(decachunky_x)), str(decachunky_z) )
        return result

    def get_decachunk_folder_path_from_chunk(self, chunky_x, chunky_z):
        result = None
        if chunky_x is not None and chunky_z is not None:
            decachunk_x = self.get_decachunky_coord_from_chunky_coord(chunky_x)
            decachunk_z = self.get_decachunky_coord_from_chunky_coord(chunky_z)
            #hectochunky_x = int(math.floor(chunky_x/100))
            #hectochunky_z = int(math.floor(chunky_z/100))
            #result = os.path.join( os.path.join(self.data_160px_path, str(hectochunky_x)), str(hectochunky_x) )
            result = self.get_decachunk_folder_path_from_decachunk(decachunk_x, decachunk_z)
        return result

    def get_decachunk_folder_path_from_decachunk(self, decachunky_x, decachunky_z):
        result = None
        if decachunky_x is not None and decachunky_z is not None:
            hectochunky_x = int(math.floor(float(decachunky_x)/10.0))
            hectochunky_z = int(math.floor(float(decachunky_z)/10.0))
            result = os.path.join( os.path.join(self.data_160px_path, str(hectochunky_x)), str(hectochunky_z) )
        return result

    def create_chunk_folder(self, chunky_x, chunky_z):
        path = self.get_chunk_folder_path(chunky_x, chunky_z)
        if not os.path.isdir(path):
            os.makedirs(path)

    def get_decachunk_image_path_from_chunk(self, chunky_x, chunky_z):
        return os.path.join(self.get_decachunk_folder_path_from_chunk(chunky_x, chunky_z), self.get_decachunk_image_name_from_chunk(chunky_x, chunky_z))

    def get_decachunk_yaml_path_from_chunk(self, chunky_x, chunky_z):
        return os.path.join(self.get_decachunk_folder_path_from_chunk(chunky_x, chunky_z), self.get_decachunk_yaml_name_from_chunk(chunky_x, chunky_z))

    def get_decachunk_image_path_from_decachunk(self, decachunky_x, decachunky_z):
        return os.path.join(self.get_decachunk_folder_path_from_decachunk(decachunky_x, decachunky_z), self.get_decachunk_image_name_from_decachunk(decachunky_x, decachunky_z))

    def get_decachunk_yaml_path_from_decachunk(self, decachunky_x, decachunky_z):
        return os.path.join(self.get_decachunk_folder_path_from_decachunk(decachunky_x, decachunky_z), self.get_decachunk_yaml_name_from_decachunk(decachunky_x, decachunky_z))

    def get_chunk_image_path(self, chunky_x, chunky_z):
        return os.path.join(self.get_chunk_folder_path(chunky_x, chunky_z), self.get_chunk_image_name(chunky_x, chunky_z))

    def get_chunk_genresult_name(self, chunky_x, chunky_z):
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        return self.genresult_name_opener_string+chunk_luid+genresult_name_end_flag

    def get_chunk_luid_from_genresult_name(self, file_name):
        return file_name[len(self.genresult_name_opener_string):-1*len(genresult_name_end_flag)]

    def get_chunk_genresult_tmp_folder(self, chunky_x, chunky_z):
        #coords = self.get_coords_from_luid(chunk_luid)
        #if coords is not None:
        #    chunky_x, chunky_z = coords
        tmp_path = self.get_chunk_genresults_base_path()
        decachunky_x = self.get_decachunky_coord_from_chunky_coord(chunky_x)
        decachunky_z = self.get_decachunky_coord_from_chunky_coord(chunky_z)
        tmp_path = os.path.join( os.path.join(tmp_path, str(decachunky_x)), str(decachunky_z) )
        return tmp_path

    def get_chunk_genresults_base_path(self):
        #formerly get_chunk_genresults_tmp_folder(self, chunk_luid)
        return os.path.join( os.path.join(os.path.dirname(os.path.abspath(__file__)), "chunkymap-genresults"), self.world_name)

    def get_chunk_genresult_tmp_path(self, chunky_x, chunky_z):
        return os.path.join(self.get_chunk_genresult_tmp_folder(chunky_x, chunky_z), self.get_chunk_genresult_name(chunky_x, chunky_z))

    def get_chunk_luid_from_yaml_name(self, file_name):
        return file_name[len(self.chunk_yaml_name_opener_string):-1*len(self.chunk_yaml_name_dotext_string)]


    def get_chunk_yaml_name(self, chunky_x, chunky_z):
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        return self.chunk_yaml_name_opener_string+chunk_luid+self.chunk_yaml_name_dotext_string

    def is_chunk_yaml_present(self, chunky_x, chunky_z):
        return os.path.isfile(self.get_chunk_yaml_path(chunky_x, chunky_z))

    def get_chunk_yaml_path(self, chunky_x, chunky_z):
        return os.path.join(self.get_chunk_folder_path(chunky_x, chunky_z), self.get_chunk_yaml_name(chunky_x, chunky_z))

    def is_chunk_yaml_marked(self, chunky_x, chunky_z):
        yaml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
        result = False
        if os.path.isfile(yaml_path):
            result = True
            #ins = open(yaml_path, 'r')
            #line = True
            #while line:
            #    line = ins.readline()
            #    if line:
            #        line_strip = line.strip()
            #        if "is_empty:" in line_strip:
            #            result = True
            #            break
            #ins.close()
        return result

    def is_chunk_yaml_marked_empty(self, chunky_x, chunky_z):
        result = False
        yaml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
        if os.path.isfile(yaml_path):
            self.prepare_chunk_meta(chunky_x, chunky_z)  # DOES get existing data if any file exists
            chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
            if "is_empty" in self.chunks[chunk_luid].metadata.keys():
                result = self.chunks[chunk_luid].metadata["is_empty"]

        return result

    def remove_chunk_image(self, chunky_x, chunky_z):
        result = False
        tmp_png_path = self.get_chunk_image_path(chunky_x, chunky_z)
        if os.path.isfile(tmp_png_path):
            result = True
            os.remove(tmp_png_path)
        return result

    def remove_chunk(self, chunky_x, chunky_z):
        result = False
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        out_path = self.get_chunk_genresult_tmp_path(chunky_x, chunky_z)
        tmp_png_path = self.get_chunk_image_path(chunky_x, chunky_z)
        yml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
        if os.path.isfile(tmp_png_path):
            os.remove(tmp_png_path)
            result = True
        if os.path.isfile(yml_path):
            os.remove(yml_path)
            result = True
        if os.path.isfile(out_path):
            os.remove(out_path)
            result = True
        #TODO: if folder becomes empty, remove it
        return result

    def is_chunk_rendered_on_dest(self, chunky_x, chunky_z):  #formerly is_chunk_empty_on_dest (reversed)
        is_rendered = False
        dest_png_path = self.get_chunk_image_path(chunky_x, chunky_z)
        if os.path.isfile(dest_png_path):
            is_rendered = True
        return is_rendered

    def prepare_decachunk_meta_from_chunk(self, chunky_x, chunky_z):
        chunk_luid = self.get_decachunk_luid_from_chunk(chunky_x, chunky_z)
        if chunk_luid not in self.decachunks.keys():
            self.decachunks[chunk_luid] = MTDecaChunk()
            #self.chunks[chunk_luid].luid = chunk_luid
            yaml_path = self.get_decachunk_yaml_path_from_chunk(chunky_x, chunky_z)
            if os.path.isfile(yaml_path):
                self.decachunks[chunk_luid].load_yaml(yaml_path)

    def prepare_decachunk_meta_from_decachunk(self, decachunky_x, decachunky_z):
        chunk_luid = self.get_decachunk_luid_from_decachunk(decachunky_x, decachunky_z)
        if chunk_luid not in self.decachunks.keys():
            self.decachunks[chunk_luid] = MTDecaChunk()
            #self.chunks[chunk_luid].luid = chunk_luid
            yaml_path = self.get_decachunk_yaml_path_from_decachunk(decachunky_x, decachunky_z)
            if os.path.isfile(yaml_path):
                self.decachunks[chunk_luid].load_yaml(yaml_path)

    def prepare_chunk_meta(self, chunky_x, chunky_z):
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        if chunk_luid not in self.chunks.keys():
            self.chunks[chunk_luid] = MTChunk()
            #self.chunks[chunk_luid].luid = chunk_luid
            yaml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
            if os.path.isfile(yaml_path):
                self.chunks[chunk_luid].load_yaml(yaml_path)


    # normally call check_chunk instead, which renders chunk only if necessary
    def _render_chunk(self, chunky_x, chunky_z):
        min_indent = "  "  # increased below
        result = False
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        png_name = self.get_chunk_image_name(chunky_x, chunky_z)
        tmp_png_path = self.get_chunk_image_tmp_path(chunky_x, chunky_z)
        genresult_name = self.get_chunk_genresult_name(chunky_x, chunky_z)
        genresult_tmp_folder_path = self.get_chunk_genresult_tmp_folder(chunky_x, chunky_z)
        if not os.path.isdir(genresult_tmp_folder_path):
            os.makedirs(genresult_tmp_folder_path)
        genresult_path = self.get_chunk_genresult_tmp_path(chunky_x, chunky_z)
        min_x = chunky_x * self.mapvars["chunk_size"]
        max_x = chunky_x * self.mapvars["chunk_size"] + self.mapvars["chunk_size"] - 1
        min_z = chunky_z * self.mapvars["chunk_size"]
        max_z = chunky_z * self.mapvars["chunk_size"] + self.mapvars["chunk_size"] - 1

        #print (min_indent+"generating chunky_x = " + str(min_x) + " to " + str(max_x) + " ,  chunky_z = " + str(min_z) + " to " + str(max_z))
        geometry_value_string = str(min_x)+":"+str(min_z)+"+"+str(int(max_x)-int(min_x)+1)+"+"+str(int(max_z)-int(min_z)+1)  # +1 since max-min is exclusive and width must be inclusive for minetestmapper.py
        cmd_suffix = ""
        genresults_folder_path = os.path.join( os.path.join(os.path.dirname(os.path.abspath(__file__)), "chunkymap-genresults"), self.world_name)
        if not os.path.isdir(genresults_folder_path):
            os.makedirs(genresults_folder_path)
        gen_error_path = os.path.join(genresults_folder_path, "singleimage"+gen_error_name_end_flag)
        cmd_suffix = " 1> \""+genresult_path+"\""
        cmd_suffix += " 2> \""+gen_error_path+"\""
        #self.mapper_id = "minetestmapper-region"
        bin_string = python_exe_path + " \"" + self.minetestmapper_py_path + "\""
        geometry_enable = False
        if not os.path.isfile(self.minetestmapper_py_path):
            bin_string = "minetestmapper"
            geometry_enable = True
        cmd_no_out_string = bin_string + " --region " + str(min_x) + " " + str(max_x) + " " + str(min_z) + " " + str(max_z) + " --maxheight "+str(self.mapvars["maxheight"])+" --minheight "+str(self.mapvars["minheight"])+" --pixelspernode "+str(self.mapvars["pixelspernode"])+" \""+minetestinfo.get_var("primary_world_path")+"\" \""+tmp_png_path+"\""
        cmd_string = cmd_no_out_string + cmd_suffix
        if self.minetestmapper_py_path==self.minetestmapper_custom_path: #if self.backend_string!="sqlite3": #if self.mapper_id=="minetestmapper-region":
            geometry_enable = True
        if geometry_enable:
            #  Since minetestmapper-numpy has trouble with leveldb:
            #    such as sudo minetest-mapper --input "/home/owner/.minetest/worlds/FCAGameAWorld" --geometry -32:-32+64+64 --output /var/www/html/minetest/try1.png
            #    where geometry option is like --geometry x:y+w+h
            #    mapper_id = "minetest-mapper"
            #    NOTE: minetest-mapper is part of the minetest-data package, which can be installed alongside the git version of minetestserver
            #    BUT *buntu Trusty version of it does NOT have geometry option
            #    cmd_string = "/usr/games/minetest-mapper --input \""+minetestinfo.get_var("primary_world_path")+"\" --draworigin --geometry "+geometry_value_string+" --output \""+tmp_png_path+"\""+cmd_suffix
            #    such as sudo python minetestmapper --input "/home/owner/.minetest/worlds/FCAGameAWorld" --geometry -32:-32+64+64 --output /var/www/html/minetest/try1.png
            # OR try PYTHON version (looks for poikilos fork which has geometry option like C++ version does):
            #script_path = "$HOME/chunkymap/minetestmapper.py"
            #region_capable_script_path = "$HOME/chunkymap/minetestmapper-poikilos.py"
            #    region_capable_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minetestmapper.py")
            #    if os.path.isfile(region_capable_script_path):
            #        script_path=region_capable_script_path
            #if os.path.isfile(region_capable_script_path):
                #script_path = region_capable_script_path
            geometry_string = str(min_x)+":"+str(min_z)+"+"+str(int(max_x)-int(min_x)+1)+"+"+str(int(max_z)-int(min_z)+1)  # +1 since max-min is exclusive and width must be inclusive for minetestmapper.py
            geometry_param = " --geometry "+geometry_string
            #poikilos_region_string = str(min_x) + ":" + str(max_x) + "," + str(min_z) + ":" + str(max_z)
            #cmd_string="sudo python "+script_path+" --input \""+minetestinfo.get_var("primary_world_path")+"\" --geometry "+geometry_value_string+" --output \""+tmp_png_path+"\""+cmd_suffix
            world_path = minetestinfo.get_var("primary_world_path")
            io_string = " --input \""+world_path+"\" --output \""+tmp_png_path+"\""
            #if "numpy" in self.minetestmapper_py_path:
            #    io_string = " \""+world_path+"\" \""+tmp_png_path+"\""
            #    geometry_param = " --region " + str(min_x) + " " + str(max_x) + " " + str(min_z) + " " + str(max_z)
            cmd_no_out_string = bin_string + " --bgcolor '" + FLAG_EMPTY_HEXCOLOR + "'" + geometry_param + io_string
            cmd_string = cmd_no_out_string + cmd_suffix
            #sudo python /home/owner/minetest/util/minetestmapper.py --bgcolor '#010000' --input "/home/owner/.minetest/worlds/FCAGameAWorld" --output /var/www/html/minetest/chunkymapdata/entire.png > entire-mtmresult.txt
            #sudo python /home/owner/minetest/util/chunkymap/minetestmapper.py --input "/home/owner/.minetest/worlds/FCAGameAWorld" --geometry 0:0+16+16 --output /var/www/html/minetest/chunkymapdata/chunk_x0z0.png > /home/owner/minetest/util/chunkymap-genresults/chunk_x0z0_mapper_result.txt
            #    sudo mv entire-mtmresult.txt /home/owner/minetest/util/chunkymap-genresults/

        dest_png_path = self.get_chunk_image_path(chunky_x, chunky_z)
        #is_empty_chunk = is_chunk_yaml_marked(chunky_x, chunky_z) and is_chunk_yaml_marked_empty(chunky_x, chunky_z)
        #if self.verbose_enable:
        #    #print(min_indent+"")
        #    print(min_indent+"Running '"+cmd_string+"'...")
        #else:
        print (min_indent+"Calling map tile renderer for: "+str((chunky_x, chunky_z)))
        min_indent += "  "
        try:
            if os.path.isfile(tmp_png_path):
                os.remove(tmp_png_path)
            subprocess.call(cmd_string, shell=True)  # TODO: remember not to allow arbitrary command execution, which could happen if input contains ';' when using shell=True
            #is_empty_before = True
            #is_marked_before = False
            self.prepare_chunk_meta(chunky_x, chunky_z)  # DOES load existing yml if exists
            old_meta = get_dict_deepcopy(self.chunks[chunk_luid].metadata)
            is_marked_before = self.chunks[chunk_luid].metadata["is_marked"]
            is_empty_before = self.chunks[chunk_luid].metadata["is_empty"]
            #if chunk_luid in self.chunks.keys():
                #is_marked_before = True
                #if (self.chunks[chunk_luid].metadata is not None) and ("is_empty" in self.chunks[chunk_luid].metadata):
                #    is_empty_before = self.chunks[chunk_luid].metadata["is_empty"]
            this_chunk = self.chunks[chunk_luid]
            if os.path.isfile(tmp_png_path):
                result = True
                this_chunk.metadata["is_empty"] = False
                try:
                    if (os.path.isfile(dest_png_path)):
                        os.remove(dest_png_path)
                except:
                    print (min_indent+"Could not finish deleting '"+dest_png_path+"'")
                try:
                    self.create_chunk_folder(chunky_x, chunky_z)
                    os.rename(tmp_png_path, dest_png_path)
                    print(min_indent+"(moved to '"+dest_png_path+"')")
                    self.rendered_this_session_count += 1
                    self.prepare_chunk_meta(chunky_x, chunky_z)  # DOES load existing yml if exists
                    self.chunks[chunk_luid].is_fresh = True
                    self.chunks[chunk_luid].metadata["is_empty"] = False
                    print (min_indent+"{rendered_this_session_count:"+str(self.rendered_this_session_count)+"}")
                except:
                    print (min_indent+"Could not finish moving '"+tmp_png_path+"' to '"+dest_png_path+"'")
            else:
                if self.is_chunk_traversed_by_player(chunk_luid):
                    print (min_indent+"WARNING: no chunk data though traversed by player:")
                    print(min_indent+"standard output stream:")
                    line_count = print_file(genresult_path, min_indent+"  ")
                    if line_count>0:
                        print(min_indent+"  #EOF: "+str(line_count)+" line(s) in '"+genresult_path+"'")
                        pass
                    else:
                        print(min_indent+"  #EOF: "+str(line_count)+" line(s) in '"+genresult_path+"'")
                        subprocess.call(cmd_no_out_string+" 2> \""+genresult_path+"\"", shell=True)
                        print(min_indent+"standard error stream:")
                        line_count = print_file(genresult_path, min_indent+"  ")
                        if (line_count<1):
                            print(min_indent+"  #EOF: "+str(line_count)+" line(s) in '"+genresult_path+"'")
                        print(min_indent+"  (done output of '"+cmd_no_out_string+"')")
                        try:
                            if os.path.exists(tmp_png_path):
                                os.rename(tmp_png_path, dest_png_path)
                        except:
                            pass
            participle = "checking result"
            is_locked = False
            err_count = 0
            if os.path.isfile(gen_error_path):
                ins = open(gen_error_path, 'r')
                line = True
                while line:
                    line = ins.readline()
                    if line:
                        if len(line.strip())>0:
                            err_count += 1
                        line_lower = line.lower()
                        if (" lock " in line_lower) or ("/lock " in line_lower):
                            is_locked = True
                            lock_line = line
                            result = None
                            break
                ins.close()
            if err_count<1:
                os.remove(gen_error_path)
            if not is_locked:
                try:
                    is_changed = this_chunk.set_from_genresult(genresult_path)
                    if is_marked_before:
                        participle = "checking for marks"
                        if (not is_empty_before) and this_chunk.metadata["is_empty"]:
                            print("ERROR: chunk changed from nonempty to empty (may happen if output of mapper was not recognized)")
                        elif this_chunk.metadata["is_empty"] and os.path.isfile(dest_png_path):
                            print("ERROR: chunk marked empty though has data (may happen if output of mapper was not recognized)")
                    this_is_worldborder_chunk = self.is_worldborder_chunk(chunky_x, chunky_z)
                    if ("is_worldborder" not in self.chunks[chunk_luid].metadata) or this_is_worldborder_chunk != self.chunks[chunk_luid].metadata["is_worldborder"]:
                        self.chunks[chunk_luid].metadata["is_worldborder"] = this_is_worldborder_chunk
                        is_changed = True

                    #chunk_yaml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
                    #self.create_chunk_folder(chunky_x, chunky_z)
                    #this_chunk.save_yaml(chunk_yaml_path)
                    #if is_changed:
                    participle = "accessing dict"
                    if not is_dict_subset(self.chunks[chunk_luid].metadata, old_meta, False):  # , True, "chunk_yaml_path")
                        participle = "saving chunk meta"
                        self.save_chunk_meta(chunky_x, chunky_z)
                    #print(min_indent+"(saved yaml to '"+chunk_yaml_path+"')")
                    if not self.is_save_output_ok:
                        if os.path.isfile(genresult_path):
                            participle = "removing "+genresult_path
                            os.remove(genresult_path)
                except:
                    print (min_indent+"Could not finish "+participle+" while deleting/moving output")
                    view_traceback()
            else:
                print(min_indent+"database locked: "+lock_line)
        except:
            print(min_indent+"Could not finish deleting/moving temp files")
            view_traceback()


        return result

    def save_chunk_meta(self, chunky_x, chunky_z):
        chunk_yaml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        if not chunk_luid in self.chunks:
            self.prepare_chunk_meta(chunky_x, chunky_z)
        self.create_chunk_folder(chunky_x, chunky_z)
        self.chunks[chunk_luid].save_yaml(chunk_yaml_path)
        print(min_indent+"(saved yaml to '"+chunk_yaml_path+"')")

    def is_used_player_index(self, index):
        result = False
        if self.players is not None:
            for this_key in self.players.keys():
                this_player = self.players[this_key]
                if "index" in this_player:
                    if int(this_player["index"])==int(index):
                        result = True
                        break
                    #else:
                    #    if self.verbose_enable:
                    #        print("existing "+this_player["index"]+" is not needle "+str(index))
                #else:
                    #print("WARNING: player "+this_key+":"+str(this_player)+" is missing index")
        return result

    def get_new_player_index(self):
        result = None
        max_player_index = None
        index = 0
        try:
            while (self.is_used_player_index(index)):
                index += 1
            result = index
        except:
            print(min_indent+"Could not finish get_new_player_index:")
            view_traceback()

        return result

    def get_new_player_index_faster(self):
        result = None
        max_player_index = None
        if self.players is not None:
            for this_key in self.players.keys():
                this_player = self.players[this_key]
                if "index" in this_player:
                    if (max_player_index is None) or (int(this_player["index"])>max_player_index):
                        max_player_index = int(this_player["index"])
                else:
                    print("WARNING: player with playerid '"+this_key+"' has no public index (programmer or admin error)")
        if max_player_index is not None:
            result = max_player_index + 1
        else:
            result = 0

        return result

    def save_player(self, playerid):
        if self.players is not None:
            if playerid is not None:
                if playerid in self.players:
                    if not os.path.isdir(self.chunkymap_players_path):
                        os.makedirs(self.chunkymap_players_path)
                        self.deny_http_access(self.chunkymap_players_path)
                    this_player = self.players[playerid]
                    if "index" in this_player:
                        player_path = os.path.join(self.chunkymap_players_path, this_player["index"])
                        save_conf_from_dict(player_path, this_player, ":")
                    else:
                        print("ERROR: cannot save player since missing 'index' ('index' is used for filename on map)")
                else:
                    print("ERROR: tried to save nonexistant playerid '"+str(playerid)+"'")
            else:
                print("ERROR: save_player(None) was attempted.")
        else:
            print("ERROR: Tried save_player but the players dict is not ready (self.players is None)")

    def check_players(self):
        if self.first_mtime_string is None:
            first_mtime = time.gmtime()
            #NOTE: time.gmtime converts long timestamp to 9-long tuple
            self.first_mtime_string = time.strftime(INTERNAL_TIME_FORMAT_STRING, first_mtime)
        print("PROCESSING PLAYERS")
        player_markers_count = 0
        if self.players is None:
            self.players = {}
            if os.path.isdir(self.chunkymap_players_path):
                folder_path = self.chunkymap_players_path
                for sub_name in os.listdir(folder_path):
                    sub_path = os.path.join(folder_path,sub_name)
                    if os.path.isfile(sub_path):
                        if (sub_name[:1]!="."):
                            if len(sub_name)>4 and sub_name[-4:]==".yml":
                                player_markers_count += 1
                                player_dict = get_dict_from_conf_file(sub_path,":")
                                if player_dict is not None:
                                    player_dict["index"] = int(sub_name[:-4])  # repair index
                                    if "playerid" in player_dict:
                                        if (player_dict["playerid"] is not None) and (player_dict["playerid"]!=""):
                                            player_dict["playerid"] = str(player_dict["playerid"])  # in case was detected as int, change back to string since is a name and so name string will be found as dict key when checked later
                                            self.players[player_dict["playerid"]] = player_dict
                                            if self.verbose_enable:
                                                print("Loading map entry index '"+str(player_dict["index"])+"' for playerid '"+str(player_dict["playerid"])+"'")
                                        else:
                                            print("ERROR: no 'playerid' in chunkymap player entry '"+sub_path+"'")
                                    else:
                                        print("WARNING: dangling player marker (no playerid) in '"+sub_path+"' so cannot be updated")
                                else:
                                    print("ERROR: could not read any yaml values from '"+sub_path+"'")
            else:
                os.makedirs(self.chunkymap_players_path)
                self.deny_http_access(self.chunkymap_players_path)
        if self.verbose_enable:
            print("player_markers_count: "+str(player_markers_count))
            #this could be huge: print("players:"+str(self.players.keys()))
        players_path = os.path.join(minetestinfo.get_var("primary_world_path"), "players")
        player_count = 0
        player_written_count = 0
        players_moved_count = 0
        players_didntmove_count = 0
        players_saved_count = 0
        for base_path, dirnames, filenames in os.walk(players_path):
            for file_name in filenames:
                file_path = os.path.join(players_path,file_name)
                #print ("  EXAMINING "+file_name)
                #badstart_string = "."
                player_name = None
                player_position = None
                #if (file_name[:len(badstart_string)]!=badstart_string):
                if (file_name[:1]!="."):
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
                                if found_name=="name":
                                    player_name = found_value
                                elif found_name=="position":
                                    player_position = found_value

                                if (player_name is not None) and (player_position is not None):
                                    is_enough_data = True
                                    break
                    ins.close()
                    player_index = None
                    #this_player = None
                    is_changed = False
                    #(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file_path)
                    moved_mtime = time.gmtime()
                    #mtime = time.gmtime(os.path.getmtime(file_path))
                    #NOTE: time.gmtime converts long timestamp to 9-long tuple
                    this_mtime_string = time.strftime(INTERNAL_TIME_FORMAT_STRING, moved_mtime)
                    #mtime = os.path.getmtime(file_path)
                    #this_mtime_string = datetime.strftime(mtime, INTERNAL_TIME_FORMAT_STRING)
                    if file_name in self.players:
                        #this_player = self.players[file_name]
                        if ("utc_mtime" not in self.players[file_name]):
                            #or (self.players[file_name]["utc_mtime"]!=this_mtime_string):
                            if self.verbose_enable:
                                print("no modified time for player '"+file_name+"' so marking for resave.")
                            self.players[file_name]["utc_mtime"] = this_mtime_string
                            is_changed = True
                            #not necessarily moved--even if resaved by server, may not have moved a whole block or at all
                        if "index" in self.players[file_name]:
                            player_index = self.players[file_name]["index"]
                        else:
                            print(min_indent+"WARNING: missing index in yml file for playerid '"+file_name+"' so making a new one.")
                            player_index = self.get_new_player_index()
                            self.players[file_name]["index"] = player_index
                            is_changed = True
                    else:
                        #if self.verbose_enable:
                            #this could be huge: print(file_name+" is not in "+str(self.players.keys()))
                        self.players[file_name] = {}
                        player_index = self.get_new_player_index()
                        print(min_indent+"Creating map entry "+str(player_index)+" for playerid '"+file_name+"'")
                        self.players[file_name]["index"] = player_index
                        self.players[file_name]["playerid"] = file_name
                        self.players[file_name]["utc_mtime"] = this_mtime_string
                        if player_name is not None:
                            self.players[file_name]["name"] = player_name
                        is_changed = True
                    player_dest_path = None
                    if player_index is not None:
                        player_dest_path = os.path.join(self.chunkymap_players_path, str(player_index)+".yml")
                    else:
                        print(min_indent+"ERROR: player_index is still None for '"+file_name+"' (this should never happen), so skipped writing map entry")
                    player_x = None
                    player_y = None
                    player_z = None
                    chunk_x = None
                    chunk_y = None
                    chunk_z = None

                    player_position_tuple = get_tuple_from_notation(player_position, file_name)
                    if player_position_tuple is not None:
                        #Divide by 10 because I don't know why (minetest issue, maybe to avoid float rounding errors upon save/load)
                        player_position_tuple = player_position_tuple[0]/10.0, player_position_tuple[1]/10.0, player_position_tuple[2]/10.0
                        player_x, player_y, player_z = player_position_tuple
                        player_x = float(player_x)
                        player_y = float(player_y)
                        player_z = float(player_z)
                        chunky_x = int((int(player_x)/self.mapvars["chunk_size"]))
                        chunky_y = int((int(player_y)/self.mapvars["chunk_size"]))
                        chunky_z = int((int(player_z)/self.mapvars["chunk_size"]))
                        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
                        self.prepare_chunk_meta(chunky_x, chunky_z)  # DOES load existing yml if exists
                        if not self.chunks[chunk_luid].metadata["is_traversed"]:
                            self.chunks[chunk_luid].metadata["is_traversed"] = True
                            self.save_chunk_meta(chunky_x, chunky_z)

                    #if is_enough_data:
                    #if player_name!="singleplayer":
                    #self.players[file_name] = get_dict_from_conf_file(player_dest_path,":")
                    #map_player_position_tuple = None
                    saved_player_x = None
                    saved_player_y = None
                    saved_player_z = None
                    #map_player_position_tuple = saved_player_x, saved_player_y, saved_player_z
                    is_moved = False
                    if "x" in self.players[file_name].keys():
                        saved_player_x = float(self.players[file_name]["x"])
                        if int(saved_player_x) != int(player_x):
                            is_moved = True
                            if self.verbose_enable:
                                print(min_indent+"x changed for playerid '"+file_name+"' so marking for save.")
                    else:
                        self.players[file_name]["x"] = player_x
                        is_moved = True
                        if self.verbose_enable:
                            print(min_indent+"No x for playerid '"+file_name+"' so marking for save:")
                            print(min_indent+str(self.players[file_name]))
                    if "y" in self.players[file_name].keys():
                        saved_player_y = float(self.players[file_name]["y"])
                        if int(saved_player_y) != int(player_y):
                            is_moved = True
                            if self.verbose_enable:
                                print(min_indent+"y changed for playerid '"+file_name+"' so marking for save.")
                    else:
                        self.players[file_name]["y"] = player_y
                        is_moved = True
                        if self.verbose_enable:
                            print(min_indent+"No y for playerid '"+file_name+"' so marking for save.")
                    if "z" in self.players[file_name].keys():
                        saved_player_z = float(self.players[file_name]["z"])
                        if int(saved_player_z) != int(player_z):
                            is_moved = True
                            if self.verbose_enable:
                                print(min_indent+"z changed for playerid '"+file_name+"' so marking for save.")
                    else:
                        self.players[file_name]["z"] = player_z
                        is_moved = True
                        if self.verbose_enable:
                            print(min_indent+"No z for playerid '"+file_name+"' so marking for save.")
                    if is_moved:
                        if self.verbose_enable:
                            print(min_indent+"Moved so marking as changed")
                        is_changed = True


                    #if (self.players[file_name] is None) or not is_same_fvec3( map_player_position_tuple, player_position_tuple):
                    #if (self.players[file_name] is None) or (saved_player_x is None) or (saved_player_z is None) or (int(saved_player_x)!=int(player_x)) or (int(saved_player_y)!=int(player_y)) or (int(saved_player_z)!=int(player_z)):
                    if is_changed:
                        if self.verbose_enable:
                            print(min_indent+player_name+" changed.")
                        # don't check y since y is elevation in minetest, don't use float since subblock position doesn't matter to map
                        #if self.players[file_name] is not None and saved_player_x is not None and saved_player_y is not None and saved_player_z is not None:
                        if is_moved:
                            #print("PLAYER MOVED: "+str(player_name)+" moved from "+str(map_player_position_tuple)+" to "+str(player_position_tuple))
                            if self.verbose_enable:
                                print(min_indent+"PLAYER MOVED: "+str(player_name)+" moved from "+str(saved_player_x)+","+str(saved_player_y)+","+str(saved_player_z)+" to "+str(player_x)+","+str(player_y)+","+str(player_z))
                            self.last_player_move_mtime_string = this_mtime_string
                            players_moved_count += 1
                            self.players[file_name]["utc_mtime"] = this_mtime_string
                        else:
                            if self.verbose_enable:
                                print(min_indent+"SAVING map entry for player '"+str(player_name)+"'")
                            players_saved_count += 1

                        #set BEFORE saving to prevent unecessary resaving on successive runs:
                        self.players[file_name]["x"] = player_x
                        self.players[file_name]["y"] = player_y
                        self.players[file_name]["z"] = player_z

                        if player_dest_path is not None:
                            if self.verbose_enable:
                                print(min_indent+"saving '"+player_dest_path+"'")
                            save_conf_from_dict(player_dest_path, self.players[file_name], ":", save_nulls_enable=False)
                        else:
                            print(min_indent+"Could not save playerid '"+file_name+"' since generating map entry path failed")


                        #outs = open(player_dest_path, 'w')
                        #outs.write("playerid:"+file_name)
                        #if player_name is not None:
                        #    outs.write("name:"+player_name+"\n")  # python automatically uses correct newline for your os when you put "\n"
                        ##if player_position is not None:
                        ##    outs.write("position:"+player_position+"\n")
                        #if player_x is not None:
                        #    outs.write("x:"+str(player_x)+"\n")
                        #if player_y is not None:
                        #    outs.write("y:"+str(player_y)+"\n")
                        #if player_z is not None:
                        #    outs.write("z:"+str(player_z)+"\n")
                        #outs.write("is_enough_data:"+str(is_enough_data))
                        #outs.close()
                        player_written_count += 1
                    else:
                        if self.verbose_enable:
                            print("DIDN'T MOVE: "+str(player_name))
                        players_didntmove_count += 1
                    player_count += 1
        #if not self.verbose_enable:
        print("PLAYERS:")
        print("  saved: "+str(player_written_count)+" (moved:"+str(players_moved_count)+"; new:"+str(players_saved_count)+")")
        last_move_msg = ""
        if (players_moved_count<1):
            if (self.last_player_move_mtime_string is not None):
                last_move_msg = " (last any moved: "+self.last_player_move_mtime_string+")"
            else:
                last_move_msg = " (none moved since started checking "+self.first_mtime_string+")"
        print("  didn't move: "+str(players_didntmove_count)+last_move_msg)

    def is_chunk_traversed_by_player(self, chunk_luid):
        result = False
        if chunk_luid in self.chunks.keys():
            result = self.chunks[chunk_luid].metadata["is_traversed"]
        return result

    def is_chunk_fresh(self, chunk_luid):
        result = False
        if chunk_luid in self.chunks.keys():
            result = self.chunks[chunk_luid].is_fresh
        return result


    #Returns: (boolean) whether the chunk image is present on dest (rendered now or earlier); else None if database is locked (then re-adds it to self.todo_positions)--only possible if there is chunk data at the given location
    def check_chunk(self, chunky_x, chunky_z):
        min_indent = "  "
        result = [False,""]
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)

        #if (is_different_world):  #instead, see above where all chunk files and player files are deleted
        #    self.remove_chunk(chunky_x, chunky_z)

        is_traversed_by_player = self.is_chunk_traversed_by_player(chunk_luid)  #ok if stale, since is only used for whether empty chunk should be regenerated

        is_render_needed = False

        if not self.is_chunk_fresh(chunk_luid):
            if is_traversed_by_player:
                if self.is_chunk_yaml_marked(chunky_x, chunky_z):
                    if self.is_chunk_yaml_marked_empty(chunky_x, chunky_z):
                        is_render_needed = True
                        result[1] = "RENDERING since nonfresh empty traversed"
                        if self.verbose_enable:
                            print (min_indent+chunk_luid+": "+result[1])
                        #else:
                            #sys.stdout.write('.')
                    else:
                        if self.is_chunk_rendered_on_dest(chunky_x, chunky_z):
                            result[1] = "SKIPPING since RENDERED nonfresh nonempty traversed"
                            if self.verbose_enable:
                                print (min_indent+chunk_luid+": "+result[1])
                        else:
                            is_render_needed = True
                            result[1] = "RENDERING since NONRENDERED nonfresh nonempty traversed"
                            if self.verbose_enable:
                                theoretical_path = self.get_chunk_image_path(chunky_x, chunky_z)
                                print (min_indent+chunk_luid+": "+result[1])
                                print (min_indent+"  {dest_png_path:"+theoretical_path+"}")
                #end if marked
                else:
                    is_render_needed = True
                    result[1] = "RENDERING since nonfresh unmarked traversed"
                    if self.verbose_enable:
                        print (min_indent+chunk_luid+": "+result[1])
                    #else:
                        #sys.stdout.write('.')
            #end if traversed
            else:
                if (self.is_chunk_yaml_marked(chunky_x, chunky_z)):
                    if (self.is_chunk_yaml_marked_empty(chunky_x, chunky_z)):
                        result[1] = "SKIPPING since nonfresh empty nontraversed"
                        if self.verbose_enable:
                            print (min_indent+chunk_luid+": "+result[1])
                    else:
                        if (self.is_chunk_rendered_on_dest(chunky_x, chunky_z)):
                            result[1] = "SKIPPING since RENDERED nonfresh nonempty nontraversed (delete png to re-render)"
                            if self.verbose_enable:
                               print (min_indent+chunk_luid+":"+result[1])
                        else:
                            is_render_needed = True
                            theoretical_path = self.get_chunk_image_path(chunky_x, chunky_z)
                            result[1] = "RENDERING since NONRENDRERED nonfresh nonempty nontraversed"
                            if self.verbose_enable:
                                print (min_indent+chunk_luid+": "+result[1])
                                print (min_indent+"  {dest_png_path:"+theoretical_path+"}")
                else:
                    is_render_needed = True
                    result[1] = "RENDERING since nonfresh unmarked nontraversed"
                    if self.verbose_enable:
                        print (min_indent+chunk_luid+": "+result[1])
                    #else:
                        #sys.stdout.write('.')
        else:
            result[1] = "SKIPPING since RENDERED fresh"
            if self.verbose_enable:
                print (min_indent+chunk_luid+": "+result[1]+" (rendered after starting "+__file__+")")
            #if (not self.is_chunk_yaml_marked(chunky_x, chunky_z)):
                #is_render_needed = True

        # This should never happen since keeping the output of minetestmapper-numpy.py (after analyzing that output) is deprecated:
        #if self.is_genresult_marked(chunk_luid) and not self.is_chunk_yaml_present(chunky_x, chunky_z):
        #    tmp_chunk = MTChunk()
        #    tmp_chunk.luid = chunk_luid
        #    genresult_path = self.get_chunk_genresult_tmp_path(chunky_x, chunky_z)
        #    tmp_chunk.set_from_genresult(genresult_path)
        #    chunk_yaml_path = self.get_chunk_yaml_path(chunky_x, chunky_z)
        #    self.create_chunk_folder(chunky_x, chunky_z)
        #    tmp_chunk.save_yaml(chunk_yaml_path)
        #    print(min_indent+"(saved yaml to '"+chunk_yaml_path+"')")


        if is_render_needed:
            self.rendered_count += 1
            if not self.verbose_enable:
                print(min_indent+chunk_luid+": "+result[1])
            sub_result = self._render_chunk(chunky_x, chunky_z)
            if sub_result is True:
                result[0] = True
            elif sub_result is None:
                result[0] = None
                self.todo_positions.append((chunky_x, chunky_z))  #redo this one
                print("Waiting to retry...")
                time.sleep(.5)

        else:
            if self.is_chunk_rendered_on_dest(chunky_x, chunky_z):
                result[0] = True
                tmp_png_path = self.get_chunk_image_path(chunky_x, chunky_z)
                #NOTE: do NOT set result[1] since specific reason was already set above
                if self.verbose_enable:
                    print(min_indent+chunk_luid+": Skipping existing map tile file " + tmp_png_path + " (delete it to re-render)")
            #elif is_empty_chunk:
                #print("Skipping empty chunk " + chunk_luid)
            #else:
                #print(min_indent+chunk_luid+": Not rendered on dest.")
        return result



    def _check_map_pseudorecursion_branchfrom(self, chunky_x, chunky_z):
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        branched_pos = chunky_x-1, chunky_z
        #only add if not in list already, to prevent infinite re-branching
        if vec2_not_in(branched_pos,self.todo_positions):
            self.todo_positions.append(branched_pos)
        branched_pos = chunky_x+1, chunky_z
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)
        branched_pos = chunky_x, chunky_z-1
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)
        branched_pos = chunky_x, chunky_z+1
        if vec2_not_in(branched_pos, self.todo_positions):
            self.todo_positions.append(branched_pos)

    def check_map_pseudorecursion_iterate(self):  # , redo_empty_enable=False):
        min_indent = ""
        if self.todo_index<0:
            self.check_map_pseudorecursion_start()
            if self.verbose_enable:
                print(min_indent+"(initialized "+str(len(self.todo_positions))+" branche(s))")
        if self.todo_index>=0:
            if self.todo_index<len(self.todo_positions):
                this_pos = self.todo_positions[self.todo_index]
                chunky_x, chunky_z = this_pos
                chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
                prev_rendered_this_session_count = self.rendered_this_session_count
                is_present, reason_string = self.check_chunk(chunky_x, chunky_z)

                if (is_present is None) or is_present:
                    if is_present:
                        self.mapvars["total_generated_count"] += 1
                        if chunky_x<self.mapvars["min_chunkx"]:
                            self.mapvars["min_chunkx"]=chunky_x
                        if chunky_x>self.mapvars["max_chunkx"]:
                            self.mapvars["max_chunkx"]=chunky_x
                        if chunky_z<self.mapvars["min_chunkz"]:
                            self.mapvars["min_chunkz"]=chunky_z
                        if chunky_z>self.mapvars["max_chunkz"]:
                            self.mapvars["max_chunkz"]=chunky_z
                        #end while square outline (1-chunk-thick outline) generated any png files
                        self.save_mapvars_if_changed()
                        prev_len = len(self.todo_positions)
                        self._check_map_pseudorecursion_branchfrom(chunky_x, chunky_z)
                        #must check_decachunk_containing_chunk AFTER _check_map_pseudorecursion_branchfrom so check_decachunk_containing_chunk can see if there are more to do before rendering superchunk
                        #always check since already checks queue and doesn't render decachunk on last rendered chunk, but instead on last queued chunk in decachunk
                        #if self.rendered_this_session_count>prev_rendered_this_session_count or self.force_rerender_decachunks_enable:

                        #Now is ok to check_decachunk_containing_chunk, since does not count current index as unfinished (allow_current_chunk_enable=False):
                        self.check_decachunk_containing_chunk(chunky_x, chunky_z)
                        if self.verbose_enable:
                            print(min_indent+"["+str(self.todo_index)+"] branching from "+str((chunky_x, chunky_z))+" (added "+str(len(self.todo_positions)-prev_len)+")")
                    #else None (database is locked) so let it be retried later
                else:
                    #Now is ok to check_decachunk_containing_chunk, since does not count current index as unfinished (allow_current_chunk_enable=False):
                    self.check_decachunk_containing_chunk(chunky_x, chunky_z)
                    if self.verbose_enable:
                        print(min_indent+"["+str(self.todo_index)+"] not branching from "+str((chunky_x, chunky_z)))
                self.todo_index += 1
                self.check_decachunk_containing_chunk(chunky_x, chunky_z)
            if self.todo_index>=len(self.todo_positions):  # check again since may have branched above, making this untrue
                self.save_mapvars_if_changed()
                self.todo_index = -1
                self.todo_positions = list()  # there seems to be issues where not empty due to delayed garbage collection?
                #while len(self.todo_positions) > 0 : self.todo_positions.pop()
        else:
            if self.verbose_enable:
                print(min_indent+"(no branches)")

    def get_coords_from_luid(self,chunk_luid):
        result = None
        if chunk_luid is not None:
            xopener_index = chunk_luid.find("x")
            zopener_index = chunk_luid.find("z")
            if xopener_index>=0 and zopener_index>xopener_index:
                x_string = chunk_luid[xopener_index+1:zopener_index]
                z_string = chunk_luid[zopener_index+1:]
                try:
                    chunky_x = int(x_string)
                    try:
                        chunky_z = int(z_string)
                        result = chunky_x, chunky_z
                    except:
                        pass
                except:
                    pass
        return result

    def apply_auto_tags_by_worldgen_mods(self, chunky_x, chunky_z):
        chunk_luid = self.get_chunk_luid(chunky_x, chunky_z)
        if chunk_luid not in self.chunks.keys():
            self.prepare_chunk_meta(chunky_x, chunky_z)
        auto_tags_string=""
        existing_tags_string=""
        tags_list = None
        if ("tags" in self.chunks[chunk_luid].metadata) and (self.chunks[chunk_luid].metadata["tags"] is not None):
            existing_tags_string=self.chunks[chunk_luid].metadata["tags"]
            tags_list=existing_tags_string.split(",")
            for index in range(0,len(tags_list)):
                tags_list[index]=tags_list[index].strip()
        else:
            tags_list = list()

        for mod_name in worldgen_mod_list:
            if mod_name in loaded_mod_list:
                if mod_name not in tags_list:
                    tags_list.append(mod_name)
                    is_changed = True

        if is_changed:
            self.chunks[chunk_luid].metadata["tags"] = ','.join(tags_list)
            self.save_chunk_meta(chunky_x, chunky_z)

    def correct_genresults_paths(self):
        count = 0
        folder_path = self.get_chunk_genresults_base_path()
        #for base_path, dirnames, filenames in os.walk(folder_path):
        for file_name in os.listdir(folder_path):
            #for file_name in filenames:
            file_path = os.path.join(folder_path,file_name)
            if os.path.isfile(file_path):
                #print ("  EXAMINING "+file_name)
                #badstart_string = "."
                player_name = None
                player_position = None
                #if (file_name[:len(badstart_string)]!=badstart_string):
                if (file_name[:1]!="."):
                    if len(file_name)>=len(self.genresult_name_opener_string)+4+len(genresult_name_end_flag):
                        chunk_luid = self.get_chunk_luid_from_genresult_name(file_name)
                        coords = self.get_coords_from_luid(chunk_luid)
                        if coords is not None:
                            chunky_x, chunky_z = coords
                            corrected_folder_path = self.get_chunk_genresult_tmp_folder(chunky_x, chunky_z)
                            if not os.path.isdir(corrected_folder_path):
                                print("    creating \""+corrected_folder_path+"\"")
                                os.makedirs(corrected_folder_path)
                            #corrected_file_path = os.path.join(corrected_folder_path, file_name)
                            corrected_file_path = self.get_chunk_genresult_tmp_path(chunky_x, chunky_z)
                            if os.path.isfile(corrected_file_path):
                                os.remove(corrected_file_path)
                            try:
                                os.rename(file_path, corrected_file_path)
                            except:
                                #TODO: why does this happen (file does not exist)???
                                print("    Could not finish moving \""+file_path+"\" to \""+corrected_file_path+"\"")

                            count += 1
                        else:
                            print("WARNING: found unusable genresults file '"+file_name+"' in ")
        if count>0:
            print("")
            print("MOVED "+str(count)+" genresult file(s)")
            print("")
            print("")

    def get_cross_coords_list(x_int, y_int, restrict_to_decachunk_enable=False):
        results = None
        if x_int is not None and y_int is not None:
            tmp = list()
            # North, East, South, West (cartesian):
            tmp.append((x_int,y_int+1))
            tmp.append((x_int+1,y_int))
            tmp.append((x_int,y_int-1))
            tmp.append((x_int-1,y_int))
            if restrict_to_decachunk_enable:
                results = list()
                starting_decachunk_luid = self.get_decachunk_luid_from_chunk(x_int, y_int)
                for result in tmp:
                    this_x, this_y = result
                    if self.get_decachunk_luid_from_chunk(this_x, this_y) == starting_decachunk_luid:
                        results.append(result)
            else:
                results = tmp
        return results

    def get_outline_coords_list(self, x_int, y_int, restrict_to_decachunk_enable=False):
        results = None
        if x_int is not None and y_int is not None:
            tmp = list()
            # North, NE, East, SE, South, SW, West, NW (cartesian):
            tmp.append((x_int,y_int+1))  # N
            tmp.append((x_int+1,y_int+1))  # NE
            tmp.append((x_int+1,y_int))  # E
            tmp.append((x_int+1,y_int-1))  # SE
            tmp.append((x_int,y_int-1)) # S
            tmp.append((x_int-1,y_int-1)) # SW
            tmp.append((x_int-1,y_int)) # W
            tmp.append((x_int-1,y_int+1)) # NW
            if restrict_to_decachunk_enable:
                results = list()
                starting_decachunk_luid = self.get_decachunk_luid_from_chunk(x_int, y_int)
                for result in tmp:
                    this_x, this_y = result
                    if self.get_decachunk_luid_from_chunk(this_x, this_y) == starting_decachunk_luid:
                        results.append(result)
            else:
                results = tmp
        return results

    def is_worldborder_count_gt_or_eq(chunky_coords_list, min_count):
        result = False
        count = 0
        for chunky_pos in chunky_coords_list:
            if is_worldborder_chunk(chunky_pos[0], chunky_pos[1]):
                count += 1
                if count >= min_count:
                    result = True
                    break
        return result


    def is_nonworldborder_isrendered_count_gt_or_eq(chunky_coords_list, min_count):
        result = False
        count = 0
        if chunky_coords_list is not None:
            for chunky_pos in chunky_coords_list:
                chunky_x, chunky_z = chunky_pos
                if is_chunk_rendered_on_dest(chunky_x, chunky_z) and not is_worldborder_chunk(chunky_x, chunky_z):
                    count += 1
                    if count >= min_count:
                        result = True
                        break
        return result

    def check_map_pseudorecursion_start(self):
        if self.todo_positions is not None and self.todo_index>=len(self.todo_positions):
            print("WARNING in check_map_pseudorecursion_start: todo index was ["+str(self.todo_index)+"] in "+str(len(self.todo_positions))+"-length list, so resetting todo_list")
            self.todo_index = -1
        if self.todo_index<0:
            print("PROCESSING MAP DATA (BRANCH PATTERN)")
            if os.path.isfile(self.minetestmapper_py_path) and os.path.isfile(self.colors_path):
                self.rendered_count = 0
                #self.todo_positions = list()  # there seems to be issues where not empty due to delayed garbage collection
                while len(self.todo_positions) > 0 : self.todo_positions.pop()
                self.todo_positions.append((0,0))
                #self.mapvars = get_dict_from_conf_file(self.world_yaml_path,":")
                self.verify_correct_map()
                decachunk_luid_list = list()
                if self.preload_all_enable:
                    self.preload_all_enable = False
                    self.correct_genresults_paths()
                    minlen=len(self.chunk_yaml_name_opener_string)+4+len(self.chunk_yaml_name_dotext_string)  # +4 for luid, such as x1z2 (ok since just a minimum)
                    #for base_path, dirnames, filenames in os.walk(self.data_16px_path):
                        #for dirname in dirnames:
                    #for decachunk_x_basepath, decachunk_x_dirnames, decachunk_x_filenames in os.walk(self.data_16px_path):
                    for decachunk_x_name in os.listdir(self.data_16px_path):
                        decachunk_x_path = os.path.join(self.data_16px_path, decachunk_x_name)
                        #for decachunk_z_basepath, decachunk_z_dirnames, decachunk_z_filenames in os.walk(decachunk_x_dirnames):
                        if decachunk_x_name[:1]!="." and os.path.isdir(decachunk_x_path):
                            for decachunk_z_name in os.listdir(decachunk_x_path):
                                decachunk_z_path = os.path.join(decachunk_x_path, decachunk_z_name)
                                if decachunk_z_name[:1]!="." and os.path.isdir(decachunk_z_path):
                                    #for chunk_filename in decachunk_z_filenames:
                                    for chunk_filename in os.listdir(decachunk_z_path):
                                        chunk_path = os.path.join(decachunk_z_path, chunk_filename)
                                        #file_path = os.path.join(self.chunkymap_thisworld_data_path,file_name)
                                        if chunk_filename[:1]!="." and os.path.isfile(chunk_path):
                                            #print ("  EXAMINING "+file_name)
                                            #badstart_string = "."
                                            #if (file_name[:len(badstart_string)]!=badstart_string):
                                            if len(chunk_filename) > minlen:
                                                chunk_luid = self.get_chunk_luid_from_yaml_name(chunk_filename)
                                                coords = self.get_coords_from_luid(chunk_luid)
                                                if coords is not None:
                                                    chunky_x, chunky_z = coords
                                                    decachunk_luid = self.get_decachunk_luid_from_chunk(chunky_x, chunky_z)
                                                    if decachunk_luid not in decachunk_luid_list:
                                                        decachunk_luid_list.append(decachunk_luid)
                                                    if "chunk_size" not in self.mapvars:
                                                        print("ERROR: '"+chunk_luid+"' has missing mapvars among {"+str(self.mapvars)+"}")
                                                        break
                                                    print("Checking chunk "+str(coords)+" *"+str(self.mapvars["chunk_size"])+"")
                                                    self.prepare_chunk_meta(chunky_x, chunky_z)

                                                    #if ("tags" not in self.chunks[chunk_luid].metadata):
                                                        #self.chunks[chunk_luid].metadata["tags"] = "moreores,caverealms"
                                                        #self.save_chunk_meta(chunky_x, chunky_z)
                                                        #print("  saved tags to '"+chunk_path+"'")
                    for decachunk_luid in decachunk_luid_list:
                        coords = self.get_coords_from_luid(decachunk_luid)
                        if coords is not None:
                            decachunky_x, decachunky_z = coords
                            chunky_x = self.get_chunky_coord_from_decachunky_coord(decachunky_x)
                            chunky_z = self.get_chunky_coord_from_decachunky_coord(decachunky_z)
                            if not os.path.isfile(self.get_decachunk_image_path_from_chunk(chunky_x, chunky_z)):
                                print("Checking decachunk "+str(decachunky_x)+","+str(decachunky_z))
                                self.check_decachunk_containing_chunk(chunky_x, chunky_z)
                        else:
                            print("ERROR: could not get coords from decachunk luid "+decachunk_luid)
                for chunk_luid in self.chunks.keys():
                    coords = self.get_coords_from_luid(chunk_luid)
                    if coords is not None:
                        chunky_x, chunky_z = coords
                        if self.chunks[chunk_luid].metadata["is_traversed"] and not self.is_chunk_rendered_on_dest(chunky_x, chunky_z):
                            if self.chunks[chunk_luid].metadata["is_empty"]:
                                self.chunks[chunk_luid].metadata["is_empty"] = False
                                self.save_chunk_meta(chunky_x, chunky_z)
                            #if coords is not None:
                            self.todo_positions.append(coords)
                            #ins = open(file_path, 'r')
                            #line = True
                            #while line:
                                #line = ins.readline()
                                #if line:
                            #ins.close()
                    else:
                        print("ERROR: could not get coords from luid '"+chunk_luid+"'")
                self.todo_index = 0
                #while (todo_index<len(self.todo_positions)):
                self.verify_correct_map()

    def verify_correct_map(self):
        #NOTE: NO LONGER NEEDED since each world has its own folder in chunkymapdata/worlds folder
        pass
        #if os.path.isfile(self.minetestmapper_py_path) and os.path.isfile(self.colors_path):
            #if self.mapvars is not None and set(['world_name']).issubset(self.mapvars):
                ##if self.verbose_enable:
                ##    print ("  (FOUND self.config["world_name"])")
                #if self.config["world_name"] != self.config["world_name"]:
                    #print("")
                    #print("")
                    #print("")
                    #print("")
                    #print("")
                    #print ("Removing ALL map data since from WORLD NAME is different (map '"+str(self.config["world_name"])+"' is not '"+str(self.config["world_name"])+"')...")
                    #print("")
                    #if os.path.isdir(self.chunkymap_thisworld_data_path):
                        #for base_path, dirnames, filenames in os.walk(self.chunkymap_thisworld_data_path):
                            #for file_name in filenames:
                                #if file_name[0] != ".":
                                    #file_path = os.path.join(self.chunkymap_thisworld_data_path,file_name)
                                    #if self.verbose_enable:
                                        #print ("  EXAMINING "+file_name)
                                    #badstart_string = "chunk"
                                    #if (len(file_name) >= len(badstart_string)) and (file_name[:len(badstart_string)]==badstart_string):
                                        #os.remove(file_path)
                                    #elif file_name==self.yaml_name:
                                        #os.remove(file_path)
                    #players_path = os.path.join(self.chunkymap_thisworld_data_path, "players")
                    #if os.path.isdir(players_path):
                        #for base_path, dirnames, filenames in os.walk(players_path):
                            #for file_name in filenames:
                                #if file_name[0] != ".":
                                    #file_path = os.path.join(self.chunkymap_thisworld_data_path,file_name)
                                    #if self.verbose_enable:
                                        #print ("  EXAMINING "+file_name)
                                    #badend_string = ".yml"
                                    #if (len(file_name) >= len(badend_string)) and (file_name[len(file_name)-len(badend_string):]==badend_string):
                                        #os.remove(file_path)
                    #self.mapvars["min_chunkx"]=0
                    #self.mapvars["max_chunkx"]=0
                    #self.mapvars["min_chunkz"]=0
                    #self.mapvars["max_chunkz"]=0
                    #self.save_mapvars_if_changed()
                    ##do not neet to run self.save_mapvars_if_changed() since already removed the yml

    def save_mapvars_if_changed(self):
        is_changed = False
        #is_different_world = False
        if self.saved_mapvars is None:
            print ("SAVING '" + self.world_yaml_path + "' since nothing was loaded or it did not exist")
            is_changed = True
        else:
            for this_key in self.mapvars:
                if this_key != "total_generated_count":  # don't care if generated count changed since may have been regenerated
                    if (this_key not in self.saved_mapvars.keys()):
                        is_changed = True
                        print ("SAVING '" + self.world_yaml_path + "' since " + str(this_key) + " not in saved_mapvars")
                        break
                    elif (str(self.saved_mapvars[this_key]) != str(self.mapvars[this_key])):
                        is_changed = True
                        print ("SAVING '" + self.world_yaml_path + "' since new " + this_key + " value " + str(self.mapvars[this_key]) + " not same as saved value " + str(self.saved_mapvars[this_key]) + "")
                        break
        if is_changed:
            save_conf_from_dict(self.world_yaml_path,self.mapvars,":")
            self.saved_mapvars = get_dict_from_conf_file(self.world_yaml_path,":")
            #self.mapvars = get_dict_from_conf_file(self.world_yaml_path,":")
        else:
            if self.verbose_enable:
                print ("  (Not saving '"+self.world_yaml_path+"' since same value of each current variable is already in file as loaded)")

    def check_map_inefficient_squarepattern(self):
        if os.path.isfile(self.minetestmapper_py_path) and os.path.isfile(self.colors_path):
            self.rendered_count = 0


            self.mapvars = get_dict_from_conf_file(self.world_yaml_path,":")


            self.verify_correct_map()

            self.mapvars["min_chunkx"] = 0
            self.mapvars["min_chunkz"] = 0
            self.mapvars["max_chunkx"] = 0
            self.mapvars["max_chunkz"] = 0
            if self.saved_mapvars is not None:
                if "min_chunkx" in self.saved_mapvars.keys():
                    self.mapvars["min_chunkx"] = self.saved_mapvars["min_chunkx"]
                if "max_chunkx" in self.saved_mapvars.keys():
                    self.mapvars["max_chunkx"] = self.saved_mapvars["max_chunkx"]
                if "min_chunkz" in self.saved_mapvars.keys():
                    self.mapvars["min_chunkz"] = self.saved_mapvars["min_chunkz"]
                if "max_chunkz" in self.saved_mapvars.keys():
                    self.mapvars["max_chunkz"] = self.saved_mapvars["max_chunkz"]

            self.mapvars["total_generated_count"] = 0

            newchunk_luid_list = list()
            this_iteration_generates_count = 1
            #if str(self.config["world_name"]) != str(self.config["world_name"]):
            #    is_different_world = True
            #    print("FULL RENDER since chosen world name '"+self.config["world_name"]+"' does not match previously rendered world name '"+self.config["world_name"]+"'")
            print("PROCESSING MAP DATA (SQUARE)")
            while this_iteration_generates_count > 0:
                this_iteration_generates_count = 0
                self.read_then_remove_signals()
                if not self.refresh_map_enable:
                    break
                for chunky_z in range (self.mapvars["min_chunkz"],self.mapvars["max_chunkz"]+1):
                    self.read_then_remove_signals()
                    if not self.refresh_map_enable:
                        break
                    for chunky_x in range(self.mapvars["min_chunkx"],self.mapvars["max_chunkx"]+1):
                        self.read_then_remove_signals()
                        if not self.refresh_map_enable:
                            break
                        #python ~/minetest/util/minetestmapper-numpy.py --region -1200 800 -1200 800 --drawscale --maxheight 100 --minheight -50 --pixelspernode 1 ~/.minetest/worlds/FCAGameAWorld ~/map.png
                        #sudo mv ~/map.png /var/www/html/minetest/images/map.png

                        #only generate the edges (since started with region 0 0 0 0) and expanding from there until no png is created:
                        is_outline = (chunky_x==self.mapvars["min_chunkx"]) or (chunky_x==self.mapvars["max_chunkx"]) or (chunky_z==self.mapvars["min_chunkz"]) or (chunky_z==self.mapvars["max_chunkz"])
                        if is_outline:
                            is_present, reason_string = self.check_chunk(chunky_x, chunky_z)
                            if is_present:
                                this_iteration_generates_count += 1
                                self.mapvars["total_generated_count"] += 1
                    if self.verbose_enable:
                        print ("")  # blank line before next chunky_z so output is more readable
                self.mapvars["min_chunkx"] -= 1
                self.mapvars["min_chunkz"] -= 1
                self.mapvars["max_chunkx"] += 1
                self.mapvars["max_chunkz"] += 1
            #end while square outline (1-chunk-thick outline) generated any png files
            self.save_mapvars_if_changed()
            if not self.verbose_enable:
                print("  rendered: "+str(self.rendered_count)+" (only checks for new chunks)")
        else:
            print ("MAP ERROR: failed since this folder must contain colors.txt and minetestmapper-numpy.py")

    def read_then_remove_signals(self):
        signal_path = self.get_signal_path()
        if os.path.isfile(signal_path):
            signals = get_dict_from_conf_file(signal_path,":")
            if signals is not None:
                print("ANALYZING "+str(len(signals))+" signal(s)")
                for this_key in signals.keys():
                    is_signal_ok = True
                    if this_key=="loop_enable":
                        if not signals[this_key]:
                            self.loop_enable = False
                        else:
                            is_signal_ok = False
                            print("WARNING: Got signal to change loop_enable to True, so doing nothing")
                    elif this_key=="refresh_players_enable":
                        if type(signals[this_key]) is bool:
                            self.refresh_players_enable = signals[this_key]
                        else:
                            is_signal_ok = False
                            print("ERROR: expected bool for "+this_key)
                    elif this_key=="refresh_map_seconds":
                        if (type(signals[this_key]) is float) or (type(signals[this_key]) is int):
                            if float(signals[this_key])>=1.0:
                                self.refresh_map_seconds = float(signals[this_key])
                            else:
                                is_signal_ok = False
                                print("ERROR: expected >=1 seconds for refresh_map_seconds (int or float)")
                        else:
                            is_signal_ok = False
                            print("ERROR: expected int for "+this_key)
                    elif this_key=="refresh_players_seconds":
                        if (type(signals[this_key]) is float) or (type(signals[this_key]) is int):
                            if float(signals[this_key])>=1.0:
                                self.refresh_players_seconds = float(signals[this_key])
                            else:
                                print("ERROR: expected >=1 seconds for refresh_players_seconds (int or float)")
                        else:
                            is_signal_ok = False
                            print("ERROR: expected int for "+this_key)
                    elif this_key=="recheck_rendered":
                        if type(signals[this_key]) is bool:
                            if signals[this_key]:
                                for chunk_luid in self.chunks.keys():
                                    self.chunks[chunk_luid].is_fresh = False
                        else:
                            is_signal_ok = False
                            print("ERROR: expected bool for "+this_key)
                    elif this_key=="refresh_map_enable":
                        if type(signals[this_key]) is bool:
                            self.refresh_map_enable = signals[this_key]
                        else:
                            is_signal_ok = False
                            print("ERROR: expected bool for "+this_key)
                    elif this_key=="verbose_enable":
                        if type(signals[this_key]) is bool:
                            self.verbose_enable = signals[this_key]
                            self.is_verbose_explicit = self.verbose_enable
                        else:
                            is_signal_ok = False
                            print("ERROR: expected true or false after colon for "+this_key)

                    else:
                        is_signal_ok = False
                        print("ERROR: unknown signal '"+this_key+"'")
                    if is_signal_ok:
                        print("RECEIVED SIGNAL "+str(this_key)+":"+str(signals[this_key]))
            else:
                print("WARNING: blank '"+signal_path+"'")
            try:
                os.remove(signal_path)
            except:
                print("ERROR: "+__file__+" must have permission to remove '"+signal_path+"'. Commands will be repeated unless command was loop_enable:false.")  # so exiting to avoid inability to avoid repeating commands at next launch.")
                #self.loop_enable = False

    def run_loop(self):
        #self.last_run_second = best_timer()
        self.loop_enable = True
        if not self.is_verbose_explicit:
            self.verbose_enable = False
        is_first_iteration = True
        while self.loop_enable:
            before_second = best_timer()
            run_wait_seconds = self.refresh_map_seconds
            if self.refresh_players_seconds < run_wait_seconds:
                run_wait_seconds = self.refresh_players_seconds
            print("")
            print("Ran "+str(self.run_count)+" time(s) for "+self.world_name)
            self.read_then_remove_signals()
            if self.loop_enable:
                if self.refresh_players_enable:
                    if self.last_players_refresh_second is None or (best_timer()-self.last_players_refresh_second > self.refresh_players_seconds ):
                        #if self.last_players_refresh_second is not None:
                            #print ("waited "+str(best_timer()-self.last_players_refresh_second)+"s for map update")
                        self.last_players_refresh_second = best_timer()
                        self.check_players()
                    else:
                        print("waiting before doing player update")
                else:
                    print("player update is not enabled")
                if self.refresh_map_enable:
                    is_first_run = True
                    map_render_latency = 0.3
                    is_done_iterating = self.todo_index<0
                    if (not is_first_iteration) or (self.last_map_refresh_second is None) or (best_timer()-self.last_map_refresh_second > self.refresh_map_seconds) or (not is_done_iterating):
                        while is_first_run or ( ((best_timer()+map_render_latency)-self.last_players_refresh_second) < self.refresh_players_seconds ):
                            self.read_then_remove_signals()
                            if not self.refresh_map_enable:
                                break
                            is_first_run = False
                            is_first_iteration = self.todo_index<0
                            #if (self.last_map_refresh_second is None) or (best_timer()-self.last_map_refresh_second > self.refresh_map_seconds):
                            #if self.last_map_refresh_second is not None:
                                #print ("waited "+str(best_timer()-self.last_map_refresh_second)+"s for map update")
                            self.last_map_refresh_second = best_timer()
                            self.check_map_pseudorecursion_iterate()
                            if self.todo_index<0:  # if done iterating
                                break
                            map_render_latency = best_timer() - self.last_map_refresh_second
                            #self.check_map_inefficient_squarepattern()
                    else:
                        print("waiting before doing map update")
                else:
                    print("map update is not enabled")
                run_wait_seconds -= (best_timer()-before_second)
                is_done_iterating = self.todo_index<0
                if ( (float(run_wait_seconds)>0.0) and (is_done_iterating)):
                    print ("sleeping for "+str(run_wait_seconds)+"s")
                    time.sleep(run_wait_seconds)
                self.run_count += 1
            else:
                self.verbose_enable = True

    def run(self):
        if self.refresh_players_enable:
            self.check_players()
        if self.refresh_map_enable:
            self.check_map_inefficient_squarepattern()
            #self.check_map_pseudorecursion_iterate()

if __name__ == '__main__':
    mtchunks = MTChunks()
    signal_path = mtchunks.get_signal_path()
    stop_line = "loop_enable:False"
    parser = argparse.ArgumentParser(description='A mapper for minetest')
    parser.add_argument('--skip-map', type = bool, metavar = ('skip_map'), default = False, help = 'draw map tiles and save YAML files for chunkymap.php to use')
    parser.add_argument('--skip-players', type = bool, metavar = ('skip_players'), default = False, help = 'update player YAML files for chunkymap.php to use')
    parser.add_argument('--no-loop', type = bool, metavar = ('no_loop'), default = False, help = 'keep running until "'+signal_path+'" contains the line '+stop_line)
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
