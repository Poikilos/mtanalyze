
#purpose: assist in data recovery where original filename is not known
#KNOWN ISSUES:
# * (status:closed reason:no solution) assumes name specified in file is same as id (filename)
import shutil
import os
from datetime import datetime

from expertmm import *
from minetestinfo import *

import time
from ast import literal_eval # as make_tuple

#C:\Users\jgustafson\Desktop\Backup\fcalocal\home\owner\.minetest\worlds\FCAGameAWorld\players
#minetest_players_path = "C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\worlds\\FCAGameAWorld\\players"
players_path = os.path.join(minetestinfo.get_var("primary_world_path"), "players")
_MAX_STACK_QTY = 99
PLAYER_STORAGE_FILE_DOT_THEN_EXT = ".conf"
#debugs_list = list()
#debugs_list.append("C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\debug_archived\\2016\\03\\16.txt")
#debugs_list.append("C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\debug_archived\\2016\\03\\17.txt")
debug_txt_path = os.path.join(minetestinfo.get_var("profile_minetest_path"), "debug.txt")
min_date_string = None
#min_date_string = "2016-03-15 12:12:00"
DEBUG_TXT_TIME_FORMAT_STRING="%Y-%m-%d %H:%M:%S"
is_start_now = False
interactive_enable = False


def confirm_min_date():
    global min_date_string
    while min_date_string is None:
        default_min_date_string = datetime.strftime(datetime.now(), DEBUG_TXT_TIME_FORMAT_STRING)
        print("")
        print("Please enter starting date for player locations and block obtaining to be replayed (only used for inventory recovery feature).")
        try:
            answer = raw_input("Replay Start [YYYY-MM-DD HH-mm-SS format] (blank for "+default_min_date_string+"): ")
        except:
            answer = input("Replay Start [YYYY-MM-DD HH-mm-SS format] (blank for "+default_min_date_string+"): ")
        if len(answer.strip())>0:
            try:
                min_date = datetime.strptime(answer, DEBUG_TXT_TIME_FORMAT_STRING)
                tmp_string = datetime.strftime(min_date, DEBUG_TXT_TIME_FORMAT_STRING)
                try:
                    confirm = raw_input(tmp_string+" ok [Y/n]? ")
                except:
                    confirm = input(tmp_string+" ok [Y/n]? ")
                if confirm.strip().lower()=="y" or confirm.strip().lower()=="yes":
                    min_date_string = tmp_string
            except:
                print("Bad date format. Please try again.")
        else:
            is_start_now = True
            min_date_string = default_min_date_string
    print("Using start "+min_date_string)
    if is_start_now:
        print("  (which is the current time, so nothing will be replayed [this is the default just be extra careful, because if you run the replay function on the same part of the log more than once, that will double #of each item each player digs and double the quantity of those items in players offline storage folder])")
    print("")
    

players_offline_storage_name = "players_offline_storage"
deprecated_players_offline_storage_name = "player_storage"
#H:\Minetest\player_storage
players_offline_storage_path = os.path.join(minetestinfo.get_var("primary_world_path"), players_offline_storage_name)
deprecated_players_offline_storage_path = os.path.join(minetestinfo.get_var("primary_world_path"),deprecated_players_offline_storage_name)
if os.path.isdir(deprecated_players_offline_storage_path):
    print("moving \""+deprecated_players_offline_storage_path+"\" to")
    print("  "+players_offline_storage_path)
    shutil.move(deprecated_players_offline_storage_path, players_offline_storage_path)
print("Using offline players_offline_storage_path:")
print("  "+players_offline_storage_path)
print("  (used for inventory recovery and other offline storage features)")
give_path = os.path.join(players_offline_storage_path, "give")
print("give_path:")
print("  (used for give commands for inventory leftover if more to transfer after filling destination inventory)")
#players_offline_storage_path = os.path.join("C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\worlds\\FCAGameAWorld", players_offline_storage_name)
irl_person_csv_name = None
irl_person_csv_path = None
world_name = None
try:
    world_name = os.path.basename(os.path.abspath(minetestinfo.get_var("primary_world_path")))
    print("")
    print("Using world_name '"+str(world_name)+"'")

