#!/usr/bin/env python
from __future__ import print_function

import os
import sys

me = 'u_skin_adder.py'

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

from mtanalyze import (  # formerly: from minetestinfo import *
    mti,
    get_required,
    FLAG_EMPTY_HEXCOLOR,
    PIL_DEP_MSG,
    PYCODETOOL_DEP_MSG,
    PCT_REPO_PATH,
    HOME_PATH,
) # paths and FLAG_EMPTY_HEXCOLOR = "#010000"

from find_pycodetool import pycodetool
# ^ works for submodules since changes sys.path

from pycodetool.parsing import *

# TODO: (?) from mtanalyze.minetestoffline import *

try:
    input = raw_input
except NameError:
    # Python 3
    pass
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

import shutil

verbose_enable = True
image_size = (64, 32)
preview_size = (16, 32)
show_no_dest_warnings = True

visual_debug_enable = False
u_skins_mod_path = None
textures_path = None
meta_path = None

def set_uskin_paths():
    global u_skins_mod_path
    global textures_path
    global meta_path
    u_skins_rel = ("Desktop\\Backup\\fcalocal\\usr\\local\\share\\minetest"
                   "\\games"
                   "\\fca_game_a\\mods\\u_skins\\u_skins")
    try_skins_paths = [
        os.path.join(HOME_PATH, u_skins_rel),
    ]
    u_skins_mod_path = None
    for try_skins_path in try_skins_paths:
        if os.path.isdir(try_skins_path):
            u_skins_mod_path = try_skins_path
            break
    if u_skins_mod_path is None:
        u_skins_mod_path = mti.get('u_skins_mod_path')
    if u_skins_mod_path is None:
        echo0("u_skins_mod_path could not be detected and it is not set"
              " in settings, so paths will not be set.")
        return 1
    shared_minetest_path = mti.get("shared_minetest_path")
    if shared_minetest_path is None:
        try_path = os.path.join(os.getcwd(), "games")
        if os.path.isdir(try_path):
            shared_minetest_path = try_path
            # ^ This is already tried in the main mtanalyze module init
        else:
            echo0('Error: You must be in a minetest directory'
                  ' containing a "games" directory, or set'
                  ' shared_minetest_path in settings.')
            return 1
    games_path = os.path.join(shared_minetest_path, "games")
    dump_path = os.path.join(u_skins_mod_path, "debug")
    # ^ dump_path is only created or used if visual_debug_enable

    world_path = None
    world_name = None
    if "primary_world_path" in mti:
        world_path = mti.get("primary_world_path")
        world_name = os.path.basename(world_path)
        print("Using world '"+world_name+"'")

    # game_name = game_path_from_gameid_dict(
    gameid = None
    game_path = None
    mods_path = None
    if not os.path.isdir(u_skins_mod_path):
        echo0('"{}" does not exist.'.format(u_skins_mod_path))
        if world_path is not None and os.path.isdir(world_path):
            gameid = get_world_var("gameid")
            print("Using game '" + str(gameid) + "'")
            if gameid is not None and games_path is not None:
                game_path = os.path.join(games_path, gameid)
                mods_path = os.path.join(game_path, "mods")
                print("Using mods_path '" + mods_path + "'")
                print("Looking for u_skins mod in u_skins modpack...")
                # u_skins_mod_path = os.path.join(
                #   os.path.join(os.path.join(game_path, "mods"),
                #                "u_skins"),
                #   "u_skins"
                # )  # get the u_skins mod in the u_skins modpack
                # print("  trying '" + u_skins_mod_path + "'")

                u_skins_modpack_path = os.path.join(mods_path, "u_skins")
                u_skins_mod_path = os.path.join(u_skins_modpack_path,
                                                "u_skins")
        else:
            print("Unknown world, so can't detect game.")

    meta_path = os.path.join(u_skins_mod_path, "meta")
    textures_path = os.path.join(u_skins_mod_path, "textures")
    return 0

image_prefix = "character_"
preview_suffix = "_preview"
default_license_string = mti.get('default_license_string')
if default_license_string is None:
    default_license_string = "CC BY-SA 3.0"
png_count = 0


class RectTransferInfo:
    src_rect = None  # a tuple of left, top, right, bottom (l, t, r b)
    dest_rect_tuple = None
    flip_h = None

    def __init__(self, src_rect, dest_rect_tuple, flip_h):
        self.flip_h = flip_h
        self.src_rect = src_rect
        self.dest_rect_tuple = dest_rect_tuple


