#!/bin/sh
rsync -tvP ../api/status.php mtio:/var/www/minetest.io/api/
rsync -tvP ../frontend/assets mtio:/var/www/minetest.io/