except:
    print("Could not finish getting world folder name.")
    view_traceback()
try:
    deprecated_irl_person_csv_name = world_name + " - Minetest Users - Real Names.txt"  #RENAMED to:
    irl_person_csv_name = "irl_person_info.csv"
    # C:\Users\jgustafson\Desktop\Backup\fcalocal\home\owner\.minetest\worlds\FCAGameAWorld\irl_person_info.csv
    print("")
    if os.path.isdir(minetestinfo.get_var("primary_world_path")):
        irl_person_csv_path = os.path.join(minetestinfo.get_var("primary_world_path"), irl_person_csv_name)
        if os.sep=="\\":
            deprecated_irl_person_csv_path = os.path.join("H:\\Minetest", deprecated_irl_person_csv_name)
            if os.path.isfile(deprecated_irl_person_csv_name):
                print("moving \""+deprecated_irl_person_csv_path+"\" to")
                print("  "+irl_person_csv_path)
                os.rename(deprecated_irl_person_csv_path, irl_person_csv_path)
        print("Using irl_person_csv_path:")
        print("  "+str(irl_person_csv_path))
        print("")
    else:
        print("No world folder found, so leaving irl_person_csv_path as None")
except:
    print("Could not finish building irl_person_csv_path.")
    view_traceback()

print("")

