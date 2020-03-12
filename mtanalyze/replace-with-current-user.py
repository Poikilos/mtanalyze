#!/usr/bin/env python3
import os
from os.path import expanduser

try:
    # Python 2
    input = raw_input
except NameError:
    # Python 3
    pass

filenames = []
filenames.append(os.path.join("unused", "chunkymap-cronjob"))
filenames.append(os.path.join("unused", "chunkymap-players-cronjob"))
filenames.append(os.path.join("unused", "chunkymap-regen-players.sh"))
filenames.append(os.path.join("unused", "chunkymap-regen.sh"))
filenames.append(os.path.join("unused",
                              "set-minutely-players-crontab-job.sh"))
filenames.append(os.path.join("unused", "set-minutely-crontab-job.sh"))
filenames.append("chunkymap-generator.sh")

home_path = expanduser("~")
home_minetest_chunkymap_path = os.path.join(home_path, "chunkymap")
print("Using chunkymap path '" + home_minetest_chunkymap_path + "'")
# home_minetest_chunkymap_unused_path = os.path.join(
#     home_minetest_chunkymap_path,
#     "unused"
# )
if "\\" not in home_minetest_chunkymap_path:
    if os.path.isdir(home_minetest_chunkymap_path):
        for filename in filenames:
            file_path = os.path.join(home_minetest_chunkymap_path,
                                     filename)
            if os.path.isfile(file_path):
                temp_path = file_path+".tmp"
                os.rename(file_path, temp_path)
                if not os.path.isfile(file_path):
                    ins = open(temp_path, 'r')
                    outs = open(file_path, 'w')
                    line = True
                    while line:
                        line = ins.readline()
                        if line:
                            line = line.replace("/home/owner",
                                                home_path)
                            outs.write(line+"\n")
                    outs.close()
                    os.remove(temp_path)
                    ins.close()
                else:
                    print("FAILED to rewrite the file '" + file_path
                          + "' (to change chunkymap path to '"
                          + home_minetest_chunkymap_path
                          + "')--perhaps it is in use. Make the file"
                          " writeable then try running " + __FILE__
                          + " again.")
                    input("Press enter to continue...")
            else:
                print("SKIPPED " + filename + " since not installed"
                      " (probably ok since deprecated files are still"
                      " listed here)")
    else:
        print("FAILED to find '" + home_minetest_chunkymap_path + "'")
        print("Please install a compatible version of minetest-server"
              " package, run minetestserver once, then if you were"
              " running a chunkymap installer that called this py file,"
              " re-run that installer (otherwise re-run this script if"
              " you are sure that installer was successful).")
        input("Press enter to continue...")
else:
    print("This script only works on GNU/Linux systems (it is not"
          " needed on Windows, since on Windows, chunkymap will detect"
          " the scripts and colors.txt in the same directory as itself"
          " instead of using the minetestserver chunkymap directory)")
