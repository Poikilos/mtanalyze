#!/usr/bin/env python
from __future__ import print_function
import os


class ChunkymapRenderer:
    def __init__(self):
        pass

    def prepare_env(self):
        # self.minetestmapper_numpy_path = os.path.join(
        #     os.path.dirname(os.path.abspath(__file__)),
        #     "minetestmapper-numpy.py"
        # )
        # self.mtm_custom_path = os.path.join(
        #     os.path.dirname(os.path.abspath(__file__)),
        #     "minetestmapper.py"
        # )
        git_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        print("MAPPERS search path (clone minetestmapper-python folder"
              " in here): " + git_path)
        self.minetestmapper_numpy_path = os.path.join(
            os.path.join(git_path, "minetestmapper-python"),
            "minetestmapper-numpy.py"
        )
        self.mtm_custom_path = os.path.join(
            os.path.join(git_path, "minetestmapper-python"),
            "minetestmapper.py"
        )
        # ^ formerly minetestmapper_custom_path
        self.mtm_py_path = self.minetestmapper_numpy_path
        # ^ formerly minetestmapper_py_path
        self.mtm_bin_dir_path = os.path.join(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                ".."
            ),
            "minetestmapper"
        )
        self.mtm_bin_path = os.path.join(
            self.mtm_bin_dir_path,
            "minetestmapper"
        )
        # ^ formerly minetestmapper_bin_path
        # mtm_bin_paths = [
        #     "/usr/local/bin/minetestmapper",
        #     "/usr/bin/minetestmapper"
        # ]
        # ABOVE AND BELOW are COMMENTED because minetestmapper is not
        # usable (neither provides standard output nor fixed size image
        # --see <https://github.com/minetest/minetestmapper/issues/49>)
        if os.path.isfile(self.mtm_bin_path):
            self.mtm_bin_enable = True
        elif os.path.isfile(os.path.join("/usr/bin", "minetestmapper")):
            self.mtm_bin_path = os.path.join(
                "/usr/bin",
                "minetestmapper"
            )
            self.mtm_bin_enable = True
        elif os.path.isfile(os.path.join("/usr/local/bin",
                                         "minetestmapper")):
            self.mtm_bin_path = os.path.join(
                "/usr/local/bin",
                "minetestmapper"
            )
            self.mtm_bin_enable = True
        if self.mtm_bin_enable:
            print()
            print("mtm_bin_path: "
                  + self.mtm_bin_path)
            print()
        else:
            print()
            print("WARNING: binary minetestmapper not found")
            print()
        # else:
        #     for try_path in mtm_bin_paths:
        #         if os.path.isfile(try_path):
        #             self.mtm_bin_path = try_path
        #             self.mtm_bin_enable = True
        # region useful if version of minetestmapper.py from Poikilos'
        # minetestmapper-python is used
        # profile_path = None
        # if 'USERPROFILE' in os.environ:
        #     profile_path = os.environ['USERPROFILE']
        # elif 'HOME' in os.environ:
        #     profile_path = os.environ['HOME']
        # minetest_program_path = os.path.join(profile_path, "minetest")
        # minetest_util_path = os.path.join(minetest_program_path,
        #                                   "util")
        # minetest_minetestmapper_path = os.path.join(
        #     minetest_util_path,
        #     "minetestmapper.py"
        # )
        # if not os.path.isfile(self.mtm_py_path):
        #     self.mtm_py_path = minetest_minetestmapper_path
        # endregion useful if version of minetestmapper.py from
        # Poikilos' fork minetestmapper-python is used (formerly in
        # the minetest repo)

        # if (self.backend_string!="sqlite3"):
        #      minetestmapper-numpy had trouble with leveldb but this
        #      fork has it fixed so use numpy always always instead of
        #      running the following line
        #      self.mtm_py_path = self.mtm_custom_path
        print("Chose image generator script: "
              + self.mtm_py_path)
        if not os.path.isfile(self.mtm_py_path):
            print("WARNING: minetestmapper script does not exist, so "
                  + __file__ + " cannot generate maps.")
            # sys.exit(2)
        self.colors_path = None
        try_clrs_dirs = []
        try_clrs_dirs.append(
            os.path.dirname(os.path.abspath(self.mtm_py_path))
        )
        try_clrs_dirs.append(os.path.dirname(
            os.path.abspath(__file__)
        ))
        for try_clrs_dir in try_clrs_dirs:
            try_clrs = os.path.join(try_clrs_dir, "colors.txt")
            if os.path.isfile(try_clrs):
                self.colors_path = try_clrs

        if self.colors_path is None:
            print("WARNING: There is no colors.txt in any of '"
                  + str(try_clrs_dirs) + "', so "
                  + __file__ + " cannot generate maps.")
            # sys.exit(2)
