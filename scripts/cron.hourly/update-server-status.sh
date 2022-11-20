#!/bin/sh
# This script exists since shell_exec returns nothing when run from
#   the internet. Therefore, scripts should use the json file as the
#   api endpoint rather thant he php script.
WEB_USER=www-data
WEB_HOME=/var/www
MTA_RC=$WEB_HOME/.config/mtanalyze.rc
if [ -f "$MTA_RC" ]; then
    . "$MTA_RC"
fi
if [ "x$MTA_API_DIR" = "x" ]; then
    >&2 echo "MTA_API_DIR must be set in the environment, or $MTA_RC such as via:"
    >&2 echo "    mkdir -p $WEB_HOME/.config"
    >&2 echo "    echo \"MTA_API_DIR=$WEB_HOME/minetest.io/api\" | sudo tee -a $MTA_RC"
    >&2 echo '    chown -R www-data:www-data $WEB_HOME/.config'
    >&2 echo '- where $WEB_HOME/minetest.io is your website root directory'
    >&2 echo '- and where www-data:www-data is your web server user and group.'
    exit 1
fi
sudo -u www-data php $MTA_API_DIR/status.php
# | sudo -u www-data tee $MTA_API_DIR/status.json
# ^ pipe is no longer necessary since status.php implements the caching.
