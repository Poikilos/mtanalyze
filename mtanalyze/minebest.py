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
# (and option to run it). Jump to line number in nano (undocumented
# in --help but found at <https://stackoverflow.com/a/36211296/4541104>
# and <https://linuxhint.com/how-to-go-to-line-x-in-nano/>):
# "nano +{} {}".format(lineN, path)

from __future__ import print_function
from __future__ import division
import os
import sys
import platform
import subprocess
import socket
import codecs
import struct
import re
from copy import deepcopy

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
python_mr = sys.version_info.major
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


# See mtanalyze/settings.py or <https://github.com/poikilos/voxboxor>
#   for real settingtypes.txt processing code. `var_types` is only a
#   short list of well-known settings:
var_types = {}
var_types['motd'] = "string"
var_types['server_address'] = "string"
var_types['server_description'] = "string"
var_types['server_name'] = "string"
var_types['serverlist_url'] = "string"
var_types['irc.channel'] = "string"
var_types['irc.nick'] = "string"
var_types['irc.server'] = "string"
var_types['remote_media'] = "string"
var_types['name'] = "string"
var_types['debug_log_level'] = "string"
var_types['travelnet_theme'] = "string"
var_types['areas.self_protection_privilege'] = "string"
var_types['debug_log_level'] = "string"
var_types['mg_name'] = "string"
var_types['secure.trusted_mods'] = "<string>,..."
var_types['secure.http_mods'] = "<string>,..."
var_types['deprecated_lua_api_handling'] = "string"
var_types['codergroups'] = "string"
var_types['game_mode'] = "string"
var_types['restriction_exempted_names'] = "<string>,..."
var_types['default_privs'] = "<string>, ..."  # spaces are allowed
var_types['mgflat_spflags'] = "<string>, ..."
var_types['mgv7_spflags'] = "<string>, ..."

transfer_var_names = ['secure.trusted_mods', 'secure.http_mods',
                      'server_address', 'static_spawn_point']

trues = ["true", "on"]
falses = ["false", "off"]


def get_braced_parts(text):
    # See <https://stackoverflow.com/questions/51051136/
    # extracting-content-between-curly-braces-in-python>
    return re.findall(r'\{(.*?)\}', text)


def symbol_to_tuple(s, allow_string=True, allow_bool=True,
                    var_name=None, var_type=None, allow_one=False,
                    tuple_format=None):
    '''
    Convert a comma-separated list of value symbols to individual
    literal values with Python types. For documentation on more keyword
    arguments see symbol_to_value.

    Keyword arguments:
    allow_one -- True: Return a tuple as long as the string isn't blank.
        False: Return None if the value doesn't contain a comma (This
        setting is usually for auto-detection of whether it is a tuple).
    tuple_format -- The tuple format can be  "..." (csv with no spaces)
        or " ..." (csv with spaces allowed [spaces will be stripped]).
        The default value is " ..." if it is None so that spaces are
        removed for usual cases (such as v3f).

    Returns:
    A tuple if parses as a tuple; None if has no commas, unless is
    forced to be a tuple by allow_one=True; None if dict (surrounded by
    "{}" curly braces); None if var_type is set and not every element
    is of that type.
    '''

    list_var_type = None
    is_dict = s.startswith("{") and s.endswith("}")
    if var_name is not None:
        list_var_type = var_types.get(var_name)
        if list_var_type is not None:
            if is_dict or ("," not in list_var_type):
                raise ValueError("A tuple was expected for {}"
                                 "".format(var_name))
    if tuple_format is None:
        tuple_format = " ..."
        # ^ By default, spaces are stripped (such as "0, 2.5, 0").
    if is_dict:
        return None
    if not allow_one:
        if "," not in s:
            return None
    part_strings = s.split(",")
    parts = []
    for raw_part_s in part_strings:
        part_s = raw_part_s
        if tuple_format == " ...":
            part_s = part_s.strip()
        elif tuple_format == "...":
            if part_s[:1].strip() != part_s[:1]:
                var_name_msg = var_name
                if var_name_msg is None:
                    var_name_msg = ""
                raise ValueError(
                    "The value of {} = {} should not contain spaces."
                    "".format(var_name_msg, s)
                )
        elif tuple_format is not None:
            raise ValueError(
                "The tuple format {} is not valid."
                "".format(tuple_format)
            )
        part = symbol_to_value(part_s, allow_string=allow_string,
                               allow_bool=allow_bool,
                               allow_tuple=False, var_type=var_type)
        if part is None:
            # If any part is not an expected value, then do not
            # consider the value as a tuple.
            return None
        else:
            parts.append(part)
    return tuple(parts)


