#!/usr/bin/env python
'''
Test other Poikilos python modules.

This module requires the parsing module from
https://github.com/poikilos/pycodetool
'''
from __future__ import print_function

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

import os
import sys
import keyword
# import types
import inspect
import traceback
if sys.version_info.major >= 3:
    if sys.version_info.minor >= 4:
        from importlib import reload
    else:
        from imp import reload
else:
    input = raw_input

MY_PATH = os.path.realpath(__file__)
MY_MODULE_PATH = os.path.split(MY_PATH)[0]
MY_REPO_PATH = os.path.split(MY_MODULE_PATH)[0]
REPOS_PATH = os.path.split(MY_REPO_PATH)[0]
try:
    import mtanalyze
except ImportError as ex:
    if (("No module named mtanalyze" in str(ex))  # Python 2
            or ("No module named 'mtanalyze'" in str(ex))):  # Python 3
        sys.path.insert(0, MY_REPO_PATH)
    else:
        raise ex

from mtanalyze import (
    PYCODETOOL_DEP_MSG,
    PCT_REPO_PATH,
    echo0,
    echo1,
)

try:
    import pycodetool
except ImportError as ex:
    if (("No module named pycodetool" in str(ex))  # Python 2
            or ("No module named 'pycodetool'" in str(ex))):  # Python 3
        sys.path.insert(0, PCT_REPO_PATH)
try:
    import pycodetool
except ImportError as ex:
    if (("No module named pycodetool" in str(ex))  # Python 2
            or ("No module named 'pycodetool'" in str(ex))):  # Python 3
        sys.stderr.write(PYCODETOOL_DEP_MSG+"\n")
        sys.stderr.flush()
        sys.exit(1)
    else:
        raise ex

from pycodetool.parsing import *

modules = []
modules.append("os")
modules.append("sys")
modules.append("keyword")
modules.append("inspect")
modules.append("traceback")
dModules = []  # dynamically-loaded modules

# THE FUNCTIONS ARE USED ON minetest-chunkymap
# AT THE BOTTOM OF THIS SCRIPT

# TODO: code checking such as:
# ANY LANGUAGE:
# * check for signs in len params (such as in Python where
#   str(len(part1+part2)) should be str(len(part1))+part2
# * check for only variable name in quotes (maybe the programmer meant
#   to use the value)
# * mixing width with y (or height or z) and mixing height with x (or
#   width)
# PYTHON:
# * check for redefining member variable (missing "self.") [since python
#   does not throw NameError on definition, only if used and not
#   defined]
# * check for use of os.dirname (should be os.path.dirname)
# * check for methods missing 'self' as first argument name
# PHP:
# * using '+' next to doublequote or singlequote in php, adjacent or
#   seperated only by whitespace (probably meant concatenate operator
#   '.')
# * using empty function (problematic since empty($value) evaluates to
#   true when $value is zero -- empty_really in parsing can be used
#   instead)
# SHELL SCRIPT:
# * don't use '*' inside quotes (fails)
# * using HOME without preceding dollar sign
# ECMAScript:
# * use of e.clientX e.clientY where rawl contains neither + or -
#   (should use some kind of modifiers for scroll and canvas position
#   such as in get_relative_mouse_point method)


def view_traceback():
    ex_type, ex, tb = sys.exc_info()
    print(str(ex_type))
    print(str(ex))
    traceback.print_tb(tb)
    del tb


class RegressionMismatch:
    sideA = None
    sideB = None
    endswith_enable = None
    startswith_enable = None

    def __init__(self, sideA, sideB, startswith_enable,
                 endswith_enable):
        self.sideA = sideA
        self.sideB = sideB
        self.endswith_enable = endswith_enable
        self.startswith_enable = startswith_enable


allQuotes = "'\""
global_case_sensitive_enable = None
y_enable = False
print("Initializing...")
mismatches = []
independent_list = ["index", "suffix", "prefix"]
independent_list.append("self")
independent_list.append("int")
independent_list.append("float")
independent_list.append("double")
independent_list.append("long")
independent_list.append("bool")
independent_list.append("str")
independent_list.append("string")
independent_list.append("strlen")
independent_list.append("len")
independent_list.append("os.path.join")
independent_list.append("open")
independent_list.append("close")
independent_list.append("None")
independent_list.append("null")
independent_list.append("NULL")
# NOTE: "for decachunk_z_name in os.listdir(decachunk_x_path):"
# is ok since z folders are in x folder
independent_endswith_list = []
for word in independent_list:
    independent_endswith_list.append("_"+word)
