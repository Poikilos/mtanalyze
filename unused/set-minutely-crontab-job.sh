#!/bin/sh
#sudo su -
# NOTE: this works only since user is a field on Ubuntu (on some GNU/Linux systems it is not, which is implied by omission at http://www.adminschoice.com/crontab-quick-reference)
# Minute, Hour, Day of Month, Month (1 to 12), Day of Week
# m h dom mon dow user command

cd ~
MT_CHUNKYMAP_CRON_TMP=mts_cron.tmp
if [ ! -f "crontab.1st" ];
then
cp /etc/crontab "crontab.1st"
fi
crontab -l > "$MT_CHUNKYMAP_CRON_TMP"
echo "* * * * * root $HOME/chunkymap/chunkymap-cronjob" >> "$MT_CHUNKYMAP_CRON_TMP"
crontab "$MT_CHUNKYMAP_CRON_TMP"
rm "$MT_CHUNKYMAP_CRON_TMP"

