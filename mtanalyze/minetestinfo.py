#!/usr/bin/env python3

# module for finding minetest paths and other installation metadata
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
from datetime import datetime
import platform
try:
    from parsing import *
except ImportError:
    print("This script requires parsing from PythonCodeTranslators")
    exit(1)

try:
    input = raw_input
except NameError:
    pass

# TODO: eliminate the following variables from generator.py (and manage
#   here centrally instead, so configuration is shared across minetest
#   helper programs):
# self.config (use mti.get_val instead)
# profile_path
# minetest_player_pos_multiplier = 10.0


worldgen_mod_list = []
worldgen_mod_list.append("caverealms")
worldgen_mod_list.append("ethereal")
worldgen_mod_list.append("lapis")
worldgen_mod_list.append("mines")
worldgen_mod_list.append("mg")
# ^ NOTE: experimental worldgen mod delays/prevents chunk generation and
#   sometimes crashes in 0.4.13 release (tested on Windows 10)
worldgen_mod_list.append("moretrees")
worldgen_mod_list.append("moreores")
# worldgen_mod_list.append("nature_classic")
# ^ NOTE: plantlife_modpack has this and other stuff, but detecting this
#   could help since it is unique to the modpack
worldgen_mod_list.append("plantlife_modpack")
# ^ ok if installed as modpack instead of putting individual mods in
#   mods folder
worldgen_mod_list.append("pyramids")
worldgen_mod_list.append("railcorridors")
worldgen_mod_list.append("sea")
worldgen_mod_list.append("technic")
worldgen_mod_list.append("technic_worldgen")
worldgen_mod_list.append("tsm_mines")
worldgen_mod_list.append("tsm_pyramids")
worldgen_mod_list.append("tsm_railcorridors")

after_broken = {}
after_broken["default:stone"] = "default:cobble"
after_broken["default:stone_with_iron"] = "default:iron_lump"
after_broken["default:stone_with_copper"] = "default:copper_lump"
after_broken["default:stone_with_coal"] = "default:coal_lump"
after_broken["default:dirt_with_grass"] = "default:dirt"
after_broken["moreores:mineral_tin"] = "moreores:tin_lump"
after_broken["default:stone_with_mese"] = "default:mese_crystal"
after_broken["moreores:mineral_silver"] = "moreores:silver_lump"
after_broken["default:stone_with_gold"] = "default:gold_lump"
after_broken["default:stone_with_diamond"] = "default:diamond"
# TODO: this stuff could be scraped from lua such as from
# /usr/local/share/minetest/games/fca_game_a/mods/technic/
# technic_worldgen/nodes.lua
after_broken["technic:mineral_uranium"] = "technic:uranium_lump"
after_broken["technic:mineral_chromium"] = "technic:chromium_lump"
after_broken["technic:mineral_zinc"] = "technic:zinc_lump"
after_broken["technic:mineral_lead"] = "technic:lead_lump"
after_broken["technic:mineral_sulfur"] = "technic:sulfur_lump"
after_broken["caverealms:hanging_thin_ice"] = "caverealms:thin_ice"
after_broken["caverealms:stone_with_moss"] = "default:cobble"
after_broken["caverealms:stone_with_lichen"] = "default:cobble"
after_broken["caverealms:stone_with_algae"] = "default:cobble"
after_broken["caverealms:constant_flame"] = "Empty"
after_broken["fire:basic_flame"] = "Empty"
after_broken["default:water_source"] = "bucket:bucket_water"
after_broken["default:river_water_source"] = "bucket:bucket_river_water"
after_broken["default:lava_source"] = "bucket:bucket_lava"
# after_broken[""] = ""


after_broken_startswith = {}
after_broken_startswith["pipeworks:mese_tube_"] = \
    "pipeworks:mese_tube_000000"
after_broken_startswith["pipeworks:conductor_tube_off_"] = \
    "pipeworks:conductor_tube_off_1"
after_broken_startswith["pipeworks:tube_"] = "pipeworks:tube_1"
after_broken_startswith["Item pipeworks:accelerator_tube_"] = \
    "pipeworks:accelerator_tube_1"

# TODO: crafts (scrape list of ingredients to remove from inventory)

genresult_name_end_flag = "_mapper_result.txt"
gen_error_name_end_flag = "_mapper_err.txt"

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
        print("ERROR: missing HOME variable")
else:
    if 'HOME' in os.environ:
        profile_path = os.environ['HOME']
        appdata_path = os.path.join(profile_path, ".config")
    else:
        print("ERROR: missing HOME variable")

configs_path = os.path.join(appdata_path, "enlivenminetest")
# conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                          "minetestmeta.yml")
conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "minetestmeta.yml")
mti = ConfigManager(conf_path, ":")
# ^ formerly minetestinfo (which was confusing).

