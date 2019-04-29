#!/bin/sh
cd $HOME
install_cmd=
package_names=
if [ -f "`command -v dnf`" ]; then
    install_cmd="sudo dnf -y install"
    package_names="fedora"
elif [ -f "`command -v yum`" ]; then
    install_cmd="sudo yum -y install"
    package_names="fedora"
elif [ -f "`sudo command -v apt`" ]; then
    sudo apt refresh
    install_cmd="sudo apt -y install"
    package_names="debian"
elif [ -f "`sudo command -v apt-get`" ]; then
    sudo apt-get refresh
    install_cmd="apt-get -y install"
    package_names="debian"
else
    echo "You're package resolver is unknown."
fi

MT_MY_WEBSITE_PATH=/var/www/html/minetest
CHUNKYMAP_INSTALLER_PATH=$HOME/git/EnlivenMinetest/mtanalyze
if [ ! -d "$CHUNKYMAP_INSTALLER_PATH" ]; then
  echo "please run install-chunkymap-on-ubuntu-from-web.sh or update-chunkymap-installer-only.sh first.";
  exit 1
fi

echo "running installer"



#MINETEST_UTIL=$HOME/minetest/util
#CHUNKYMAP_DEST=$MINETEST_UTIL
CHUNKYMAP_DEST=$HOME/chunkymap


#cd $HOME/git/EnlivenMinetest/mtanalyze
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
# rm -Rf "$CHUNKYMAP_INSTALLER_PATH"
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

if [ "@$package_names" = "@fedora" ]; then
    py3=/usr/lib64/python3.7
    if [ -z "`ls $py3/site-packages | grep numpy`" ]; then
        echo "Installing python3-numpy..."
        $install_cmd python3-numpy
    fi
    if [ -z "`ls $py3/site-packages | grep PIL`" ]; then
        echo "Installing python3-pillow..."
        $install_cmd python3-pillow
    fi
    if [ -z "`ls $py3/site-packages | grep leveldb`" ]; then
        echo "Installing python3-leveldb..."
        $install_cmd python3-leveldb
    fi
elif [ "@$package_names" = "@debian" ]; then
    py2=/usr/lib/python2.7
    # NOTE: fedora 29 has no python2-numpy, only python3-numpy
    if [ -z "`ls $py2/dist-packages | grep numpy`" ]; then
        echo "Installing python-numpy..."
        $install_cmd python-numpy
    fi
    if [ -z "`ls $py2/dist-packages | grep PIL`" ]; then
        echo "Installing python-pil..."
        $install_cmd python-pil
    fi
    if [ -z "`ls $py2/dist-packages | grep leveldb`" ]; then
        echo "Installing python-leveldb..."
        $install_cmd python-leveldb
    fi
else
    echo "Package names are unknown for your OS. You must install the"
    echo "  following packages manually:"
    echo "    python-numpy python-pil python-leveldb"
fi
# see also:
# /usr/lib/python2.7/dist-packages
# /usr/lib/python3/dist-packages
# ignored:
# /usr/local/lib/python2.7/site-packages
# /usr/lib/python2.7/site-packages
# /usr/lib/python3/site-packages
# /usr/lib/python3.6/site-packages
# /usr/lib/python3.7/site-packages
# locate site-packages | grep -v flask | grep -v kivy | grep -v trashbin | grep -v ninja | grep -v Meld | grep -v Blender | grep -v GIMP | grep -v Kivy | grep -v Brainwy | grep -v blender | grep -v inkscape | grep -v cygwin | grep -v LibreOffice | grep -v jython | grep -v pythonforandroid | grep -v tank
echo ""
if [ -f $MT_MY_WEBSITE_PATH/chunkymap.php ]; then
    echo "Updating existing $MT_MY_WEBSITE_PATH from $CHUNKYMAP_DEST/web..."
    cp -f $CHUNKYMAP_DEST/web/chunkymap.php $MT_MY_WEBSITE_PATH/
    cp -f $CHUNKYMAP_DEST/web/viewchunkymap.php $MT_MY_WEBSITE_PATH/
    cp -f $CHUNKYMAP_DEST/web/browser.php $MT_MY_WEBSITE_PATH/
else
    echo "To see what needs to be in your website directory (first run minetestinfo.py, generator.py, or singleimage.py to confirms your website directory for automated copying from web folder below):"
    echo "cd $CHUNKYMAP_DEST/web"
fi
echo ""
echo "To view helpful scripts:"
echo "cd $CHUNKYMAP_DEST"
echo ""
echo "To learn more about chunkymap:"
echo "nano $CHUNKYMAP_DEST/README.md"
echo
echo "To start now assuming configuration matches yours (nano $CHUNKYMAP_DEST/README.md before this):"
#echo "bash $CHUNKYMAP_DEST/chunkymap-generator.sh"
echo "python3 $CHUNKYMAP_DEST/generator.py"
echo
echo "Test using:"
echo "cd /var/www/html/minetest"
echo "php --syntax-check viewchunkymap.php"
echo "php -S localhost:8001 viewchunkymap.php"
echo
echo
# NOTE: colors.txt is generated now, so shouldn't be in $CHUNKYMAP_DEST until first run (first time minetestinfo.py is included by one of the other py files)


