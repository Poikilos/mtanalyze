#!/usr/bin/env python
'''
Execute this script to create a single image (though size is limited
by technical reasons) of the largest possible region of the Minetest
world selected using configuration files generated by minetestinfo.py
'''
# TODO: info files generated by minetestinfo.py are deprecated
from __future__ import print_function

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

import subprocess
import os
import sys
# import stat
import shutil
import platform

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
    echo0,
    echo1,
    echo2,
    genresult_name_end_flag,
    gen_error_name_end_flag,
)

from mtanalyze.minetestoffline import (
    WorldInfo,
)

# python_exe_path is from:
from pythoninfo import *
try:
    from PIL import Image  # ImageDraw, ImageFont, ImageColor
except ImportError as ex:
    print(str(ex))
    print(PIL_DEP_MSG)
    sys.exit(1)
except ModuleNotFoundError as ex:
    print(str(ex))
    print(PIL_DEP_MSG)
    sys.exit(1)

from chunkymaprenderer import ChunkymapRenderer
no_leveldb_msg = """
To fix this error, try:
  Ubuntu (tested on Trusty to Zesty):
    apt install python-leveldb  # python2 version
  Arch-based distros:
    sudo pacman -Syu --noconfirm yaourt
    yaourt -Syu --noconfirm --aur python2-leveldb
"""