game_path_from_gameid_dict = {}
FLAG_EMPTY_HEXCOLOR = "#010000"


def is_yes(s):
    if s.lower() == "y":
        return True
    if s.lower() == "yes":
        return True
    return False


class MTDecaChunk:

    metadata = None
    last_changed_utc_second = None

    def __init__(self):
        self.metadata = {}
        self.metadata["last_saved_utc_second"] = None
        self.metadata["luid_list"] = None
        # ^ what chunks this decachunk contains (as saved to 160px
        #   image)

    def load_yaml(self, yml_path):
        self.metadata = get_dict_modified_by_conf_file(self.metadata,
                                                       yml_path,
                                                       ":")

    def save_yaml(self, yml_path):
        save_conf_from_dict(yml_path, self.metadata,
                            assignment_operator=":",
                            save_nulls_enable=False)


class MTChunk:
    # x = None
    # z = None
    metadata = None
    is_fresh = None
    # luid = None

    def __init__(self):
        # NOTE: variables that need to be saved (and only they) should
        # be stored in dict
        self.metadata = {}
        self.is_fresh = False

        self.metadata["is_empty"] = False  # formerly is_marked_empty
        self.metadata["is_marked"] = False
        self.metadata["width"] = None
        self.metadata["height"] = None
        self.metadata["image_w"] = None
        self.metadata["image_h"] = None
        self.metadata["image_left"] = None
        self.metadata["image_top"] = None
        self.metadata["image_right"] = None
        self.metadata["image_bottom"] = None
        self.metadata["is_traversed"] = False
        self.metadata["tags"] = None

    def load_yaml(self, yml_path):
        self.metadata = get_dict_modified_by_conf_file(
            self.metadata,
            yml_path,
            ":"
        )

    def save_yaml(self, yml_path):
        save_conf_from_dict(
            yml_path,
            self.metadata,
            assignment_operator=":",
            save_nulls_enable=False
        )

    # requires output such as from minetestmapper-numpy.py
    # returns whether save is needed (whether metadata was changed)
    def set_from_genresult(self, this_genresult_path):
        # this_genresult_path = \
        #     mtchunks.get_chunk_genresult_path(chunk_luid)
        participle = "getting copy of dict"
        is_changed = False
        old_meta = get_dict_deepcopy(self.metadata)
        meta = self.metadata
        if os.path.isfile(this_genresult_path):
            # may have data such as:
            # Result image (w=16 h=16) will be written to
            #   chunk_x0z0.png
            # Unknown node names: meze:meze default:stone_with_iron
            #   air default:dirt_with_snow default:stone_with_copper
            #   default:snow
            # Unknown node ids: 0x0 0x1 0x2 0x3 0x4 0x5 0x6 0x7
            # Drawing image
            # Saving to: chunk_x0z0.png
            # ('PNG Region: ', [0, 64, 0, 64])
            # ('Pixels PerNode: ', 1)
            # ('border: ', 0)
            meta["is_marked"] = True
            participle = "opening '"+this_genresult_path+"'"
            ins = open(this_genresult_path, 'r')
            line = True
            counting_number = 1
            while line:
                participle = "reading line "+str(counting_number)
                line = ins.readline()
                if line:
                    strp = line.strip()
                    if ("does not exist" in strp):
                        # ^ official minetestmapper.py says
                        #   "World does not exist" but Poikilos
                        #   fork and minetestmapper-numpy.py
                        #   says "data does not exist"
                        meta["is_empty"] = True
                        break
                    elif "Result image" in strp:
                        oparen_index = strp.find("(")
                        if (oparen_index > -1):
                            cparen_index = strp.find(
                                ")",
                                oparen_index+1
                            )
                            if (cparen_index > -1):
                                osta = oparen_index+1
                                oend = cparen_index
                                ops_s = strp[osta:oend]
                                ops = ops_s.split(" ")
                                # if len(ops) == 2:
                                for op_s in ops:
                                    if "=" not in op_s:
                                        print("Bad assignment"
                                              " (operator) so ignoring"
                                              " command '" + op_s + "'")
                                        continue
                                    chunks = op_s.split("=")
                                    if len(chunks) != 2:
                                        print("Bad assignment"
                                              " (not 2 sides) so"
                                              " ignoring command '"
                                              + op_s+"'")
                                        continue
                                    # TODO: check for ValueError (?)
                                    if chunks[0].strip() == "w":
                                        c1 = chunks[1]
                                        meta["image_w"] = int(c1)
                                    elif chunks[0].strip() == "h":
                                        c1 = chunks[1]
                                        meta["image_h"] = int(c1)
                                    else:
                                        print("Bad name for image"
                                              " variable so ignoring"
                                              " variable named '"
                                              + str(chunks[0])+"'")
                                # else:
                                #     print("Bad assignment count so"
                                #           " ignoring operations"
                                #           " string '"+ops_s+"'")
                    elif "PNG Region" in strp:
                        ob_i = strp.find("[")
                        if ob_i > -1:
                            cb_i = strp.find("]", ob_i+1)
                            if cb_i > -1:
                                rv_l_s = strp[ob_i+1:cb_i]
                                rv_l = rv_l_s.split(",")
                                if len(rv_l) == 4:
                                    meta = meta
                                    # pngregion = [pngminx, pngmaxx,
                                    #              pngminz, pngmaxz]
                                    # # ^ from minetestmapper-numpy.py
                                    meta["image_left"] = int(rv_l[0])
                                    meta["image_right"] = int(rv_l[1])
                                    meta["image_top"] = int(rv_l[2])
                                    meta["image_bottom"] = int(rv_l[3])
                                else:
                                    print("Bad map rect, so ignoring: "
                                          + rv_l_s)
                    elif (len(strp) > 5) and (strp[:5] == "xmin:"):
                        self.metadata["image_left"] = int(strp[5:].strip())
                    elif (len(strp) > 5) and (strp[:5] == "xmax:"):
                        self.metadata["image_right"] = int(strp[5:].strip())
                    elif (len(strp) > 5) and (strp[:5] == "zmin:"):
                        # (zmin is bottom since cartesian)
                        self.metadata["image_bottom"] = int(strp[5:].strip())
                    elif (len(strp) > 5) and (strp[:5] == "zmax:"):
                        # (zmax is top since cartesian)
                        self.metadata["image_top"] = int(strp[5:].strip())
                counting_number += 1
            ins.close()
        participle = "checking for changes"
        is_changed = is_dict_subset(self.metadata, old_meta, False)
        return is_changed