class MinetestInventoryItem:
    owner = None  # optional, only used for debug output
    name = None
    qty = None
    param = None  # normally toolid
    suffix = None

    #If addend is negative, will return negative if can't take that many, otherwise 0
    def push_qty(self, addend):
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
            if self.name!="Empty":
                if self.qty is not None:
                    result = "Item"
                    result += " "+self.name
                    if (self.qty!=1) or (self.param is not None) or (self.suffix is not None):
                        result += " "+str(self.qty)
                        if self.param is not None:
                            result += " "+self.param
                        if self.suffix is not None:
                            result += " "+self.suffix

                else:
                    owner_msg = ""
                    if self.owner is not None:
                        owner_msg = " owned by "+self.owner
                    print("ERROR in get_item_as_inventory_line: qty is None for "+self.name+owner_msg)
                    is_msg = True
            else:
                result = "Empty"
        else:
            owner_msg = ""
            if self.owner is not None:
                owner_msg = " owned by "+self.owner
            print("ERROR in get_item_as_inventory_line: name is None for item"+owner_msg)
            is_msg = True
        if interactive_enable:
            if is_msg:
                try:
                    raw_input("Press enter to continue...")
                except:
                    input("Press enter to continue...")
        return result

    def set_from_inventory_line(self, line):
        self.name = None
        self.qty = None
        self.param = None
        self.suffix = None
        if line!="Empty":
            parts = line.strip().split(" ")
            is_warning = False
            if (len(parts)!=2) and (len(parts)!=3) and (len(parts)!=4):
                print("inventory has extra unknown params that will be ignored but retained: "+line)
                is_warning = True
            if len(parts)>=2:
                if parts[0]=="Item":
                    self.name = parts[1].strip()
                    if len(parts)>2:
                        self.qty = int(parts[2].strip())
                        if len(parts)>=4:
                            self.param = parts[3].strip()
                        if len(parts)>4:
                            self.suffix = " " + " ".join(parts[5:])
                    else:
                        self.qty = 1
                else:
                    print("Not an item line: "+line)
                    is_warning = True
            else:
                print("Failed to parse line since too few ("+len(parts)+") param(s).")
                is_warning = True
            global interactive_enable
            if interactive_enable:
                if is_warning:
                    try:
                        raw_input("Press enter to continue...")
                    except:
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
        if item_id!="Empty":
            for index in range(0,len(self.items)):
                if self.items[index].name==item_id:
                    qty = self.items[index].push_qty(qty)
                    if qty==0:
                        break
            if qty!=0:
                for index in range(0,len(self.items)):
                    if self.items[index].name=="Empty":
                        self.items[index].name = item_id
                        self.items[index].qty = 0
                        self.items[index].param = None  #TODO: set this! id needed for tools (see itemstring format at https://github.com/minetest/minetest/blob/master/doc/world_format.txt )
                        self.items[index].suffix = None
                        qty = self.items[index].push_qty(qty)
                        if qty==0:
                            break
        else:
            qty = 0
        return qty

    def write_to_stream(self, outs):
        global interactive_enable
        if self.name is not None:
            #if self.width is not None:
            if self.width is None:
                self.width = 0
            if self.items is not None:
                outs.write("List "+self.name+" "+str(len(self.items))+"\n")
                outs.write("Width "+str(self.width)+"\n")
                for item in self.items:
                    line = item.get_item_as_inventory_line()
                    if line is not None:
                        outs.write(line+"\n")
                outs.write("EndInventoryList"+"\n")
            else:
                print("ERROR in minetestinventory.write_to: items is None")
                if interactive_enable:
                    try:
                        raw_input("Press enter to continue...")
                    except:
                        input("Press enter to continue...")
            #else:
            #    print("ERROR in minetestinventory.write_to: width is None")
            #    raw_input("Press enter to continue...")
        else:
            print("ERROR in minetestinventory.write_to: name is None")
            if interactive_enable:
                try:
                    raw_input("Press enter to continue...")
                except:
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
        self._player_args["pitch"] = 24.9  # not sure what range is, so using an example
        self._player_args["position"] = "(0.0,0.0,0.0)"
        self._player_args["version"] = 1
        self._player_args["yaw"] = 0.0
        self.playerid = playerid
        self.inventories = list()
    
    #Set multiplied internal pos using actual pos
    def set_pos(self, pos):
        if (len(pos)==3):
            self._player_args["position"] = float(pos[0])*minetest_player_pos_multiplier, float(pos[1])*minetest_player_pos_multiplier, float(pos[2])*minetest_player_pos_multiplier
        else:
            print("Failed to set position since length of tuple recieved is not 3: "+str(pos))

    #Get actual pos from internal multiplied pos
    def get_pos(self):
        result = None
        if self._player_args is not None:
            if "position" in self._player_args:
                if isinstance(self._player_args["position"], str):
                    self._player_args["position"] = literal_eval(self._player_args["position"])
                element_count = len(self._player_args["position"])
                
                if (element_count!=3):
                    #if element_count>1:
                    if element_count==2:
                        self.set_pos(self._player_args["position"][0]/minetest_player_pos_multiplier, 8.0, self._player_args["position"][1]/minetest_player_pos_multiplier)
                        print("ERROR in get_pos: Element count "+str(element_count)+" too low (should have numbers for 3 axes) for player position, so repaired by using as x and z, resulting in "+str(self.get_pos()))
                    elif element_count>3:
                        self.set_pos(self._player_args["position"][0]/minetest_player_pos_multiplier, self._player_args["position"][1]/minetest_player_pos_multiplier, self._player_args["position"][2]/minetest_player_pos_multiplier)
                        print("ERROR in get_pos: Element count "+str(element_count)+" incorrect (should have numbers for 3 axes) for player position, so set to "+str(self.get_pos()))
                    else:
                        self.set_pos(0,0,0)
                        print("ERROR in get_pos: Element count "+str(element_count)+" too low (should have numbers for 3 axes) for player position, so set to 0,0,0")
                
                #self._player_args["position"] = float(pos[0]), float(pos[1]), float(pos[2])
            else:
                self.set_pos(0,0,0)
                print("ERROR in get_pos: Missing position in _player_args for player id "+self.get_safe_player_id_quoted()+" so setting to 0,0,0")
        else:
            print("ERROR in get_pos: Missing _player_args for player id "+self.get_safe_player_id_quoted()+" so setting to 0,0,0")
            self.set_pos(0,0,0)
        return self._player_args["position"][0]/minetest_player_pos_multiplier, self._player_args["position"][1]/minetest_player_pos_multiplier, self._player_args["position"][2]/minetest_player_pos_multiplier
    
    def get_safe_player_id_quoted(self):
        result = None
        if self.player_id is None:
            result = "None"
        else:
            result = "'"+str(self.player_id)+"'"
        return result    
    # returns how many didnt' fit in any inventory lists
    def push_item(self, item_id, qty):
        main_index = -1
        for index in range(0,len(self.inventories)):
            if self.inventories[index].name=="main":
                main_index = index
                break
        if main_index>-1:
            qty = self.inventories[main_index].push_item(item_id, qty)
        else:
            print("ERROR: no inventory List named 'main' for "+self.playerid)
        if qty!=0:
            for index in range(0,len(self.inventories)):
                if self.inventories[index].name=="craft":
                    qty = self.inventories[index].push_item(item_id, qty)
                    #break even if nonzero, since only have this one inventory left (no bag guaranteed)
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
                outs.write(this_key+" = "+str(self._player_args[this_key])+"\n")
            outs.write("PlayerArgsEnd"+"\n")
            for inventory in self.inventories:
                #if type(inventory) is MinetestInventory:
                inventory.write_to_stream(outs)
                #else:
                #    print("ERROR in minetestplayer.save: '"+this_key+"' is not a MinetestInventory")
            outs.write("EndInventory"+"\n")
            if self.oops_list is not None:
                for line in self.oops_list:
                    outs.write(line+"\n")
            outs.close()
        else:
            print("ERROR in minetestplayer.save: missing 'name' in _player_args")

    def load(self):
        if self.playerid is not None and len(self.playerid.strip())>0:
            player_path = os.path.join(players_path, self.playerid)
            self.load_from_file(player_path)
        else:
            print("ERROR in minetestplayer.load: 'playerid' member was not set (unique filename for players folder)")

    def load_from_file(self, player_path):
        section = "PlayerArgs"
        ins = None
        try:
            ins = open(player_path, 'r')
            line = True
            this_inventory = None
            while line:
                line = ins.readline()
                if line:
                    line = line.strip()
                    if len(line)>0:
                        ao = " = "
                        ao_index = line.find(ao)
                        if line=="PlayerArgsEnd":
                            section = "(commands)"
                        elif section=="PlayerArgs":
                            if ao_index>-1:
                                n = line[:ao_index].strip()
                                v = line[ao_index+len(ao):].strip()
                                self._player_args[n] = v
                        elif section=="(commands)":
                            width_opener = "Width "
                            list_opener = "List "
                            if len(line)>len(list_opener) and line[:len(list_opener)]==list_opener:
                                list_name = None
                                list_name_ender = " "
                                list_name_index = len(list_opener)
                                list_name_ender_index = line.find(list_name_ender, list_name_index+1)
                                if list_name_ender_index>-1:
                                    list_name = line[list_name_index:list_name_ender_index].strip()
                                else:
                                    list_name = line[list_name_index].strip()
                                if len(list_name)>0:
                                    this_inventory = MinetestInventory()
                                    this_inventory.name = list_name
                                    self.inventories.append(this_inventory)
                                else:
                                    print("ERROR: name for inventory item for "+self.playerid)
                            elif line=="EndInventoryList":
                                section = "(commands)"
                                this_inventory = None
                            elif line=="EndInventory":
                                if this_inventory is not None:
                                    print("WARNING: EndInventory before EndInventoryList for "+self.playerid)
                                section = "(EOF)"
                            elif len(line)>len(width_opener) and line[:len(width_opener)]==width_opener:
                                width_string = line[len(width_opener):].strip()
                                if this_inventory is not None:
                                    try:
                                        this_inventory.width = int(width_string)
                                    except:
                                        print("ERROR: Failed to parse '"+width_string+"' as integer Width for "+self.playerid)
                                else:
                                    print("ERROR: found Width before List for line '"+line+"' for "+self.playerid)
                            else:
                                item_opener = "Item "
                                if (line=="Empty") or (len(line)>len(item_opener) and line[:len(item_opener)]==item_opener):
                                    this_item = MinetestInventoryItem()
                                    this_item.set_from_inventory_line(line)
                                    this_item.owner = self.playerid
                                    this_inventory.items.append(this_item)
                                else:
                                    print("ERROR: can't parse '"+line+"' for "+self.playerid)
                        elif section=="(EOF)":
                            print("ERROR: unknown line after EndInventory (will be saved) for "+self.playerid)
                            if self.oops_list is None:
                                self.oops_list = list()
                            self.oops_list.append(line)
        except:
            print("Could not finish minetestplayer.load_from_file:")
            view_traceback()
        try:
            if ins is not None:
                ins.close()
        except:
            pass


