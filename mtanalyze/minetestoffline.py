#!/usr/bin/env python
from __future__ import print_function
'''
Process minetest player files when server is not running
such as assist in data recovery where original filename is not known
'''
# (such as where player_id does not match filename of plr file,
# as caused by data recovery or other corruption)
# Copyright (C) 2018 Jake Gustafson

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA

import shutil
import os
from datetime import datetime

myPath = os.path.realpath(__file__)
myPackage = os.path.split(myPath)[0]
myRepo = os.path.split(myPackage)[0]
repos = os.path.split(myRepo)[0]
me = 'minetestoffline.py'

try:
    try:
        from parsing import *
    except ImportError as ex:
        from pycodetool.parsing import *
except ImportError:
    print("This script requires parsing from poikilos/pycodetool")
    print("Try (in a Terminal):")
    print()
    print("cd \"{}\"".format(repos))
    print("git clone https://github.com/poikilos/pycodetool.git"
          " pycodetool")
    print()
    print()
    exit(1)

from minetestinfo import *

import time
from ast import literal_eval  # as make_tuple

try:
    input = raw_input
except NameError:
    pass  # Python 3

tmp_prof = os.path.join("C:\\", "Users", "jgustafson")
desktop = os.path.join(tmp_prof, "Desktop")
bak_p = os.path.join(tmp_prof, "Backup", "fcalocal", "home", "owner")
bak_mt = os.path.join(bak_p, ".minetest")
bak_worlds = os.path.join(bak_mt, "worlds")
tmp_prof = None
# plrs = os.path.join(bak_mt, "worlds", "FCAGameAWorld", "players")
players_path = os.path.join(mti.get_var("primary_world_path"),
                            "players")
_MAX_STACK_QTY = 99
poiDotExt = ".conf"  # formerly PLAYER_STORAGE_FILE_DOT_THEN_EXT
# debugs_list = list()
# dbga = os.path.join(bak_mt, "debug_archived")
# moPath = os.path.join(dbga, "2016", "03")
# debugs_list.append(os.path.join(moPath, "16.txt"))
# debugs_list.append(os.path.join(moPath, "17.txt"))
debug_txt_path = os.path.join(
    mti.get_var("profile_minetest_path"),
    "debug.txt"
)
min_date_string = None
# min_date_string = "2016-03-15 12:12:00"
debugDTFmt = "%Y-%m-%d %H:%M:%S"
is_start_now = False
interactive_enable = False


def is_yes(s):
    if s.lower() == "y":
        return True
    if s.lower() == "yes":
        return True
    return False


def confirm_min_date():
    global min_date_string
    while min_date_string is None:
        default_min_date_string = datetime.strftime(datetime.now(),
                                                    debugDTFmt)
        print("")
        print("Please enter starting date for player locations and"
              " block obtaining to be replayed (only used for inventory"
              " recovery feature).")
        answer = input("Replay Start [YYYY-MM-DD HH-mm-SS format]"
                       " (blank for " + default_min_date_string
                       + "): ")
        if len(answer.strip()) > 0:
            try:
                min_date = datetime.strptime(answer, debugDTFmt)
                tmp_string = datetime.strftime(min_date, debugDTFmt)
                confirm = input(tmp_string+" ok [Y/n]? ")
                if is_yes(confirm.strip()):
                    min_date_string = tmp_string
            except ValueError:
                print("Bad date format. Please try again.")
        else:
            is_start_now = True
            min_date_string = default_min_date_string
    print("Using start "+min_date_string)
    if is_start_now:
        print("  (which is the current time, so nothing will be"
              " replayed [this is the default just be extra careful,"
              " because if you run the replay function on the same part"
              " of the log more than once, that will double #of each"
              " item each player digs and double the quantity of those"
              " items in players offline storage folder])")
    print("")


offline_inv_name = "players_offline_storage"
# ^ formerly players_offline_storage_name
old_offline_inv_name = "player_storage"
# ^ formerly deprecated_players_offline_storage_name
# H:\Minetest\player_storage
g_offline_inv_path = os.path.join(
    mti.get_var("primary_world_path"),
    offline_inv_name
)
# ^ formerly players_offline_storage_path
g_old_off_inv_path = os.path.join(
    mti.get_var("primary_world_path"),
    old_offline_inv_name
)
# ^ formerly deprecated_players_offline_storage_path
if os.path.isdir(g_old_off_inv_path):
    print("moving \"" + g_old_off_inv_path
          + "\" to")
    print("  " + g_offline_inv_path)
    shutil.move(g_old_off_inv_path,
                g_offline_inv_path)