def irr_to_mt(irr_pos):
    i = None
    try:
        i = len(irr_pos)
    except TypeError:
        # if isinstance(irr_pos, int):
        #     return irr_pos / 10.0
        return irr_pos / 10.0
    if i == 3:
        return (irr_pos[0] / 10.0, irr_pos[1] / 10.0, irr_pos[2] / 10.0)
    elif i == 2:
        return (irr_pos[0] / 10.0, irr_pos[1] / 10.0)
    elif i == 1:
        return (irr_pos[0] / 10.0,)
    else:
        raise ValueError("Converting Irrlicht tuples of this size is"
                         " not implemented.")
    return None


def irr_to_mt_s(irr_pos):
    return ','.join(irr_to_mt(irr_pos))


def mt_to_irr(mt_pos):
    i = None
    try:
        i = len(mt_pos)
    except TypeError:
        # if isinstance(mt_pos, int):
        #     return float(mt_pos) * 10.0
        return mt_pos * 10.0
    if i == 3:
        return (mt_pos[0] * 10.0, mt_pos[1] * 10.0, mt_pos[2] * 10.0)
    elif i == 2:
        return (mt_pos[0] * 10.0, mt_pos[1] * 10.0)
    elif i == 1:
        return (mt_pos[0] * 10.0,)
    else:
        raise ValueError("Converting Minetest tuples of this size is"
                         " not implemented.")
    return None


def get_gameid_from_game_path(path):
    result = None
    if path is not None:
        result = os.path.basename(path)
    return result


def get_game_name_from_game_path(path):
    result = None
    if path is not None:
        game_conf_path = os.path.join(path, "game.conf")
        if os.path.isfile(game_conf_path):
            game_conf_dict = get_dict_from_conf_file(game_conf_path)
            if "name" in game_conf_dict:
                result = game_conf_dict["name"]
                if (result is None) or (len(result.strip()) < 1):
                    result = None
                    print("WARNING: missing 'name' in game.conf in '"
                          + path + "'")
                else:
                    result = result.strip()
        else:
            print("WARNING: no game.conf in '"+path+"'")
    return result


def get_game_path_from_gameid(gameid):
    """This is case-insensitive."""
    result = None
    games_path = os.path.join(mti.get_var("shared_minetest_path"),
                              "games")
    if gameid is not None:
        if os.path.isdir(games_path):
            game_count = 0
            for this_game_name in os.listdir(games_path):
                game_count += 1
                this_game_path = os.path.join(games_path, this_game_name)
                if this_game_name.startswith("."):
                    continue
                if not os.path.isdir(this_game_path):
                    continue
                this_gameid = get_gameid_from_game_path(this_game_path)
                # print("get_game_path_from_gameid is seeing if '"
                #       + str(this_gameid) + "' is the desired '"
                #       + gameid + "'")
                if this_gameid is None:
                    continue
                if this_gameid.lower() == gameid.lower():
                    result = this_game_path
                    break
                # else:
                #     print("skipping '"+this_game_path+"'")
            if game_count <= 0:
                print("WARNING: " + str(game_count) + " games in '"
                      + games_path + "'.")
        else:
            print("ERROR: cannot get game_path from gameid since"
                  " games path is not ready yet (or '" + games_path
                  + "' does not exist for some other reason such as"
                  " shared_minetest_path is wrong and does not contain"
                  " games folder)")
    else:
        print("ERROR: can't try get_game_path_from_gameid since"
              " gameid param is None.")
    return result


