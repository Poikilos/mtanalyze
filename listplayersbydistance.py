
from minetestoffline import *
import math

# (used below)
def list_players_by_distance(single_axis_enable):

    #from ast import literal_eval # as make_tuple

    #players_path = os.path.join(minetestinfo.get_var("primary_world_path"), "players")
    players_path = "C:\\Users\\jgustafson\\Desktop\\Backup\\fcalocal\\home\\owner\\.minetest\\worlds\\FCAGameAWorld\\players"

    #extra_path = os.path.join(dest_players_path, "extra_players")

    players = dict()

    if os.path.isdir(players_path):
        folder_path = players_path
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path,sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1]!="."):
                    #is_player_file = False
                    print("EXAMINING "+sub_name)
                    players[sub_name] = MinetestPlayer(sub_name)
                    players[sub_name].load_from_file(sub_path)
    playerid_max_len = 0
    for key in players:
        players[key].tag = True
        if len(players[key].playerid) > playerid_max_len:
            playerid_max_len = len(players[key].playerid)
    is_more = True
    while is_more:
        is_more = False
        min_abs = 32000  # ok since max worldgen limit of Minetest is 31000
        min_dist = math.sqrt(32000**2 * 32000**2)
        min_key = None
        for key in players:
            if players[key].tag:
                is_more = True
                pos = players[key].get_pos()
                if single_axis_enable:
                    this_max_abs = abs(pos[0])
                    # get max axis intentionally, to sort properly
                    # skip y (height axis) intentionally
                    if abs(pos[2])>this_max_abs:
                        this_max_abs = abs(pos[2])
                    if this_max_abs<=min_abs:
                        min_abs = this_max_abs
                        min_key = key
                    #if abs(pos[2])<=min_abs:  
                    #    min_abs = pos[2]
                    #    min_key = key
                else:
                    dist = math.sqrt(pos[0]**2 * pos[2]**2)
                    if dist<=min_dist:
                        min_dist = dist
                        min_key = key
        if min_key is not None:
            players[min_key].tag = False
            id_padding = ""
            if (len(players[min_key].playerid)<playerid_max_len):
                id_padding = ' '*(playerid_max_len-len(players[min_key].playerid))
            print(players[min_key].playerid + ","+id_padding+" \"" + str(players[min_key].get_pos())+"\"")

list_players_by_distance(True)
raw_input("Press enter to exit...")
