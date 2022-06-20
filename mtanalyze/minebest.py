#!/usr/bin/env python
'''
Show information about a minetest world. This simplified submodule of
mtanalyze makes some assumptions in order to be used as a minimal
Command-line Interface (CLI) command.

The default directory to look for Minetest is ~/minetest, or instead
"/opt/minebest" if present.
To use your minetest directory, either:
- Set the BESTDIR environment variable to your minetest folder path
- or place this file in your_minetest/mtbin

The directory must contain either a worlds or mtworlds directory.

Each world usually contains a game when using the Minetest framework.

Related Projects:
- Minebest by Robert Kiraly ("OldCoder")
- mtctl by Miniontoby
- mtinfo by BuckarooBanzay

Arguments:
-n            Set the maximum number of lines for showing each log file.

Examples:
minebest list  # Show a list of Minetest worlds.
minebest log world1  # show the log from a world called world1
'''

# TODO: when showing a debug log, output a suggested nano command
# (and option to run it). Jump to line number in nano (undocumented):
# "nano +{} {}".format(lineN, path)

from __future__ import print_function
from __future__ import division
import os
import sys
import platform
import subprocess
import socket

# TODO:
'''
MTUSER = minebest
WHOAMI = os.getlogin()
if WHOAMI != MTUSER:
    echo0("Note: Switching to {}".format(MTUSER))
    cmd_arg = ""
    delimit = ""
    for arg in sys.argv:
        cmd_arg += delimit + arg
        delimit = " "
    cmd_parts = ["su", MTUSER, "-c", cmd_arg]

    # See <https://stackoverflow.com/a/4760517/4541104>
    # answered Jan 21, 2011 at 15:27 by senderle
    # edited Dec 19, 2021 at 11:14 by user14745999

    # result = subprocess.run(['ls', '-l'], stdout=subprocess.PIPE)
    # print(result.stdout)
    # ^ Python 3.5 or higher

    subprocess.check_output(cmd_parts)
    exit 0
fi
'''

SEPARATOR = "-------------"

profile = None
if platform.system() == "Windows":
    profile = os.environ['USERPROFILE']
else:
    profile = os.environ['HOME']

verbosity = 0
myDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(myDir)

for argI in range(1, len(sys.argv)):
    arg = sys.argv[argI]
    if arg.startswith("--"):
        if arg == "--verbose":
            verbosity = 1
        elif arg == "--debug":
            verbosity = 2