print("Using offline g_offline_inv_path:")
print("  " + g_offline_inv_path)
print("  (used for inventory recovery and other offline storage"
      " features)")
give_path = os.path.join(g_offline_inv_path, "give")
print("give_path:")
print("  (used for give commands for inventory leftover if more to"
      " transfer after filling destination inventory)")
# g_offline_inv_path = os.path.join(bak_worlds, "FCAGameAWorld",
#                                   offline_inv_name)
irl_person_csv_name = None
irl_person_csv_path = None
world_name = None
world_name = os.path.basename(
    os.path.abspath(mti.get_var("primary_world_path"))
)
print("")
print("Using world_name '"+str(world_name)+"'")


deprecated_irl_person_csv_name = (
    world_name + " - Minetest Users - Real Names.txt"
)
# ^ RENAMED to value below:
irl_person_csv_name = "irl_person_info.csv"  # in world dir
print("")
if os.path.isdir(mti.get_var("primary_world_path")):
    irl_person_csv_path = os.path.join(
        mti.get_var("primary_world_path"),
        irl_person_csv_name
    )
    if os.sep == "\\":
        deprecated_irl_person_csv_path = os.path.join(
            "H:\\Minetest",
            deprecated_irl_person_csv_name
        )
        if os.path.isfile(deprecated_irl_person_csv_name):
            print("moving \"" + deprecated_irl_person_csv_path
                  + "\" to")
            print("  " + irl_person_csv_path)
            os.rename(deprecated_irl_person_csv_path,
                      irl_person_csv_path)
    print("Using irl_person_csv_path:")
    print("  "+str(irl_person_csv_path))
    print("")
else:
    print("No world folder found, so leaving irl_person_csv_path as"
          " None")

print("")


class MinetestInventoryItem:
    owner = None  # optional, only used for debug output
    name = None
    qty = None
    param = None  # normally toolid
    suffix = None

    def push_qty(self, addend):
        """
        Sequential arguments:
        addend: Add this many, but if the addend is negative, take
        items.

        Returns: If addend is negative and player doesn't have enough,
            return negative; otherwise, return 0.
        """
        leftover = 0
        self.qty += addend
        if self.qty > _MAX_STACK_QTY:
            leftover = self.qty - _MAX_STACK_QTY
            self.qty = _MAX_STACK_QTY
        elif self.qty < 0:
            leftover = self.qty
            self.qty = 0
            self.name = "Empty"
            self.param = None
            self.suffix = None
        return leftover

    def get_item_as_inventory_line(self):
        global interactive_enable
        result = None
        is_msg = False
        if self.name is not None:
            if self.name != "Empty":
                if self.qty is not None:
                    result = "Item"
                    result += " "+self.name
                    if ((self.qty != 1) or
                            (self.param is not None) or
                            (self.suffix is not None)):
                        result += " "+str(self.qty)
                        if self.param is not None:
                            result += " "+self.param
                        if self.suffix is not None:
                            result += " "+self.suffix

                else:
                    owner_msg = ""
                    if self.owner is not None:
                        owner_msg = " owned by " + self.owner
                    print("ERROR in get_item_as_inventory_line: qty is"
                          " None for " + self.name+owner_msg)
                    is_msg = True
            else:
                result = "Empty"
        else:
            owner_msg = ""
            if self.owner is not None:
                owner_msg = " owned by "+self.owner
            print("ERROR in get_item_as_inventory_line: name is None"
                  " for item"+owner_msg)
            is_msg = True
        if interactive_enable:
            if is_msg:
                input("Press enter to continue...")
        return result

    def set_from_inventory_line(self, line):
        self.name = None
        self.qty = None
        self.param = None
        self.suffix = None
        if line != "Empty":
            parts = line.strip().split(" ")
            is_warning = False
            if ((len(parts) != 2) and (len(parts) != 3) and
                    (len(parts) != 4)):
                print("inventory has extra unknown params that will be"
                      " ignored but retained: " + line)
                is_warning = True
            if len(parts) >= 2:
                if parts[0] == "Item":
                    self.name = parts[1].strip()
                    if len(parts) > 2:
                        self.qty = int(parts[2].strip())
                        if len(parts) >= 4:
                            self.param = parts[3].strip()
                        if len(parts) > 4:
                            self.suffix = " " + " ".join(parts[5:])
                    else:
                        self.qty = 1
                else:
                    print("Not an item line: "+line)
                    is_warning = True
            else:
                print("Failed to parse line since too few ("
                      + len(parts) + ") param(s).")
                is_warning = True
            global interactive_enable
            if interactive_enable:
                if is_warning:
                    input("Press enter to continue...")
        else:
            self.name = "Empty"