mismatches.append(RegressionMismatch("_x", "_z", False, True))

if y_enable:
    mismatches.append(RegressionMismatch("_x", "_y", False, True))
    mismatches.append(RegressionMismatch("_y", "_z", False, True))

mismatches.append(RegressionMismatch("_x_", "_z_", False, False))
if y_enable:
    mismatches.append(RegressionMismatch("_x_", "_y_", False, False))
    mismatches.append(RegressionMismatch("_y_", "_z_", False, False))

mismatches.append(RegressionMismatch("x", "z", False, True))
if y_enable:
    mismatches.append(RegressionMismatch("x", "y", False, True))
    mismatches.append(RegressionMismatch("y", "z", False, True))

mismatches.append(RegressionMismatch("x_", "z_", True, False))
if y_enable:
    mismatches.append(RegressionMismatch("x_", "y_", True, False))
    mismatches.append(RegressionMismatch("y_", "z_", True, False))

if global_case_sensitive_enable is True:
    mismatches.append(RegressionMismatch("_X_", "_Z_", False, False))
    if y_enable:
        mismatches.append(RegressionMismatch("_X_", "_Y_", False, False))
        mismatches.append(RegressionMismatch("_Y_", "_Z_", False, False))

    mismatches.append(RegressionMismatch("_X", "_Z", False, True))
    if y_enable:
        mismatches.append(RegressionMismatch("_X", "_Y", False, True))
        mismatches.append(RegressionMismatch("_Y", "_Z", False, True))

    mismatches.append(RegressionMismatch("X", "Z", False, True))
    if y_enable:
        mismatches.append(RegressionMismatch("X", "Y", False, True))
        mismatches.append(RegressionMismatch("Y", "Z", False, True))

    mismatches.append(RegressionMismatch("X_", "Z_", True, False))
    if y_enable:
        mismatches.append(RegressionMismatch("X_", "Y_", True, False))
        mismatches.append(RegressionMismatch("Y_", "Z_", True, False))


def is_dependend_variable(name):
    for mm in mismatches:
        if mm.startswith_enable:
            if startswith(name, mm.sideA):
                return True
            if startswith(name, mm.sideB):
                return True
        elif mm.endswith_enable:
            if endswith(name, mm.sideA):
                return True
            if endswith(name, mm.sideB):
                return True
        else:
            if mm.sideA in name:
                return True
            elif mm.sideA in name:
                return True
    return False

# splits by any non-alphanumeric characters
# print(keyword.kwlist)
#  DOESN'T WORK (from linuxbochs on <http://stackoverflow.com/questions/
#  6315496/display-a-list-of-user-defined-functions-in-the-python-idle-
#  session> ):
# function_list = \
#     [f for f in globals().values() if type(f) == types.FunctionType]
#  DOESN'T WORK
# def dummy(): pass
# function_list = \
#     [f.__name__ for f in globals().values() if type(f) == type(dummy)]


function_list = []
for moduleS in modules:
    exec("function_list += inspect.getmembers(" + moduleS
         + ", inspect.isroutine)")
    # NOTE: isfunction does NOT include c-defined functions such as those
    # in math
function_names = []
for function_tuple in function_list:
    function_names.append(function_tuple[0])
print("  (Ignoring known routines:")
print(','.join(function_names)+")")
print("")
print("")


def split_non_alnum(haystack, strip_enable=True,
                    enable_skip_keywords=True):
    global independent_list
    global function_names
    global modules
    results = []
    index = 0
    start_index = 0
    while index <= len(haystack):
        if index == len(haystack) or not haystack[index].isalnum():
            word = haystack[start_index:index]
            skips = [keyword.kwlist, function_names, independent_list,
                     modules]
            if not enable_skip_keywords or not in_any(word, skips):
                if strip_enable:
                    results.append(word.strip())
                else:
                    results.append(word)
            start_index = index+1
        index += 1
    return results


issue_count = 0
file_list = []
# def is_identifier(needle, dot_continues_enable):
#     result = True
#     for index in range(0,len(needle)):
#         if needle[index] not in identifier_chars:
#             result = False
#             break
#     return result