def echo0(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def echo1(*args, **kwargs):
    if verbosity < 1:
        return
    print(*args, file=sys.stderr, **kwargs)


def echo2(*args, **kwargs):
    if verbosity < 2:
        return
    print(*args, file=sys.stderr, **kwargs)

def startsWithAny(haystack, needles):
    for needle in needles:
        if haystack.startswith(needle):
            return True
    return False

def containsAny(haystack, needles):
    for needle in needles:
        if needle in haystack:
            return True
    return False

def usage():
    echo0(__doc__)

trues = ["true", "on"]
falses = ["false", "off"]

def symbol_to_tuple(s, allow_string=True, allow_bool=True):
    if "," not in s:
        return None
    part_strings = s.split(",")
    parts = []
    for part_s in part_strings:
        part = symbol_to_value(part_s, allow_string=allow_string,
                               allow_bool=allow_bool,
                               allow_tuple=False)
        if part is None:
            # If any part is not an expected value, then do not
            # consider the value as a tuple.
            return None
        else:
            parts.append(part)
    return tuple(parts)


def symbol_to_value(s, allow_string=True, allow_bool=True,
                    allow_tuple=True, allow_string_tuple=True):
    '''
    Keyword arguments:
    allow_string -- If false, return None if doesn't evaluate
        to an int nor float.
    allow_tuple -- This should always be False if called by
        symbol_to_tuple! True is only for detecting a tuple.
        Setting this to True within symbol_to_tuple would allow
        recursive tuples. Only numeric tuples are allowed (not str nor
        boolean).
    allow_string_tuple -- Allow a tuple of strings (no quotes, just
        commas). This is common for Minetest.
    '''
    result = None
    if s.startswith('"') and s.endswith('"'):
        if allow_string:
            return s[1:-1]
        else:
            return None
    try:
        result = int(s)
    except ValueError:
        try:
            result = float(s)
        except ValueError:
            got_tuple = None
            if allow_tuple:
                got_tuple = symbol_to_tuple(
                    s,
                    allow_string=allow_string_tuple,
                    allow_bool=False,
                )
            # ^ allow_bool=False because a tuple of booleans doesn't
            #   have a known usage for Minetest.
            if allow_bool and s.lower() in trues:
                return True
            elif allow_bool and s.lower() in falses:
                return False
            elif got_tuple is not None:
                result = got_tuple
            elif allow_string:
                result = s
    return result


def get_conf_value(path, var_name, use_last=True):
    '''
    Keyword arguments:
    use_last -- Keep reading the file even if the variable is found, in
        case it is set twice.
    '''
    result = None
    result_line_n = None
    lineN = 0
    with open(path, 'r') as ins:
        for rawL in ins:
            lineN += 1  # Counting numbers start at 1.
            line = rawL.strip()
            if line == "":
                continue
            if line.startswith("#"):
                continue
            signI = line.find("=")
            if signI < 0:
                continue
            name = line[:signI].strip()
            value = line[signI+1:].strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
                # print("{}:{}: Warning: {} was not in quotes."
                #       "".format(path, lineN, result_line_n, name))
            else:
                tmp = symbol_to_value(value, allow_string=False)
                if tmp is not None:
                    value = tmp
                else:
                    echo1('{}:{}: INFO: The type of "{}" for {} is not'
                          ' detectable. It will become a string.'
                          ''.format(path, lineN, value, name))
                    value = tmp
            if len(name) == 0:
                continue
            if name == var_name:
                if result is not None:
                    print("{}:{}: Warning: Line {} already set {}."
                          "".format(path, lineN, result_line_n, name))
                result_line_n = lineN
                result = value
                if not use_last:
                    break
    return result

def check_server(address, port):
    # from <https://stackoverflow.com/a/32382603/4541104>
    # Create a TCP socket
    if not isinstance(port, int):
        raise ValueError(
            "port must be an int but {} is a(n) {}"
            "".format(port, type(port).__name__)
        )
    s = socket.socket()
    print("Attempting to connect to %s on port %s" % (address, port))
    try:
        s.connect((address, port))
        print("Connected to %s on port %s" % (address, port))
        return True
    except socket.error as e:
        print("Connection to %s on port %s failed: %s" % (address, port, e))
        return False
    finally:
        s.close()


class Minetest:
    def __init__(self, data_dir=None, worlds_dir=None, logs_path=None):
        '''
        Keyword arguments:
        data_dir -- is the folder containing worlds and other things
            (only used for other things if worlds_dir is specified). The
            default is ~/minetest, but if /opt/minebest is present that
            is the default; However, if this script is copied to any
            directory named mtbin, then the parent directory will be
            assumed to be minebest regardless of its name.
        worlds_dir -- is the folder containing worlds. If a
            subdirectory is named using the special keyworlds "live" or
            "static" then each is treated as another folder containing
            worlds. The default value is f'{data_dir}/worlds', otherwise
            f'{data_dir}/mtworlds' if that is present.
        logs_path -- The directory that contains log(s) such as
            debug.txt, or if present, f'{world_name}.txt' instead. The
            default directory is f'{data_dir}/bin', but if
            f'{data_dir}/log' is present, that will be used instead.
        '''
        worlds = None
        self.good = False
        BESTDIR = os.environ.get("BESTDIR")
        if data_dir is None:
            try_data_dir = "/opt/minebest"
            data_dir = os.path.join(profile, "minetest")
            if os.path.isdir(try_data_dir):
                data_dir = try_data_dir
            # ^ set to default (changes below if detected)
        if BESTDIR is None:
            # Detect minebest if BESTDIR is not set explicitly.
            tryMBBinDir = os.path.join(parentDir, "mtbin")
            if myDir == tryMBBinDir:
                # If x/mtbin exists, assume x is the BESTDIR dir.
                data_dir = parentDir
        else:
            data_dir = BESTDIR
        print("data_dir={}".format(data_dir))
        if logs_path is None:
            self.logs_path = os.path.join(data_dir, "bin")
            try_logs_path = os.path.join(data_dir, "log")
            if os.path.isdir(try_logs_path):
                self.logs_path = try_logs_path
        else:
            self.logs_path = logs_path
        self.data_dir = data_dir
        if worlds_dir is None:
            self.worlds_dir = os.path.join(data_dir, "worlds")
            minebest_worlds_dir = os.path.join(data_dir, "mtworlds")
            if os.path.isdir(minebest_worlds_dir):
                self.worlds_dir = minebest_worlds_dir
        else:
            self.worlds_dir = worlds_dir
        print("worlds_dir={}".format(self.worlds_dir))
        self.good = True
        metas, err = self.load_worlds_meta()
        if err is not None:
            raise RuntimeError(err)

    def find_world(self, world_name):
        for worldI in range(len(self.worlds)):
            world = self.worlds[worldI]
            if world.get('name') == world_name:
                return worldI
        return -1

    def get_world(self, world_name):
        worldI = self.find_world(world_name)
        if worldI >= 0:
            return self.worlds[worldI]
        return None

    def get_world_log_paths(self, world_name):
        world = self.get_world(world_name)
        if world is None:
            echo0("There is no world named {}".format(world_name))
            return None
        results = world.get('log_paths')
        if results is None:
            try_log = os.path.join(self.logs_path, "debug.txt")
            if os.path.isfile(try_log):
                results = [try_log]
        return results

    def get_log(self, world_name,
                ignore_startswith=["[MOD]", "[OK]", "COLON: "],
                ignore_contains=[" ACTION[", " WARNING[",
                                 "3d_armor)[3d_armor]"],
                reset_at_separator=False, max_lines=32):
        '''
        Get the log only from the last run. The reset and max arguments
        only apply on a per-log basis (both f'{world_name}.log and
        f'debug-{world_name}.log' will both be read if they exist).

        Keyword arguments:
        reset_at_separator -- Clear the buffer at each instance of
            "-------------" in each log so that only lines from the
            last server restart are shown.
        max_lines -- Only show the tail of the log (If <= 0, show all).
        '''
        if max_lines <= 0:
            max_lines = None
        log_paths = self.get_world_log_paths(world_name)
        if log_paths is None:
            return None
        all_lines = []
        # if len(log_paths) == 1:
        #     all_lines.append("")
        all_lines.append("")
        title = "Log"
        if len(log_paths) > 1:
            title = "Logs"
        all_lines.append(
            "{} (max_lines={}, reset_at_separator={}"
            " ignore_startswith={}, ignore_contains={}):"
            "".format(title, max_lines, reset_at_separator,
                      ignore_startswith, ignore_contains)
        )
        all_lines.append("")

        for log_path in log_paths:
            with open(log_path, 'r') as ins:
                lines = []
                # if len(log_paths) > 1:
                lines.append("")
                lines.append("# {}"
                             "".format(log_path))
                lines.append("")
                custom_count = len(lines)
                for rawL in ins:
                    line = rawL.strip()
                    if reset_at_separator and (SEPARATOR in line):
                        # such as in:
                        '''
                        -------------
                          Separator
                        -------------
                        '''
                        lines = lines[:custom_count]
                        continue
                    if startsWithAny(line, ignore_startswith):
                        continue
                    if containsAny(line, ignore_contains):
                        continue
                    lines.append(line)
                if (max_lines is not None) and (len(lines) > max_lines):
                    lines = lines[len(lines)-max_lines:]
                all_lines += lines
        return all_lines

    def show_log(self, world_name, reset_at_separator=False,
                 max_lines=32):
        lines = self.get_log(
            world_name,
            reset_at_separator=reset_at_separator,
            max_lines=max_lines,
        )
        if lines is None:
            # An error should have already been shown by __init__.
            return
        for line in lines:
            print(line)

    def get_worlds_from(self, path, category_subs=["live", "static"]):
        '''
        Get a tuple that contains a world metadatas list and an error
        (or None).

        Keyword arguments:
        category_subs -- If a subdirectory under path is named the same
            as any string in this list, look for more worlds there
            instead of considering that directory a world.
        '''
        worlds = []
        err = None
        if not os.path.isdir(path):
            usage()
            err = ('Error: Your minebest structure is not'
                   ' recognized. "{}" does not exist.'.format(path))
            return None, err
        for sub in os.listdir(path):
            subPath = os.path.join(path, sub)
            if not os.path.isdir(subPath):
                continue
            if sub in category_subs:
                echo0('* loading worlds from specially-named directory'
                      ' "{}"'.format(sub))
                got_worlds, deep_error = self.get_worlds_from(subPath)
                if got_worlds is not None:
                    worlds += got_worlds
                if deep_error is not None:
                    if err is not None:
                        err += "; " + deep_error
                    else:
                        err = deep_error
                continue
            world_conf_path = os.path.join(subPath, "world.conf")
            world_mt_path = os.path.join(subPath, "world.mt")
            world = {
                'name': sub,
                'path': subPath,
            }
            world['port'] = None
            world['running'] = None
            try_log_paths = []
            try_log_paths.append(os.path.join(
                self.logs_path,
                "{}.log".format(sub),
            ))
            try_log_paths.append(os.path.join(
                self.logs_path,
                "debug-{}.log".format(sub),
            ))
            world['log_paths'] = []  # set to None if len stays 0
            for try_log_path in try_log_paths:
                if os.path.isfile(try_log_path):
                    world['log_paths'].append(try_log_path)
                else:
                    echo1('INFO: There is no log file "{}"'
                          ' in {} ("debug.txt" will also be'
                          ' checked if present there).'
                          ''.format(try_log_path, self.logs_path))

            if len(world['log_paths']) == 0:
                world['log_paths'] = None

            if not os.path.isfile(world_mt_path):
                echo0("Error: {} in worlds directory {} doesn't contain"
                      " world.mt".format(sub, path))
            if os.path.isfile(world_conf_path):
                # This file is for Final Minetest only.
                world['port'] = get_conf_value(world_conf_path, "port")
                if world['port'] is not None:
                    port = int(world['port'])
                    world['running'] = False
                    '''
                    # See <https://stackoverflow.com/a/19196218/4541104>
                    # edited Mar 5, 2019 at 23:52 by ejohnso49
                    # answered Oct 5, 2013 at 9:38 by mrjandro
                    sock = socket.socket(socket.AF_INET,
                                         socket.SOCK_STREAM)
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        world['running'] = True
                    else:
                        echo1("connect_ex 127.0.0.1:{} responded with"
                              " code {}."
                              "".format(port, result))
                    '''
                    # ^ always returns code 111 for some reason, so:
                    result = check_server("127.0.0.1", port)
                    if result:
                        world['running'] = True
                    else:
                        world['running'] = False
                        echo1("check_server 127.0.0.1:{} responded with"
                              " {}."
                              "".format(port, result))

            else:
                echo1("INFO: {} in worlds directory {} doesn't contain"
                      " world.conf".format(sub, path))
            worlds.append(world)
        return worlds, err

    def load_worlds_meta(self):
        '''
        Make set self.worlds to a list of dicts. Each dict contains
        metadata about a world.
        '''
        if not self.good:
            msg = ("load_worlds_meta couldn't proceed since the"
                   " installation couldn't be analyzed by"
                   " minebest:Minetest.")
            return None, msg
        self.worlds, err = self.get_worlds_from(self.worlds_dir)
        return self.worlds, err

    def list_worlds(self):
        names = None
        if worlds is None:
            worlds, err = self.load_worlds_meta()
            if err is not None:
                return None, err
            names = []
            for world in worlds:
                names.append(world.name)
        return names, None


def main():
    global verbosity
    param1 = None
    command = None
    single_world_commands = ["log"]
    multi_world_commands = ["list"]

    var_name = None
    options = {}
    options['max_lines'] = 32
    for argI in range(1, len(sys.argv)):
        arg = sys.argv[argI]
        if var_name is not None:
            try:
                value = int(arg)
            except ValueError:
                try:
                    value = float(arg)
                except ValueError:
                    value = arg
            default_v = options.get(var_name)
            if default_v is not None:
                if type(value) != type():
                    usage()
                    echo0("Error: {} must be a {}"
                          " but {} is a(n) {}"
                          "".format(var_name, type(default_v).__name__,
                                    value, type(value).__name__))
                    return 1
            var_name = None
            continue
        if arg.startswith("-"):
            if arg == "--verbose":
                verbosity = 1
            elif arg == "--debug":
                verbosity = 2
            elif arg == "-n":
                var_name = "max_lines"
            else:
                usage()
                echo0("Invalid argument: {}".format(arg))
                return 1
        elif command is None:
            command = arg
        elif param1 is None:
            param1 = arg
        else:
            usage()
            echo0("Invalid argument: {}".format(arg))
            return 1

    if command is None:
        usage()
        echo0("You must specify a command.")
        return 1

    try:
        minetest = Minetest()
    except Exception as ex:
        usage()
        if "Your Minebest structure is not recognized" in str(ex):
            echo0("{}".format(ex))
            return 1
        else:
            raise ex

    if command in multi_world_commands:
        if param1 is not None:
            usage()
            echo0("You specified both a multi-world"
                  " command and a world name.")
            return 1
        elif command == "list":
            multi_world_command = True
            worlds, err = minetest.load_worlds_meta()
            if err is not None:
                echo0(err)
                return 1
            echo1("got {} world(s)".format(len(worlds)))
            for world in worlds:
                running = world.get('running')
                status = ""
                if running is True:
                    status = "is running"
                print("{} {}    {}"
                      "".format(world['port'], world['name'],
                                status))
        else:
            usage()
            echo0('Error: The "{}" command is not implemented.'
                  ''.format(command))
            return 1
    elif command in single_world_commands:
        if param1 is None:
            usage()
            echo0("Error: You must specify a world.")
            return 1
        world_name = param1
        if command == "log":
            print("")
            minetest.show_log(world_name,
                              max_lines=options['max_lines'])
        else:
            usage()
            echo0('Error: The "{}" command is not implemented.'
                  ''.format(command))
            return 1
    else:
        usage()
        echo0("Error: invalid command {}".format(command))
        return 1


    return 0


if __name__ == "__main__":
    sys.exit(main())
