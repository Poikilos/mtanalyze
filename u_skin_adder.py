import os
#from PIL import Image, ImageDraw, ImageFont, ImageColor
from expertmm import *
from minetestinfo import *  #paths and FLAG_EMPTY_HEXCOLOR = "#010000"
try:
    from PIL import Image, ImageDraw, ImageFont, ImageColor
except:
    print("You must first install Pillow's PIL."
    print("On Windows:")
    print("Right-click windows menu, 'Command Prompt (Admin)' then:")
    print("pip install Pillow")
    print("")
    print("On *nix-like systems:")
    print("sudo pip install Pillow")
    exit()
import shutil

u_skins_mod_path = os.path.join(profile_path,"Desktop\\Backup\\fcalocal\\usr\\local\\share\\minetest\\games\\fca_game_a\\mods\\u_skins\\u_skins")
games_path = os.path.join(minetestinfo.get_var("shared_minetest_path"), "games")

verbose_enable = True
image_size = (64,32)
preview_size = (16,32)

visual_debug_enable = False
dump_path = os.path.join(u_skins_mod_path, "debug")  # only created or used if visual_debug_enable

world_path = None
world_name = None
if minetestinfo.contains("primary_world_path"):
    world_path = minetestinfo.get_var("primary_world_path")
    world_name = os.path.basename(world_path)
    print("Using world '"+world_name+"'")

#game_name = game_path_from_gameid_dict(
gameid = None
game_path = None
mods_path = None
if not os.path.isdir(u_skins_mod_path):
    if world_path is not None and os.path.isdir(world_path):
        gameid=get_world_var("gameid")
        print("Using game '"+str(gameid)+"'")
        if gameid is not None and games_path is not None:
            game_path = os.path.join(games_path, gameid)
            mods_path=os.path.join(game_path, "mods")
            print("Using mods_path '"+mods_path+"'")
            print("Looking for u_skins mod in u_skins modpack...")
            #u_skins_mod_path = os.path.join(  os.path.join( os.path.join(game_path, "mods"), "u_skins" ),  "u_skins"  )  # get the u_skins mod in the u_skins modpack
            #print("  trying '"+u_skins_mod_path+"'")

            u_skins_modpack_path = os.path.join(mods_path, "u_skins")
            u_skins_mod_path = os.path.join(u_skins_modpack_path, "u_skins")
    else:
        print("Unknown world, so can't detect game.")
meta_path = os.path.join(u_skins_mod_path,"meta")
textures_path = os.path.join(u_skins_mod_path,"textures")
image_prefix = "character_"
preview_suffix = "_preview"

default_license_string = "CC BY-SA 3.0"


png_count = 0

class RectTransferInfo:
    source_rect_tuple = None
    dest_rect_tuple = None
    flip_h = None

    def __init__(self, source_rect_tuple, dest_rect_tuple, flip_h):
        self.flip_h = flip_h
        self.source_rect_tuple = source_rect_tuple
        self.dest_rect_tuple = dest_rect_tuple

rect_trans_list = list()
rect_trans_list.append(RectTransferInfo((8,8,8,8),(4,0,8,8),False))  # face
rect_trans_list.append(RectTransferInfo((20,20,8,12),(4,8,8,12),False))  # shirt
#rect_trans_list.append(RectTransferInfo((44,28,4,4),(0,16,4,4),False))  # hand.r
#rect_trans_list.append(RectTransferInfo((44,28,4,4),(12,16,4,4),True))  # hand.l (True since must be flipped manually)
rect_trans_list.append(RectTransferInfo((44,20,4,12),(0,8,4,12),False))  # arm.r
rect_trans_list.append(RectTransferInfo((44,20,4,12),(12,8,4,12),True))  # arm.l (True since on hands, left one must be flipped manually)
rect_trans_list.append(RectTransferInfo((4,20,4,12),(8,20,4,12),False))  # leg.l
rect_trans_list.append(RectTransferInfo((4,20,4,12),(4,20,4,12),True))  # leg.r (True since on legs, right one must be flipped manually)
#yes, the flipping is different for leg vs arm


class USkinInfo:
    author_string = None
    name_string = None
    license_name_string = None

    #region temp
    source_image_path = None
    #endregion temp

    def __init__(self):
        pass

    def set_from_skindb_skin_file_path(self, file_path, license_name_string):
        self.author_string = None
        self.name_string = None
        self.license_name_string=license_name_string
        self.source_image_path = file_path
        file_name = os.path.basename(self.source_image_path)
        noext_name = file_name
        dot_index = file_name.rfind(".")
        if dot_index>=0:
            noext_name = file_name[:dot_index]
        by_string = "_by_"
        by_index = noext_name.rfind(by_string)
        #print("noext_name:"+noext_name)
        if by_index>=0:
            self.author_string = noext_name[by_index+len(by_string):]
            self.name_string = noext_name[:by_index]
        else:
            self.author_string = "<unknown>"
            self.name_string = noext_name

    def set_from_metadata_path(self, metadata_file_path):
        is_ok = False
        self.name_string = None
        self.author_string = None
        self.license_name_string = None
        if os.path.isfile(metadata_file_path):
            ins = open(metadata_file_path, 'r')
            line = True
            counting_number = 1
            while line:
                participle = "reading line "+str(counting_number)
                line = ins.readline()
                if line:
                    line_strip = line.strip()
                    if len(line_strip)>0:
                        if self.name_string is None:
                            self.name_string = line_strip
                        elif self.author_string is None:
                            self.author_string = line_strip
                            is_ok = True
                        elif self.license_name_string is None:
                            self.license_name_string = line_strip
                counting_number += 1
            ins.close()
            if not is_ok:
                raw_input("ERROR: Did not find line 2 for name_string in '"+metadata_file_path+"'")
        else:
            raw_input("Missing '"+metadata_file_path+"' -- press enter to continue...")
        return is_ok

    def print_dump(self, min_indent):
        print(min_indent+"name_string:"+self.name_string)
        print(min_indent+"author_string:"+self.author_string)
        print(min_indent+"license_name_string:"+self.license_name_string)

    def _save_metadata(self, metadata_file_path):
        outs = open(metadata_file_path, 'w')
        outs.write(self.name_string+"\n")
        outs.write(self.author_string+"\n")
        outs.write(self.license_name_string+"\n")
        outs.close()


    def push_next_skin_file_if_self_is_new(self):
        result = False
        os.listdir(textures_path)
        this_index = 1
        while os.path.isfile( get_png_path_from_index(this_index) ):
            this_index += 1
        if not skin_exists(self.name_string, self.author_string):
            #image_name = get_png_name_from_index(this_index)
            image_path = get_png_path_from_index(this_index)
            metadata_name = get_metadata_name_from_index(this_index)
            metadata_path = os.path.join(meta_path, metadata_name)
            #preview_name = get_preview_name_from_index(this_index)
            preview_path = get_preview_path_from_index(this_index)
            print("saving to image_path:"+image_path)
            print("saving to metadata_path:"+metadata_path)
            self._save_metadata(metadata_path)
            #actually save the skin and metadata files:
            print("saving to preview_path:"+preview_path)
            self.print_dump("  ")

            shutil.copy(self.source_image_path, image_path)
            result = True
            preview_im = Image.new("RGBA", preview_size, "#000000")
            fill_image_with_transparency(preview_im)
            skin_im = Image.open(open(self.source_image_path, 'rb'))  # double-open to make sure file is finished writing
            #NOTE: PIL automatically closes, otherwise you can do something like https://bytes.com/topic/python/answers/24308-pil-do-i-need-close
            #fp = open(file_name, "rb")
            #im = Image.open(fp) # open from file object
            #im.load() # make sure PIL has read the data
            #fp.close()
            for rect_trans in rect_trans_list:
                source_left, source_top, source_right, source_bottom = rect_trans.source_rect_tuple
                source_right+=source_left
                source_bottom+=source_top
                pil_source_rect_tuple = source_left, source_top, source_right, source_bottom

                partial_im = skin_im.crop(pil_source_rect_tuple)

                dest_left, dest_top, dest_right, dest_bottom = rect_trans.dest_rect_tuple
                dest_right+=dest_left
                dest_bottom+=dest_top
                pil_dest_rect_tuple = dest_left, dest_top, dest_right, dest_bottom

                preview_im.paste(partial_im, (dest_left, dest_top))
                debug_img_name="debug "+str(pil_source_rect_tuple)+".png"
                if visual_debug_enable:
                    #if visual_debug_enable:
                        #raw_input("Press enter to save temp cropping images to '"+dump_path+"'")

                    if not os.path.isdir(dump_path):
                        os.makedirs(dump_path)
                    debug_img_path = os.path.join(dump_path, debug_img_name)
                    #if not os.path.isfile(debug_img_path):
                    print("  saving "+debug_img_path)
                    print("  (after pasting to destination rect "+str(pil_dest_rect_tuple)+")")
                    partial_im.save(debug_img_path)

            preview_im.save(preview_path)
            print("Saved preview to '"+preview_path+"'")
            print("")
        else:
            print("Skin already exists: "+self.name_string+" by "+self.author_string)

def get_png_path_from_index(this_index):
    return os.path.join(textures_path, get_png_name_from_index(this_index))

def get_png_name_from_index(this_index):
    return image_prefix+str(this_index)+".png"

def get_preview_path_from_index(this_index):
    return os.path.join(textures_path, get_preview_name_from_index(this_index))

def get_preview_name_from_index(this_index):
    return image_prefix+str(this_index)+preview_suffix+".png"

def get_metadata_name_from_index(this_index):
    return image_prefix+str(this_index)+".txt"

def get_metadata_path_from_index(this_index):
    return os.path.join(meta_path, get_metadata_name_from_index(this_index))

print("Loading existing skin metadata to avoid duplication (but ignoring metadata files that do not have pngs)")
si_list = list()
this_index = 1
while os.path.isfile( get_png_path_from_index(this_index) ):
    existing_metadata_path = get_metadata_path_from_index(this_index)
    this_si = USkinInfo()
    is_ok=this_si.set_from_metadata_path(get_metadata_path_from_index(this_index))
    if is_ok:
        #if not skin_exists(this_si.name_string, this_si.author_string):
        si_list.append(this_si)
        #if verbose_enable:
        #    print("Added skin metadata:")
        #    this_si.print_dump("  ")
    this_index += 1
print("  Found metadata for "+str(len(si_list))+" png file(s).")
print("  The functions in "+__file__+" are now ready.")
print("    * These functions mark destination as '"+default_license_string+"' license unless you")
print("      first change the global default_license_string variable")
print("      in your program that has:")
print("          from u_skin_adder import *")
print("    * Skin filename should include _by_ (with underscores) to specify author.")
print("    * Examples:")
print("      load_new_skins_from_folder(folder_path)")
print("      add_skin_if_new(file_path)")

def fill_image_with_transparency(im):
    #modified version of: unutbu. "Python PIL: how to make area transparent in PNG? (answer 7 Dec 2010 at 19:08)" <http://stackoverflow.com/questions/4379978/python-pil-how-to-make-area-transparent-in-png>. 7 Dec 2010. 8 Apr 2016.
    #who cited http://stackoverflow.com/questions/890051/how-do-i-generate-circular-thumbnails-with-pil
    #import Image
    #import ImageDraw
    #im = Image.open("image.png")
    #transparent_area = (50,80,100,200)
    transparent_area = (0,0,im.size[0],im.size[1])

    mask=Image.new('L', im.size, color=255)
    draw=ImageDraw.Draw(mask)

    draw.rectangle(transparent_area, fill=0)
    im.putalpha(mask)
    #im.save('/tmp/output.png')


show_no_dest_warnings = True
def skin_exists(name_string, author_string):
    global show_no_dest_warnings
    #global si_list
    result = False
    count = 0
    #if verbose_enable:
    #    print("  Checking for existing "+name_string+" by "+author_string+":")
    for si in si_list:
        if si.name_string==name_string and si.author_string==author_string:
            result = True
            break
        #else:
        #    if verbose_enable:
        #        print("    "+si.name_string+" by "+si.author_string+" is not it.")
        count += 1
    if not result:
        if count<1:
            #if show_no_dest_warnings:
            raw_input("WARNING: 0 skins during skin_exists check. Press enter to continue...")
                #show_no_dest_warnings = False
    return result



#if os.path.isdir(meta_path):
#

#accepts CC BY 3.0 skins, and looks for _by_ in name, followed by author (otherwise puts <unknown> on author line of metadata txt file in u_skin/meta folder)
def add_skin_if_new(sub_path):
    this_usi = USkinInfo()
    this_usi.set_from_skindb_skin_file_path(sub_path, default_license_string)
    return this_usi.push_next_skin_file_if_self_is_new()

def load_new_skins_from_folder(in_path):
    #in_path = os.path.join(profile_path,"Downloads\\skins-to-add")
    #if not os.path.isdir(in_path):
    #    in_path = "."
    #    print("Looking for new textures in current directory")

    if not skin_exists("Sam 0","Jordach"):
        print("")
        print("WARNING: Missing 'Sam 0' by 'Jordach'")
        print("  among "+str(len(si_list))+" skin(s).")
        print("  Only continue if you expected that skin to not be there.")
        raw_input("  Press enter to continue...")


    if os.path.isdir(meta_path):
        if os.path.isdir(textures_path):
            if os.path.isdir(in_path):
                folder_path = in_path
                new_count = 0
                found_count = 0
                old_count = 0
                for sub_name in os.listdir(folder_path):
                    sub_path = os.path.join(folder_path,sub_name)
                    if os.path.isfile(sub_path):
                        if (sub_name[:1]!="."):
                            if len(sub_name)>4 and sub_name[-4:]==".png":
                                found_count += 1
                                if add_skin_if_new(sub_path):
                                    new_count += 1
                                else:
                                    old_count += 1
                print("Added "+str(new_count)+" new skins(s) among "+str(found_count)+" discovered in specified source folder.")
                if old_count>0:
                    print("  "+str(old_count)+" (with matching author and title) were already in destination.")
            else:
                print("ERROR: Failed to get new texture files since in_path does not exist:'"+in_path+"'")
        else:
            print("ERROR: missing textures_path (tried '"+textures_path+"')")
    else:
        print("ERROR: missing meta_path (tried '"+meta_path+"')")

#raw_input("Press return to exit.")
#load_new_skins_from_folder("C:\\Users\\Owner\\ownCloud\\Pictures\\Projects\\Characters - Mine - In-Game\\Minetest Player Skins")
#add_skin_if_new("z:\\yelby.png")
