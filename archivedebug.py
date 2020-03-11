import os
import datetime
from minetestinfo import *
if os.path.isdir(mti.get_var("profile_minetest_path")):
    print(__file__+"...")
    debug_txt_path = os.path.join(
        mti.get_var("profile_minetest_path"),
        "debug.txt"
    )
    debug_archived_folder_name = "debug_archived"
    debug_archived_folder_path = os.path.join(
        mti.get_var("profile_minetest_path"),
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
