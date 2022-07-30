#!/usr/bin/env python3
'''
Usable mapping code will gradually be moved to
mtanalyze/client/clientmap.py
and mtanalyze/minetestoffline.py

# NOTE: parsing.py is from
# <https://raw.githubusercontent.com/poikilos/pycodetool
# /master/pycodetool/parsing.py>
'''
import sys
import os
import json

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
    echo0,
    echo1,
    is_yes,
    TRY_SHARE_MT_DIRS,
    mti,
    _OLD_json_path,
)
from mtanalyze.minetestoffline import (
    combineColorLists,
)
user_excluded_mod_count = 0
new_mod_list = []
prepackaged_game_mod_list = []
prepackaged_gameid = None

try:
    import pycodetool
except ImportError:
    pctPackageRel = os.path.join('pycodetool', 'pycodetool')
    pctPackage = os.path.join(repos, pctPackageRel)
    pctRepo = os.path.dirname(pctPackage)
    if os.path.isfile(os.path.join(pctPackage, 'parsing.py')):
        echo0('[mtchunk] found pycodetool in "{}"'.format(pctRepo))
        sys.path.append(pctRepo)

try:
    from pycodetool.parsing import ( #import *
        # ConfigParser,
        # ConfigManager,
        save_conf_from_dict,
        get_dict_modified_by_conf_file,
        get_dict_from_conf_file,
        get_dict_deepcopy,
        is_dict_subset,
    )
except ImportError as ex:
    echo0(str(ex))
    echo0("This script requires parsing from poikilos/pycodetool")
    echo0("Try (in a Terminal):")
    echo0()
    echo0("cd \"{}\"".format(repos))
    echo0("git clone https://github.com/poikilos/pycodetool.git"
          " pycodetool")
    echo0()
    echo0()
    sys.exit(1)