class MinetestInventory:
    name = None
    width = None
    items = None

    def __init__(self):
        self.items = list()  # IS allowed to have duplicate names

    def push_item(self, item_id, qty):
        if item_id != "Empty":
            for index in range(0, len(self.items)):
                if self.items[index].name == item_id:
                    qty = self.items[index].push_qty(qty)
                    if qty == 0:
                        break
            if qty != 0:
                for index in range(0, len(self.items)):
                    if self.items[index].name == "Empty":
                        self.items[index].name = item_id
                        self.items[index].qty = 0
                        self.items[index].param = None
                        # TODO: ^ set this! id needed for tools (
                        #   itemstring format at <https://github.com/
                        #   minetest/minetest/blob/master/doc
                        #   /world_format.txt> )
                        self.items[index].suffix = None
                        qty = self.items[index].push_qty(qty)
                        if qty == 0:
                            break
        else:
            qty = 0
        return qty

    def write_to_stream(self, outs):
        global interactive_enable
        if self.name is not None:
            # if self.width is not None:
            if self.width is None:
                self.width = 0
            if self.items is not None:
                outs.write("List " + self.name + " "
                           + str(len(self.items)) + "\n")
                outs.write("Width " + str(self.width) + "\n")
                for item in self.items:
                    line = item.get_item_as_inventory_line()
                    if line is not None:
                        outs.write(line+"\n")
                outs.write("EndInventoryList"+"\n")
            else:
                print("ERROR in minetestinventory.write_to: items is"
                      " None")
                if interactive_enable:
                    input("Press enter to continue...")
            # else:
            #      print("ERROR in minetestinventory.write_to: width is"
            #            " None")
            #      input("Press enter to continue...")
        else:
            print("ERROR in minetestinventory.write_to: name is None")
            if interactive_enable:
                input("Press enter to continue...")


