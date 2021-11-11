#!/usr/bin/env python
from __future__ import print_function
'''
MIP is for "Minetest [Run] In-place". That means this will only generate
documentation for games in "$HOME/minetest/games" (or USERPROFILE if
the environment variable is present).
'''
import sys
import os

from mtanalyze import mti

print()
me = os.path.split(__file__)[-1]
shared_minetest_path = mti.get('shared_minetest_path')
profile_minetest_path = mti.get('profile_minetest_path')
if shared_minetest_path is not None:
    if shared_minetest_path == profile_minetest_path:
        print('RUN_IN_PLACE is apparently true (profile_minetest_path'
              ' matches shared_minetest_path).')
    else:
        print('RUN_IN_PLACE is apparently false (profile_minetest_path'
              ' differs from shared_minetest_path).')
else:
    print('RUN_IN_PLACE is unknown since shared_minetest_path is'
          ' not known.')
print()
print("[ {} ] mti.get() results for name in"
      " mti.keys():".format(me))
print()
# checkNames = ["minetestserver_path"]
checkNames = mti.keys()
for name in checkNames:
    if mti.get(name) is not None:
        print("{}: {}".format(name, mti.get(name)))
    else:
        print("{} is not known.".format(name))

print()
print("[ {} ] done.".format(me))