class ChunkymapOfflineRenderer(ChunkymapRenderer):

    # minetestmapper_numpy_path = None
    # mtm_custom_path = None
    # mtm_py_path = None
    # mtm_bin_path = None
    # backend_string = None
    # world_path = None
    # world_name = None
    # boundary_x_min = None
    # boundary_x_max = None
    # boundary_z_min = None
    # boundary_z_max = None
    # mtm_bin_enable = None
    # mtm_bin_dir_path = None

    def __init__(self, world_path):
        if world_path is None:
            raise ValueError("You must provide a world_path.")
        # limit to 8192x8192 for browsers to be able to load it
        # NOTE: a 16464x16384 or 12288x12288 image fails to load in
        # browser, but 6112x6592 works
        # 6144*2 = 12288
        self.boundary_x_min = -4096  # formerly -10000
        self.boundary_x_max = 4096  # formerly 10000
        self.boundary_z_min = -4096  # formerly -10000
        self.boundary_z_max = 4096  # formerly 10000
        self.mtm_bin_enable = False
        # ^ set below automatically if present

        # self.world_path = get_required(
        #     "primary_world_path",
        #     caller_name="ChunkymapOfflineRenderer",
        # )
        self.world_path = world_path
        self.world = WorldInfo(world_path)
        self.backend_string = self.world.get_mt("backend")
        if self.backend_string is not None:
            self.backend_string = self.backend_string.strip()
            if len(self.backend_string) == 0:
                self.backend_string = None
        if self.backend_string is None:
            raise ValueError('"{}" does not set: backend'
                             ''.format(self.world.mt_path))
        self.prepare_env()  # from super


        if not os.path.isdir(self.world_path):
            print("ERROR: missing world '" + self.world_path
                  + "', so exiting " + __file__ + ".")
            sys.exit(2)
        else:
            self.world_name = os.path.basename(self.world_path)

    def RenderSingleImage(self):
        dest_colors_path = os.path.join(self.mtm_bin_dir_path,
                                        "colors.txt")

        genresults_folder_path = os.path.join(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "chunkymap-genresults"
            ),
            self.world_name
        )
        if not os.path.isdir(genresults_folder_path):
            os.makedirs(genresults_folder_path)
        genresult_path = os.path.join(
            genresults_folder_path,
            "singleimage"+genresult_name_end_flag
        )
        gen_error_path = os.path.join(
            genresults_folder_path,
            "singleimage"+gen_error_name_end_flag
        )
        cmd_suffix = " 1> \"" + genresult_path + "\""
        cmd_suffix += " 2> \"" + gen_error_path + "\""
        # if self.boundary_x_min is None:
        #     print("ERROR: boundary_x_min is None")
        # if self.boundary_x_max is None:
        #     print("ERROR: boundary_x_max is None")
        # if self.boundary_z_min is None:
        #     print("ERROR: boundary_z_min is None")
        # if self.boundary_z_max is None:
        #     print("ERROR: boundary_z_max is None")
        geometry_string = (
            str(self.boundary_x_min) + ":" + str(self.boundary_z_min)
            + "+" + str(self.boundary_x_max-self.boundary_x_min) + "+"
            + str(self.boundary_z_max-self.boundary_z_min)
        )
        # ^ "-10000:-10000+20000+20000" #2nd two params are sizes
        # VERY BIG since singleimage mode (if no geometry param,
        # minetestmapper-numpy reverts to its default which is
        # -2000 2000 -2000 2000):
        region_string = (
            str(self.boundary_x_min) + " " + str(self.boundary_x_max)
            + " " + str(self.boundary_z_min) + " "
            + str(self.boundary_z_max)
        )
        # ^ "-10000 10000 -10000 10000"

        # geometry_string = (
        #     str(min_x) + ":"+str(min_z) + "+"
        #     + str(int(max_x)-int(min_x)+1) + "+"
        #     + str(int(max_z)-int(min_z)+1)
        # )
        # ^ +1 since max-min is exclusive and width must be inclusive
        #   for old minetestmapper.py
        region_param = " --region " + region_string
        # ^ minetestmapper-numpy.py --region xmin xmax zmin zmax
        geometry_param = " --geometry " + geometry_string
        # ^ " --geometry -10000:-10000+20000+20000"
        # ^^ minetestmapper-python/minetestmapper.py --geometry
        #    <xmin>:<zmin>+<width>+<height>
        limit_param = geometry_param
        # region_string = (str(min_x) + ":" + str(max_x) + ","
        #                           + str(min_z) + ":" + str(max_z))

        # cmd_no_out_string = (
        #     python_exe_path + " " + self.mtm_py_path
        #     + " --bgcolor '" + self.FLAG_EMPTY_HEXCOLOR
        #     + "' --input \""
        #     + str(get_required("primary_world_path",
        #                        caller_name="RenderSingleImage"))
        #     + "\" --geometry " + geometry_string + " --output \""
        #     + tmp_png_path + "\""
        # )
        png_name = "singleimage.png"

        tmp_png_path = os.path.join(genresults_folder_path, png_name)
        squote = ""
        # ^ leave blank for windows, since doesn't process it out
        if "windows" not in platform.system().lower():
            squote = "'"
        io_string = (" --input \"" + self.world_path + "\" --output \""
                     + tmp_png_path + "\"")
        if ((not self.mtm_bin_enable) and
                ("numpy" in self.mtm_py_path)):
            limit_param = region_param
            io_string = (" -i \"" + self.world_path + "\" -o \""
                         + tmp_png_path + "\"")
            # FIXME: Why was -i and -o implicit before?
            # geometry_param = " --region " + str(min_x) + " "
            #   + str(max_x) + " " + str(min_z) + " " + str(max_z)
            # print("Using numpy style parameters.")
            # print("  since using "+self.mtm_py_path)
            # print()
        this_colors_path = dest_colors_path
        if (os.path.isfile(self.colors_path) and
                not os.path.isfile(dest_colors_path)):
            this_colors_path = self.colors_path
        if self.mtm_bin_enable:
            cmd_no_out_string = (self.mtm_bin_path
                                 + " --colors " + this_colors_path
                                 + " --bgcolor " + squote
                                 + FLAG_EMPTY_HEXCOLOR + squote
                                 + io_string + limit_param)
        else:
            cmd_no_out_string = (get_python2_exe_path() + " "
                                 + self.mtm_py_path
                                 + " --bgcolor " + squote
                                 + FLAG_EMPTY_HEXCOLOR + squote
                                 + io_string + limit_param)
        cmd_string = cmd_no_out_string + cmd_suffix
        print("")
        print("")
        print("Running")
        print("    "+cmd_string)
        if self.mtm_bin_enable:
            # if (os.path.isfile(self.colors_path) and
            #         not os.path.isfile(dest_colors_path)):
            #     print("Copying...'" + self.colors_path + "' to  '"
            #           + dest_colors_path + "'")
            #     shutil.copyfile(self.colors_path, dest_colors_path)
            print("  mapper_path: " + self.mtm_bin_path)
        else:
            print("  mapper_path: " + self.mtm_py_path)
        print("  colors_path: "+self.colors_path)
        print("  backend: " + self.backend_string)
        print("    # (this may take a while...)")
        if os.path.isfile(tmp_png_path):
            os.remove(tmp_png_path)
        # subprocess.call("touch \"" + tmp_png_path + "\"", shell=True)
        subprocess.call(cmd_string, shell=True)
        final_png_path = tmp_png_path
        www_uid = None
        www_gid = None
        www_minetest_path = get_required("www_minetest_path",
                                         caller_name="RenderSingleImage")
        www_chunkymapdata_path = os.path.join(
            www_minetest_path,
            "chunkymapdata"
        )
        www_chunkymapdata_worlds_path = os.path.join(
            www_chunkymapdata_path,
            "worlds"
        )
        www_chunkymapdata_world_path = os.path.join(
            www_chunkymapdata_worlds_path,
            self.world_name
        )
        try:
            www_minetest_path = get_required("www_minetest_path",
                                             caller_name="RenderSingleImage")
            www_stat = os.stat(
                www_minetest_path
            )
            www_uid = www_stat.st_uid
            www_gid = www_stat.st_gid
            # import pwd
            # www_u_name = pwd.getpwuid(uid)[0]
            # www_g_name = pwd.getgrgid(gid)[0]
            # import pwd
            # import grp
            # www_uid = pwd.getpwnam("www_data").pw_uid
            # www_gid = grp.getgrnam("nogroup").gr_gid
        except PermissionError as ex:
            # echo0(str(ex))
            echo0("Unable to get stat on www directory \"{}\","
                  " so will not be able to automatically set owner"
                  " of result jpg there. Make sure you manually set"
                  " owner of singleimage.jpg in '{}"
                  "' to www-data user and group."
                  "".format(mti.get("www_minetest_path"),
                            www_chunkymapdata_world_path))
            echo0("  " + str(sys.exc_info()))

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
        if os.path.isfile(tmp_png_path):
            if not os.path.isdir(www_chunkymapdata_world_path):
                os.makedirs(www_chunkymapdata_world_path)
            if mti.contains("www_minetest_path"):
                dest_png_path = os.path.join(
                    www_chunkymapdata_world_path,
                    png_name
                )
                if os.path.isfile(dest_png_path):
                    os.remove(dest_png_path)
                print("Moving temp image from " + tmp_png_path + " to "
                      + dest_png_path + "...")

                # move_cmd_string = "mv"
                # if "windows" in platform.system().lower():
                #     move_cmd_string= "move"
                # this_move_cmd_string = (move_cmd_string + " \""
                #                         + tmp_png_path + "\" to \""
                #                         + dest_png_path + "\"...")
                # subprocess.call(this_move_cmd_string, shell=True)
                shutil.move(tmp_png_path, dest_png_path)

                final_png_path = dest_png_path
            print("Png image saved to:")
            print("  "+final_png_path)
            print("Converting to jpg...")
            pngim = Image.open(final_png_path)
            # jpgim = Image.new('RGB', pngim.size, (0, 0, 0))
            # jpgim.paste(pngim.convert("RGB"),
            #             (0,0,pngim.size[0],pngim.size[0]))
            jpg_name = "singleimage.jpg"
            dest_jpg_path = os.path.join(www_chunkymapdata_world_path,
                                         jpg_name)
            if os.path.isfile(dest_jpg_path):
                os.remove(dest_jpg_path)
                if not os.path.isfile(dest_jpg_path):
                    print("  removed old '"+dest_jpg_path+"'")
                else:
                    print("  failed to remove'"+dest_jpg_path+"'")
            # jpgim.save(dest_jpg_path)
            pngim.save(dest_jpg_path, 'JPEG')
            if os.path.isfile(dest_jpg_path):
                print("jpg image saved to:")
                print("  "+dest_jpg_path)
                if www_gid is not None:
                    os.chown(dest_jpg_path, www_uid, www_gid)
                    print("changed owner to same as www folder")
                os.remove(final_png_path)
                print("removed temporary file "+final_png_path)
            else:
                print("Could not write '"+dest_jpg_path+"'")
            if os.path.isfile(genresult_path):
                print("Results:")
                print("  "+genresult_path)
                mtchunk = MTChunk()
                mtchunk.set_from_genresult(genresult_path)
                mtchunk.metadata["is_traversed"] = True
                dest_yaml_name = "singleimage.yml"
                dest_yaml_path = os.path.join(
                    www_chunkymapdata_world_path,
                    dest_yaml_name
                )
                mtchunk.save_yaml(dest_yaml_path)
        else:
            print('No image could be generated from "{}"'
                  ''.format(self.world_path))
            if is_locked:
                print("(database is locked--shutdown server first or"
                      " try generator.py to render chunks"
                      " individually).")
            elif os.path.isfile(gen_error_path):
                # ins = open(genresult_path, 'r')
                ins = open(gen_error_path, 'r')
                line = True
                while line:
                    line = ins.readline()
                    if line:
                        print("  " + line.strip())
                        if "No module named leveldb" in line:
                            print(no_leveldb_msg)
                ins.close()
            else:
                echo0("* and there is no {}".format(gen_error_path))


def main():
    cmor = ChunkymapOfflineRenderer(
        get_required("world", caller_name="singleimage")
    )
    cmor.RenderSingleImage()
    return 0


if __name__ == "__main__":
    sys.exit(main())