player_file_indicator_string = "PlayerArgsEnd"
player_file_extension = ""  # player files have no extension in minetest
replay_file_ao = "="
def recover_player_files_by_content(recovery_source_path, dest_players_path):
    extra_path = os.path.join(dest_players_path, "extra_players")
    if os.path.isdir(recovery_source_path):
        folder_path = recovery_source_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path,sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1]!="."):
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
                            if ao_index>-1:
                                n = line[:ao_index].strip()
                                v = line[ao_index+len(ao):].strip()
                                if n == "name":
                                    name = v
                                    if is_player_file:
                                        break
                            elif line.strip()=="PlayerArgsEnd":
                                is_player_file = True
                                if name is not None:
                                    break
                    ins.close()
                    if is_player_file:
                        dest_path = ""
                        dest_path = os.path.join(dest_players_path, name)
                        if (name is not None) and (not os.path.isfile(dest_path)):
                            shutil.copyfile(sub_path, dest_path)
                        else:
                            if not os.path.isdir(extra_path):
                                os.makedirs(extra_path)
                            dest_path = os.path.join(extra_path, sub_name)
                            shutil.copyfile(sub_path, dest_path)
                        print("  recovered to '"+dest_path+"'")
players = None
def load_players_offline_storage(this_players_offline_storage_path):
    global players
    players = {}
    if not os.path.exists(this_players_offline_storage_path):
        os.makedirs(this_players_offline_storage_path)
    else:
        folder_path = this_players_offline_storage_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path,sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1]!="."):
                    if (len(sub_name)>4) and (sub_name[-len(PLAYER_STORAGE_FILE_DOT_THEN_EXT):]==PLAYER_STORAGE_FILE_DOT_THEN_EXT):
                        playerid = sub_name[:-len(PLAYER_STORAGE_FILE_DOT_THEN_EXT)]
                        players[playerid] = get_dict_from_conf_file(sub_path, replay_file_ao)