class MinetestPlayer:
    playerid = None
    _player_args = None
    inventories = None
    oops_list = None
    tag = None

    def __init__(self, playerid):
        self._player_args = {}
        self._player_args["breath"] = 11
        self._player_args["hp"] = playerid
        if playerid is not None:
            self._player_args["name"] = 20
        self._player_args["pitch"] = 24.9
        # ^ I'm not sure what the range is, so this is an example value.
        self._player_args["position"] = "(0.0,0.0,0.0)"
        self._player_args["version"] = 1
        self._player_args["yaw"] = 0.0
        self.playerid = playerid
        self.inventories = list()

    def set_pos(self, pos):
        """
        Set the multiplied (Irrlicht) internal pos from an actual
        (metric) pos.
        """
        if (len(pos) == 3):
            self._player_args["position"] = mt_to_irr(pos)
        else:
            print("Failed to set position since length of tuple"
                  " recieved is not 3: "+str(pos))

    def get_pos(self):
        """
        Get the actual (metric) pos from the internal multiplied
        (Irrlicht) pos.
        """
        result = None
        _p_a = self._player_args
        if _p_a is not None:
            if "position" in _p_a:
                if isinstance(_p_a["position"], str):
                    _p_a["position"] = literal_eval(_p_a["position"])
                element_count = len(_p_a["position"])

                if (element_count != 3):
                    # if element_count > 1:
                    if element_count == 2:
                        old_pos = _p_a["position"]
                        new_pos = old_pos[0], 80.0, old_pos[1]
                        self.set_pos(irr_to_mt(new_pos))
                        print("ERROR in get_pos: Element count "
                              + str(element_count)
                              + " too low (should have numbers for"
                              " 3 axes) for player position,"
                              " so repaired by using as x and z,"
                              " resulting in "+str(self.get_pos()))
                    elif element_count > 3:
                        self.set_pos(irr_to_mt(_p_a["position"]))
                        print("ERROR in get_pos: Element count "
                              + str(element_count) + " incorrect"
                              " (should have numbers for 3 axes) for"
                              " player position, so set to "
                              + str(self.get_pos()))
                    else:
                        self.set_pos(0, 0, 0)
                        print("ERROR in get_pos: Element count is "
                              + str(element_count)
                              + " too low (should have numbers for"
                              " 3 axes) for player position,"
                              " so it will become 0,0,0")

                # _p_a["position"] = (float(pos[0]),
                #                     float(pos[1]),
                #                     float(pos[2])
            else:
                self.set_pos(0, 0, 0)
                print("ERROR in get_pos: Missing position in _player"
                      "_args for player id "
                      + self.get_safe_player_id_quoted()
                      + " so setting to 0,0,0")
        else:
            print("ERROR in get_pos: Missing _player_args for player"
                  " id " + self.get_safe_player_id_quoted()
                  + " so setting to 0,0,0")
            self.set_pos(0, 0, 0)
        return irr_to_mt(_p_a["position"])

    def get_safe_player_id_quoted(self):
        result = None
        if self.player_id is None:
            result = "None"
        else:
            result = "'"+str(self.player_id)+"'"
        return result

    def push_item(self, item_id, qty):
        """
        Add an item to this player.
        Returns: how many didn't fit in any inventory lists
        """
        # TODO: Preserve itemstack metadata: tool wear, etc
        main_index = -1
        for index in range(0, len(self.inventories)):
            if self.inventories[index].name == "main":
                main_index = index
                break
        if main_index > -1:
            qty = self.inventories[main_index].push_item(item_id, qty)
        else:
            print("ERROR: no inventory List named 'main' for "
                  + self.playerid)
        if qty != 0:
            for index in range(0, len(self.inventories)):
                if self.inventories[index].name == "craft":
                    qty = self.inventories[index].push_item(item_id,
                                                            qty)
                    # break even if nonzero, since only have this one
                    # inventory left (no bag guaranteed)
                    break
        return qty

    def save(self):
        if "name" in self._player_args:
            player_path = os.path.join(players_path, self.playerid)
            self.save_as(player_path)

    def save_as(self, player_path):
        if "name" in self._player_args:
            outs = open(player_path, 'w')
            for this_key in self._player_args:
                outs.write(this_key + " = "
                           + str(self._player_args[this_key]) + "\n")
            outs.write("PlayerArgsEnd"+"\n")
            for inventory in self.inventories:
                # if type(inventory) is MinetestInventory:
                inventory.write_to_stream(outs)
                # else:
                #     print("ERROR in plr.save: '" + this_key
                #           + "' is not a MinetestInventory")
            outs.write("EndInventory"+"\n")
            if self.oops_list is not None:
                for line in self.oops_list:
                    outs.write(line+"\n")
            outs.close()
        else:
            print("ERROR in plr.save: missing 'name' in _player_args")

    def load(self):
        if self.playerid is not None and len(self.playerid.strip()) > 0:
            player_path = os.path.join(players_path, self.playerid)
            self.load_from_file(player_path)
        else:
            print("ERROR in plr.load: 'playerid' member was not set"
                  " (unique filename for players folder)")

    def load_from_file(self, player_path):
        section = "PlayerArgs"
        ins = None
        ins = open(player_path, 'r')
        line = True
        this_inv = None
        while line:
            line = ins.readline()
            if line:
                line = line.strip()
                if len(line) > 0:
                    ao = " = "
                    ao_index = line.find(ao)
                    if line == "PlayerArgsEnd":
                        section = "(commands)"
                    elif section == "PlayerArgs":
                        if ao_index > -1:
                            n = line[:ao_index].strip()
                            v = line[ao_index+len(ao):].strip()
                            self._player_args[n] = v
                    elif section == "(commands)":
                        width_opener = "Width "
                        list_opener = "List "
                        if line.startswith(list_opener):
                            l_n = None  # list name
                            l_n_ender = " "
                            l_n_i = len(list_opener)
                            l_n_end = line.find(l_n_ender, l_n_i+1)
                            if l_n_end > -1:
                                l_n = line[l_n_i:l_n_end].strip()
                            else:
                                l_n = line[l_n_i].strip()
                            if len(l_n) > 0:
                                this_inv = MinetestInventory()
                                this_inv.name = l_n
                                self.inventories.append(this_inv)
                            else:
                                print("ERROR: name for inventory"
                                      " item for " + self.playerid)
                        elif line == "EndInventoryList":
                            section = "(commands)"
                            this_inv = None
                        elif line == "EndInventory":
                            if this_inv is not None:
                                print("WARNING: EndInventory before"
                                      " EndInventoryList for "
                                      + self.playerid)
                            section = "(EOF)"
                        elif line.startswith(width_opener):
                            w_i = len(width_opener)
                            width_string = line[w_i:].strip()
                            if this_inv is not None:
                                try:
                                    this_inv.width = int(
                                        width_string
                                    )
                                except ValueError:
                                    print("ERROR: Failed to parse '"
                                          + width_string
                                          + "' as integer Width"
                                          " for " + self.playerid)
                            else:
                                print("ERROR: found Width before"
                                      " List for line '" + line
                                      + "' for " + self.playerid)
                        else:
                            item_opener = "Item "
                            isFree = line == "Empty"
                            isFree = line.startswith(item_opener)
                            if isFree:
                                this_item = MinetestInventoryItem()
                                this_item.set_from_inventory_line(
                                    line
                                )
                                this_item.owner = self.playerid
                                this_inv.items.append(this_item)
                            else:
                                print("ERROR: can't parse '" + line
                                      + "' for " + self.playerid)
                    elif section == "(EOF)":
                        print("ERROR: unknown line after"
                              " EndInventory (will be saved) for "
                              + self.playerid)
                        if self.oops_list is None:
                            self.oops_list = list()
                        self.oops_list.append(line)
        if ins is not None:
            ins.close()