def init_minetestinfo():
    global dict_entries_modified_count
    global profile_path
    if not mti.contains("www_minetest_path"):
        default_www_minetest_path = "/var/www/html/minetest"
        if "windows" in platform.system().lower():
            default_www_minetest_path = None
            prioritized_try_paths = []
            prioritized_try_paths.append("C:\\wamp\\www")
            prioritized_try_paths.append("C:\\www")
            prioritized_try_paths.append(
                os.path.join("C:\\", "Program Files",
                             "Apache Software Foundation",
                             "Apache2.2", "htdocs")
            )

            prioritized_try_paths.append("C:\\Inetpub\\Wwwroot")

            # prioritized_try_paths.append(
            #     os.path.join("C:\\", "Program Files",
            #                  "Apache Software Foundation",
            #                  "Apache2.2", "htdocs", "folder_test",
            #                  "website")
            # )
            for try_path in prioritized_try_paths:
                if os.path.isdir(try_path):
                    deep_path = os.path.join(try_path, "minetest")
                    if os.path.isdir(deep_path):
                        default_www_minetest_path = deep_path
                    else:
                        default_www_minetest_path = try_path
                    break
            if default_www_minetest_path is None:
                print("WARNING: could not detect website directory"
                      " automatically. You need WAMP or similar web"
                      " server with php 5 or higher to use minetest"
                      " website scripts. You can change"
                      " www_minetest_path to your server's website root"
                      " later by editing '" + mti._config_path
                      + "'")
                default_www_minetest_path = os.path.dirname(
                    os.path.abspath(__file__)
                )
        else:
            try_path = os.path.join(profile_path, "public_html")
            if os.path.isdir(try_path):
                deep_path = os.path.join(try_path, "minetest")
                if os.path.isdir(deep_path):
                    default_www_minetest_path = deep_path
                else:
                    default_www_minetest_path = try_path
                    print("(using '" + default_www_minetest_path
                          + "' since no '" + deep_path + "'")
                print("You can test the php website like:")
                print("  cd '" + default_www_minetest_path + "'")
                print("  php -S localhost:8000")
                print("  # but for production use a full web server")
                print("  # see http://php.net/manual/en/features."
                      "commandline.webserver.php")
        mti.prepare_var("www_minetest_path", default_www_minetest_path,
                        "your web server directory (or other folder"
                        " where minetest website features and data"
                        " should be placed)")

    default_profile_minetest_path = os.path.join(profile_path,
                                                 ".minetest")
    if "windows" in platform.system().lower():
        default_profile_minetest_path = "C:\\games\\Minetest"
    mti.prepare_var("profile_minetest_path",
                    default_profile_minetest_path,
                    ("user minetest path containing worlds"
                     " folder and debug.txt"))
    if not os.path.isdir(mti.get_var("profile_minetest_path")):
        print("(WARNING: missing "
              + mti.get_var("profile_minetest_path")
              + ", so please close and update profile_minetest_path"
              " in '" + mti._config_path
              + "' before next run)")
    print("")

    if not mti.contains("worlds_path"):
        pmp = mti.get_var("profile_minetest_path")
        mti._data["worlds_path"] = os.path.join(pmp, "worlds")
        mti.save_yaml()

    default_shared_minetest_path = "/usr/share/games/minetest"

    # packaged versions get priority
    # /usr/share/games/minetest: Ubuntu Xenial 0.4.15 and
    #   Zesty 0.4.16 packages.
    # /usr/share/minetest: arch package
    # /usr/local/share/minetest: compiled from source
    try_paths = ["/usr/share/minetest", "/usr/share/games/minetest",
                 "/usr/local/share/minetest"]
    if "windows" in platform.system().lower():
        default_shared_minetest_path = "C:\\Games\\Minetest"
    else:
        for try_path in try_paths:
            print("checking for '" + try_path + "'")
            if os.path.isdir(try_path):
                default_shared_minetest_path = try_path
                break

    while True:
        print("default default_shared_minetest_path is '"
              + default_shared_minetest_path + "'")
        mti.prepare_var(
            "shared_minetest_path",
            default_shared_minetest_path,
            "path containing Minetest's games folder"
        )
        games_path = os.path.join(
            mti.get_var("shared_minetest_path"),
            "games"
        )
        if not os.path.isdir(games_path):
            answer = input(
                "WARNING: '"
                + mti.get_var("shared_minetest_path")
                + "' does not contain a games folder. If you use this"
                + " shared_minetest_path, some features may not work"
                + " correctly (such as adding worldgen mod labels to"
                + " chunks, and future programs that may use this"
                + " metadata to install minetest games). Are you sure"
                + " you want to use y/n [blank for 'n' (no)]? "
            )
            if is_yes(answer):
                print("You can change the value of shared_minetest_path"
                      + " later by editing '"
                      + mti._config_path + "'.")
                print("")
                break
            else:
                mti.remove_var("shared_minetest_path")
        else:
            break
    load_world_and_mod_data()
    print("")
    lib_path = os.path.join(profile_path, "minetest")
    util_path = os.path.join(lib_path, "util")
    base_colors_txt = os.path.join(util_path, "colors.txt")
    if not os.path.isfile(base_colors_txt):
        base_colors_txt = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "colors (base).txt"
        )
    colors_folder_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "colors"
    )
    colors_repos_folder_path = os.path.join(colors_folder_path, "repos")
    colors_fragments_folder_path = os.path.join(
        colors_folder_path,
        "fragments"
    )
    head_colors_txt = os.path.join(
        colors_repos_folder_path,
        "VenessaE.txt"
    )

    dest_colors_txt = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "colors.txt"
    )
    if not os.path.isfile(dest_colors_txt):
        print("")
        print("Generating colors ("+dest_colors_txt+")...")
        base_colors = get_dict_from_conf_file(
            base_colors_txt,
            assignment_operator=" ",
            inline_comments_enable=True
        )
        merged_colors = get_dict_deepcopy(base_colors)
        print("")
        print(base_colors_txt + " has " + str(len(merged_colors))
              + " color(s)")
        if os.path.isfile(head_colors_txt):
            head_colors = get_dict_from_conf_file(
                head_colors_txt,
                assignment_operator=" ",
                inline_comments_enable=True
            )
            print(os.path.basename(head_colors_txt) + " has "
                  + str(len(head_colors)) + " color(s)")
            # merged_colors = get_dict_modified_by_conf_file(
            #     merged_colors,
            #     head_colors_txt,
            #     assignment_operator=" ",
            #     inline_comments_enable=True
            # )
            entries_changed_count = 0
            entries_new_count = 0
            for this_key in head_colors:
                if this_key not in merged_colors:
                    merged_colors[this_key] = head_colors[this_key]
                    entries_new_count += 1
                elif merged_colors[this_key] != head_colors[this_key]:
                    merged_colors[this_key] = head_colors[this_key]
                    entries_changed_count += 1
            print("  " + singular_or_plural("entry",
                                            "entries",
                                            (entries_new_count
                                             + entries_changed_count))
                  + " (" + str(entries_new_count) + " new, "
                  + str(entries_changed_count)
                  + " changed) merged from "
                  + os.path.basename(head_colors_txt))
        else:
            print("Missing '"+head_colors_txt+"'")
        this_name = "sfan5.txt"
        show_max_count = 7
        this_path = os.path.join(colors_repos_folder_path, this_name)
        append_colors = get_dict_from_conf_file(
            this_path,
            assignment_operator=" ",
            inline_comments_enable=True
        )
        if os.path.isfile(this_path):
            appended_count = 0
            print("")
            print("Reading "+this_path+"...")
            for this_key in append_colors.keys():
                if this_key not in merged_colors:
                    merged_colors[this_key] = append_colors[this_key]
                    if appended_count < show_max_count:
                        print("  "+this_key+" "+merged_colors[this_key])
                    elif appended_count == show_max_count:
                        print("  ...")
                    appended_count += 1
            print("  " + singular_or_plural("entry",
                                            "entries",
                                            appended_count)
                  + " appended from " + this_name)
        else:
            print("Missing "+this_path)
        folder_path = colors_fragments_folder_path
        if os.path.isdir(folder_path):
            for sub_name in os.listdir(folder_path):
                sub_path = os.path.join(folder_path, sub_name)
                if sub_name[:1] != "." and os.path.isfile(sub_path):
                    print("")
                    print("Reading "+sub_path+"...")
                    appended_count = 0
                    append_colors = get_dict_from_conf_file(
                        sub_path,
                        assignment_operator=" ",
                        inline_comments_enable=True
                    )
                    for this_key in append_colors.keys():
                        if this_key not in merged_colors:
                            merged_colors[this_key] = \
                                append_colors[this_key]
                            if appended_count < show_max_count:
                                print("  " + this_key + " "
                                      + merged_colors[this_key])
                            elif appended_count == show_max_count:
                                print("  ...")
                            appended_count += 1
                    print("  " + singular_or_plural("entry",
                                                    "entries",
                                                    appended_count)
                          + " appended from " + sub_name)
        exclusions_name = "colors - invisible.txt"
        exclusions_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            exclusions_name
        )
        exclusions_list = []
        if os.path.isfile(exclusions_path):
            ins = open(exclusions_path, 'r')
            line = True
            counting_number = 1
            while line:
                participle = "reading line "+str(counting_number)
                line = ins.readline()
                if line:
                    strp = line.strip()
                    if len(strp) > 0:
                        exclusions_list.append(strp)

            ins.close()
            print("Listed " + str(len(exclusions_list))
                  + " invisible blocks to exclude using '"
                  + exclusions_name + "'.")
        else:
            print("Missing "+exclusions_path)
        for this_key in merged_colors.keys():
            if this_key in exclusions_list:
                merged_colors.remove(this_key)
                print("Removed invisible block '"+this_key+"'")

        save_conf_from_dict(dest_colors_txt, merged_colors,
                            assignment_operator=" ")
        print("Finished writing " + str(len(merged_colors))
              + " value(s) to '" + dest_colors_txt + "'")
    else:
        print("Using colors from " + dest_colors_txt)
    default_minetestserver_path = "/usr/bin/minetestserver"
    server_msg = ""
    if not os.path.isfile(default_minetestserver_path):
        try_path = "/usr/local/bin/minetestserver"
        if os.path.isfile(try_path):
            default_minetestserver_path = try_path

    if not os.path.isfile(default_minetestserver_path):
        try_path = os.path.join(profile_path,
                                "minetest/bin/minetestserver")
        if os.path.isfile(try_path):
            # built from source
            default_minetestserver_path = try_path
    if not os.path.isfile(default_minetestserver_path):
        server_msg = " (not found in any known location)"
        default_minetestserver_path = "minetestserver"

    mti.prepare_var(
        "minetestserver_path",
        default_minetestserver_path,
        "minetestserver executable" + server_msg
    )


