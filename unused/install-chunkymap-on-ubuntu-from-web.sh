#!/bin/sh
echo "This script is deprecated. Use git pull instead."
exit 1
cd $HOME
CHUNKYMAP_INSTALLER_DIR=$HOME/Downloads/minetest-chunkymap
if [ ! -d "$HOME/Downloads" ]; then
	mkdir "$HOME/Downloads"
fi

#chmod +x update-chunkymap-installer-only.sh

#./update-chunkymap-installer-only.sh:
cd $HOME/Downloads
if [ -f master.zip ]; then
  rm master.zip
fi
wget https://github.com/poikilos/minetest-chunkymap/archive/master.zip
if [ -f minetest-chunkymap.zip ]; then
  rm -f minetest-chunkymap.zip
fi
mv master.zip minetest-chunkymap.zip
if [ -d minetest-chunkymap-master ]; then
  rm -Rf minetest-chunkymap-master
fi
unzip minetest-chunkymap.zip
#mv minetest-chunkymap-master minetest-chunkymap
if [ -d "$CHUNKYMAP_INSTALLER_DIR"]; then
  rm -Rf "$CHUNKYMAP_INSTALLER_DIR"
fi
mv minetest-chunkymap-master "$CHUNKYMAP_INSTALLER_DIR"
#cd minetest-chunkymap
chmod +x "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh"
chmod +x "$CHUNKYMAP_INSTALLER_DIR/update-chunkymap-installer-only.sh"
chmod +x "$CHUNKYMAP_INSTALLER_DIR/update-chunkymap-on-ubuntu-from-web.sh"
chmod +x "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu-from-web.sh"

#mv -f "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh" "$HOME/Downloads/"
#mv -f "$CHUNKYMAP_INSTALLER_DIR/update-chunkymap-on-ubuntu-from-web.sh" "$HOME/Downloads/"
#mv -f "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu-from-web.sh" "$HOME/Downloads/"


chmod +x "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh"
sh "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh"

cp -f "$CHUNKYMAP_INSTALLER_DIR/chunkymap-generator.sh" "$HOME/"
chmod +x "$HOME/chunkymap-generator.sh"
