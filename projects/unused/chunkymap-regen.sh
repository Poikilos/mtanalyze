#!/bin/sh
echo "[ chunkymap-regen.sh ] WARNING: generator.py is deprecated"
echo "  in favor of webapp since webapp is planned to run as same user"
echo "  as ran minetestserver"
# NOTE: only works since all scripts in /etc/cron.*/ or crontab run as
# root. Really, you should impersonate www-data
# python $HOME/chunkymap/generator.py --no-loop true

# get dir where script resides (see al's answer at https://stackoverflow
# .com/questions/242538/unix-shell-script-find-out-which-directory-the-
# script-file-resides
# Absolute path to this script, e.g. /home/user/bin/foo.sh
SCRIPT=$(readlink -f "$0")
# Absolute path this script is in, thus /home/user/bin
SCRIPTPATH=$(dirname "$SCRIPT")
SCRIPTS_PATH="$SCRIPTPATH"
if [ ! -f "$SCRIPTS_PATH/generator.py" ]; then
  # this should always happen unless you have used custom file structure
  SCRIPTS_PATH=$(dirname "$SCRIPTPATH")
fi
if [ -f $SCRIPTS_PATH/generator.py ]; then
  python3 $SCRIPTS_PATH/generator.py --no-loop true
else
  print("ERROR: missing $SCRIPTS_PATH/generator.py")
fi