def split_non_identifier(haystack, strip_enable=True,
                         enable_skip_keywords=True,
                         enable_skip_independent=True,
                         dot_continues_enable=True):
    results = []
    index = 0
    start_index = 0
    is_in_quote_char = None
    prev_char = None
    escaped_dq_enable = True
    while index <= len(haystack):
        if ((index < len(haystack)) and (is_in_quote_char is None) and
                (haystack[index] in allQuotes)):
            is_in_quote_char = haystack[index]
        elif ((index < len(haystack)) and
                (is_in_quote_char is not None) and
                (haystack[index] == is_in_quote_char and
                    (prev_char != "\\" or is_in_quote_char != "\""))):
            is_in_quote_char = None
        elif ((index == len(haystack)) or
                ((is_in_quote_char is None) and
                    not is_identifier_valid(haystack[index],
                                            dot_continues_enable))):
            word = haystack[start_index:index]
            if (not enable_skip_keywords) or word not in keyword.kwlist:
                if ((not enable_skip_independent) or
                        (word not in independent_list and
                            not endswith_any(
                                word,
                                independent_endswith_list
                            ))):
                    if strip_enable:
                        results.append(word.strip())
                    else:
                        results.append(word)
            start_index = index+1
        if index < len(haystack):
            prev_char = haystack[index]
        index += 1
    return results


