#!/bin/sh
cd $HOME
CHUNKYMAP_DEPRECATED_PATH=$HOME/minetest/util
CHUNKYMAP_DEST_PATH=$HOME/chunkymap
if [ ! -d "$CHUNKYMAP_DEST_PATH" ]; then
  mkdir "$CHUNKYMAP_DEST_PATH"
fi

if [ ! -f "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen.py" ]; then
  CHUNKYMAP_DEPRECATED_PATH=$CHUNKYMAP_DEST_PATH
  mv "$CHUNKYMAP_DEPRECATED_PATH/colors (base).txt" "$CHUNKYMAP_DEST_PATH/colors (base).txt"
else
  cp -f "$CHUNKYMAP_DEPRECATED_PATH/colors.txt" "$CHUNKYMAP_DEST_PATH/colors (base).txt"
fi

if [ -d "$HOME/minetest-stuff/minetest-chunkymap" ]; then
  #remove deprecated path:
  rm -Rf $HOME/minetest-stuff/minetest-chunkymap
fi

rm -f "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen.sh"
rm -f "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen-players.sh"
rm -f "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-cronjob"
rm -f "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-players-cronjob"
rm -f "$CHUNKYMAP_DEPRECATED_PATH/set-minutely-players-crontab-job.sh"
rm -f "$CHUNKYMAP_DEPRECATED_PATH/set-minutely-crontab-job.sh"


mv "$CHUNKYMAP_DEPRECATED_PATH/web" "$CHUNKYMAP_DEST_PATH/web"
mv "$CHUNKYMAP_DEPRECATED_PATH/unused" "$CHUNKYMAP_DEST_PATH/unused"
sudo mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-genresults" "$CHUNKYMAP_DEST_PATH/chunkymap-genresults"
mv "$CHUNKYMAP_DEPRECATED_PATH/archivedebug.py" "$CHUNKYMAP_DEST_PATH/archivedebug.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/colors-missing.txt" "$CHUNKYMAP_DEST_PATH/colors-missing.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-erase-png-files-in-www-minetest-chunkymapdata.bat" "$CHUNKYMAP_DEST_PATH/erase-png-files-in-www-minetest-chunkymapdata.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-erase-wamp-www-minetest-chunkymapdata-worlds.bat" "$CHUNKYMAP_DEST_PATH/erase-wamp-www-minetest-chunkymapdata-worlds.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/poikilos.py" "$CHUNKYMAP_DEST_PATH/poikilos.py"
rm "$CHUNKYMAP_DEPRECATED_PATH/poikilos.pyc"
mv "$CHUNKYMAP_DEPRECATED_PATH/pgrs.py" "$CHUNKYMAP_DEST_PATH/pgrs.py"
rm "$CHUNKYMAP_DEPRECATED_PATH/pgrs.pyc"
rm "$CHUNKYMAP_DEPRECATED_PATH/pgrstmp.py"
rm "$CHUNKYMAP_DEPRECATED_PATH/pgrstmp.pyc"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen.py" "$CHUNKYMAP_DEST_PATH/generator.py"
rm "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen.pyc"
mv "$CHUNKYMAP_DEPRECATED_PATH/get_python_architecture.py" "$CHUNKYMAP_DEST_PATH/get_python_architecture.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/install-chunkymap-on-ubuntu.sh" "$CHUNKYMAP_DEST_PATH/install-chunkymap-on-ubuntu.sh"
mv "$CHUNKYMAP_DEPRECATED_PATH/install-chunkymap-on-ubuntu-from-web.sh" "$CHUNKYMAP_DEST_PATH/install-chunkymap-on-ubuntu-from-web.sh"
mv $CHUNKYMAP_DEPRECATED_PATH/*.bat
mv "$CHUNKYMAP_DEPRECATED_PATH/install-chunkymap-on-windows.py" "$CHUNKYMAP_DEST_PATH/install-chunkymap-on-windows.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/minetestinfo.py" "$CHUNKYMAP_DEST_PATH/minetestinfo.py"
rm "$CHUNKYMAP_DEPRECATED_PATH/minetestinfo.pyc"
mv "$CHUNKYMAP_DEPRECATED_PATH/minetestmapper-poikilos.py" "$CHUNKYMAP_DEST_PATH/minetestmapper-poikilos.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/minetestmapper-numpy.py" "$CHUNKYMAP_DEST_PATH/minetestmapper-numpy.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/minetestmeta.yml" "$CHUNKYMAP_DEST_PATH/minetestmeta.yml"
mv "$CHUNKYMAP_DEPRECATED_PATH/minetestoffline.py" "$CHUNKYMAP_DEST_PATH/minetestoffline.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/post-update.sh" "$CHUNKYMAP_DEST_PATH/post-update.sh"
mv "$CHUNKYMAP_DEPRECATED_PATH/pythoninfo.py" "$CHUNKYMAP_DEST_PATH/pythoninfo.py"
rm "$CHUNKYMAP_DEPRECATED_PATH/pythoninfo.pyc"
mv "$CHUNKYMAP_DEPRECATED_PATH/README.md" "$CHUNKYMAP_DEST_PATH/README.md"
mv "$CHUNKYMAP_DEPRECATED_PATH/replace-with-current-user.py" "$CHUNKYMAP_DEST_PATH/replace-with-current-user.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/singleimage.py" "$CHUNKYMAP_DEST_PATH/singleimage.py"
mv "$CHUNKYMAP_DEPRECATED_PATH/stop-mts.sh" "$CHUNKYMAP_DEST_PATH/stop-mts.sh"
mv "$CHUNKYMAP_DEPRECATED_PATH/update-chunkymap-installer-only.sh" "$CHUNKYMAP_DEST_PATH/update-chunkymap-installer-only.sh"
mv "$CHUNKYMAP_DEPRECATED_PATH/update-chunkymap-on-ubuntu-from-web.sh" "$CHUNKYMAP_DEST_PATH/update-chunkymap-on-ubuntu-from-web.sh"

mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen-loop.bat" "$CHUNKYMAP_DEST_PATH/chunkymap-generator.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-regen-loop.sh" "$CHUNKYMAP_DEST_PATH/chunkymap-generator.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signal stop refreshing player.bat" "$CHUNKYMAP_DEST_PATH/send signal - stop refreshing player.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signal STOP.bat" "$CHUNKYMAP_DEST_PATH/send signal - STOP.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signal verbose_enable True.bat" "$CHUNKYMAP_DEST_PATH/send signal - verbose_enable True.bat"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - change map refresh.txt" "$CHUNKYMAP_DEST_PATH/signals example - change map refresh.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - change player refresh.txt" "$CHUNKYMAP_DEST_PATH/signals example - change player refresh.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - no player update.txt" "$CHUNKYMAP_DEST_PATH/signals example - no player update.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - prevent or cancel map refresh.txt" "$CHUNKYMAP_DEST_PATH/signals example - prevent or cancel map refresh.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - stop looping.txt" "$CHUNKYMAP_DEST_PATH/signals example - stop looping.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - verbose_enable True.txt" "$CHUNKYMAP_DEST_PATH/signals example - verbose_enable True.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-signals example - turn on verbose.txt" "$CHUNKYMAP_DEST_PATH/signals example - verbose_enable True.txt"
mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap-update C wamp www.bat" "$CHUNKYMAP_DEST_PATH/update C wamp www.bat"
sudo mv "$CHUNKYMAP_DEPRECATED_PATH/chunkymap.yml" "$CHUNKYMAP_DEST_PATH/chunkymap.yml"


