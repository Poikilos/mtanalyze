#!/bin/sh
echo "This script is outdated. Use git pull instead."
exit 1
cd $HOME
CHUNKYMAP_INSTALLER_DIR=$HOME/Downloads/minetest-chunkymap
if [ ! -d "$HOME/Downloads" ]; then
	mkdir "$HOME/Downloads"
fi

cd $HOME/Downloads
if [ -f master.zip ]; then
  rm master.zip
fi
if [ -d "$HOME/Downloads/minetest-chunkymap" ]; then
  rm -Rf "$HOME/Downloads/minetest-chunkymap"
fi
if [ -d "$HOME/Downloads/minetest-chunkymap-master" ]; then
  rm -Rf "$HOME/Downloads/minetest-chunkymap-master"
fi
wget https://github.com/poikilos/minetest-chunkymap/archive/master.zip
if [ -f minetest-chunkymap.zip ]; then
  rm -f minetest-chunkymap.zip
fi
mv master.zip minetest-chunkymap.zip

unzip minetest-chunkymap.zip
if [ -d "$CHUNKYMAP_INSTALLER_DIR" ]; then
  rm -Rf "$CHUNKYMAP_INSTALLER_DIR"
fi
mv "$HOME/Downloads/minetest-chunkymap-master" "$HOME/Downloads/minetest-chunkymap"

#cd minetest-chunkymap
chmod +x "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh"
chmod +x "$CHUNKYMAP_INSTALLER_DIR/update-chunkymap-installer-only.sh"
chmod +x "$CHUNKYMAP_INSTALLER_DIR/update-chunkymap-on-ubuntu-from-web.sh"

#mv -f "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh" "$HOME/Downloads/"
#DON'T copy cp -f "$CHUNKYMAP_INSTALLER_DIR/update-chunkymap-on-ubuntu-from-web.sh" "$HOME/" yet, since may be running (see post-update.sh instead)
