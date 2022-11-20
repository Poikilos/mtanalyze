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
if [ "x$MT_WEBSITE_API" = "x" ]; then
    >&2 echo "MT_WEBSITE_API must be set in the environment, such as via:"
    >&2 echo "    mkdir -p $WEB_HOME/.config"
    >&2 echo "    echo \"MT_WEBSITE_API=$WEB_HOME/minetest.io/api\" | sudo tee -a $MTA_RC"
    >&2 echo '    chown -R www-data:www-data $WEB_HOME/.config'
    >&2 echo '- where $WEB_HOME/minetest.io is your website root directory'
    >&2 echo '- and where www-data:www-data is your web server user and group.'
    exit 1
fi
sudo -u www-data php $MT_WEBSITE_API/status.php | sudo -u www-data tee $MT_WEBSITE_API/status.json
