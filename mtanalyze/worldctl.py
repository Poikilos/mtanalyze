#!/usr/bin/env python
'''
Work with Minetest worlds.

License: See __init__.py in Poikilos' mtanalyze.

Usage in python:

Command-line interface:

world.py --mg_name carpathian --create ~/minetest/worlds/worldname
# ^ where ~/minetest/worlds is your Minetest worlds directory
'''

import sys
import os
me = "worldctl"

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
)


def usage():
    echo0("How to use {}:".format(me))
    echo0(__doc__)

default_map_meta_str = '''
mg_biome_np_humidity_blend = {
	flags = defaults
	lacunarity = 2
	persistence = 1
	seed = 90003
	spread = (8,8,8)
	scale = 1.5
	octaves = 2
	offset = 0
}
mg_biome_np_heat_blend = {
	flags = defaults
	lacunarity = 2
	persistence = 1
	seed = 13
	spread = (8,8,8)
	scale = 1.5
	octaves = 2
	offset = 0
}
mg_flags = caves, dungeons, light, decorations
chunksize = 5
mapgen_limit = 31000
mg_biome_np_heat = {
	flags = defaults
	lacunarity = 2
	persistence = 0.5
	seed = 5349
	spread = (1000,1000,1000)
	scale = 50
	octaves = 3
	offset = 50
}
water_level = 1
mg_biome_np_humidity = {
	flags = defaults
	lacunarity = 2
	persistence = 0.5
	seed = 842
	spread = (1000,1000,1000)
	scale = 50
	octaves = 3
	offset = 50
}
seed = 11536835411475436897
mg_name = carpathian
[end_of_params]
'''

# default_world_mt_str =
'''
enable_damage = true
creative_mode = false
player_backend = sqlite3
backend = sqlite3
gameid = Bucket_Game
'''

defaultWorldDef = {
    'enable_damage': "true",
    'creative_mode': "false",
    'player_backend': "sqlite3",
    'backend': "sqlite3",
    'gameid': "Bucket_Game",
}


def make_world(path, mapgenDef=None, worldDef=None):
    '''

    Keyword arguments:
    worldDef -- This is a dictionary that becomes world.mt (See
      world.mt documentation). For example, you must set 'gameid', and
      can optionally set values such as 'load_mod_vines = true' to load
      mods from Minetest's "mods" directory rather than only from the
      game.
    '''
    if os.path.isdir(path):
        raise ValueError("Error: \"{}\" already exists.".format(path))
    parent = os.path.split(path)[0]
    if worldDef is None:
        worldDef = defaultWorldDef
    if not os.path.isdir(parent):
        raise ValueError("Error: \"{}\" is not a directory."
                         "".format(parent))
    if worldDef.get('gameid') is None:
        return {'error': "You must choose a gameid."}
    os.mkdir(path)
    mapmetaPath = os.path.join(path, "map_meta.txt")
    worldmtPath = os.path.join(path, "world.mt")
    map_meta_str = default_map_meta_str
    with open(mapmetaPath) as mmOut:
        # TODO: finish this (validate and/or fill each mapgenDef value)
        mg_name = mapgenDef.get('mg_name')
        if mg_name is not None:
            map_meta_str = map_meta_str.replace(
                "mg_name = carpathian",
                "mg_name = {}".format(mg_name)
            )
        seed = mapgenDef.get('seed')
        if seed is not None:
            map_meta_str = map_meta_str.replace(
                "seed = 11536835411475436897",
                "seed = {}".format(mg_name)
            )
        mmOut.write(map_meta_str + "\n")
    with open(worldmtPath) as wmtOut:
        for k,v in worldDef.items():
            wmtOut.write("{} = {}\n".format(k, v))
    return {}


def main():
    if len(sys.argv) < 2:
        usage()
        # 1st arg is self
        # echo0("Error: You must provide a path"
        #       " (or call make_world in Python).")
        return 1
    op = None
    prevArg = None
    results = None
    mapgenDef = {}
    worldPath = None
    for arg in sys.argv:
        if prevArg is None:
            prevArg = arg
            continue
        if prevArg == "--mg_name":
            mapgenDef['mg_name'] = arg
        elif prevArg == "--seed":
            mapgenDef['seed'] = arg
        elif prevArg == "--create":
            op = "create"
            worldPath = arg
        prevArg = arg

    if op is None:
        usage()
        echo0("Error: You must specify an option"
              " (or call make_world in Python).")
        return 1

    if op == "create":
        results = make_world(worldPath, mapgenDef)

    if 'error' in results:
        usage()
        echo0(results['error'])
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