player_file_indicator_string = "PlayerArgsEnd"
player_file_extension = ""  # player files have no extension in minetest
replay_file_ao = "="


def recover_player_files_by_content(recovery_source_path,
                                    dest_players_path):
    extra_path = os.path.join(dest_players_path, "extra_players")
    if os.path.isdir(recovery_source_path):
        folder_path = recovery_source_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if not os.path.isfile(sub_path):
                continue
            if sub_name.startswith("."):
                continue
            is_player_file = False
            ins = open(sub_path, 'r')
            name = None
            print("EXAMINING "+sub_name)
            line = True
            while line:
                line = ins.readline()
                if line:
                    ao = "="
                    ao_index = line.find(ao)
                    if ao_index > -1:
                        n = line[:ao_index].strip()
                        v = line[ao_index+len(ao):].strip()
                        if n == "name":
                            name = v
                            if is_player_file:
                                break
                    elif line.strip() == "PlayerArgsEnd":
                        is_player_file = True
                        if name is not None:
                            break
            ins.close()
            if is_player_file:
                dest_path = ""
                dest_path = os.path.join(dest_players_path, name)
                enableNew = name is not None
                if os.path.isfile(dest_path):
                    enableNew = False
                if enableNew:
                    shutil.copyfile(sub_path, dest_path)
                else:
                    if not os.path.isdir(extra_path):
                        os.makedirs(extra_path)
                    dest_path = os.path.join(extra_path,
                                             sub_name)
                    shutil.copyfile(sub_path, dest_path)
                print("  recovered to '" + dest_path + "'")


players = None


def load_players_offline_storage(offline_inv_path):
    global players
    players = {}
    if not os.path.exists(offline_inv_path):
        os.makedirs(offline_inv_path)
    else:
        folder_path = offline_inv_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if not os.path.isfile(sub_path):
                continue
            if sub_name.startswith("."):
                continue
            if not sub_name.endswith(poiDotExt):
                return
            playerid = sub_name[:-len(poiDotExt)]
            players[playerid] = get_dict_from_conf_file(
                sub_path,
                replay_file_ao
            )


def move_storage_to_players(offline_inv_path, plrs_path, give_cmds_path,
                            move_plr_enable=True):
    """
    Move all items in offline storage to players.

    Keyword arguments:
    plrs_path -- This must be the path to the players' data files.
    give_cmds_path -- This file will hold /give commands.
    move_plr_enable -- Enable changing the position of players.

    Returns:
    a list of give commands (only in cases where transfers failed)
    """
    # give_cmds_path: was formerly leftover_give_commands_folder_path
    # plrs_path: was formerly output_players_folder_path
    # move_plr_enable: was formerly change_player_position_enable
    gives = {}  # give commands (The keys are player ids.)
    if os.path.isdir(offline_inv_path):
        folder_path = offline_inv_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1] != "."):
                    if len(sub_name) > len(poiDotExt):
                        playerid = sub_name[:-len(poiDotExt)]
                        player_path = os.path.join(players_path,
                                                   playerid)
                        if os.path.isfile(player_path):
                            this_storage = get_dict_from_conf_file(
                                sub_path,
                                "="
                            )
                            plr = MinetestPlayer(playerid)
                            plr.load_from_file(player_path)
                            is_changed = False
                            for this_key in this_storage.keys():
                                if this_key != "position":
                                    item_id = this_key
                                    qty = int(this_storage[this_key])
                                    leftover = plr.push_item(item_id,
                                                             qty)
                                    if leftover != 0:
                                        line = "/give {} {} {}".format(
                                            plr.playerid,
                                            item_id,
                                            leftover
                                        )
                                        if playerid not in gives:
                                            gives[playerid] = list()
                                        gives[playerid].append(line)
                                    is_changed = True
                                else:
                                    if move_plr_enable:
                                        _p_a = plr._player_args
                                        _p_a["position"] = \
                                            this_storage[this_key]
                                        is_changed = True
                                        print("  moved " + playerid
                                              + " to "
                                              + _p_a["position"])
                            if is_changed:
                                plr.save_as(player_path)
                                print("  saved '"+player_path+"'")
                            if playerid in gives.keys():
                                give_commands = gives[playerid]
                                mode_string = 'w'
                                if not os.path.isdir(give_cmds_path):
                                    os.makedirs(give_cmds_path)
                                player_commands_path = os.path.join(
                                    give_cmds_path,
                                    playerid+".txt"
                                )
                                if os.path.isfile(player_commands_path):
                                    mode_string = 'a'
                                outs = open(player_commands_path,
                                            mode_string)
                                for line in give_commands:
                                    outs.write(line+"\n")
                                    print(line)
                                outs.close()
                            os.remove(sub_path)
                            # save_conf_from_dict(sub_path,
                            #                     this_storage, "=")
                        else:
                            print("WARNING: no playerid '" + playerid
                                  + "', so keeping storage file")
    else:
        print("ERROR: missing players' offline storage folder '"
              + offline_inv_path + "'")