class MTDecaChunk:
    '''
    This is formerly from mtanalyze formerly mtanalyze.minetestinfo.
    It is deprecated because it uses YAML.
    '''
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
    '''
    This is formerly from mtanalyze formerly mtanalyze.minetestinfo.
    It is deprecated because it uses YAML.
    '''
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
                                        echo0("Bad assignment"
                                              " (operator) so ignoring"
                                              " command '" + op_s + "'")
                                        continue
                                    chunks = op_s.split("=")
                                    if len(chunks) != 2:
                                        echo0("Bad assignment"
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
                                        echo0("Bad name for image"
                                              " variable so ignoring"
                                              " variable named '"
                                              + str(chunks[0])+"'")
                                # else:
                                #     echo0("Bad assignment count so"
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
                                    echo0("Bad map rect, so ignoring: "
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
        is_changed = is_dict_subset(self.metadata, old_meta)
        return is_changed


def getServerPath():
    tryMtServerPath = "/usr/bin/minetestserver"
    server_msg = ""
    if not os.path.isfile(tryMtServerPath):
        try_path = "/usr/local/bin/minetestserver"
        if os.path.isfile(try_path):
            tryMtServerPath = try_path

    if not os.path.isfile(tryMtServerPath):
        try_path = os.path.join(profile_path,
                                "minetest/bin/minetestserver")
        if os.path.isfile(try_path):
            # built from source
            tryMtServerPath = try_path
    if not os.path.isfile(tryMtServerPath):
        server_msg = " (not found in any known location)"
        tryMtServerPath = "minetestserver"

    define_conf_var(
        "minetestserver_path",
        tryMtServerPath,
        "minetestserver executable" + server_msg
    )
    echo0("[ {} ] generating minetestinfo is complete.".format(me))
    return tryMtServerPath


def init_minetestinfo(**kwargs):
    '''
    This function is deprecated. See mti in mtanalyze instead.

    Keyword arguments:
    shared_minetest_path -- Specify the path to the installed minetest
      binaries and shared data such ~/minetest,
      /usr/share/games/minetest, or something like
      /var/lib/flatpak/app/net.minetest.Minetest/x86_64/stable/73f448a59aa3768d073aee8f38ca72f5c2c9dc79ff6d38a9b702f5630c6d7f1c/files
      (where ID may vary).
    minetest_appdata_path -- Specify the user data path where files such
    as worlds are stored. NOT YET IMPLEMENTED
    For non-RUN_IN_PLACE installations, the data folder differs from
      shared_minetest_path and may be something like:
      /.var/app/net.minetest.Minetest/.minetest  # (for flatpak)
      ~/.minetest  # (for distro-packaged versions)
    '''
    global dict_entries_modified_count
    global profile_path
    if mti.get("www_minetest_path") is None:
        default_www_minetest_path = "/var/www/html/minetest"
        if "windows" in platform.system().lower():
            default_www_minetest_path = None
            TRY_WWW_PATHS = []  # best should be first.
            TRY_WWW_PATHS.append("C:\\wamp\\www")
            TRY_WWW_PATHS.append("C:\\www")
            TRY_WWW_PATHS.append(
                os.path.join("C:\\", "Program Files",
                             "Apache Software Foundation",
                             "Apache2.2", "htdocs")
            )

            TRY_WWW_PATHS.append("C:\\Inetpub\\Wwwroot")

            # TRY_WWW_PATHS.append(
            #     os.path.join("C:\\", "Program Files",
            #                  "Apache Software Foundation",
            #                  "Apache2.2", "htdocs", "folder_test",
            #                  "website")
            # )
            for try_path in TRY_WWW_PATHS:
                if os.path.isdir(try_path):
                    deep_path = os.path.join(try_path, "minetest")
                    if os.path.isdir(deep_path):
                        default_www_minetest_path = deep_path
                    else:
                        default_www_minetest_path = try_path
                    break
            if default_www_minetest_path is None:
                echo0("WARNING: could not detect website directory"
                      " automatically. You need WAMP or similar web"
                      " server with php 5 or higher to use minetest"
                      " website scripts. You can change"
                      " www_minetest_path to your server's website root"
                      " later by editing \"{}\" or using"
                      " mtanalyze.set_var".format(_OLD_json_path))
                default_www_minetest_path = myPackage
        else:
            try_path = os.path.join(profile_path, "public_html")
            if os.path.isdir(try_path):
                deep_path = os.path.join(try_path, "minetest")
                if os.path.isdir(deep_path):
                    default_www_minetest_path = deep_path
                else:
                    default_www_minetest_path = try_path
                    echo0("(using '" + default_www_minetest_path
                          + "' since no '" + deep_path + "'")
                echo0("You can test the php website like:")
                echo0("  cd '" + default_www_minetest_path + "'")
                echo0("  php -S localhost:8000")
                echo0("  # but for production use a full web server")
                echo0("  # see http://php.net/manual/en/features."
                      "commandline.webserver.php")
        define_conf_var("www_minetest_path", default_www_minetest_path,
                        "your web server directory (or other folder"
                        " where minetest website features and data"
                        " should be placed)")

    default_profile_minetest_path = os.path.join(profile_path,
                                                 ".minetest")
    if platform.system() == "Windows":
        default_profile_minetest_path = "C:\\games\\Minetest"
    define_conf_var("user_minetest_path",
                    default_profile_minetest_path,
                    ("user minetest path (formerly"
                     " profile_minetest_path) containing worlds"
                     " folder and debug.txt or bin/debug.txt"))
    if mti.get("user_minetest_path") is None:
        raise ValueError("'user_minetest_path' is not set.")
    elif not os.path.isdir(mti.get("user_minetest_path")):
        echo0("(WARNING: missing "
              + mti.get("user_minetest_path")
              + ", so please close and update user_minetest_path"
              " in '" + _OLD_json_path
              + "' before next run)")
    echo0("")

    if mti.get("worlds_path") is None:
        pmp = mti.get("user_minetest_path")
        set_var("worlds_path", os.path.join(pmp, "worlds"))
        save_config()

    default_shared_minetest_path = "/usr/share/games/minetest"

    # packaged versions get priority
    # /usr/share/games/minetest: Ubuntu Xenial 0.4.15 and
    #   Zesty 0.4.16 packages.
    # /usr/share/minetest: arch package
    # /usr/local/share/minetest: compiled from source
    if "windows" in platform.system().lower():
        default_shared_minetest_path = "C:\\Games\\Minetest"
    else:
        for try_path in TRY_SHARE_MT_DIRS:
            echo0("checking for '" + try_path + "'")
            if os.path.isdir(try_path):
                default_shared_minetest_path = try_path
                break

    while True:
        echo0("default default_shared_minetest_path is '"
              + default_shared_minetest_path + "'")
        define_conf_var(
            "shared_minetest_path",
            default_shared_minetest_path,
            "path containing Minetest's games folder"
        )
        games_path = os.path.join(
            mti.get("shared_minetest_path"),
            "games"
        )
        if not os.path.isdir(games_path):
            echo0(
                "WARNING: '"
                + mti.get("shared_minetest_path")
                + "' does not contain a games folder. If you use this"
                + " shared_minetest_path, some features may not work"
                + " correctly (such as adding worldgen mod labels to"
                + " chunks, and future programs that may use this"
                + " metadata to install minetest games)."
            )
            answer = "y"
            if is_yes(answer):
                echo0("You can change the value of shared_minetest_path"
                      + " later by editing '"
                      + _OLD_json_path + "' or using mtanalyze.set_var.")
                echo0("")
                break
            else:
                mti.remove_var("shared_minetest_path")
        else:
            break
    load_world_and_mod_data()
    echo0("")
    dest_colors_txt = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "colors.txt"
    )
    combineColorLists(
        dest_colors_txt,
        os.path.join(profile_path, "minetest")
    )
    tryMtServerPath = getServerPath()
    define_conf_var(
        "minetestserver_path",
        tryMtServerPath,
        "minetestserver executable" + server_msg
    )


mti = {}  # The configuration for mtanalyze is stored in _OLD_json_path.
mti_help = {}


def save_config():
    with open(_OLD_json_path, 'w') as ins:
        json.dump(mti, ins, indent=2, sort_keys=True)


def set_var(key, value):
    '''
    Use this function instead of accessing mti directly so that the
    metadata is saved immediately.
    '''
    mti[key] = value
    save_config


def load_config():
    global mti
    if os.path.isfile(_OLD_json_path):
        if os.path.getsize(_OLD_json_path) == 0:
            echo0("WARNING: The empty config file \"{}\" will be"
                  " deleted.".format(_OLD_json_path))
            os.remove(_OLD_json_path)
    if os.path.isfile(_OLD_json_path):
        # mti = ConfigManager(_OLD_json_path, ":")
        # ^ formerly minetestinfo (which was confusing).
        # ^ ConfigManager or ConfigManager is from pycodetool.parsing
        with open(_OLD_json_path, 'r') as ins:
            try:
                mti = json.load(ins)
            except json.decoder.JSONDecodeError:
                raise ValueError("The configuration file \"{}\""
                                 " is not valid json."
                                 "".format(_OLD_json_path))
    elif os.path.isfile(_OLD_yaml_path):
        echo0("WARNING: The old config \"{}\" will be ignored"
              " and \"{}\" will be generated."
              "".format(_OLD_yaml_path, _OLD_json_path))


def define_conf_var(key, value, help_msg):
    '''
    Define a variable. Only set it if it doesn't already have a value.
    Get the existing value otherwise the default (defined by "value").
    (This function replaces `mti.prevare_var`--mti was a class but is
    now a dict.)
    '''
    if help_msg is None:
        raise ValueError("help_msg is None for {}".format(key))
    mti_help[key] = help_msg
    return mti.setdefault(key, value)




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
                    echo0("WARNING: missing 'name' in game.conf in '"
                          + path + "'")
                else:
                    result = result.strip()
        else:
            echo0("WARNING: no game.conf in '"+path+"'")
    return result


def get_game_path_from_gameid(gameid):
    """This is case-insensitive."""
    result = None
    games_path = os.path.join(mti.get("shared_minetest_path"), "games")
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
                # echo0("get_game_path_from_gameid is seeing if '"
                #       + str(this_gameid) + "' is the desired '"
                #       + gameid + "'")
                if this_gameid is None:
                    continue
                if this_gameid.lower() == gameid.lower():
                    result = this_game_path
                    break
                # else:
                #     echo0("skipping '"+this_game_path+"'")
            if game_count <= 0:
                echo0("WARNING: " + str(game_count) + " games in '"
                      + games_path + "'.")
        else:
            echo0("ERROR: cannot get game_path from gameid since"
                  " games path is not ready yet (or '" + games_path
                  + "' does not exist for some other reason such as"
                  " shared_minetest_path is wrong and does not contain"
                  " games folder)")
    else:
        echo0("ERROR: can't try get_game_path_from_gameid since"
              " gameid param is None.")
    return result


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
    if mti.get("primary_world_path") is not None:
        if not os.path.isdir(mti.get("primary_world_path")):
            is_missing_world = True
            echo0("primary_world_path ERROR: '"
                  + mti.get("primary_world_path")
                  + "' is not a folder.")

    if (mti.get("primary_world_path") is None) or is_missing_world:
        echo0("LOOKING FOR WORLDS IN "
              + mti.get("worlds_path"))
        folder_path = mti.get("worlds_path")
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
                    echo0("  " + sub_name + (" "*(30-len(sub_name)))
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
                            #     mti.get(
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
            echo0("MISSING WORLD '"
                  + mti.get("primary_world_path") + "'")
            if default_world_path is not None:
                echo0("(so a default was picked below that you can"
                      " change)")
            else:
                echo0("(and no world could be found in worlds_path '"
                      + mti.get("worlds_path") + "')")

        default_message = ""
        if default_world_path is not None:
            default_message = (" set to default: ["
                               + default_world_path + "])")
        # input_string = input("World path" + default_message + ": ")
        echo0("World path" + default_message)
        input_string = default_world_path
        if len(input_string) > 0:
            try_path = os.path.join(
                mti.get("worlds_path"),
                input_string
            )
            this_pwp = input_string  # this primary world path
            pw_exists = os.path.isdir(this_pwp)
            if (not pw_exists) and os.path.isdir(try_path):
                this_pwp = try_path
            set_var("primary_world_path", this_pwp)
            auto_chosen_world = False
        else:
            if default_world_path is not None:
                set_var("primary_world_path", default_world_path)
        save_config()
    echo0("Using world at '"+mti.get("primary_world_path")+"'")
    # game_name = None
    # if mti.get("game_path") is not None:
    #     game_name = os.path.basename(mti.get("game_path"))
    tmp_gameid = get_world_var("gameid")
    tmp_game_gameid = get_gameid_from_game_path(
        mti.get("game_path")
    )
    if tmp_game_gameid is not None:
        # echo0("World gameid is "+str(tmp_gameid))
        echo0(" (game.conf in game_path has 'gameid' "
              + str(tmp_game_gameid) + ")")
    if mti.get("game_path") is not None:
        if (tmp_gameid is None):
            is_world_changed = True
        elif tmp_gameid.lower() != tmp_game_gameid.lower():
            is_world_changed = True

    default_gameid = None
    games_path = os.path.join(
        mti.get("shared_minetest_path"),
        "games"
    )
    if (mti.get("game_path") is None) or is_world_changed:
        if mti.get("game_path") is not None:
            default_gameid = get_gameid_from_game_path(
                mti.get("game_path")
            )
        if default_gameid is None:
            default_gameid = get_world_var("gameid")
        if default_gameid is not None:
            explained_string = ""
            if mti.get("game_path") is not None:
                explained_string = (" is different than game_path in "
                                    + _OLD_json_path
                                    + " so game_path must be confirmed")
            echo0("")
            echo0("gameid '" + default_gameid + "' detected in world"
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
                echo0("ERROR: got default gameid '" + default_gameid
                      + "' but there is no matching game path that has"
                      " this in game.conf.")
            if len(games_list) > 0:
                for try_gameid in games_list:
                    echo0("  "+try_gameid)
                path_msg = " (or gameid if listed above)"
            define_conf_var(
                "game_path",
                default_game_path,
                "game (your subgame) path"+path_msg
            )
            if mti.get("game_path") is None:
                echo0("Warning: You must set game_path using set_var"
                      " before using related operations.")
            elif mti.get("game_path") in games_list:
                # convert game_path to a game path (this is why
                # intentionally used as param for
                # get_game_path_from_gameid)
                try_path = get_game_path_from_gameid(
                    mti.get("game_path")
                )
                if try_path is not None:
                    if os.path.isdir(try_path):
                        set_var("game_path", try_path)
            elif (not os.path.isdir(mti.get("game_path"))):
                try_path = os.path.join(
                    games_path,
                    mti.get("game_path")
                )
                if os.path.isdir(try_path):
                    set_var("game_path", try_path)
        else:
            echo0("WARNING: could not get default gameid--perhaps"
                  " 'games_path' in '" + _OLD_json_path
                  + "' is wrong.")

    mods_path = None
    prepackaged_game_path = None
    global prepackaged_gameid
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
                echo0("WARNING: Neither a minetest_game nor a minetest"
                      + " dir is in " + games_path + ", so"
                      + " \"" + prepackaged_game_path + "\""
                      + " will be used.")
    echo0("")
    if len(prepackaged_game_mod_list) < 1:
        prepackaged_game_mod_list = \
            get_modified_mod_list_from_game_path(
                prepackaged_game_mod_list,
                prepackaged_game_path
            )
        echo0(prepackaged_gameid + " has "
              + str(len(prepackaged_game_mod_list)) + " mod(s): "
              + ','.join(prepackaged_game_mod_list))

    if ((mti.get("game_path") is not None) and
            os.path.isdir(mti.get("game_path"))):
        loaded_mod_list = get_modified_mod_list_from_game_path(
            loaded_mod_list,
            mti.get("game_path")
        )
        # echo0("Mod list for current game: "+','.join(loaded_mod_list))

        for this_mod in loaded_mod_list:
            if this_mod not in prepackaged_game_mod_list:
                new_mod_list.append(this_mod)
        new_mod_list_msg = ""
        if len(new_mod_list) > 0:
            new_mod_list_msg = ": "+','.join(new_mod_list)
        gameid = os.path.basename(mti.get("game_path"))
        echo0("")
        echo0(gameid + " has " + str(len(new_mod_list))
              + " mod(s) beyond "
              + prepackaged_gameid + new_mod_list_msg + ")")
        if (user_excluded_mod_count > 0):
            echo0("  (not including " + str(user_excluded_mod_count)
                  + " mods(s) excluded by world.mt)")
    else:
        echo0("Could not find game folder '{}'."
              " Please fix game_path in '{}' to point to your"
              " game, so that game and mod management features will"
              " work. You can also set it via mtanalyze.set_var"
              "".format(mti.get("game_path"), _OLD_json_path))


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


game_path_from_gameid_dict = {}
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
            echo0("WARNING: Tried to get '" + name + "' from world but"
                  " this world.mt does not have the variable")
    return result


def check_world_mt():
    global world_mt_mapvars_world_path
    world_path = mti.get("primary_world_path")
    # world_mt_mapvars = None
    global world_mt_mapvars
    if ((world_mt_mapvars is not None) and
            (world_path == world_mt_mapvars_world_path)):
        return
    if world_mt_mapvars is not None:
        echo0("WARNING: reloading world.mt since was using '"
              + world_mt_mapvars_world_path + "' but now using '"
              + world_path + "'")
    world_mt_mapvars_world_path = world_path
    if world_path is None:
        echo0("ERROR: Tried to get '" + name + "' but"
              " primary_world_path is None")
        return
    this_world_mt_path = os.path.join(world_path, "world.mt")
    # DO convert strings to autodetected types:
    world_mt_mapvars = get_dict_from_conf_file(this_world_mt_path, "=")
    if world_mt_mapvars is None:
        echo0("ERROR: Tried to get world.mt settings but couldn't"
              " read '" + this_world_mt_path + "'")


def main():
    load_config()
    echo0("[mtanalyze.mtchunk:main] loaded config")
    return 0


if __name__ == "__main__":
    sys.exit(main())
