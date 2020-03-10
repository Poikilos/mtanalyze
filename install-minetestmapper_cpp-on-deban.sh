#!/bin/sh
sudo apt-get install libgd-dev libsqlite3-dev libleveldb-dev libhiredis-dev libpq-dev
cd
git clone https://github.com/minetest/minetestmapper.git
cmake . -DENABLE_LEVELDB=1 -DENABLE_REDIS=1
make -j2