def convert_storage_to_give_commands_DEPRECATED(offline_inv_path,
                                                output_folder_path,
                                                irl_person_csv_path):
    global players
    # if players is None:
    #     load_players_offline_storage(offline_inv_path)
    while True:
        print("")
        playerid = None
        playerid = input("Minetest Username: ")
        realNameS = None
        realNameS = input("Real Name: ")
        iuser_desc = "first initial + last name + grad year"
        identifiable_user_string = input(iuser_desc + ": ")
        if len(playerid) > 0:
            poi_path = os.path.join(offline_inv_path, playerid)
            if os.path.isfile(poi_path):
                # if len(realNameS) > 0:
                iuser_strp = identifiable_user_string.strip()
                if len(iuser_strp) > 0:
                    appends = open(irl_person_csv_path, 'a')
                    # line = (playerid.strip().replace(","," ")
                    #         + "," + realNameS.replace(","," ") + ",")
                    line = (playerid.strip().replace(",", " ")
                            + "," + realNameS + ","
                            + iuser_strp.replace(",", " "))
                    appends.append(line+"\n")
                    appends.close()
                    this_player = get_dict_from_conf_file(poi_path, "=")
                    position_string = None
                    # TODO: output_folder_path
                    for this_key in this_player:
                        if this_key != "position":
                            line = "/give {} {} {}".format(
                                playerid,
                                this_key,
                                this_player[this_key]
                            )
                            print(line)
                        else:
                            position_string = this_player[this_key]
                    if position_string is not None:
                        irr_pos = s_to_tuple(position_string)
                        # ^ irr_pos: 10 Irrlicht units per node
                        if len(irr_pos) == 3:
                            loc_s = irr_to_mt_s(irr_pos)
                            print("/teleport " + playerid + " " + loc_s)
                        else:
                            print("bad coords: " + loc_s)
                    appends.close()
                else:
                    print(iuser_desc
                          + " not accepted, so nothing will be done.")

            else:
                print("No storage file was found named '" + poi_path
                      + "'")
        else:
            break


