import subprocess
import os
#import stat
import shutil
from minetestinfo import *
#python_exe_path is from:
from pythoninfo import *
#from PIL import Image, ImageDraw, ImageFont, ImageColor
from PIL import Image

class ChunkymapOfflineRenderer:

    #minetestmapper_numpy_path = None
    #minetestmapper_custom_path = None
    #minetestmapper_py_path = None
    #minetestmapper_bin_path = None
    #backend_string = None
    #world_path = None
    #world_name = None
    #boundary_x_min = None
    #boundary_x_max = None
    #boundary_z_min = None
    #boundary_z_max = None
    #mtm_bin_enable = None
    #mtm_bin_dir_path = None

    def __init__(self):
        self.boundary_x_min = -4096  #formerly -10000
        self.boundary_x_max = 4096  #formerly 10000
        self.boundary_z_min = -4096  #formerly -10000
        self.boundary_z_max = 4096  #formerly 10000
        self.mtm_bin_enable = False  # set below automatically if present
        #NOTE: 6144*2 = 12288
        #NOTE: a 16464x16384 or 12288x12288 image fails to load in browser, but 6112x6592 works

        self.backend_string = get_world_var("backend")

        #region the following is also in singleimage.py
        self.minetestmapper_numpy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minetestmapper-numpy.py")
        self.minetestmapper_custom_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minetestmapper-expertmm.py")
        self.minetestmapper_py_path = self.minetestmapper_numpy_path
        self.mtm_bin_dir_path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)),".."),"minetestmapper")
        self.minetestmapper_bin_path = os.path.join(self.mtm_bin_dir_path,"minetestmapper")
        if os.path.isfile(self.minetestmapper_bin_path):
            self.mtm_bin_enable = True
        #region useful if version of minetestmapper.py from expertmm fork of minetest is used
        #profile_path = None
        #if 'USERPROFILE' in os.environ:
        #    profile_path = os.environ['USERPROFILE']
        #elif 'HOME' in os.environ:
        #    profile_path = os.environ['HOME']
        #minetest_program_path = os.path.join(profile_path, "minetest")
        #minetest_util_path = os.path.join(minetest_program_path,"util")
        #minetest_minetestmapper_path = os.path.join(minetest_util_path,"minetestmapper.py")
        #if not os.path.isfile(self.minetestmapper_py_path):
        #    self.minetestmapper_py_path = minetest_minetestmapper_path 
        #endregion useful if version of minetestmapper.py from expertmm fork of minetest is used
        
        #if (self.backend_string!="sqlite3"):
            # minetestmapper-numpy had trouble with leveldb but this fork has it fixed so use numpy always always instead of running the following line
            # self.minetestmapper_py_path = self.minetestmapper_custom_path
        print("Chose image generator script: "+self.minetestmapper_py_path)
        if not os.path.isfile(self.minetestmapper_py_path):
            print("ERROR: script does not exist, so exiting "+__file__+".")
            sys.exit(2)
        self.colors_path = os.path.join(os.path.dirname(os.path.abspath(self.minetestmapper_py_path)), "colors.txt")
        if not os.path.isfile(self.colors_path):
            print("ERROR: missing '"+self.colors_path+"', so exiting "+__file__+".")
            sys.exit(2)
        self.world_path = minetestinfo.get_var("primary_world_path")
        if not os.path.isdir(self.world_path):
            print("ERROR: missing world '"+self.world_path+"', so exiting "+__file__+".")
            sys.exit(2)
        else:
            self.world_name = os.path.basename(self.world_path)
        #endregion the following is also in singleimage.py

    def RenderSingleImage(self):
        dest_colors_path = os.path.join(self.mtm_bin_dir_path,"colors.txt")
        genresults_folder_path = os.path.join( os.path.join(os.path.dirname(os.path.abspath(__file__)), "chunkymap-genresults"), self.world_name)
        if not os.path.isdir(genresults_folder_path):
            os.makedirs(genresults_folder_path)
        genresult_path = os.path.join(genresults_folder_path, "singleimage"+genresult_name_closer_string)
        gen_error_path = os.path.join(genresults_folder_path, "singleimage"+gen_error_name_closer_string)
        cmd_suffix = " 1> \""+genresult_path+"\""
        cmd_suffix += " 2> \""+gen_error_path+"\""
        #if self.boundary_x_min is None:
        #    print("ERROR: boundary_x_min is None")
        #if self.boundary_x_max is None:
        #    print("ERROR: boundary_x_max is None")
        #if self.boundary_z_min is None:
        #    print("ERROR: boundary_z_min is None")
        #if self.boundary_z_max is None:
        #    print("ERROR: boundary_z_max is None")
        geometry_string = str(self.boundary_x_min)+":"+str(self.boundary_z_min)+"+"+str(self.boundary_x_max-self.boundary_x_min)+"+"+str(self.boundary_z_max-self.boundary_z_min)  # "-10000:-10000+20000+20000" #2nd two params are sizes
        #VERY BIG since singleimage mode (if no geometry param, minetestmapper-numpy reverts to its default which is -2000 2000 -2000 2000):
        region_string = str(self.boundary_x_min)+" "+str(self.boundary_x_max)+" "+str(self.boundary_z_min)+" "+str(self.boundary_z_max) # "-10000 10000 -10000 10000"
        
        #geometry_string = str(min_x)+":"+str(min_z)+"+"+str(int(max_x)-int(min_x)+1)+"+"+str(int(max_z)-int(min_z)+1)  # +1 since max-min is exclusive and width must be inclusive for minetestmapper.py
        region_param = " --region "+region_string  # minetestmapper-numpy.py --region xmin xmax zmin zmax
        geometry_param = " --geometry "+geometry_string # " --geometry -10000:-10000+20000+20000"  # minetestmapper-expertmm.py --geometry <xmin>:<zmin>+<width>+<height>
        limit_param = geometry_param
        #expertmm_region_string = str(min_x) + ":" + str(max_x) + "," + str(min_z) + ":" + str(max_z)

        #cmd_no_out_string = python_exe_path+" "+self.minetestmapper_py_path+" --bgcolor '"+self.FLAG_EMPTY_HEXCOLOR+"' --input \""+minetestinfo.get_var("primary_world_path")+"\" --geometry "+geometry_string+" --output \""+tmp_png_path+"\""
        png_name = "singleimage.png"

        tmp_png_path = os.path.join(genresults_folder_path, png_name)
        squote = ""
        if os_name!="windows":
            squote = "'"
        io_string = " --input \""+self.world_path+"\" --output \""+tmp_png_path+"\""
        if (not self.mtm_bin_enable) and ("numpy" in self.minetestmapper_py_path):
            limit_param = region_param
            io_string = " \""+self.world_path+"\" \""+tmp_png_path+"\""
            #geometry_param = " --region " + str(min_x) + " " + str(max_x) + " " + str(min_z) + " " + str(max_z)
            #print("Using numpy style parameters.")
            #print("  since using "+self.minetestmapper_py_path)
            #print()
        if self.mtm_bin_enable:
            cmd_no_out_string = self.minetestmapper_bin_path+" --colors "+dest_colors_path+" --bgcolor "+squote+FLAG_EMPTY_HEXCOLOR+squote+io_string+limit_param
        else:
            cmd_no_out_string = python_exe_path+" "+self.minetestmapper_py_path+" --bgcolor "+squote+FLAG_EMPTY_HEXCOLOR+squote+io_string+limit_param
        cmd_string = cmd_no_out_string + cmd_suffix
        print("")
        print("")
        print("Running")
        print("    "+cmd_string)
        if self.mtm_bin_enable:
            if os.path.isfile(self.colors_path) and not os.path.isfile(dest_colors_path):
                print("Copying...'"+self.colors_path+"' to  '"+dest_colors_path+"'")
                shutil.copyfile(self.colors_path,dest_colors_path)
            print("  mapper_path: " + self.minetestmapper_bin_path)
        else:
            print("  mapper_path: " + self.minetestmapper_py_path)
        print("  colors_path: "+self.colors_path)
        print("  backend: " + self.backend_string)
        print("    # (this may take a while...)")
        if os.path.isfile(tmp_png_path):
            os.remove(tmp_png_path)
        #subprocess.call("touch \""+tmp_png_path+"\"", shell=True)
        subprocess.call(cmd_string, shell=True)
        final_png_path = tmp_png_path
        www_uid = None
        www_gid = None
        www_chunkymapdata_path = os.path.join(minetestinfo.get_var("www_minetest_path"), "chunkymapdata")
        www_chunkymapdata_worlds_path = os.path.join(www_chunkymapdata_path, "worlds")
        www_chunkymapdata_world_path = os.path.join(www_chunkymapdata_worlds_path, self.world_name)
        try:
            www_stat = os.stat(minetestinfo.get_var("www_minetest_path"))
            www_uid = www_stat.st_uid
            www_gid = www_stat.st_gid
            #import pwd
            #www_u_name = pwd.getpwuid(uid)[0]
            #www_g_name = pwd.getgrgid(gid)[0]
            #import pwd
            #import grp
            #www_uid = pwd.getpwnam("www_data").pw_uid
            #www_gid = grp.getgrnam("nogroup").gr_gid
        except:
            print("Unable to get stat on www directory \""+minetestinfo.get_var("www_minetest_path")+"\", so will not be able to automatically set owner of result jpg there. Make sure you manually set owner of singleimage.jpg in '"+www_chunkymapdata_world_path+"' to www_data user and group.")
            print("  "+str(sys.exc_info()))

        is_locked = False
        err_count = 0
        if os.path.isfile(gen_error_path):
            ins = open(gen_error_path, 'r')
            line = True
            while line:
                line = ins.readline()
                if line:
                    if len(line.strip())>0:
                        err_count += 1
                    line_lower = line.lower()
                    if (" lock " in line_lower) or ("/lock " in line_lower):
                        is_locked = True
                        lock_line = line
                        result = None
                        break
            ins.close()
        if err_count<1:
            os.remove(gen_error_path)
        if os.path.isfile(tmp_png_path):
            if not os.path.isdir(www_chunkymapdata_world_path):
                os.makedirs(www_chunkymapdata_world_path)
            if minetestinfo.contains("www_minetest_path"):
                dest_png_path = os.path.join(www_chunkymapdata_world_path, png_name)
                if os.path.isfile(dest_png_path):
                    os.remove(dest_png_path)
                print("Moving temp image from "+tmp_png_path+" to "+dest_png_path+"...")
                
                #move_cmd_string = "mv"
                #if os_name=="windows":
                #    move_cmd_string= "move"
                #this_move_cmd_string = move_cmd_string+" \""+tmp_png_path+"\" to \""+dest_png_path+"\"..."
                #subprocess.call(this_move_cmd_string, shell=True)
                shutil.move(tmp_png_path, dest_png_path)   #avoids error below according to 

                # os.rename(tmp_png_path, dest_png_path)  # fails with the following output:
                # Moving temp image from /home/owner/chunkymap/chunkymap-genresults/FCAGameAWorld/singleimage.png to /var/www/html/minetest/chunkymapdata/worlds/FCAGameAWorld/singleimage.png...
                # Traceback (most recent call last):
                #  File "chunkymap/singleimage.py", line 157, in <module>
                #     cmor.RenderSingleImage()
                #   File "chunkymap/singleimage.py", line 118, in RenderSingleImage
                #     os.rename(tmp_png_path, dest_png_path)
                # OSError: [Errno 18] Invalid cross-device link
                
                final_png_path = dest_png_path
            print("Png image saved to:")
            print("  "+final_png_path)
            print("Converting to jpg...")
            pngim = Image.open(final_png_path)
            #jpgim = Image.new('RGB', pngim.size, (0, 0, 0))
            #jpgim.paste(pngim.convert("RGB"), (0,0,pngim.size[0],pngim.size[0]))
            jpg_name = "singleimage.jpg"
            dest_jpg_path = os.path.join(www_chunkymapdata_world_path, jpg_name)
            if os.path.isfile(dest_jpg_path):
                os.remove(dest_jpg_path)
                if not os.path.isfile(dest_jpg_path):
                    print("  removed old '"+dest_jpg_path+"'")
                else:
                    print("  failed to remove'"+dest_jpg_path+"'")
            #jpgim.save(dest_jpg_path)
            pngim.save(dest_jpg_path, 'JPEG')
            if os.path.isfile(dest_jpg_path):
                print("jpg image saved to:")
                print("  "+dest_jpg_path)
                if www_gid is not None:
                    os.chown(dest_jpg_path, www_uid, www_gid)
                    print("changed owner to same as www folder")
                os.remove(final_png_path)
                print("removed temporary file "+final_png_path)
            else:
                print("Could not write '"+dest_jpg_path+"'")
            if os.path.isfile(genresult_path):
                print("Results:")
                print("  "+genresult_path)
                mtchunk = MTChunk()
                mtchunk.set_from_genresult(genresult_path)
                mtchunk.metadata["is_traversed"] = True
                dest_yaml_name = "singleimage.yml"
                dest_yaml_path = os.path.join(www_chunkymapdata_world_path, dest_yaml_name)
                mtchunk.save_yaml(dest_yaml_path)
        else:

            print("No image could be generated from '"+self.world_path+"'")
            if is_locked:
                print("(database is locked--shutdown server first or try generator.py to render chunks individually).")

cmor = ChunkymapOfflineRenderer()
cmor.RenderSingleImage()
