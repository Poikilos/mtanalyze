#./install-chunkymap-on-ubuntu.sh
echo ""
echo " "
echo "Now performing POST-UPDATE (the updated updater)"
CHUNKYMAP_INSTALLER_DIR=$HOME/Downloads/minetest-chunkymap
CHUNKYMAP_DEST=$HOME/chunkymap
if [ ! -d "$HOME/Downloads" ]; then
	mkdir "$HOME/Downloads"
fi
cd $HOME/Downloads
chmod +x "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh"
echo ""
echo "running install-chunkymap-on-ubuntu.sh..."
sh "$CHUNKYMAP_INSTALLER_DIR/install-chunkymap-on-ubuntu.sh"
echo "...returned to update-chunkymap-on-ubuntu-from-web.sh"
echo ""
echo "destination set to $CHUNKYMAP_DEST"
MT_MY_WEBSITE_PATH=/var/www/html/minetest

# IF already installed to default MT_MY_WEBSITE_PATH, update the files:
if [ -f "$HOME/chunkymap/web/chunkymap.php" ]; then
	if [ -f "$MT_MY_WEBSITE_PATH/chunkymap.php" ]; then
		sudo cp -f "$HOME/chunkymap/web/chunkymap.php" "$MT_MY_WEBSITE_PATH/"
		echo "updated $MT_MY_WEBSITE_PATH/chunkymap.php"
		#sudo cp --no-clobber "$HOME/Downloads/minetest-chunkymap/web/viewchunkymap.php" "$MT_MY_WEBSITE_PATH/viewchunkymap.php"
		sudo cp -f "$HOME/chunkymap/web/viewchunkymap.php" "$MT_MY_WEBSITE_PATH/viewchunkymap.php"
		echo "updated $MT_MY_WEBSITE_PATH/viewchunkymap.php"
		# cannot put wildcard in quotes on unix
		#sudo cp -R --no-clobber $HOME/Downloads/minetest-chunkymap/web/images/* "$MT_MY_WEBSITE_PATH/images/"
		#--no-clobber: do not overwrite existing
	fi
fi
cp -f "$CHUNKYMAP_DEST/update-chunkymap-on-ubuntu-from-web.sh" "$HOME/"
