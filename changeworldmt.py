#!/usr/bin/env python3
'''
Change a world.mt value in multiple worlds.

Examples:
1. If you did mkdir ~/git && git clone https://github.com/poikilos/mtanalyze.git ~/git/mtanalyze
cd worlds
~/git/mtanalyze/changeworldmt.py gameid Bucket_Game bucket_game

2. If you copied changeworldmt.py to a directory in PATH:
cd worlds
changeworldmt.py gameid Bucket_Game bucket

'''
from __future__ import print_function
import sys
import os
import shutil

from mtanalyze import (
    echo0,
    echo1,
)

def usage():
    print(__doc__)


def changeMtVarInWorldIf(worldPath, vname, new, whereEquals=None):
    '''
    Change the value named vname in world.mt inside the given worldPath
    but if whereEquals is not None, only change the value if the current
    value is whereEquals.
    Returns: True or False indicating whether anything changed

    Keyword arguments:
    whereEquals -- If this is not None, the value will only change to
                   new if the current value matches whereEquals.
                   If this is None, then always change the value named
                   vname.
    '''
    realWMT = os.path.join(worldPath, "world.mt")
    if not os.path.isfile(realWMT):
        raise ValueError("{} is not a recognized world directory"
                         " because it doesn't contain world.mt"
                         "".format(worldPath))
    tempWMT = os.path.join(worldPath, "world.mt.mtanalyze.tmp")
    oldWMT = realWMT + ".old"
    '''
    if os.path.isfile(oldWMT):
        print("  * restoring {}".format(oldWMT))
        os.remove(realWMT)
        shutil.move(oldWMT, realWMT)
    '''

    changed = False
    with open(realWMT, 'r') as ins:
        with open(tempWMT, 'w') as outs:
            for rawL in ins:
                line = rawL.rstrip()
                if line.strip().startswith("#"):
                    outs.write(line + "\n")  # unmodified
                    continue
                parts = line.strip().split("=")
                if len(parts) != 2:
                    echo1("  * len(\"{}\".split(\"=\")) != 2".format(line))
                    outs.write(line + "\n")  # unmodified
                    continue
                name, value = parts
                nameIndented = name.rstrip()
                name = nameIndented.strip()
                indent = ""
                if len(name) < len(nameIndented):
                    indent = nameIndented[:-len(name)]
                value = value.strip()
                match = True
                if whereEquals is not None:
                    match = (value == whereEquals)
                    if not match:
                        echo1("  * value {} != {}"
                              "".format(value, whereEquals))
                if (name != vname) or (not match):
                    echo1("  * name {} != {}".format(name, vname))
                    outs.write(line + "\n")  # unmodified
                    continue
                outs.write("{}{} = {}\n".format(indent, vname, new))
                changed = True
    if changed:
        # os.remove(realWMT)
        if not os.path.isfile(oldWMT):
            shutil.move(realWMT, oldWMT)
        shutil.move(tempWMT, realWMT)
    return changed


def changeMtVarInAllWorldsWhere(parent, vname, new, whereEquals=None):
    '''
    Change a value in all worlds but only if the variable name is
    vname and the current value is whereEquals.
    '''
    worldCount = 0
    changedCount = 0
    for sub in os.listdir(parent):
        subPath = os.path.join(parent, sub)
        worldPath = subPath
        if sub.startswith("."):
            continue
        if not os.path.isdir(subPath):
            continue
        realWMT = os.path.join(worldPath, "world.mt")
        if not os.path.isfile(realWMT):
            continue
        worldCount += 1
        print("* {}".format(realWMT))
        changed = changeMtVarInWorldIf(worldPath, vname, new,
                                       whereEquals=whereEquals)
        if changed:
            changedCount += 1
            print("  * edited".format(realWMT))
    print("{} world(s) found in {}".format(worldCount, parent))
    print("{} were edited".format(changedCount))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()
        print("Error: You must specify a variable name and the old and new values.")
        exit(1)
    parent = os.path.abspath(".")
    changeMtVarInAllWorldsWhere(parent, sys.argv[1], sys.argv[3], whereEquals=sys.argv[2])



