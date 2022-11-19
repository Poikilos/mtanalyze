#!/usr/bin/env python3
'''
Collect ffprobe output.
'''
from __future__ import print_function
import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple
import json

textNames = [
    "00README",
    "README",
    ".gitignore",
    ".gitmodules",
    "config",
    "config.ld",  # such as in coderedit/
    "LICENSE",
    ".luacheckrc",
    "hud.conf.with_hunger",
    "hud.conf.no_hunger",
    "COPYING",
    "farming.conf_example",
    "License",
    "NOTES",
    "LICENSE.LGPLv2.1",
    "generate", # such as codercore/rotate/textures/generate
    "Changelog",
    "fixit", # such as coderbuild/greeknodes/src/fixit
    ".gitattributes",
    ".git", # such as coderbuild/castle/src/original/castle_tapestries/.git (content is: "gitdir: ../.git/modules/castle_tapestries")
    "Makefile",
    ".editorconfig",
    "TODO",
    "castle_tapestries_README",
    "castle_tapestries_LICENSE",
    "mergefoods",
    "a",
    "license",
    "p1",  # old temp file bucket_game-190613/mods/coderbuild/cottages/p1
]

typeExtensions = {}
# See https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
typeExtensions['model'] = [
    "obj",
    "b3d",
    "x",
]
typeExtensions['sound'] = [
    "wav",
    "ogg",
    "mp3",
]
typeExtensions['application/lua'] = ["lua"]
typeExtensions['application/javascript'] = ["js"]  # such as ehlphabet/src/gen.js
typeExtensions['application/x-perl'] = ["pl"]
typeExtensions['text/lua-doc'] = ["luadoc"]
typeExtensions['text/json'] = ["json"]
typeExtensions['application/x-shellscript'] = ["sh"]
typeExtensions['text/x-python'] = ["py"]
typeExtensions['application/zip'] = ["zip"]
typeExtensions['application/octet-stream'] = ["save", "bak", "1st", "old", "obsolete", "db"]
typeExtensions['application/win-lnk'] = ["lnk"] # I made this up--mimetype says application/octet-stream
typeExtensions['application/x-msdos-program'] = ["bat"]
typeExtensions['text/plain'] = [
    "txt",
    "txt1",
    "md",
    "markdown",  # odd but used in ircpack/irc/irc/README.markdown
    "conf",
    "ini",
    "po",  # translation file
    "pot",  # translation file
    "tr",  # translation file
    "patch",
    "example",
    "tt",  # such as coderbuild/castle/doc/license_castle_weapons_sounds.tt
    "skin",  # such as for old versions of bucket_game (before mod storage was used)
    "0",
]
typeExtensions['text/yaml'] = ["yml", "yaml"]
typeExtensions['image/raster'] = [
    "png",
    "jpg",
    "bmp",
]
typeExtensions['image/paint-net-project'] = ["pdn"] # Paint.NET project file such as christmas_craft/textures/lights_animated.pdn

typeExtensions['image/vector'] = [
    "svg",
]
typeExtensions['application/minetest-schematic'] = ["mts"]  # Minetest Schematic
typeExtensions['application/minetest-nodebox'] = ["nbe"]  # Minetest Nodebox
typeExtensions['application/minetest-worldedit'] = ["we"]  # Minetest worldedit Schematic
typeExtensions['application/x-blender'] = ["blend", "blend1", "blend-poikilos"]
typeExtensions['image/x-xcf'] = ["xcf"]
typeExtensions['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] = ["xlsx"]
typeExtensions['application/vnd.oasis.opendocument.spreadsheet'] = ["ods"]
typeExtensions['text/csv'] = ["csv"]
typeExtensions['text/rst'] = ["rst"]

# ^ more can be obtained using the mimetype command.

simpleTypeExtensions = {}

for typeStr, extensions in typeExtensions.items():
    if "/" in typeStr:
        parts = typeStr.split("/")
        simpleTypeStr = parts[0]
        got = simpleTypeExtensions.get(simpleTypeStr)
        if got is None:
            got = []
            simpleTypeExtensions[simpleTypeStr] = got
        for ext in extensions:
            # For example, append everything in 'image/raster' and
            # 'image/vector' to 'image'.
            got.append(ext)

for typeStr, extensions in simpleTypeExtensions.items():
    got = typeExtensions.get(typeStr)
    if got is None:
        typeExtensions[typeStr] = extensions
    else:
        print("[ ffcmd ] WARNING: {} exists in typeExtensions"
              " and has {} (appending {})"
              "".format(typeStr, got, extensions))
        for ext in extensions:
            got[typeStr].append(extension)

typeDotExtensions = {}
for typeStr, extensions in typeExtensions.items():
    typeDotExtensions[typeStr] = []
    for ext in extensions:
        typeDotExtensions[typeStr].append("." + ext)

metaDirs = [
    ".git"
]
slashMetaDirs = []
for metaDir in metaDirs:
    slashMetaDirs.append("/" + metaDir)


class FFProbeResult(NamedTuple):
    '''
    Store the results of an ffprobe command.

    Based on CC BY-SA 3.0 code May 21 '20 at 5:36
    [mikebridge](https://stackoverflow.com/users/267280/mikebridge) on
    <https://stackoverflow.com/a/61927951/4541104>.
    '''
    return_code: int
    json: str
    error: str


def ffprobe(file_path) -> FFProbeResult:
    '''
    Get the results of an ffprobe command.

    Based on CC BY-SA 3.0 code May 21 '20 at 5:36
    [mikebridge](https://stackoverflow.com/users/267280/mikebridge) on
    <https://stackoverflow.com/a/61927951/4541104>.
    '''
    command_array = ["ffprobe",
                     "-v", "quiet",
                     "-print_format", "json",
                     "-show_format",
                     "-show_streams",
                     file_path]
    result = subprocess.run(command_array, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    return FFProbeResult(return_code=result.returncode,
                         json=result.stdout,
                         error=result.stderr)

if __name__ == '__main__':
    '''
    Based on CC BY-SA 3.0 code May 21 '20 at 5:36
    [mikebridge](https://stackoverflow.com/users/267280/mikebridge) on
    <https://stackoverflow.com/a/61927951/4541104>.
    '''
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--input', help='File Name', required=True)
    args = parser.parse_args()
    if not Path(args.input).is_file():
        print("could not read file: " + args.input)
        exit(1)
    print('File:       {}'.format(args.input))
    ffprobe_result = ffprobe(file_path=args.input)
    if ffprobe_result.return_code == 0:
        # Print the raw json string
        print(ffprobe_result.json)

        # or print a summary of each stream
        d = json.loads(ffprobe_result.json)
        streams = d.get("streams", [])
        for stream in streams:
            print(f'{stream.get("codec_type", "unknown")}: {stream.get("codec_long_name")}')

    else:
        print("ERROR")
        print(ffprobe_result.error, file=sys.stderr)