def debug_log_replay_to_offline_player_storage(debug_txt_path,
                                               offline_inv_path,
                                               min_date_string):
    """
    Keyword arguments:
    offline_inv_path -- The offline storage path for, in this case.
    items that players can't fit into their inventories.
    """
    global players
    min_date = None
    if min_date_string is not None:
        min_date = datetime.strptime(min_date_string,
                                     debugDTFmt)
    print("This will only work if server is offline.")
    print("  (Using min date "+str(min_date)+")")
    input("  press enter to continue, otherwise exit this Window or"
          " Ctrl-C to terminate script in GNU/Linux systems...")
    if players is None:
        load_players_offline_storage(offline_inv_path)

    ins = open(debug_txt_path, 'r')
    line = True
    while line:
        line = ins.readline()
        if line:
            ao = ": ACTION[Server]: "
            ao_index = line.find(ao)
            # look for lines such as:
            # 2016-03-03 11:42:17: ACTION[Server]: 1234567your digs
            # default:stone at (-21,-81,-80)

            if ao_index > -1:
                date_string = line[:ao_index].strip()
                action_date = datetime.strptime(
                    date_string,
                    debugDTFmt
                )
                if (min_date is None) or (action_date >= min_date):
                    action_s = line[ao_index+len(ao):].strip()
                    name_ender = " digs "
                    name_end = action_s.find(name_ender)
                    delta = 1
                    if name_end < 0:
                        name_ender = " places node "
                        name_end = action_s.find(name_ender)
                        delta = -1
                    position_string = None
                    pos_s = None
                    at_delimiter = " at ("
                    is_enough_information = False
                    this_player = None
                    if name_end > -1:
                        # also save location to player file in
                        # MULTIPLIED BY 10 format such as:
                        # position = (-623.69,34.62,1246.17)
                        playerid = action_s[:name_end]
                        print("playerid:" + playerid)
                        ne_l = len(name_ender)
                        item_end = action_s.find(" ", name_end+ne_l)

                        if item_end > -1:
                            item_s = action_s[name_end + ne_l:item_end]
                            is_enough_information = True
                            if "digs" in name_ender:
                                broken = after_broken.get(item_s)
                                if broken is not None:
                                    item_s = broken
                                else:
                                    ab_openers = after_broken_startswith
                                    # ^ comes from minetestinfo.py
                                    for pat, full in ab_openers.items():
                                        if item_s.startswith(pat):
                                            item_s = full
                                            break
                            print("  " + item_s)
                            if playerid not in players:
                                players[playerid] = {}
                            this_player = players[playerid]
                            if item_s not in this_player:
                                this_player[item_s] = delta
                            else:
                                this_player[item_s] += delta
                    else:
                        name_ender = " punches object "
                        name_end = action_s.find(name_ender)
                        if name_end > -1:
                            playerid = action_s[:name_end]
                            print(playerid + ":")
                            is_enough_information = True
                            if playerid not in players:
                                players[playerid] = {}
                            this_player = players[playerid]

                    if is_enough_information:
                        at_delimiter_index = action_s.find(
                            at_delimiter
                        )
                        if at_delimiter_index > -1:
                            at_ender = ")"
                            at_end = action_s.find(
                                at_ender,
                                at_delimiter_index + len(at_delimiter)
                            )
                            if at_end > -1:
                                pos_s_i = (at_delimiter_index
                                           + len(at_delimiter))
                                pos_s = action_s[pos_s_i:at_end]
                                pos_strings = pos_s.split(",")
                                if len(pos_strings) == 3:
                                    coords = [float(pos_strings[0])*10,
                                              float(pos_strings[1])*10,
                                              float(pos_strings[2])*10]
                                    position_string = (
                                        "(" + str(coords[0]) + ","
                                        + str(coords[1]) + ","
                                        + str(coords[2]) + ")"
                                    )
                                else:
                                    print("WARNING: bad event coords '"
                                          + str(pos_strings) + "'")
                        if min_date is None:
                            print("  note: Saving since min_date is"
                                  " None")
                        else:
                            print("  note: Saving since "
                                  + datetime.strftime(action_date,
                                                      debugDTFmt)
                                  + " >= "
                                  + datetime.strftime(min_date,
                                                      debugDTFmt))

                    if position_string is not None:
                        this_player["position"] = position_string
                        print("  position: " + position_string)
                    if pos_s is not None:
                        # this_player["position"] = position_string
                        print("  block: " + pos_s)

    for playerid in players.keys():
        player_replay_path = os.path.join(
            offline_inv_path,
            playerid + poiDotExt
        )
        save_conf_from_dict(player_replay_path, players[playerid],
                            replay_file_ao)

    # ins.close()
    # outs = open(output_path, 'w')
    # outs.write(line+"\n")
    # outs.close()


def player_inventory_transfer(from_playerid, to_playerid):
    from_player_path = os.path.join(players_path, from_playerid)
    to_player_path = os.path.join(players_path, to_playerid)
    to_player_givescript_path = os.path.join(give_path, to_playerid)


