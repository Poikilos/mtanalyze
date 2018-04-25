#!/bin/sh

DEST_WWW_PATH=/var/www/html
if [ -f /var/www/html/minetest/chunkymap.php ]; then
  DEST_WWW_PATH=/var/www/html/minetest
fi

if [ -f viewchunkymap.php ]; then
  rm viewchunkymap.php
fi
wget https://github.com/poikilos/minetest-chunkymap/raw/master/web/viewchunkymap.php
sudo mv -f viewchunkymap.php $DEST_WWW_PATH/
if [ -f chunkymap.php ]; then
  rm chunkymap.php
fi
wget https://github.com/poikilos/minetest-chunkymap/raw/master/web/chunkymap.php
sudo mv -f chunkymap.php $DEST_WWW_PATH/

DEST_FULLNAME=$DEST_WWW_PATH/chunkymap.php
if [ -f "$DEST_FULLNAME" ]; then
  echo "$DEST_FULLNAME saved successfully."
else
  echo "FAILED to save $DEST_FULLNAME."
fi

DEST_FULLNAME=$DEST_WWW_PATH/viewchunkymap.php
if [ -f "$DEST_FULLNAME" ]; then
  echo "$DEST_FULLNAME saved successfully."
else
  echo "FAILED to save $DEST_FULLNAME."
fi