#returns list of give commands if has problem
def move_storage_to_players(this_players_offline_storage_path, output_players_folder_path, leftover_give_commands_folder_path, change_player_position_enable=True):
    give_commands_by_playerid = {}
    if os.path.isdir(this_players_offline_storage_path):
        folder_path = this_players_offline_storage_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path,sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1]!="."):
                    if len(sub_name) > len(PLAYER_STORAGE_FILE_DOT_THEN_EXT):
                        playerid = sub_name[:-len(PLAYER_STORAGE_FILE_DOT_THEN_EXT)]
                        player_path = os.path.join(players_path, playerid)
                        if os.path.isfile(player_path):
                            this_storage = get_dict_from_conf_file(sub_path, "=")
                            minetestplayer = MinetestPlayer(playerid)
                            minetestplayer.load_from_file(player_path)
                            is_changed = False
                            for this_key in this_storage.keys():
                                if this_key != "position":
                                    item_id = this_key
                                    qty = int(this_storage[this_key])
                                    leftover = minetestplayer.push_item(item_id, qty)
                                    if leftover!=0:
                                        line = "/give "+minetestplayer.playerid+" "+item_id+" "+str(leftover)
                                        if playerid not in give_commands_by_playerid:
                                            give_commands_by_playerid[playerid] = list()
                                        give_commands_by_playerid[playerid].append(line)
                                    is_changed = True
                                else:
                                    if change_player_position_enable:
                                        minetestplayer._player_args["position"] = this_storage[this_key]
                                        is_changed = True
                                        print("  moved "+playerid+" to "+minetestplayer._player_args["position"])
                            if is_changed:
                                minetestplayer.save_as(player_path)
                                print("  saved '"+player_path+"'")
                            if playerid in give_commands_by_playerid.keys():
                                give_commands = give_commands_by_playerid[playerid]
                                mode_string = 'w'
                                if not os.path.isdir(leftover_give_commands_folder_path):
                                    os.makedirs(leftover_give_commands_folder_path)
                                player_commands_path = os.path.join(leftover_give_commands_folder_path, playerid+".txt")
                                if os.path.isfile(player_commands_path):
                                    mode_string = 'a'
                                outs = open(player_commands_path, mode_string)
                                for line in give_commands:
                                    outs.write(line+"\n")
                                    print(line)
                                outs.close()
                            os.remove(sub_path)  # save_conf_from_dict(sub_path, this_storage, "=")
                        else:
                            print("WARNING: no playerid '"+playerid+"', so keeping storage file")
    else:
        print("ERROR: missing players' offline storage folder '"+this_players_offline_storage_path+"'")