def set_player_names_to_file_names():
    assignment_operator = "="
    correct_count = 0
    incorrect_count = 0
    # NOTE: uses global min_indent
    line_count = 1
    print(min_indent + "set_player_names_to_file_names:")
    if os.path.isdir(players_path):
        folder_path = players_path
        print(min_indent + "  Examining players:")
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1] != "."):
                    # print(min_indent + "    " + sub_name)
                    # stated_name = get_initial_value_from_conf(
                    #     sub_path,
                    #     "name",
                    #     "="
                    # )
                    stated_name = None
                    line_index = 0
                    if sub_path is not None:
                        if os.path.isfile(sub_path):
                            plr = MinetestPlayer(sub_name)
                            plr.load_from_file(sub_path)
                            _p_a = plr._player_args
                            if "name" in _p_a:
                                if _p_a["name"] is not None:
                                    if len(_p_a["name"]) > 0:
                                        if sub_name == _p_a["name"]:
                                            # ^ purposely case sensitive
                                            #   especially for minetest
                                            #   linux version
                                            correct_count += 1
                                        else:
                                            incorrect_count += 1

                                            print(
                                                min_indent + "      "
                                                "Changing incorrect"
                                                " name "
                                                + _p_a["name"]
                                                + " found in "
                                                + sub_name
                                            )
                                            _p_a["name"] = sub_name
                                            plr.save()
                                    else:
                                        print(min_indent
                                              + "      WARNING: name is"
                                              " blank in "+sub_path)
                                else:
                                    print(min_indent + "      WARNING:"
                                          " name not found in "
                                          + sub_path)

                        # else:
                        #     print(min_indent + "    ERROR in"
                        #           " set_player_names_to_file_names: '"
                        #           + str(sub_path)
                        #           + "' is not a file.")
                    else:
                        print(min_indent + "    ERROR in"
                              " set_player_names_to_file_names: path is"
                              " None.")

    print(min_indent + "  Summary:")
    # +" of set_player_names_to_file_names:"
    print(min_indent + "    " + str(correct_count)
          + " correct name(s)")
    print(min_indent + "    " + str(incorrect_count)
          + " incorrect name(s)")

# plrs = os.path.join(bak_mt, "worlds", "FCAGameAWorld", "players")
# recover_player_files_by_content("C:\\1.RaiseDataRecovery", plrs)

# ## RESTORE ITEMS FROM DEBUG.TXT:
# log_path = os.path.join(
#     bak_mt,
#     "debug.txt"
# )
# "C:\Users\jgustafson\Desktop\Backup\fcalocal\home\owner\.minetest"
# "\debug_archived\2016\03\"
# # debug_log_replay_to_offline_player_storage(
# #     log_path,
# #     g_offline_inv_path,
# #     min_date_string
# # )

# confirm_min_date()
# # for debug_path in debugs_list:
# #     debug_log_replay_to_offline_player_storage(
# #         debug_path,
# #         g_offline_inv_path,
# #         min_date_string
# #     )
# debug_log_replay_to_offline_player_storage(
#     debug_txt_path,
#     g_offline_inv_path,
#     min_date_string
# )


min_date_string = "2016-03-21 00:00:00"
log_path = os.path.join(
    bak_mt,
    "debug 2017-03-24 stolen panels, cables, battery boxes ONLY.txt"
)
debug_log_replay_to_offline_player_storage(
    log_path,
    g_offline_inv_path,
    min_date_string
)


def switch_player_file_contents(player1_path, player2_path):
    # switches everything except name

    player1 = MinetestPlayer(os.path.basename(player1_path))
    player2 = MinetestPlayer(os.path.basename(player2_path))
    tmp_id = player1.playerid
    tmp_name = player1.get_name()
    player1.set_name(player2.get_name())
    player2.set_name(tmp_name)
    player1.playerid = player2.playerid
    player2.playerid = tmp_id
    player1.save()
    player2.save()

# convert_storage_to_give_commands_DEPRECATED(
#     g_offline_inv_path,
#     give_path, irl_person_csv_path
# )

# move_storage_to_players(g_offline_inv_path, players_path,
# give_path, move_plr_enable=True)


# ## FOR TESTING PURPOSES:
#  C:\Users\jgustafson\Desktop\Backup\fcalocal\home\owner\
#  .minetest\worlds\FCAGameAWorld\players\
# plr = MinetestPlayer("mrg")
# plr.load()
# item_id = "default:glass"
# leftover = plr.push_item(item_id,1286)
# print("/give "+plr.playerid+" "+item_id+" "+str(leftover))
# plr.playerid = "mrg-try1"
# plr.save()
if os.sep == "\\":
    print("# REMEMBER If you later copy player files to a GNU/Linux"
          " machine cd to your world's players folder then run dos2unix"
          " such as:")
    print("    sudo apt-get update")
    print("    sudo apt-get install dos2unix")
    print("    cd "
          + os.path.join(mti.get_var("primary_world_path"),
                         "players"))
    print("    dos2unix *")
    print("# to convert line endings, otherwise inventory and all"
          " PlayerArgs will be loaded as blank (if using player files"
          " with Windows line endings on GNU/Linux copy of minetest).")