rect_trans_list = list()
rect_trans_list.append(RectTransferInfo((8, 8, 8, 8), (4, 0, 8, 8),
                       False))
# ^ face
rect_trans_list.append(RectTransferInfo((20, 20, 8, 12), (4, 8, 8, 12),
                       False))
# ^ shirt
# rect_trans_list.append(RectTransferInfo((44, 28, 4, 4), (0, 16, 4, 4),
#                        False))
# ^ hand.r
# rect_trans_list.append(RectTransferInfo((44, 28, 4, 4),
#                        (12, 16, 4, 4), True))
# ^ hand.l (True since must be flipped manually)
rect_trans_list.append(RectTransferInfo((44, 20, 4, 12), (0, 8, 4, 12),
                       False))
# ^ arm.r
rect_trans_list.append(RectTransferInfo((44, 20, 4, 12), (12, 8, 4, 12),
                       True))
# ^ arm.l (True since on hands, left one must be flipped manually)
rect_trans_list.append(RectTransferInfo((4, 20, 4, 12), (8, 20, 4, 12),
                       False))
# ^ leg.l
rect_trans_list.append(RectTransferInfo((4, 20, 4, 12), (4, 20, 4, 12),
                       True))
# ^ leg.r (True since on legs, right one must be flipped manually)
# yes, the flipping is different for leg vs arm


class USkinInfo:
    author_string = None
    name_string = None
    license_name_string = None

    # region temp
    source_image_path = None
    # endregion temp

    def __init__(self):
        pass

    def set_from_skindb_skin_file_path(self, file_path, license_name_string):
        self.author_string = None
        self.name_string = None
        self.license_name_string = license_name_string
        self.source_image_path = file_path
        file_name = os.path.basename(self.source_image_path)
        noext_name = file_name
        dot_index = file_name.rfind(".")
        if dot_index >= 0:
            noext_name = file_name[:dot_index]
        by_string = "_by_"
        by_index = noext_name.rfind(by_string)
        # print("noext_name:" + noext_name)
        if by_index >= 0:
            self.author_string = noext_name[by_index+len(by_string):]
            self.name_string = noext_name[:by_index]
        else:
            self.author_string = "<unknown>"
            self.name_string = noext_name

    def set_from_metadata_path(self, metadata_file_path):
        is_ok = False
        self.name_string = None
        self.author_string = None
        self.license_name_string = None
        if os.path.isfile(metadata_file_path):
            ins = open(metadata_file_path, 'r')
            line = True
            counting_number = 1
            while line:
                participle = "reading line " + str(counting_number)
                line = ins.readline()
                if line:
                    line_strip = line.strip()
                    if len(line_strip) > 0:
                        if self.name_string is None:
                            self.name_string = line_strip
                        elif self.author_string is None:
                            self.author_string = line_strip
                            is_ok = True
                        elif self.license_name_string is None:
                            self.license_name_string = line_strip
                counting_number += 1
            ins.close()
            if not is_ok:
                input("ERROR: Did not find line 2 for name_string in '"
                      + metadata_file_path + "'")
        else:
            input("Missing '" + metadata_file_path
                  + "' -- press enter to continue...")
        return is_ok

    def print_dump(self, min_indent):
        print(min_indent + "name_string:" + self.name_string)
        print(min_indent + "author_string:" + self.author_string)
        print(min_indent + "license_name_string:"
              + self.license_name_string)

    def _save_metadata(self, metadata_file_path):
        outs = open(metadata_file_path, 'w')
        outs.write(self.name_string+"\n")
        outs.write(self.author_string+"\n")
        outs.write(self.license_name_string+"\n")
        outs.close()

    def push_next_skin_file_if_self_is_new(self):
        result = False
        os.listdir(textures_path)
        this_index = 1
        while os.path.isfile(get_png_path_from_index(this_index)):
            this_index += 1
        if not skin_exists(self.name_string, self.author_string):
            # image_name = get_png_name_from_index(this_index)
            image_path = get_png_path_from_index(this_index)
            metadata_name = get_metadata_name_from_index(this_index)
            metadata_path = os.path.join(meta_path, metadata_name)
            # preview_name = get_preview_name_from_index(this_index)
            preview_path = get_preview_path_from_index(this_index)
            print("saving to image_path:"+image_path)
            print("saving to metadata_path:"+metadata_path)
            self._save_metadata(metadata_path)
            # actually save the skin and metadata files:
            print("saving to preview_path:"+preview_path)
            self.print_dump("  ")

            shutil.copy(self.source_image_path, image_path)
            result = True
            preview_im = Image.new("RGBA", preview_size, "#000000")
            fill_image_with_transparency(preview_im)
            skin_im = Image.open(open(self.source_image_path, 'rb'))
            # ^ double-open to make sure file is finished writing
            # NOTE: PIL automatically closes, otherwise you can do
            # something like <https://bytes.com/topic/python/answers/
            #   24308-pil-do-i-need-close>
            # fp = open(file_name, "rb")
            # im = Image.open(fp) # open from file object
            # im.load() # make sure PIL has read the data
            # fp.close()
            for rect_trans in rect_trans_list:
                src_l, src_t, src_r, src_b = rect_trans.src_rect
                src_r += src_l
                src_b += src_t
                pil_source_rect_tuple = (src_l, src_t, src_r, src_b)

                partial_im = skin_im.crop(pil_source_rect_tuple)

                dst_l, dst_t, dst_r, dst_b = rect_trans.dest_rect_tuple
                dst_r += dst_l
                dst_b += dst_t
                pil_dest_rect_tuple = (dst_l, dst_t, dst_r,
                                       dst_b)

                preview_im.paste(partial_im, (dst_l, dst_t))
                debug_img_name = ("debug " + str(pil_source_rect_tuple)
                                  + ".png")
                if visual_debug_enable:
                    # if visual_debug_enable:
                    #     input("Press enter to save temp cropping"
                    #           " images to '" + dump_path + "'")

                    if not os.path.isdir(dump_path):
                        os.makedirs(dump_path)
                    debug_img_path = os.path.join(dump_path,
                                                  debug_img_name)
                    # if not os.path.isfile(debug_img_path):
                    print("  saving "+debug_img_path)
                    print("  (after pasting to destination rect "
                          + str(pil_dest_rect_tuple) + ")")
                    partial_im.save(debug_img_path)

            preview_im.save(preview_path)
            print("Saved preview to '" + preview_path + "'")
            print("")
        else:
            print("Skin already exists: " + self.name_string + " by "
                  + self.author_string)