def endswith(haystack, needle, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    if (haystack is not None and needle is not None and
            len(needle) > 0 and len(haystack) >= len(needle)):
        if enable_case_sensitive:
            if haystack[-len(needle):] == needle:
                # print("haystack[-len(needle):] = "
                #       + haystack[-len(needle):]
                #       + " in "+haystack)
                result = True
        else:
            if haystack[-len(needle):].lower() == needle.lower():
                # print("haystack[-len(needle):].lower() = "
                #       + haystack[-len(needle):].lower()
                #       + " in "+haystack)
                result = True
    return result


def startswith(haystack, needle, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    if (haystack is not None and
            needle is not None and
            len(needle) > 0 and
            len(haystack) >= len(needle)):
        if enable_case_sensitive:
            if haystack[:len(needle)] == needle:
                result = True
        else:
            if haystack[:len(needle)].lower() == needle.lower():
                result = True
    return result


def any_endswith(haystacks, needle, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    for haystack in haystacks:
        if endswith(haystack, needle, enable_case_sensitive):
            result = True
            break
    return result


def endswith_any(haystack, needles, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    for needle in needles:
        if endswith(haystack, needle, enable_case_sensitive):
            result = True
            break
    return result


def any_startswith(haystacks, needle, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    for haystack in haystacks:
        if startswith(haystack, needle, enable_case_sensitive):
            result = True
            break
    return result


def startswith_any(haystack, needles, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    for needle in needles:
        if startswith(haystack, needle, enable_case_sensitive):
            result = True
            break
    return result


def endswith_any(haystack, needles, enable_case_sensitive=False):
    if global_case_sensitive_enable is not None:
        enable_case_sensitive = global_case_sensitive_enable
    result = False
    for needle in needles:
        if endswith(haystack, needle, enable_case_sensitive):
            result = True
            break
    return result


def lower_all(s_or_list):
    if s_or_list is None:
        return None
        # Prevent an AttributeError unrelated to string vs list
        # which would break the logic below.
    try:
        return s_or_list.lower()  # It is a string.
    except AttributeError:
        # It is a list.
        return [s.lower() for s in s_or_list]


def in_any(needle, haystacks, CI=False):
    """
    Check whether needle is in any haystack. Each haystack can be a
    string or a list (haystacks would be a list of lists of strings in
    the latter situation). If CI=False, then you can provide other types
    of lists (but must be list of lists), since only `in` (not
    lower_all) will occur then.
    """
    # TODO: test with number lists and CI=False.
    if global_case_sensitive_enable is not None:
        CS = global_case_sensitive_enable
    if needle is None or len(needle) < 1:
        return False
    for haystack in haystacks:
        if haystack is not None and len(haystack) > 0:
            if CI:
                if needle.lower() in lower_all(haystack):
                    return True
            else:
                if needle in haystack:
                    return True
    return False


min_indent = ""


def increase_indent():
    global min_indent
    min_indent += "  "


def decrease_indent():
    global min_indent
    if len(min_indent) >= 2:
        min_indent = min_indent[:-2]


def is_imported(module):
    return module in dModules


def check_coord_mismatch(path):
    global file_list
    global issue_count
    global modules
    print("Running check_coord_mismatch on " + path + "...")
    global function_list
    global pgrstmp
    if (path not in file_list):
        file_list.append(path)
    line_n = 1
    ins = open(path, 'r')
    rawl = True
    global min_indent
    problematic_line_count = 0
    inline_comment_delimiter = "#"
    inline_line_break = None
    file_path_lower = path.lower()
    if len(path) > 3 and (file_path_lower[-3:] == ".cs"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(path) > 2 and (file_path_lower[-2:] == ".c"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(path) > 2 and (file_path_lower[-2:] == ".h"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(path) > 4 and (file_path_lower[-4:] == ".hpp"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(path) > 4 and (file_path_lower[-4:] == ".cpp"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(path) > 4 and (file_path_lower[-4:] == ".php"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(path) > 3 and (file_path_lower[-3:] == ".py"):
        inline_comment_delimiter = "#"
    elif len(path) > 4 and (file_path_lower[-4:] == ".pyw"):
        inline_comment_delimiter = "#"
    else:
        answer = input("what is the inline comment delimiter for the"
                       " sourcecode file type of " + path
                       + " [blank for " + inline_comment_delimiter
                       + "]? ")
        if len(answer) > 0:
            inline_comment_delimiter = answer

    dup_ignore_list = function_names + independent_list + modules
    while True:
        rawl = ins.readline()
        if not rawl:
            break
        prev_issue_count = issue_count
        strp = rawl.strip()
        comment_index = find_unquoted_even_commented(
            strp,
            inline_comment_delimiter
        )
        if comment_index > -1:
            strp = strp[:comment_index]
        sublines = []

        if inline_line_break is not None:
            remaining_string = strp
            while True:
                inlineBrI = find_unquoted_even_commented(
                    remaining_string,
                    inline_line_break
                )
                # ^ inline strp break index (do NOT check for
                # INLINE COMMENT since
                # already removed it using detected delimiter
                # above)
                if inlineBrI < 0:
                    break
                sublines.append(remaining_string[:inlineBrI])
                remaining_string = remaining_string[inlineBrI+1:]

            if len(remaining_string) > 0:
                sublines.append(remaining_string)
        else:
            sublines.append(strp)
        for subline in sublines:
            strp = subline
            if len(strp) < 1 or strp.startswith("#"):
                continue
            ao_index = strp.find("=")
            importS = "import "
            from_string = "from "
            importI = -1
            if strp[:len(importS)] == importS:
                importI = 0
            elif strp[:len(from_string)] == from_string:
                importS = from_string
                importI = strp.find(importS)
            if importI >= 0:
                moduleS = strp[importI+len(importS):].strip()
                space_index = moduleS.find(" ")
                if space_index > -1:
                    moduleS = moduleS[:space_index]
                if moduleS not in modules:
                    modules.append(moduleS)
                    try:
                        # tmp_tuples = []
                        importS = "import "+moduleS
                        # exec exec_string
                        try_enable = False
                        outs = open('pgrstmp.py', 'w')
                        outs.write("def get_module_contents():"+"\n")
                        outs_indent = "    "
                        outs.write(outs_indent+"results = None"+"\n")
                        if try_enable:
                            outs.write(outs_indent+"try:"+"\n")
                            outs_indent = "        "
                        outs.write(outs_indent+"import inspect"+"\n")
                        outs.write(outs_indent+importS+"\n")
                        exec_string = ("tmp_tuples = inspect.getmembers"
                                       "(" + moduleS + ", "
                                       "inspect.isroutine)")
                        outs.write(outs_indent + exec_string + "\n")
                        outs.write(outs_indent + "results = []" + "\n")
                        outs.write(outs_indent + "for function_tuple in"
                                   " tmp_tuples:"+"\n")
                        outs.write(outs_indent + "    results.append"
                                   "(function_tuple[0])"+"\n")

                        outs_indent = "    "
                        if try_enable:
                            outs.write(outs_indent + "except:" + "\n")
                            outs_indent = "        "
                            outs.write(outs_indent + "print(\"Could not"
                                       " finish get_module_contents\")"
                                       "\n")
                        outs_indent = "    "
                        outs.write(outs_indent + "return results"
                                   + "\n")
                        outs.write("\n")
                        outs.close()
                        if "pgrstmp" in dModules:
                            import pgrstmp
                            # ^ prevent "'pgrstmp' is not defined below
                            reload(pgrstmp)
                        else:
                            import pgrstmp
                            # ^ poikilos regression suite temporary code
                            dModules.append("pgrstmp")
                        tmp_list = pgrstmp.get_module_contents()
                        os.remove("pgrstmp.py")
                        new_list = None
                        if tmp_list is not None:
                            new_list = []
                            for routine_string in tmp_list:
                                if routine_string not in function_list:
                                    new_list.append(routine_string)
                        if new_list is not None:
                            function_list += new_list
                            fmt = ("Found {} new method(s) from {} to"
                                   " ignore: {}")
                            msg = fmt.format(len(new_list), moduleS,
                                             ','.join(new_list))
                            print(msg)
                            if len(new_list) > 0:
                                dup_ignore_list = (function_names
                                                   + independent_list
                                                   + modules)
                        else:
                            print("unable to import module named '"
                                  + moduleS + "', so some routines may"
                                  " not be successfully ignored:")
                        del pgrstmp
                    except ImportError:
                        print("Could not finish importing module"
                              " named '" + moduleS + "', so some"
                              " routines"
                              " may not be successfully ignored:")
                        view_traceback()
            if ao_index < 0:
                ao_index = strp.find(">")
            if ao_index < 0:
                ao_index = strp.find("<")
            if ao_index < 0:
                ao_index = strp.find(" in ")

            if ao_index <= 0:  # intentionally <=0 instead of =
                continue
            # if ao_index > 0:
            increase_indent()
            names_string = strp[:ao_index].strip()
            values_string = strp[ao_index+1:].strip()
            names = split_non_identifier(names_string)
            values = split_non_identifier(values_string)
            msg = None

            msgPrefix = " WARNING: "
            tSI = 0  # this start index
            names_string = strp[:ao_index].strip()
            values_string = strp[ao_index+1:].strip()
            names = split_non_identifier(names_string)
            values = split_non_identifier(values_string)

            # while True:
            #     this_chunk_len = get_operation_chunk_len(
            #         strp,
            #         tSI,
            #         1,
            #         line_n
            #     )
            #     if this_chunk_len < 1:
            #         break
            #     partial_string = strp[tSI:tSI+this_chunk_len]
            #     tSI += this_chunk_len

            duplicate_index = find_dup(names,
                                       ignore_numbers_enable=True)
            if duplicate_index > -1:
                if names[duplicate_index] not in dup_ignore_list:
                    if is_dependend_variable(names[duplicate_index]):
                        nameI = rawl.find(names[duplicate_index])
                        msgPrefix = " WARNING: "
                        issue_count += 1
                        fmt = ("{}({},{}){}name '{}' is used twice"
                               " (perhaps other coord should have been"
                               " used)")
                        msg = fmt.format(path, line_n, nameI,
                                         msgPrefix,
                                         names[duplicate_index])
                        print(msg)
                        break
            duplicate_index = find_dup(values)
            if duplicate_index > -1:
                if values[duplicate_index] not in dup_ignore_list:
                    if is_dependend_variable(values[duplicate_index]):
                        nameI = rawl.find(
                            values[duplicate_index]
                        )
                        msgPrefix = " WARNING: "
                        issue_count += 1
                        fmt = ("{}({},{}){}value '{}' is used twice"
                               " (perhaps other coord should have been"
                               " used)")
                        msg = fmt.format(path, line_n, nameI,
                                         msgPrefix,
                                         values[duplicate_index])
                        print(msg)
                        break

            msg = None

            for mm in mismatches:
                both_present = False
                onlyMisMatchCo = (" ERROR (only has mismatch): ")
                msgPrefix = " WARNING: "
                if mm.startswith_enable:
                    if ((any_startswith(names, mm.sideA) and
                            not any_startswith(names, mm.sideB)) and
                            any_startswith(values, mm.sideB)):
                        nameI = rawl.find(mm.sideA) + 1
                        if not both_present:
                            both_present = any_startswith(values,
                                                          mm.sideA)
                            msgPrefix = onlyMisMatchCo
                        # if msg is None:
                        fmt = ("{} ({},{}){}name starts with {}, but"
                               " {} on right in check/assignment")
                        msg = fmt.format(path, line_n, nameI,
                                         msgPrefix, mm.sideA, mm.sideB)
                        print(msg)
                        issue_count += 1
                        break

                    elif ((any_startswith(names, mm.sideB) and
                            not any_startswith(names, mm.sideA)) and
                            any_startswith(values, mm.sideA)):
                        nameI = rawl.find(mm.sideB) + 1
                        if not both_present:
                            both_present = any_startswith(values,
                                                          mm.sideB)
                            msgPrefix = onlyMisMatchCo
                        # if msg is None:
                        # TODO: is sideA supposed to be second here?
                        fmt = ("{} ({},{}){}name starts with {}, but"
                               " {} on right in check/assignment")
                        msg = fmt.format(path, line_n, nameI,
                                         msgPrefix, mm.sideB, mm.sideA)
                        print(msg)
                        issue_count += 1
                        break
                elif mm.endswith_enable:
                    if ((any_endswith(names, mm.sideA) and
                            not any_endswith(names, mm.sideB)) and
                            any_endswith(values, mm.sideB)):
                        nameI = rawl.find(mm.sideA) + 1
                        if not both_present:
                            both_present = any_endswith(values,
                                                        mm.sideA)
                            msgPrefix = onlyMisMatchCo
                        # if msg is None:
                        fmt = ("{} ({},{}){}name ends with {}, but"
                               " {} on right in check/assignment")
                        msg = fmt.format(path, line_n, nameI,
                                         msgPrefix, mm.sideA, mm.sideB)
                        print(msg)
                        issue_count += 1
                        break

                    elif ((any_endswith(names, mm.sideB) and
                            not any_endswith(names, mm.sideA)) and
                            any_endswith(values, mm.sideA)):
                        nameI = rawl.find(mm.sideB) + 1
                        if not both_present:
                            both_present = any_endswith(values,
                                                        mm.sideB)
                            msgPrefix = onlyMisMatchCo
                        if msg is None:
                            fmt = ("{} ({},{}){}name ends with {}, but"
                                   " {} on right in check/assignment")
                            msg = fmt.format(path, line_n,
                                             nameI, msgPrefix,
                                             mm.sideB, mm.sideA)
                        print(msg)
                        issue_count += 1
                        break

                else:
                    inAOnly = (in_any(mm.sideA, names) and
                               not in_any(mm.sideB, names))
                    if inAOnly and in_any(mm.sideB, values):
                        valI = (rawl.find(mm.sideA) + 1)
                        if not both_present:
                            both_present = in_any(mm.sideA, values)
                            msgPrefix = onlyMisMatchCo
                        # if msg is None:
                        fmt = ("{} ({},{}){}name contains"
                               " {}, but {} on right side"
                               " in check/assignment")
                        msg = fmt.format(path, line_n, valI,
                                         msgPrefix, mm.sideA, mm.sideB)
                        print(msg)
                        issue_count += 1
                        break
                    elif ((in_any(mm.sideB, names) and
                          not in_any(mm.sideA, names)) and
                            in_any(mm.sideA, values)):
                        valI = rawl.find(mm.sideB) + 1
                        if not both_present:
                            both_present = in_any(mm.sideB, values)
                            msgPrefix = onlyMisMatchCo
                        # if msg is None:
                        msg = (path + " (" + str(line_n)
                               + "," + str(valI) + ")"
                               + msgPrefix + "name contains "
                               + mm.sideB + ", but " + mm.sideA
                               + " on right side of check/assignment")
                        print(msg)
                        issue_count += 1
                        break
        if issue_count > prev_issue_count:
            print("strp " + str(line_n) + ": " + rawl.strip())
            echo1("  ao_index:" + str(ao_index))
            echo1("  names: " + ','.join(names))
            echo1("  values: " + ','.join(values))
            print("")
            problematic_line_count += 1
        line_n += 1

    ins.close()


independent_list.append("decachunk_x_path")
independent_list.append("chunk_assoc")
independent_list.append("chunk_luid")
independent_list.append("file_name")
independent_list.append("chunkymap_view_zoom_multiplier")
independent_list.append("\"0\"")
independent_list.append("temp")
independent_list.append("haystack")
independent_list.append("needle")
independent_list.append("strp")  # TODO: line_strip (former name) too ?
independent_list.append("self.chunks")
independent_list.append("self.mapvars")
independent_list.append(".metadata")
independent_list.append("\" \\\"\"")
independent_list.append("\" \"")
independent_list.append("player_position_tuple")

print("  (Ignoring the following independent variables:")
print(','.join(independent_list)+")")

# set_verbosity(1)
check_coord_mismatch("generator.py")
check_coord_mismatch(os.path.join("..", "web", "chunkymap.php"))
print("Found " + str(issue_count) + " issue(s) in "
      + str(len(file_list)) + " file(s)")
if issue_count > 0:
    print("Please run again after these issues are fixed to check for"
          " more on same lines.")