def convert_storage_to_give_commands_DEPRECATED(this_players_offline_storage_path, output_folder_path, irl_person_csv_path):
    global players
    #if players is None:
    #    load_players_offline_storage(this_players_offline_storage_path)
    while True:
        print("")
        playerid = None
        try:
            playerid = raw_input("Minetest Username: ")
        except:
            playerid = input("Minetest Username: ")
        real_name_string = None
        try:
            real_name_string = raw_input("Real Name: ")
        except:
            real_name_string = input("Real Name: ")
        identifiable_user_description = "first initial + last name + grad year"
        try:
            identifiable_user_string = raw_input(identifiable_user_description+": ")
        except:
            identifiable_user_string = input(identifiable_user_description+": ")
        if len(playerid)>0:
            player_storage_path = os.path.join(this_players_offline_storage_path, playerid)
            if os.path.isfile(player_storage_path):
                #if len(real_name_string)>0:
                identifiable_user_string_strip = identifiable_user_string.strip()
                if len(identifiable_user_string_strip)>0:
                    appends = open(irl_person_csv_path, 'a')
                    #line = playerid.strip().replace(","," ")+","+real_name_string.replace(","," ")+","
                    line = playerid.strip().replace(","," ")+","+real_name_string+","+identifiable_user_string_strip.replace(","," ")
                    appends.append(line+"\n")
                    appends.close()
                    this_player = get_dict_from_conf_file(player_storage_path, "=")
                    position_string = None
                    #TODO: output_folder_path
                    for this_key in this_player:
                        if this_key!="position":
                            line = "/give "+playerid+" "+this_key+" "+str(this_player[this_key])
                            print(line)
                        else:
                            position_string = this_player[this_key]
                    if position_string is not None:
                        ten_to_one_coords = get_tuple_from_notation(position_string)
                        if len(ten_to_one_coords)==3:
                            location_string = str(ten_to_one_coords[0]/10)+","+str(ten_to_one_coords[1]/10)+","+str(ten_to_one_coords[2]/10)
                            print("/teleport "+playerid+" "+location_string)
                        else:
                            print("bad coords: "+location_string)
                    appends.close()
                else:
                    print(identifiable_user_description+" not accepted, so nothing will be done.")

            else:
                print("No storage file was found named '"+player_storage_path+"'")
        else:
            break