def get_png_path_from_index(this_index):
    return os.path.join(textures_path,
                        get_png_name_from_index(this_index))


def get_png_name_from_index(this_index):
    return image_prefix+str(this_index)+".png"


def get_preview_path_from_index(this_index):
    return os.path.join(textures_path,
                        get_preview_name_from_index(this_index))


def get_preview_name_from_index(this_index):
    return image_prefix+str(this_index)+preview_suffix+".png"


def get_metadata_name_from_index(this_index):
    return image_prefix+str(this_index)+".txt"


def get_metadata_path_from_index(this_index):
    return os.path.join(meta_path,
                        get_metadata_name_from_index(this_index))

def load_skin_metadata():
    print("Loading existing skin metadata to avoid duplication (but"
          " ignoring metadata files that do not have pngs)")
    si_list = list()
    this_index = 1
    while os.path.isfile(get_png_path_from_index(this_index)):
        existing_metadata_path = get_metadata_path_from_index(this_index)
        this_si = USkinInfo()
        is_ok = this_si.set_from_metadata_path(
            get_metadata_path_from_index(this_index)
        )
        if is_ok:
            # if not skin_exists(this_si.name_string,
            #                    this_si.author_string):
            si_list.append(this_si)
            # if verbose_enable:
            #     print("Added skin metadata:")
            #     this_si.print_dump("  ")
        this_index += 1
    print("  Found metadata for "+str(len(si_list))+" png file(s).")
    print("  The functions in "+__file__+" are now ready.")
    print("    * These functions mark destination as '"
          + default_license_string + "' license unless you")
    print("      first change mti['default_license_string']")
    print("      in your program that has:")
    print("          from u_skin_adder import *")
    print("          from mtanalyze import mti")
    print("      or use the --default_license_string option")
    print("    * Skin filename should include _by_ (with underscores) to"
          " specify author.")
    print("    * Python examples:")
    print("      load_new_skins_from_folder(folder_path)")
    print("      add_skin_if_new(file_path)")