def load_world_and_mod_data():
    # if games_path =
    global loaded_mod_list
    global prepackaged_game_mod_list
    loaded_mod_list.clear()
    prepackaged_game_mod_list.clear()
    new_mod_list.clear()
    is_world_changed = False
    auto_chosen_world = False
    is_missing_world = False

    default_world_path = None
    if mti.contains("primary_world_path"):
        if not os.path.isdir(mti.get_var("primary_world_path")):
            is_missing_world = True
            print("primary_world_path ERROR: '"
                  + mti.get_var("primary_world_path")
                  + "' is not a folder.")

    if (not mti.contains("primary_world_path")) or is_missing_world:
        print("LOOKING FOR WORLDS IN "
              + mti.get_var("worlds_path"))
        folder_path = mti.get_var("worlds_path")
        # if os.path.isdir(folder_path):
        world_count = 0
        index = 0
        world_number = 0
        default_world_name = None
        if os.path.exists(folder_path):
            for sub_name in os.listdir(folder_path):
                sub_path = os.path.join(folder_path, sub_name)
                if sub_name[:1] != "." and os.path.isdir(sub_path):
                    world_count += 1
                    this_dt = datetime.fromtimestamp(
                        os.path.getmtime(sub_path)
                    )
                    print("  " + sub_name + (" "*(30-len(sub_name)))
                          + " <" + this_dt.strftime('%Y-%m-%d %H:%M:%S')
                          + ">")
                    wn = world_number
                    wc = world_count
                    if (sub_name != "world") or (wn == (wc-1)):
                        if not auto_chosen_world:
                            default_world_name = sub_name
                            default_world_path = sub_path
                            # was os.path.join(base_path, sub_name)
                            # was os.path.join(
                            #     mti.get_var(
                            #         "worlds_path"
                            #     ),
                            #     "try7amber"
                            # )
                        auto_chosen_world = True
                    elif default_world_name == "world":
                        if not auto_chosen_world:
                            default_world_name = sub_name
                            default_world_path = sub_path
                        auto_chosen_world = True
                    world_number += 1
                    index += 1

        if is_missing_world:
            print("MISSING WORLD '"
                  + mti.get_var("primary_world_path") + "'")
            if default_world_path is not None:
                print("(so a default was picked below that you can"
                      " change)")
            else:
                print("(and no world could be found in worlds_path '"
                      + mti.get_var("worlds_path") + "')")

        default_message = ""
        if default_world_path is not None:
            default_message = (" (or world name if above; blank for ["
                               + default_world_path + "])")
        input_string = input("World path" + default_message + ": ")
        if len(input_string) > 0:
            try_path = os.path.join(
                mti.get_var("worlds_path"),
                input_string
            )
            this_pwp = input_string  # this primary world path
            pw_exists = os.path.isdir(this_pwp)
            if (not pw_exists) and os.path.isdir(try_path):
                this_pwp = try_path
            mti._data["primary_world_path"] = this_pwp
            auto_chosen_world = False
        else:
            if default_world_path is not None:
                mti._data["primary_world_path"] = default_world_path
        mti.save_yaml()
    print("Using world at '"+mti.get_var("primary_world_path")+"'")
    # game_name = None
    # if mti.contains("game_path"):
    #     game_name = os.path.basename(mti.get_var("game_path"))
    tmp_gameid = get_world_var("gameid")
    tmp_game_gameid = get_gameid_from_game_path(
        mti.get_var("game_path")
    )
    if tmp_game_gameid is not None:
        # print("World gameid is "+str(tmp_gameid))
        print(" (game.conf in game_path has 'gameid' "
              + str(tmp_game_gameid) + ")")
    if mti.contains("game_path"):
        if (tmp_gameid is None):
            is_world_changed = True
        elif tmp_gameid.lower() != tmp_game_gameid.lower():
            is_world_changed = True

    default_gameid = None
    games_path = os.path.join(
        mti.get_var("shared_minetest_path"),
        "games"
    )
    if (not mti.contains("game_path")) or is_world_changed:
        if mti.contains("game_path"):
            default_gameid = get_gameid_from_game_path(
                mti.get_var("game_path")
            )
        if default_gameid is None:
            default_gameid = get_world_var("gameid")
        if default_gameid is not None:
            explained_string = ""
            if mti.contains("game_path"):
                explained_string = (" is different than game_path in "
                                    + mti._config_path
                                    + " so game_path must be confirmed")
            print("")
            print("gameid '" + default_gameid + "' detected in world"
                  + explained_string + ".")
        game_folder_name_blacklist = []
        # is only used if there is no game defined in world
        game_folder_name_blacklist.append("minetest_game")
        game_folder_name_blacklist.append("minetest")
        # on arch, 0.4.16 uses the directory name minetest instead
        games_list = []
        if default_gameid is None:
            folder_path = games_path
            if os.path.isdir(folder_path):
                sub_names = os.listdir(folder_path)
                real_count = 0
                for sub_name in sub_names:
                    if (sub_name[:1] != "."):
                        real_count += 1
                real_index = 0
                for sub_name in sub_names:
                    sub_path = os.path.join(folder_path, sub_name)
                    if os.path.isdir(sub_path) and sub_name[:1] != ".":
                        blacklisted = \
                            sub_name in game_folder_name_blacklist
                        if ((not blacklisted) or
                                (real_index >= real_count-1)):
                            this_gameid = \
                                get_gameid_from_game_path(sub_path)
                            if default_gameid is None:
                                default_gameid = this_gameid
                            games_list.append(this_gameid)
                    real_index += 1
        if default_gameid is not None:
            path_msg = ""
            default_game_path = get_game_path_from_gameid(
                default_gameid
            )
            if default_game_path is None:
                print("ERROR: got default gameid '" + default_gameid
                      + "' but there is no matching game path that has"
                      " this in game.conf.")
            if len(games_list) > 0:
                for try_gameid in games_list:
                    print("  "+try_gameid)
                path_msg = " (or gameid if listed above)"
            mti.prepare_var(
                "game_path",
                default_game_path,
                "game (your subgame) path"+path_msg
            )
            if mti.get_var("game_path") in games_list:
                # convert game_path to a game path (this is why
                # intentionally used as param for
                # get_game_path_from_gameid)
                try_path = get_game_path_from_gameid(
                    mti.get_var("game_path")
                )
                if try_path is not None:
                    if os.path.isdir(try_path):
                        mti.set_var("game_path", try_path)
            elif (not os.path.isdir(mti.get_var("game_path"))):
                try_path = os.path.join(
                    games_path,
                    mti.get_var("game_path")
                )
                if os.path.isdir(try_path):
                    mti.set_var("game_path", try_path)
        else:
            print("WARNING: could not get default gameid--perhaps"
                  " 'games_path' in '" + mti._config_path
                  + "' is wrong.")

    mods_path = None
    prepackaged_game_path = None
    if games_path is not None:
        # from release 0.4.16 on, directory is just called minetest
        try_id = "minetest_game"
        try_path = os.path.join(games_path, try_id)
        if os.path.isdir(try_path):
            prepackaged_game_path = try_path
            prepackaged_gameid = try_id
        else:
            try_id = "minetest"  # on arch, 0.4.16 uses this name
            try_path = os.path.join(games_path, try_id)
            if os.path.isdir(try_path):
                prepackaged_game_path = try_path
                prepackaged_gameid = try_id
            else:
                prepackaged_gameid = "minetest_game"
                prepackaged_game_path = os.path.join(games_path,
                                                     prepackaged_gameid)
                print("WARNING: neither minetest_game nor minetest"
                      + " in " + games_path + ", so reverting to"
                      + " default location for it: "
                      + prepackaged_game_path)
    print("")
    if len(prepackaged_game_mod_list) < 1:
        prepackaged_game_mod_list = \
            get_modified_mod_list_from_game_path(
                prepackaged_game_mod_list,
                prepackaged_game_path
            )
        print(prepackaged_gameid + " has "
              + str(len(prepackaged_game_mod_list)) + " mod(s): "
              + ','.join(prepackaged_game_mod_list))

    if (mti.contains("game_path") and
            os.path.isdir(mti.get_var("game_path"))):
        loaded_mod_list = get_modified_mod_list_from_game_path(
            loaded_mod_list,
            mti.get_var("game_path")
        )
        # print("Mod list for current game: "+','.join(loaded_mod_list))

        for this_mod in loaded_mod_list:
            if this_mod not in prepackaged_game_mod_list:
                new_mod_list.append(this_mod)
        new_mod_list_msg = ""
        if len(new_mod_list) > 0:
            new_mod_list_msg = ": "+','.join(new_mod_list)
        gameid = os.path.basename(mti.get_var("game_path"))
        print("")
        print(gameid + " has " + str(len(new_mod_list))
              + " mod(s) beyond "
              + prepackaged_gameid + new_mod_list_msg + ")")
        if (user_excluded_mod_count > 0):
            print("  (not including " + str(user_excluded_mod_count)
                  + " mods(s) excluded by world.mt)")
    else:
        print("Could not find game folder '"
              + mti.get_var("game_path")
              + "'. Please fix game_path in '"
              + mti._config_path + "' to point to your"
              " subgame, so that game and mod management features will"
              " work.")