def debug_log_replay_to_offline_player_storage(debug_txt_path, this_players_offline_storage_path, min_date_string):
    global players
    min_date = None
    if min_date_string is not None:
        min_date = datetime.strptime(min_date_string, DEBUG_TXT_TIME_FORMAT_STRING)
    print("This will only work if server is offline.")
    print("  (Using min date "+str(min_date)+")")
    try:
        raw_input("  press enter to continue, otherwise exit this Window or Ctrl-C to terminate script in GNU/Linux systems...")
    except:
        input("  press enter to continue, otherwise exit this Window or Ctrl-C to terminate script in GNU/Linux systems...")
    if players is None:
        load_players_offline_storage(this_players_offline_storage_path)

    ins = open(debug_txt_path, 'r')
    line = True
    while line:
        line = ins.readline()
        if line:
            ao = ": ACTION[Server]: "
            ao_index = line.find(ao)
            #look for lines such as:
            #2016-03-03 11:42:17: ACTION[Server]: 1234567your digs default:stone at (-21,-81,-80)

            if ao_index>-1:
                date_string = line[:ao_index].strip()
                action_date = datetime.strptime(date_string, DEBUG_TXT_TIME_FORMAT_STRING)
                if (min_date is None) or (action_date>=min_date):
                    action_string = line[ao_index+len(ao):].strip()
                    name_ender = " digs "
                    name_ender_index = action_string.find(name_ender)
                    delta = 1
                    if name_ender_index < 0:
                        name_ender = " places node "
                        name_ender_index = action_string.find(name_ender)
                        delta = -1
                    position_string = None
                    position_one_to_one_string = None
                    at_delimiter = " at ("
                    is_enough_information = False
                    this_player = None
                    if name_ender_index > -1:
                        #also save location to player file in MULTIPLIED BY 10 format such as:
                        #position = (-623.69,34.62,1246.17)
                        playerid = action_string[:name_ender_index]
                        print("playerid:"+playerid)
                        item_ender_index = action_string.find(" ",name_ender_index+len(name_ender))

                        if item_ender_index > -1:
                            item_string = action_string[name_ender_index+len(name_ender):item_ender_index]
                            is_enough_information = True
                            if "digs" in name_ender:
                                if item_string in after_broken:
                                    item_string = after_broken[item_string]
                                else:
                                    for item_startswith in after_broken_startswith:
                                        if item_startswith == item_string[:len(item_startswith)]:
                                            item_string = after_broken_startswith[item_startswith]
                                            break
                            print("  "+item_string)
                            if playerid not in players:
                                players[playerid] = {}
                            this_player = players[playerid]
                            if item_string not in this_player:
                                this_player[item_string] = delta
                            else:
                                this_player[item_string] += delta
                    else:
                        name_ender = " punches object "
                        name_ender_index = action_string.find(name_ender)
                        if name_ender_index > -1:
                            playerid = action_string[:name_ender_index]
                            print(playerid+":")
                            is_enough_information = True
                            if playerid not in players:
                                players[playerid] = {}
                            this_player = players[playerid]

                    if is_enough_information:
                        at_delimiter_index = action_string.find(at_delimiter)
                        if at_delimiter_index>-1:
                            at_ender = ")"
                            at_ender_index = action_string.find(at_ender,at_delimiter_index+len(at_delimiter))
                            if at_ender_index>-1:
                                position_one_to_one_string = action_string[at_delimiter_index+len(at_delimiter):at_ender_index]
                                pos_strings = position_one_to_one_string.split(",")
                                if len(pos_strings)==3:
                                    coords = [float(pos_strings[0])*10, float(pos_strings[1])*10, float(pos_strings[2])*10]
                                    position_string = "(" + str(coords[0])+","+str(coords[1])+","+str(coords[2]) + ")"
                                else:
                                    print("WARNING: bad event coords '"+str(pos_strings)+"'")
                        if min_date is None:
                            print("  note: Saving since min_date is None")
                        else:
                            print("  note: Saving since "+datetime.strftime(action_date,DEBUG_TXT_TIME_FORMAT_STRING)+" >= "+datetime.strftime(min_date,DEBUG_TXT_TIME_FORMAT_STRING))

                    if position_string is not None:
                        this_player["position"] = position_string
                        print("  position: "+position_string)
                    if position_one_to_one_string is not None:
                        #this_player["position"] = position_string
                        print("  block: "+position_one_to_one_string)

    for playerid in players.keys():
        player_replay_path = os.path.join(this_players_offline_storage_path, playerid+PLAYER_STORAGE_FILE_DOT_THEN_EXT)
        save_conf_from_dict(player_replay_path, players[playerid], replay_file_ao)

    #ins.close()
    #outs = open(output_path, 'w')
    #outs.write(line+"\n")
    #outs.close()

def player_inventory_transfer(from_playerid, to_playerid):
    from_player_path = os.path.join(players_path, from_playerid)
    to_player_path = os.path.join(players_path, to_playerid)
    to_player_givescript_path = os.path.join(give_path, to_playerid)