def fill_image_with_transparency(im):
    # modified version of: unutbu. "Python PIL: how to make area
    #   transparent in PNG? (answer 7 Dec 2010 at 19:08)"
    #   <http://stackoverflow.com/questions/4379978/python-pil-how-to-
    #     make-area-transparent-in-png>. 7 Dec 2010. 8 Apr 2016.
    # who cited <http://stackoverflow.com/questions/890051/
    #   how-do-i-generate-circular-thumbnails-with-pil>
    # import Image
    # import ImageDraw
    # im = Image.open("image.png")
    # transparent_area = (50,80,100,200)
    transparent_area = (0, 0, im.size[0], im.size[1])

    mask = Image.new('L', im.size, color=255)
    draw = ImageDraw.Draw(mask)

    draw.rectangle(transparent_area, fill=0)
    im.putalpha(mask)
    # im.save('/tmp/output.png')


def skin_exists(name_string, author_string):
    global show_no_dest_warnings
    # global si_list
    result = False
    count = 0
    # if verbose_enable:
    #     print("  Checking for existing " + name_string + " by "
    #           + author_string + ":")
    for si in si_list:
        if (si.name_string == name_string and
                si.author_string == author_string):
            result = True
            break
        # else:
        #     if verbose_enable:
        #         print("    " + si.name_string+" by "
        #                + si.author_string + " is not it.")
        count += 1
    if not result:
        if count < 1:
            # if show_no_dest_warnings:
            input("WARNING: 0 skins during skin_exists check. Press"
                  " enter to continue...")
            #     show_no_dest_warnings = False
    return result
# if os.path.isdir(meta_path):
#


# accepts CC BY 3.0 skins, and looks for _by_ in name, followed by
# author (otherwise puts <unknown> on author line of metadata txt file
# in u_skin/meta folder)
def add_skin_if_new(sub_path):
    this_usi = USkinInfo()
    this_usi.set_from_skindb_skin_file_path(sub_path, default_license_string)
    return this_usi.push_next_skin_file_if_self_is_new()


def load_new_skins_from_folder(in_path):
    # in_path = os.path.join(HOME_PATH,"Downloads\\skins-to-add")
    # if not os.path.isdir(in_path):
    #     in_path = "."
    #     print("Looking for new textures in current directory")

    if not skin_exists("Sam 0", "Jordach"):
        print("")
        print("WARNING: Missing 'Sam 0' by 'Jordach'")
        print("  among "+str(len(si_list))+" skin(s).")
        print("  Only continue if you expected that skin to not be"
              " there.")
        input("  Press enter to continue...")

    if os.path.isdir(meta_path):
        if os.path.isdir(textures_path):
            if os.path.isdir(in_path):
                folder_path = in_path
                new_count = 0
                found_count = 0
                old_count = 0
                for sub_name in os.listdir(folder_path):
                    sub_path = os.path.join(folder_path, sub_name)
                    if os.path.isfile(sub_path):
                        if (sub_name[:1] != "."):
                            if (len(sub_name) > 4 and
                                    sub_name[-4:] == ".png"):
                                found_count += 1
                                if add_skin_if_new(sub_path):
                                    new_count += 1
                                else:
                                    old_count += 1
                print("Added " + str(new_count) + " new skins(s) among "
                      + str(found_count) + " discovered in specified"
                      " source folder.")
                if old_count > 0:
                    print("  " + str(old_count) + " (with matching"
                          " author and title) were already in"
                          " destination.")
            else:
                print("ERROR: Failed to get new texture files since"
                      " in_path does not exist:'"+in_path+"'")
        else:
            print("ERROR: missing textures_path (tried '"
                  + textures_path + "')")
    else:
        print("ERROR: missing meta_path (tried '"+meta_path+"')")


def main():
    # mtanalyze processes the args and sets up mti.
    if 'u_skins_mod_path' not in mti:
        echo0("Set u_skins_mod_path using the --u_skins_mod_path option")
        return 1
    code = set_uskin_paths()
    if code != 0:
        echo0("set_uskin_paths failed, so nothing will be done.")
        return code
    load_skin_metadata()

    # input("Press return to exit.")
    # load_new_skins_from_folder("C:\\Users\\Owner\\ownCloud\\Pictures\\"
    #                            "Projects\\Characters - Mine - In-Game\\"
    #                            "Minetest Player Skins")
    # add_skin_if_new("z:\\yelby.png")
    return 0

if __name__ == "__main__":
    sys.exit(main())
