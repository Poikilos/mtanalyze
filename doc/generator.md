# Map Generator
(formerly minetest-chunkymap)

The generator submodule is a Minetest online web live map generator not
requiring mods, with an emphasis on compatibility and features without
regard to speed, efficiency, or ease of use.

This may eventually be replaced by features of EnlivenMinetest/webapp
(It may be split into a different project eventually. If the webapp
directory is missing from the EnlivenMinetest project, search the
EnlivenMinetest readme.md file for "webapp").

Compatible with GNU/Linux systems, Windows, or possibly other systems (but on Windows, generator.py must be scheduled by hand with Scheduled Tasks)


## Features
* Fast HTML Canvas map with only players who moved recently
* A virtually unlimited number of markers (with alpha for outlines etc) can be placed on the map.
For markers with images that are 32px or below, px is scaled to pt (pt is manually determined for display type and orientation, instead of using default pt which is rather small on mobile devices such as iPhone&reg; 5c)
* No mods are required--Uses Python and PHP (generator.py detects border chunks by setting a flag color as the bgcolor; distinguishes empty chunks from locked database [retries if locked])
* generator.py can loop forever (to keeps certain runtime data to reduce drive reads & writes):
```bash
sudo python generator.py
#or run as user that has read & write priveleges to $HOME/chunkymap and your website's minetest folder (or website root if installing chunkymap.php there)
#or to get back to it later with screen -r, instead install screen command (or tmux may work) then run:
screen -t chunkymapregen python $HOME/chunkymap/generator.py
#where -t chunkymapregen just names the screen chunkymapregen
#Then if you are using screen and want to leave the output without terminating the process press Ctrl a d
# ( to run only once, run: python generator.py --no-loop true )
```

- Save jpg or png named as player's index to the players folder of the world to change player's icon on map (index is a number assigned for use with ajax when $show_player_names_enable is false). The index can be found in the player's yml file generated by generator.py.
- Other programs (or echo command) can send signals to generator.py via signals.txt in same folder (which will be deleted after read, so must be created by same user/group)
  - to maintain stability of  your text editor, save the file, close it, then move/copy it to the directory (or save it as something else then rename it to signals.txt).
    or use echo command (recommended).
    - On GNU/Linux systems do something like:
```bash
echo "refresh_map_enable:False" > $HOME/chunkymap/signals.txt
sleep 15s
echo "loop_enable:False" > $HOME/chunkymap/signals.txt
```

    - In Windows(R) Command Prompt do something like:
```bash
REM cd to the minetest-chunkymap or minetest-chunkymap-master folder you unzipped
echo refresh_map_enable:False > signals.txt
echo loop_enable:False > signals.txt
```

  - list of signals:
```YAML
loop_enable:True
loop_enable:False
#verbose_enable is false for looped (default) mode and true for non-looped mode
verbose_enable:True
verbose_enable:False
refresh_players_enable:True
refresh_players_enable:False
refresh_map_enable:True
refresh_map_enable:False
#rerenders chunks that were rendered in this run:
recheck_rendered:True
#where 1 is number of seconds (only delays first iteration--further iterations continue until refreshing player is needed):
refresh_map_seconds:1
#where 1 is number of seconds:
refresh_players_seconds:1
```


## Developer Notes
### set_from_genresult
minetestinfo.py's Chunk set_from_genresult expects the following lines (such as from minetestmapper.py or minetestmapper-numpy.py):
Result image (w=512 h=3152) will be written to C:\Users\jgustafson\Documents\GitHub\minetest-chunkymap\chunkymap-genresults\Enliven20170213v7\singleimage.png
Drawing image
Saving to: C:\Users\jgustafson\Documents\GitHub\minetest-chunkymap\chunkymap-genresults\Enliven20170213v7\singleimage.png
('PNG Region: ', [-208, 304, -688, 2464])
('pngMinX: ', '-208')
('pngMaxZ: ', '2464')
('Pixels PerNode: ', 1)
('border: ', 0)

where PNG Region values are left,right,top,bottom respectively.
where required values are Result image dimensions, and PNG Region or xmin,xmax,zmin,zmax.

### Player username privacy
check_players in generator.py intentionally makes up an index and uses that as the filename on the destination, so that ajax can update players without knowing either their id (filename of minetest player file) or display name (listed in the player file)
(this way, only usernames can be known if chunkymap.php allows that, or the person is logged in to the server)
Because of the feature, generator.py must prevent duplicates based on value of id in the resulting yml files (minetest player filename as id).
This should be hard to corrupt since id is used as the indexer for the players dict (however, extra files with no matching entry in the dict will still need to be deleted if they exist)

### Changing paths
games_path, mods_path, players_path, and other subdirectories of the major ones should not be stored in minetestmeta.yml, since otherwise the values may deviate from the parent directories when the parent directories change.
To avoid this problem, instead derive the paths from the parent paths using your favorite language such as in the following examples:

```python
games_path = os.path.join(mti.get_var("shared_minetest_path"), "games")
mods_path = os.path.join(mti.get_var("game_path"), "mods")
players_path = os.path.join(mti.get_var("primary_world_path"), "players")
world_path = None
world_name = None
if mti.contains("primary_world_path"):
    world_path = mti.get_var("primary_world_path")
    world_name = os.path.basename(world_path)
#region alternative method:
gameid = None
game_path = None
if world_path is not None and os.path.isdir(world_path):
    gameid=get_world_var("gameid")
if gameid is not None and games_path is not None:
    game_path = os.path.join(games_path, gameid)
#endregion alternative method:

```