def get_modified_mod_list_from_game_path(mod_list, game_path):
    global user_excluded_mod_count
    if mod_list is None:
        mod_list = []
    if game_path is not None and os.path.isdir(game_path):
        mods_path = os.path.join(game_path, "mods")
        folder_path = mods_path
        missing_load_mod_setting_count = 0
        check_world_mt()
        user_excluded_mod_count = 0
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if os.path.isdir(sub_path) and not sub_name.startswith("."):
                load_this_mod = True
                # TODO: eliminate this--load_mod_* is not a thing
                # for subgames--all of subgame's mods are loaded if
                # subgame is loaded
                lmvn = "load_mod_" + sub_name
                # ^ load mod variable name
                if world_has_var(lmvn):
                    load_this_mod = get_world_var(lmvn)
                    if not load_this_mod:
                        user_excluded_mod_count += 1
                if load_this_mod is True:
                    if sub_name not in mod_list:
                        mod_list.append(sub_name)
    return mod_list


def world_has_var(name):
    if world_mt_mapvars is None:
        return False
    return name in world_mt_mapvars


world_mt_mapvars = None
world_mt_mapvars_world_path = None


def get_world_var(name):
    result = None
    check_world_mt()
    if world_mt_mapvars is not None:
        # Don't do .get(name) -- show warning only if not present
        # (allow None)
        if name in world_mt_mapvars:
            result = world_mt_mapvars[name]
        else:
            print("WARNING: Tried to get '" + name + "' from world but"
                  " this world.mt does not have the variable")
    return result


def check_world_mt():
    global world_mt_mapvars_world_path
    world_path = mti.get_var("primary_world_path")
    # world_mt_mapvars = None
    global world_mt_mapvars
    if ((world_mt_mapvars is not None) and
            (world_path == world_mt_mapvars_world_path)):
        return
    if world_mt_mapvars is not None:
        print("WARNING: reloading world.mt since was using '"
              + world_mt_mapvars_world_path + "' but now using '"
              + world_path + "'")
    world_mt_mapvars_world_path = world_path
    if world_path is None:
        print("ERROR: Tried to get '" + name + "' but"
              " primary_world_path is None")
        return
    this_world_mt_path = os.path.join(world_path, "world.mt")
    # DO convert strings to autodetected types:
    world_mt_mapvars = get_dict_from_conf_file(this_world_mt_path, "=")
    if world_mt_mapvars is None:
        print("ERROR: Tried to get world.mt settings but couldn't"
              " read '" + this_world_mt_path + "'")


init_minetestinfo()
print("[ minetestinfo.py ] generating minetestinfo is complete.")

if __name__ == '__main__':
    print(" Import this into your py file via `import minetestinfo` ")
