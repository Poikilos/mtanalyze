#!/bin/sh
cd $HOME
MT_MY_WEBSITE_PATH=/var/www/html/minetest
CHUNKYMAP_INSTALLER_PATH=$HOME/git/EnlivenMinetest/mtanalyze
if [ ! -d "$HOME/Downloads/minetest-chunkymap" ]; then
  echo "please run install-chunkymap-on-ubuntu-from-web.sh or update-chunkymap-installer-only.sh first.";
else
#else run everything from here down
echo "running installer"

#MINETEST_UTIL=$HOME/minetest/util
#CHUNKYMAP_DEST=$MINETEST_UTIL
CHUNKYMAP_DEST=$HOME/chunkymap


#cd $HOME/Downloads
#rm -f $HOME/minetestmapper-numpy.py
#wget https://github.com/spillz/minetest/raw/master/util/minetestmapper-numpy.py
#cp -f "$CHUNKYMAP_INSTALLER_PATH/minetestmapper-numpy.py" "$HOME/minetest/util/minetestmapper-numpy.py"
if [ ! -d "$CHUNKYMAP_DEST" ]; then
  mkdir "$CHUNKYMAP_DEST"
fi
#if [ ! -d "$CHUNKYMAP_DEST/unused/" ]; then
#  mkdir "$CHUNKYMAP_DEST/unused/"
#fi
#NOTE: chmod +x is done last (see below)

# asterisk CANNOT be in quotes
cp -Rf $CHUNKYMAP_INSTALLER_PATH/* "$CHUNKYMAP_DEST/"
rm -Rf "$CHUNKYMAP_INSTALLER_PATH"
rm $CHUNKYMAP_DEST/*.bat
rm "$CHUNKYMAP_DEST/install-chunkymap-on-windows.py"

#region DEPRECATED
#if [ ! -d "$CHUNKYMAP_DEST" ]; then



#cp -f "$CHUNKYMAP_INSTALLER_PATH/generator.py" "$CHUNKYMAP_DEST/"
#chmod +x "$CHUNKYMAP_DEST/generator.py"

#cp -f "$CHUNKYMAP_INSTALLER_PATH/README.md" "$CHUNKYMAP_DEST/"
#remove files place in dest by old version of installer script:
#install scripts (already done above with wildcard so commented lines below are deprecated):
#cp -f "$CHUNKYMAP_INSTALLER_PATH/chunkymap-generator.sh" "$CHUNKYMAP_DEST/"
#install not-recommended scripts:
#cp -f "$CHUNKYMAP_INSTALLER_PATH/unused/chunkymap-regen.sh" "$CHUNKYMAP_DEST/unused/"
#cp -f "$CHUNKYMAP_INSTALLER_PATH/unused/chunkymap-regen-players.sh" "$CHUNKYMAP_DEST/unused/"
#cp -f "$CHUNKYMAP_INSTALLER_PATH/unused/chunkymap-cronjob" "$CHUNKYMAP_DEST/unused/"
#cp -f "$CHUNKYMAP_INSTALLER_PATH/unused/chunkymap-players-cronjob" "$CHUNKYMAP_DEST/unused/"
#cp -f "$CHUNKYMAP_INSTALLER_PATH/unused/set-minutely-players-crontab-job.sh" "$CHUNKYMAP_DEST/unused/"
#cp -f "$CHUNKYMAP_INSTALLER_PATH/unused/set-minutely-crontab-job.sh" "$CHUNKYMAP_DEST/unused/"
#if [ ! -d "$CHUNKYMAP_DEST/web" ]; then
#	mkdir "$CHUNKYMAP_DEST/web"
#fi
#cp -Rf "$CHUNKYMAP_INSTALLER_PATH/web" "$CHUNKYMAP_DEST/"

#if [ ! -d "$CHUNKYMAP_DEST/chunkymap" ]; then
#  mkdir "$CHUNKYMAP_DEST/chunkymap"
#fi
#cp -f "$CHUNKYMAP_INSTALLER_PATH/minetestmapper-poikilos.py" "$CHUNKYMAP_DEST/"
#cp --no-clobber $CHUNKYMAP_INSTALLER_PATH/signals* "$CHUNKYMAP_DEST/"
#cd "$CHUNKYMAP_INSTALLER_PATH"
cd $CHUNKYMAP_DEST
python replace-with-current-user.py  # the py file only manipulates the shell scripts that must run as root but use regular user's minetest
# so chmod those files AFTER running the py above (since it rewrites them and therefore removes x attribute if present):



#fi
#endregion DEPRECATED



chmod +x "$CHUNKYMAP_DEST/chunkymap-generator.sh"
chmod -x "$CHUNKYMAP_DEST/unused/chunkymap-regen.sh"
chmod -x "$CHUNKYMAP_DEST/unused/chunkymap-regen-players.sh"
chmod -x "$CHUNKYMAP_DEST/unused/chunkymap-cronjob"
chmod -x "$CHUNKYMAP_DEST/unused/set-minutely-crontab-job.sh"
chmod -x "$CHUNKYMAP_DEST/unused/set-minutely-players-crontab-job.sh"

cp -f $HOME/chunkymap/chunkymap-generator.sh $HOME/
chmod +x $HOME/chunkymap-generator.sh

#if [ -f "$HOME/update-chunkymap-on-ubuntu-from-web.sh" ]; then
cp -f "$HOME/chunkymap/update-chunkymap-on-ubuntu-from-web.sh" "$HOME/"
#fi
#cp -f "$HOME/chunkymap/install-chunkymap-on-ubuntu-from-web.sh" "$HOME/install-chunkymap-on-ubuntu-from-web.sh"

#remove deprecated stuff
#rm "$HOME/install-chunkymap-on-ubuntu-from-web.sh"
#rm "$HOME/mapper-refresh-minetestserver.bat"
#rm "$HOME/mapper-refresh-minetestserver"

sudo apt-get install python-numpy python-pil python-leveldb
echo ""
echo "To see what needs to be in your website directory (first run minetestinfo.py, generator.py, or singleimage.py to confirms your website directory for automated copying from web folder below):"
echo "cd $CHUNKYMAP_DEST/web"
echo ""
echo "To view helpful scripts:"
echo "cd $CHUNKYMAP_DEST"
echo ""
echo "To learn more about chunkymap:"
echo "nano $CHUNKYMAP_DEST/README.md"
echo
echo "To start now assuming configuration matches yours (nano $CHUNKYMAP_DEST/README.md before this):"
echo sh chunkymap/chunkymap-generator.sh
echo
# NOTE: colors.txt is generated now, so shouldn't be in $CHUNKYMAP_DEST until first run (first time minetestinfo.py is included by one of the other py files)


fi

