#!/usr/bin/env python3
'''
Detect stereo files in the minetest directory using ffprobe.

For an example of the json that ffprobe provides, see
ffprobe-json-example.json in the doc directory of the mtanalyze repo.

Examples:
~/git/mtanalyze/findstereofiles.py ~/minetest/games/Bucket_Game

~/git/mtanalyze/findstereofiles.py ~/minetest/games/Bucket_Game --patch ~/git/EnlivenMinetest/Bucket_Game-branches/stereo_to_mono-vs-211107c

~/git/mtanalyze/findstereofiles.py ~/minetest/games/Bucket_Game --patch ~/git/EnlivenMinetest/Bucket_Game-branches/stereo_to_mono-vs-211107c-qscale_a_1
# ^ Such as if hard-coded "-qscale:a 1" in findstereofiles.py.
# Then analyze difference in size using meld like:
cd ~/git/EnlivenMinetest/Bucket_Game-branches/stereo_to_mono-vs-211107c-qscale_a_1
find -type f -exec ls -lh {} \; > ../stereo_to_mono-vs-211107c-qscale_a_1.stats.txt
cd ..
meld stereo_to_mono-vs-211107c-qscale_a_1.stats.txt stereo_to_mono-vs-211107c.stats.txt
# apply:
# Set BUCKET_GAME to Bucket_Game dir then: cd EnlivenMinetest && git pull && rsync -rt Bucket_Game-branches/stereo_to_mono-vs-211107c-qscale_a_1/ $BUCKET_GAME

Known issues:
- This script doesn't detect
  "Error initializing output stream 0:0 -- Error while opening encoder
  for output stream #0:0 - maybe incorrect parameters such as bit_rate,
  rate, width or height"
  such as for sounds in coderbuild/castle/src/original/ropes/sounds/
  (which don't need to be changed anyway since they are originals)
  - This may only occur when -ab 192K is used.
- This script doesn't use compression options, but that is probably
  going to not change (unless the option of passing arguments along
  to ffmpeg is implemented)
  - Bitrate options were not as successful as ffmpeg's defaults in:
    ffmpeg version 4.3.2-0+deb11u2
    built with gcc 10 (Debian 10.2.1-6)
    See <https://github.com/poikilos/EnlivenMinetest/issues/407> for
    file size outcomes of various compression options vs no compression
    options.
'''
from __future__ import print_function
import argparse
from pathlib import Path
import os
import json
import sys

from mtanalyze.ffcmd import (
    FFProbeResult,
    ffprobe,
    typeDotExtensions,
    textNames,
    metaDirs,
)

def endsWithAnyCI(haystack, needles):
    for needle in needles:
        if haystack.lower().endswith(needle.lower()):
            return True
    return False

def printNonMatchingStream(root, parent, name, matchValue,
                           patch_prefix=None):
    '''
    Sequential arguments:
    root -- Specify where the recursive search started for the purpose
            of reconstructing the source such as for the patch_prefix
            option.
    name -- which named entry in the stream metadata to check such as
            "channel_layout"
    matchValue -- which value to check against, such as "mono" if you
                  want to show all non-mono streams

    Keyword arguments:
    patch_prefix -- If this is not None, use this directory to place the
                    file, converted to mono, of the same name (keep all
                    of the subdirectories starting after root but
                    replace root with patch_prefix).
    '''
    if root.endswith(os.path.sep):
        raise ValueError("root can't end with {}".format(os.path.sep))
    for sub in os.listdir(parent):
        if endsWithAnyCI(sub, typeDotExtensions['image']):
            continue
        if endsWithAnyCI(sub, typeDotExtensions['text']):
            continue
        if endsWithAnyCI(sub, typeDotExtensions['model']):
            continue
        if endsWithAnyCI(sub, typeDotExtensions['application']):
            continue
        if sub in textNames:
            continue
        subPath = os.path.join(parent, sub)
        if os.path.isdir(subPath):
            if sub in metaDirs:
                # Skip metadata directories such as ".git"
                continue
            printNonMatchingStream(root, subPath, name, matchValue,
                                   patch_prefix=patch_prefix)
            continue
        relParent = parent[len(root)+1:]
        relPath = subPath[len(root)+1:]
        # print('File: {}'.format(subPath))
        ffprobe_result = ffprobe(file_path=subPath)
        if ffprobe_result.return_code == 0:
            # print(ffprobe_result.json)
            d = json.loads(ffprobe_result.json)
            # ^ The object has a "format" dict and a "streams" list
            #   containing a stream for each item.
            streams = d.get("streams", [])
            for stream in streams:
                v = stream.get(name)
                if v == matchValue:
                    pass
                    # print("{}: {}".format(v, subPath))
                else:
                    if patch_prefix is None:
                        print("{}: {}".format(v, subPath))
                        # print("There is no patch prefix.")
                        continue
                    if v == "stereo":
                        destParent = os.path.join(patch_prefix, relParent)
                        destPath = os.path.join(patch_prefix, relPath)
                        if not os.path.exists(destParent):
                            os.makedirs(destParent)
                            # otherwise raises FileExistsError if exists
                        # print(destParent)
                        import subprocess
                        print("- [ ] {}".format(relPath))
                        if os.path.isfile(destPath):
                            continue

                        subprocess.run('ffmpeg -i \"{}\" -ac 1 \"{}\"'.format(subPath, destPath), shell=True)
                        # ^ +1 to skip the os.path.sep.
                    else:
                        pass
                        # print("{} is not \"stereo\"".format(v))
                # print(f'{stream.get("codec_type", "unknown")}: {stream.get("codec_long_name")}')
        else:
            # The file can't be probed, so ignore it unless it is
            # known to be a sound file.
            # if endsWithAnyCI(sub, typeDotExtensions['sound']):
            print("ERROR: Couldn't probe {}".format(subPath))
            print(ffprobe_result.error, file=sys.stderr)
            pass

if __name__ == '__main__':
    '''
    Based on CC BY-SA 3.0 code May 21 '20 at 5:36
    [mikebridge](https://stackoverflow.com/users/267280/mikebridge) on
    <https://stackoverflow.com/a/61927951/4541104>.
    '''

    parser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument('input', help='Game Path')
    parser.add_argument('-p', '--patch', help='Patch directory for converted files', required=False)
    args = parser.parse_args()
    if not Path(args.input).is_dir():
        print("could not read directory: " + args.input)
        exit(1)
    modsPath = os.path.join(args.input, "mods")
    if not os.path.isdir(modsPath):
        print("The provided path doesn't seem to be a game since the"
              " mods path \"{}\" doesn't exist.".format(modsPath))
        exit(1)
    print("[ {} ] patch={}".format(sys.argv[0], args.patch))
    print("[ {} ] traversing {}...".format(sys.argv[0], args.input))
    if args.patch is None:
        printNonMatchingStream(args.input, args.input, "channel_layout", "mono")
    else:
        printNonMatchingStream(args.input, args.input, "channel_layout", "mono", patch_prefix=args.patch)
        parts = os.path.split(args.patch)
        patch_name = parts[-1]
        if len(parts) > 1:
            parentParts = os.path.split(parts[0])
            if parentParts[-1] == "Bucket_Game-branches":
                print("Set BUCKET_GAME to Bucket_Game dir then: cd EnlivenMinetest && git pull && rsync -rt Bucket_Game-branches/{}/ $BUCKET_GAME".format(patch_name))
            else:
                print("parentParts: {}".format(parentParts))