def set_player_names_to_file_names():
    assignment_operator = "="
    correct_count = 0
    incorrect_count = 0
    #NOTE: uses global min_indent
    line_count = 1
    print(min_indent+"set_player_names_to_file_names:")
    if os.path.isdir(players_path):
        folder_path = players_path
        print(min_indent+"  Examining players:")
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path,sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1]!="."):
                    #print(min_indent+"    "+sub_name)
                    #stated_name = get_initial_value_from_conf(sub_path, "name", "=")
                    stated_name = None
                    line_index = 0
                    if sub_path is not None:
                        if os.path.isfile(sub_path):
                            player = MinetestPlayer(sub_name)
                            player.load_from_file(sub_path)
                            if "name" in player._player_args:
                                if player._player_args["name"] is not None:
                                    if len(player._player_args["name"])>0:
                                        if sub_name==player._player_args["name"]:  #purposely case sensitive especially for minetest linux version
                                            correct_count += 1
                                        else:
                                            incorrect_count += 1
                                            print(min_indent+"      Changing incorrect name "+player._player_args["name"]+" found in "+sub_name)
                                            player._player_args["name"] = sub_name
                                            player.save()
                                    else:
                                        print(min_indent+"      WARNING: name is blank in "+sub_path)
                                else:
                                    print(min_indent+"      WARNING: name not found in "+sub_path)
                            
                        #else:
                        #    print(min_indent+"    ERROR in set_player_names_to_file_names: '"+str(sub_path)+"' is not a file.")
                    else:
                        print(min_indent+"    ERROR in set_player_names_to_file_names: path is None.")

    print(min_indent+"  Summary:")  # of set_player_names_to_file_names:")
    print(min_indent+"    "+str(correct_count)+" correct name(s)")
    print(min_indent+"    "+str(incorrect_count)+" incorrect name(s)")
#recover_player_files_by_content("C:\\1.RaiseDataRecovery", "C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\worlds\\FCAGameAWorld\\players")

### RESTORE ITEMS FROM DEBUG.TXT:
#"C:\Users\jgustafson\Desktop\Backup\fcalocal\home\owner\.minetest\debug_archived\2016\03\"
##debug_log_replay_to_offline_player_storage("C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\debug.txt", players_offline_storage_path, min_date_string)

#confirm_min_date()
##for debug_path in debugs_list:
##    debug_log_replay_to_offline_player_storage(debug_path, players_offline_storage_path, min_date_string)
#debug_log_replay_to_offline_player_storage(debug_txt_path, players_offline_storage_path, min_date_string)
min_date_string="2016-03-21 00:00:00"
debug_log_replay_to_offline_player_storage("C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\debug 2017-03-24 stolen panels, cables, battery boxes ONLY.txt", players_offline_storage_path, min_date_string)

def switch_player_file_contents(player1_path, player2_path):
    #switches everything except name
    
    player1 = MinetestPlayer(os.path.basename(player1_path))
    player2 = MinetestPlayer(os.path.basename(player2_path))
    tmp_id = player1.playerid
    tmp_name = player1.get_name()
    player1.set_name(player2.get_name())
    player2.set_name(tmp_name)
    player1.playerid=player2.playerid
    player2.playerid=tmp_id
    player1.save()
    player2.save()

#convert_storage_to_give_commands_DEPRECATED(players_offline_storage_path, give_path, irl_person_csv_path)

#move_storage_to_players(players_offline_storage_path, players_path, give_path, change_player_position_enable=True)


### FOR TESTING PURPOSES:
# C:\Users\jgustafson\Desktop\Backup\fcalocal\home\owner\.minetest\worlds\FCAGameAWorld\players\
#minetestplayer = MinetestPlayer("mrg")
#minetestplayer.load()
#item_id = "default:glass"
#leftover = minetestplayer.push_item(item_id,1286)
#print("/give "+minetestplayer.playerid+" "+item_id+" "+str(leftover))
#minetestplayer.playerid = "mrg-try1"
#minetestplayer.save()
if os.sep == "\\":
    print("# REMEMBER If you later copy player files to a GNU/Linux machine cd to your world's players folder then run dos2unix such as:")
    print("    sudo apt-get update")
    print("    sudo apt-get install dos2unix")
    print("    cd "+os.path.join(minetestinfo.get_var("primary_world_path"), "players"))
    print("    dos2unix *")
    print("# to convert line endings, otherwise inventory and all PlayerArgs will be loaded as blank (if using player files with Windows line endings on GNU/Linux copy of minetest).")
