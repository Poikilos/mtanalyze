#!/bin/bash
echo "chunkymap-generator is deprecated: see notes at top of generator.py"
# get dir where script resides (see al's answer at https://stackoverflow
# .com/questions/242538/unix-shell-script-find-out-which-directory-the-
# script-file-resides
# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")

echo To reconnect with this screen type:
echo
echo sudo screen -r chunkymapgen
echo
# -S names the socket (-t only sets the title)
# FAILS: flock -n /var/run/chunkymap-regen.lockfile -c "screen -S chunkymapregen python $SCRIPTPATH/unused/chunkymap-regen.py"
# FAILS: screen -S chunkymapregen flock -n /var/run/chunkymap-regen.lockfile -c python $SCRIPTPATH/unused/chunkymap-regen.py
# sudo screen -S chunkymapgen python $SCRIPTPATH/generator.py
sudo screen -S chunkymapgen python3 "$SCRIPTPATH/generator.py"
# or:
# python3 ~/GitHub/EnlivenMinetest/mtanalyze/generator.py
# see also:
# python3 ~/GitHub/EnlivenMinetest/mtanalyze/singleimage.py
