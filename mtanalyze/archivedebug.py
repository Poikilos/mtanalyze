#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import datetime

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

from mtanalyze import ( # formerly: from minetestinfo import *
    mti,
    get_required,
    echo0,
)

def main():
    profile_minetest_path = get_required("profile_minetest_path")
    if profile_minetest_path is None:
        echo0("profile_minetest_path was not set,"
              " so debug_txt_path was not set.")
    elif os.path.isdir(profile_minetest_path):
        print(__file__+"...")
        debug_txt_path = os.path.join(
            profile_minetest_path,
            "debug.txt"
        )
        debug_archived_folder_name = "debug_archived"
        debug_archived_folder_path = os.path.join(
            profile_minetest_path,
            debug_archived_folder_name
        )
        if os.path.isfile(debug_txt_path):
            print("NOT YET IMPLEMENTED (backup is not implemented)")
        else:
            print("There is no '" + debug_txt_path + "'")
            if os.sep == "\\":
                print("  (maybe it was already archived after last server"
                      " activity,")
                print("  or you are not running minetestserver and this"
                      " script")
                print("  does not apply to you).")
            else:
                print("  (maybe it was already archived after last server"
                      " activity).")
    else:
        print("Missing folder '"+profile_minetest_path+"'.")
        print("The folder should be your .minetest folder or other folder"
              " containing 'debug.txt' (at least '"
              + debug_archived_folder_name + "' will be there if "
              + __file__ + " ran successfully before).")
    return 0

if __name__ == "__main__":
    sys.exit(main())
