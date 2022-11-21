#!/bin/sh
rsync -tvP api/status.php mtio:/var/www/minetest.io/api/
code=$?
if [ $code -ne 0 ]; then exit $code; fi

rsync -tvP frontend/assets mtio:/var/www/minetest.io/
code=$?
if [ $code -ne 0 ]; then exit $code; fi

src_js=frontend/assets/js/mtanalyze.js
dst_js=~/Nextcloud/www/minetest.io/assets/js/mtanalyze.js
if [ -f $dst_js ]; then
    echo "Also merge any differences that appear below:"
    if [ -f "`command -v diff`" ]; then
        diff -u $src_js $dst_js
        code=$?
    else
        echo "Warning: diff isn't installed, so there may be unknown differences to merge"
        code=1
    fi
    if [ $code -ne 0 ]; then
        echo "such as via:"
        echo "    cp $src_js $dst_js"
    else
        echo "(there are no differences)"
    fi
    return $code
fi