### gameid
The gameid (in game.conf in a subgame folder, and world.mt in a world folder) is NOT case-sensitive: for example, minetest_game has the gameid 'Minetest' (first letter capitalized) but the worlds generated by Minetest client have the gameid 'minetest' (lowercase) in their world.mt
Yet somehow for everything else, gameid in world.mt is the name of the game FOLDER (NOT the name variable in the folder's game.conf)

### map update
The map update function is only able to detect new chunks, and only checks edge chunks if player is present in one

### chunkymap.yml
The following are saved to chunkymap.yml (and confirmed interactively if not already set):

```
www_minetest_path (such as /var/www/html/minetest)
user_minetest_path
world_name
world_path
```

### cron job
Installing as cron job is OPTIONAL (and NOT recommended):
(schedules update script every minute that runs the py file unless the py file is not complete [may take longer than 1 minute so
requires GNU flock])

IF you are using a distro such as Ubuntu 14.04 where first line of /etc/crontab is "m h dom mon dow user command" then if you want regular refresh of map then run:
- (otherwise first edit the script to fit your crontab then)
- (if you are not using /var/www/html/minetest/chunkymapdata, edit chunkymap-cronjob script to use the correct directory, then)
```bash
chmod +x set-minutely-crontab-job.sh && ./set-minutely-crontab-job.sh
```


## Requirements
- A minetest version compatible with minetestmapper-numpy.py Made by Jogge, modified by celeron55, new LevelDB features fixed by Poikilos
  - Watch <https://github.com/poikilos/minetestmapper-python> for
    progress on getting such mappers to work on recent versions of
    Minetest.
- Python 2.7 (any 2.7.x)
- Other requirements for Windows are below; Requirements for GNU/Linux are anything installed by install-chunkymap-on-ubuntu.sh (for other distros, modify it and send me a copy as a GitHub issue as described below in the Installation section)


## Installation
(NOTE: map refresh skips existing tiles unless you delete the related png and text files in your chunkymapdata directory)
- If you are not using Ubuntu, first edit the installer for your distro (and please send the modified file to me [submit as new issue named such as: DISTRONAME installer except instead of DISTRONAME put the distro you made work])

### Ubuntu

#### Prerequisites
If you use python3 and get the error "No module named 'PIL'" try:
```
sudo apt-get install python3-pil
```
(if can't connect, see https://ubuntuforums.org/showthread.php?t=2282646 )

#### Install from web

Install the git version of minetest (or otherwise install 0.4.13 or other version compatible with the map generators used by chunkymap)
such as:
```bash
#if you have a version before 2016-03-23:
if [ -f rename-deprecated.sh ]; then
rm rename-deprecated.sh
fi
wget https://github.com/poikilos/minetest-chunkymap/raw/master/rename-deprecated.sh
sudo sh rename-deprecated.sh

if [ -f install-chunkymap-on-ubuntu-from-web.sh ]; then
rm install-chunkymap-on-ubuntu-from-web.sh
fi
wget https://github.com/poikilos/minetest-chunkymap/raw/master/install-chunkymap-on-ubuntu-from-web.sh
chmod +x install-chunkymap-on-ubuntu-from-web.sh
./install-chunkymap-on-ubuntu-from-web.sh

#or later run:
#rm update-chunkymap-on-ubuntu-from-web.sh
#wget https://github.com/poikilos/minetest-chunkymap/raw/master/update-chunkymap-on-ubuntu-from-web.sh
#chmod +x update-chunkymap-on-ubuntu-from-web.sh
#./update-chunkymap-on-ubuntu-from-web.sh

#then (shutdown minetest first then) create singleimage map:
sudo python chunkymap/singleimage.py
#then start generator which will update player entries on your website (can be made anonymous--see viewchunkymap.php):
sudo python chunkymap/generator.py
```

OPTION 2: IF you are using Ubuntu go to a terminal, cd to this directory,
then switch user to the one that will run minetestserver
(since install-chunkymap-on-ubuntu.sh DOES replace "/home/owner" with current user's home [replace-with-current-user.py, which is automatically called by install, will change /home/owner to current user's directory in each script that install copies to $HOME/chunkymap])
then go to Terminal and run:
```bash
minetestserver
```

Then, when it is finished loading, press Ctrl C then run:
```bash
chmod +x install-chunkymap-on-ubuntu.sh && ./install-chunkymap-on-ubuntu.sh
```

### Linux Post-install Steps
Rename viewchunkymap.php so it won't be overwritten on update if you want to modify it (or anything you want) then make a link to it on your website or share the link some other way.
```bash
# The commands below will work if you are using the web installer, or have done mv minetest-chunkymap-master "$HOME/Downloads/minetest-chunkymap" (and if you are using /var/www/html/minetest -- otherwise change that below)
MT_MY_WEBSITE_PATH=/var/www/html/minetest
sudo cp -f "$HOME/Downloads/minetest-chunkymap/web/chunkymap.php" "$MT_MY_WEBSITE_PATH/chunkymap.php"
sudo cp -f "$HOME/Downloads/minetest-chunkymap/web/viewchunkymap.php" "$MT_MY_WEBSITE_PATH/viewchunkymap.php"
sudo cp -R --no-clobber "$HOME/Downloads/minetest-chunkymap/web/images/*" "$MT_MY_WEBSITE_PATH/images/"
#--no-clobber: do not overwrite existing
# after you do this, the update script will do it for you if you are using /var/www/html/minetest, otherwise edit the update script before using it to get these things updated
```

### Windows
- Install Python 2.7
- Run install-chunkymap-on-windows.bat
  - (which just runs C:\Python27\python install-chunkymap-on-windows.py)
  - (the installer will automatically download and install numpy and Pillow -- see also install-on-windows-manually.md)