def symbol_to_value(s, allow_string=True, allow_bool=True,
                    allow_tuple=True, allow_string_tuple=True,
                    var_name=None, var_type=None):
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
    var_name -- Set the variable name in order to help detect the type
        (The global dict var_types is used to define the type of vars
        by name).
    var_type -- Specify the var type so it doesn't have to be detected.
        this should be set if symbol_to_value calls itself and the
        type of the tuple element is known (for example, if the type of
        var_name is string list, exclude var_name but set
        var_type="string".
    '''
    result = None
    type_parts = None  # If not None, the expected value is a tuple.
    homogeneous_type = None
    tuple_format = None
    if var_name is not None:
        if var_type is None:
            var_type = var_types.get(var_name)
    if var_type is not None:
        if "," in var_type:
            type_parts = var_type.split(",")
            tp0 = type_parts[0]
            tp1 = None
            if len(type_parts) > 1:
                tp1 = type_parts[1]
            if tp0.startswith("<") and tp0.endswith(">"):
                tp0 = tp0[0][1:-1]
                type_parts[0] = tp0
            if (len(type_parts) == 2) and (tp1 in ["...", " ..."]):
                homogeneous_type = tp0
                tuple_format = tp1
            else:
                raise NotImplementedError(
                    'Non-homogeneous type for {} (only var_type like'
                    ' "type", "<type>,...", or "<type>, ..." [tuple'
                    ' with spaces allowed] is implemented)'
                    ''.format(var_type)
                )
    if type_parts is None:
        # Only check for a string literal if not a tuple.
        if s.startswith('"') and s.endswith('"'):
            if allow_string:
                return s[1:-1]
            else:
                return None
    else:
        if not allow_tuple:
            raise ValueError(
                "type_parts for {} was {} but allow_tuple=False."
                "".format(var_name, type_parts)
            )
    try:
        if type_parts is not None:
            ValueError("Checking for int skipped.")
        result = int(s)
    except ValueError:
        try:
            if type_parts is not None:
                ValueError("Checking for float skipped.")
            result = float(s)
        except ValueError:
            got_tuple = None
            allow_one = False
            if type_parts is not None:
                # Force a tuple even if there is no comma if a tuple is
                # expected.
                allow_one = True
            if s.startswith("{") and s.endswith("}"):
                # TODO: implement dict such as { x=100, y=100, z=100 }"
                #   for areas.self_protection_max_size
                pass
                # Dict is not implemented, so it will become a string.
            if allow_tuple:
                got_tuple = symbol_to_tuple(
                    s,
                    allow_string=allow_string_tuple,
                    allow_bool=False,
                    allow_one=allow_one,
                    var_type=homogeneous_type,
                    tuple_format=tuple_format,
                )
            # ^ allow_bool=False because a tuple of booleans doesn't
            #   have a known usage for Minetest.
            if type_parts is not None:
                result = got_tuple
                if got_tuple is None:
                    raise ValueError(
                        "A {} tuple was expected for {}"
                        "".format(homogeneous_type, var_name)
                    )
            elif allow_bool and s.lower() in trues:
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
            '''
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
                # echo0("{}:{}: Warning: {} was not in quotes."
                #       "".format(path, lineN, result_line_n, name))
            else:
            '''
            tmp = symbol_to_value(value, allow_string=True,
                                  var_name=name)
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
                    echo0("{}:{}: Warning: Line {} already set {}."
                          "".format(path, lineN, result_line_n, name))
                result_line_n = lineN
                result = value
                if not use_last:
                    break
    return result


"""
def check_minetest_server(address, port):
    '''
    Send a dummy reliable packet to the server.
    minetest/doc/protocol.txt
    '''
    pass
    # TODO: finish this
"""


def _check_generic_server(address, port):
    '''
    This doesn't work for Minetest (connection is refused--UDP doesn't
    have a connection, unlike TCP).
    '''
    # from <https://stackoverflow.com/a/32382603/4541104>
    # Create a TCP socket
    if not isinstance(port, int):
        raise ValueError(
            "port must be an int but {} is a(n) {}"
            "".format(port, type(port).__name__)
        )
    s = socket.socket()
    echo1("Attempting to connect to %s on port %s" % (address, port))
    try:
        s.connect((address, port))
        echo1("Connected to %s on port %s" % (address, port))
        return True
    except socket.error as e:
        echo1("Connection to %s on port %s failed: %s" % (address, port, e))
        return False
    finally:
        s.close()


def check_server(host, port):
    '''
    Do a server detection by constructing and examining packets
    manually (based on the PHP example "check_if_minetestserver_up" in
    minetest/doc/protocol.txt)

    For more detailed packet construction code, see
    voxboxor/network/connection.py in
    <https://github.com/poikilos/voxboxor>.
    '''
    # from <https://stackoverflow.com/a/32382603/4541104>
    # Create a TCP socket
    if not isinstance(port, int):
        raise ValueError(
            "port must be an int but {} is a(n) {}"
            "".format(port, type(port).__name__)
        )
    sock = socket.socket()
    # NOTE: from socket import socket doesn't help. using socket() after
    #   that doesn't result in a function.
    echo1("Attempting to connect to %s on port %s" % (host, port))
    try:
        # sock.connect((host, port))
        # ^ always returns 111 connection refused
        #   so send a UDP packet as per <https://pythontic.com/modules/
        #   socket/udp-client-server-example>:
        # msgFromClient       = "Hello UDP Server"
        # buf                 = str.encode(msgFromClient)
        serverAddressPort   = (host, port)
        bufferSize          = 1000  # minetest/doc/protocol.txt has 1000
        # ^ "ask for enough bytes to cover the entire message or it will
        #   be dropped" -<https://stackoverflow.com/a/36116486/4541104>
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # ^ The PHP example also uses SOL_UDP
        # ^ kwargs names for args used above are: family, type
        # ^ SOCK_DGRAM is UDP
        # buf = codecs.decode("4f45740300000003ffdc01", "hex")
        # ^ This hex string is from minetest/doc/protocol.txt example
        # ^ codecs.decode works for Python 2 or 3 according to
        #   <https://stackoverflow.com/a/9641622/4541104>
        buf = b'OEt\x03\x00\x00\x00\x03\xff\xdc\x01'
        # ^ This hex string is the one a voxboxor nose test displays
        #   (It is identical to the example, just defined differently in
        #   Python)

        echo1("Sending %s connect packet to %s on port %s"
              % (type(buf).__name__, host, port))
        sock.sendto(buf, (host, port))
        # ^ buf must be bytes (See <https://docs.python.org/3/library/
        #   socket.html#socket.socket.sendto>
        echo1("Receiving response...")
        sock.settimeout(3)
        msgFromServer, conn_info = sock.recvfrom(bufferSize)
        # ^ recvfrom is for UDP and returns (data, connection info)
        #   (recv is for TCP and only has one return--see
        #   <https://stackoverflow.com/a/36116194/4541104>).
        # ^ raises exception on timeout
        # msgFromServer[0] is 79 if up and has expected protocol
        peer_id_bytes = msgFromServer[9:11]
        values = struct.unpack(">H", peer_id_bytes)
        # ^ '>' since Minetest packets are always big-endian
        peer_id = values[0]  # There is only one value in the substring.
        # ^ H for u16 (for a complete packet struct, see
        #   <https://github.com/poikilos/voxboxor>).
        msg = "Message from Server: {}".format(msgFromServer[0])
        echo1(msg)
        echo1("- peer_id: {}".format(peer_id))
        return True
    except socket.error as e:
        echo1("Connection to %s on port %s failed: %s" % (host, port, e))
        return False
    finally:
        echo1("Closing connection.")
        sock.close()


class Minetest:
    minebest_list_fmt = "{port: <5} {name: <16}{status}"

    def __init__(self, data_dir=None, worlds_dir=None, logs_path=None,
                 echo_status_fmt=None):
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
        echo_status_fmt -- Output text to the console in this format
            immediately after each world is analyzed.
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
        echo0("data_dir={}".format(data_dir))
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
        echo0("worlds_dir={}".format(self.worlds_dir))
        self.good = True
        metas, err = self.load_worlds_meta(
            echo_status_fmt=echo_status_fmt,
        )
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

    def get_worlds_from(self, path, category_subs=["live", "static"],
                        echo_status_fmt=None):
        '''
        Get a tuple that contains a world metadatas list and an error
        (or None).

        Keyword arguments:
        category_subs -- If a subdirectory under path is named the same
            as any string in this list, look for more worlds there
            instead of considering that directory a world.
        echo_status_fmt -- After each world is analyzed, echo world
            keys in this format such as "{: <5} {: <16}{}" for
            minebest format (produces output such as:
            "30000 notcraft        is running")
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

                got_worlds, deep_error = self.get_worlds_from(
                    subPath,
                    category_subs=[],  # prevent deeper directories
                    echo_status_fmt=echo_status_fmt,
                )
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
                    echo2('INFO: There is no log file "{}"'
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
                for test_name in transfer_var_names:
                    world[test_name] = get_conf_value(world_conf_path,
                                                      test_name)
                    echo2("test setting: world[{}]={}"
                          "".format(test_name, world[test_name]))
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
            world['status'] = None
            if world.get('running') is True:
                world['status'] = "is running"
            elif world.get('running') is False:
                world['status'] = "is down"
            if echo_status_fmt is not None:
                tmp_world = deepcopy(world)
                if not isinstance(echo_status_fmt, str):
                    raise TypeError(
                        "echo_status_fmt must be str (to be"
                        " used) or None but is {}"
                        "".format(type(echo_status_fmt).__name__)
                    )
                echo2("")
                echo2("echo_status_fmt={}".format(echo_status_fmt))
                echo2("world={}".format(world))
                required_vars = get_braced_parts(echo_status_fmt)
                for i in range(len(required_vars)):
                    ender = required_vars[i].find(":")
                    if ender >= 0:
                        required_vars[i] = required_vars[i][:ender]
                    if len(required_vars[i]) == 0:
                        raise ValueError(
                            'All of the placeholders in'
                            ' the format must be named, but [{}] was'
                            ' sequential in "{}".'
                            ''.format(i, echo_status_fmt)
                        )
                    if required_vars[i] not in world:
                        tmp_world[required_vars[i]] = None
                        echo2("adding required '{}' temporarily"
                              "".format(required_vars[i]))
                echo2("required_vars={}".format(required_vars))
                for k, v in tmp_world.items():
                    if v is None:
                        tmp_world[k] = "None"
                msg = echo_status_fmt.format(**tmp_world)
                # ^ Without changing None to "None", expansion
                #   (when echo_status_fmt=minebest_list_fmt)
                #   works in python2 and python3 terminal but not when
                #   running the script in python3 (3.9.2) :( why??
                #   It works fine on python2
                print(msg)
            worlds.append(world)
        return worlds, err

    def load_worlds_meta(self, echo_status_fmt=None):
        '''
        Make set self.worlds to a list of dicts. Each dict contains
        metadata about a world.

        Keyword arguments:
        echo_status_fmt -- Show a world in this format immediately each
            time a world is done being analyzed.
        '''
        if not self.good:
            msg = ("load_worlds_meta couldn't proceed since the"
                   " installation couldn't be analyzed by"
                   " minebest:Minetest.")
            return None, msg
        self.worlds, err = self.get_worlds_from(
            self.worlds_dir,
            echo_status_fmt=echo_status_fmt,
        )
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
        echo_status_fmt = None
        if command == "list":
            echo_status_fmt=Minetest.minebest_list_fmt
        minetest = Minetest(echo_status_fmt=echo_status_fmt)
    except ValueError as ex:
        usage()
        if "Your Minebest structure is not recognized" in str(ex):
            echo0("{}".format(ex))
            return 1
        else:
            raise ex
    except Exception as ex:
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
            # already done during Minetest object init in this case
            multi_world_command = True
            '''
            worlds, err = minetest.load_worlds_meta()
            if err is not None:
                echo0(err)
                return 1
            echo1("got {} world(s)".format(len(worlds)))
            for world in worlds:
                running = world.get('running')
                if running is True:
                    status = "is running"
                elif running is False:
                    status = "is down"
                else:
                    status = "None"
                print("{: <5} {: <16}{}"
                      "".format(world['port'], world['name'],
                                status))
            '''
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
