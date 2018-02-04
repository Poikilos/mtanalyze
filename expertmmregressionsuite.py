#!/usr/bin/env python3

# script for testing other expertmm modules
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
#import types
import inspect
import traceback

module_list = list()
module_list.append("os")
module_list.append("sys")
module_list.append("keyword")
module_list.append("inspect")
module_list.append("traceback")

from expertmm import *

### THE FUNCTIONS ARE USED ON minetest-chunkymap AT THE BOTTOM OF THIS SCRIPT ###

#TODO: code checking such as:
# ANY LANGUAGE:
# * check for signs in len params (such as in Python where str(len(part1+part2)) should be str(len(part1))+part2
# * check for only variable name in quotes (maybe the programmer meant to use the value)
# * mixing width with y (or height or z) and mixing height with x (or width)
# PYTHON:
# * check for redefining member variable (missing "self.") [since python does not throw NameError on definition, only if used and not defined]
# * check for use of os.dirname (should be os.path.dirname)
# * check for methods missing 'self' as first argument name
# PHP:
# * using '+' next to doublequote or singlequote in php, adjacent or seperated only by whitespace (probably meant concatenate operator '.')
# * using empty function (problematic since empty($value) evaluates to true when $value is zero -- empty_really in expertmm can be used instead)
# SHELL SCRIPT:
# * don't use '*' inside quotes (fails)
# * using HOME without preceding dollar sign
# ECMAScript:
# * use of e.clientX e.clientY where line contains neither + or - (should use some kind of modifiers for scroll and canvas position such as in get_relative_mouse_point method)


def view_traceback():
    ex_type, ex, tb = sys.exc_info()
    print(str(ex_type))
    print(str(ex))
    traceback.print_tb(tb)
    del tb

class RegressionMismatch:
    side_a_string = None
    side_b_string = None
    endswith_enable = None
    startswith_enable = None

    def __init__(self, side_a_string, side_b_string, startswith_enable, endswith_enable):
        self.side_a_string = side_a_string
        self.side_b_string = side_b_string
        self.endswith_enable = endswith_enable
        self.startswith_enable = startswith_enable

global_case_sensitive_enable = None
y_enable = False
print("Initializing...")
regression_mismatches = list()
independent_list = ["index","suffix","prefix"]
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
#NOTE: "for decachunk_z_name in os.listdir(decachunk_x_path):" is ok since z folders are in x folder
independent_endswith_list = list()
for word in independent_list:
    independent_endswith_list.append("_"+word)
regression_mismatches.append(RegressionMismatch("_x","_z",False,True))

if y_enable:
    regression_mismatches.append(RegressionMismatch("_x","_y",False,True))
    regression_mismatches.append(RegressionMismatch("_y","_z",False,True))

regression_mismatches.append(RegressionMismatch("_x_","_z_",False,False))
if y_enable:
    regression_mismatches.append(RegressionMismatch("_x_","_y_",False,False))
    regression_mismatches.append(RegressionMismatch("_y_","_z_",False,False))

regression_mismatches.append(RegressionMismatch("x","z",False,True))
if y_enable:
    regression_mismatches.append(RegressionMismatch("x","y",False,True))
    regression_mismatches.append(RegressionMismatch("y","z",False,True))

regression_mismatches.append(RegressionMismatch("x_","z_",True,False))
if y_enable:
    regression_mismatches.append(RegressionMismatch("x_","y_",True,False))
    regression_mismatches.append(RegressionMismatch("y_","z_",True,False))

if global_case_sensitive_enable is True:
    regression_mismatches.append(RegressionMismatch("_X_","_Z_",False,False))
    if y_enable:
        regression_mismatches.append(RegressionMismatch("_X_","_Y_",False,False))
        regression_mismatches.append(RegressionMismatch("_Y_","_Z_",False,False))

    regression_mismatches.append(RegressionMismatch("_X","_Z",False,True))
    if y_enable:
        regression_mismatches.append(RegressionMismatch("_X","_Y",False,True))
        regression_mismatches.append(RegressionMismatch("_Y","_Z",False,True))

    regression_mismatches.append(RegressionMismatch("X","Z",False,True))
    if y_enable:
        regression_mismatches.append(RegressionMismatch("X","Y",False,True))
        regression_mismatches.append(RegressionMismatch("Y","Z",False,True))

    regression_mismatches.append(RegressionMismatch("X_","Z_",True,False))
    if y_enable:
        regression_mismatches.append(RegressionMismatch("X_","Y_",True,False))
        regression_mismatches.append(RegressionMismatch("Y_","Z_",True,False))
def is_dependend_variable(name):
    result = False
    for regression_mismatch in regression_mismatches:
        if regression_mismatch.startswith_enable:
            if startswith(name, regression_mismatch.side_a_string):
                result = True
                break
            if startswith(name, regression_mismatch.side_b_string):
                result = True
                break
        elif regression_mismatch.endswith_enable:
            if endswith(name, regression_mismatch.side_a_string):
                result = True
                break
            if endswith(name, regression_mismatch.side_b_string):
                result = True
                break
        else:
            if regression_mismatch.side_a_string in name:
                result = True
                break
            elif regression_mismatch.side_a_string in name:
                result = True
                break

    return result
#splits by any non-alphanumeric characters
#print(keyword.kwlist)
# DOESN'T WORK (from linuxbochs on http://stackoverflow.com/questions/6315496/display-a-list-of-user-defined-functions-in-the-python-idle-session ):
#function_list = [f for f in globals().values() if type(f) == types.FunctionType]
# DOESN'T WORK
#def dummy(): pass
#function_list = [f.__name__ for f in globals().values() if type(f) == type(dummy)]
function_list = list()
for module_string in module_list:
    exec ("function_list += inspect.getmembers("+module_string+", inspect.isroutine)")
  # NOTE: isfunction does NOT include c-defined functions such as those in math
function_names = list()
for function_tuple in function_list:
    function_names.append(function_tuple[0])
print("  (Ignoring known routines:")
print(','.join(function_names)+")")
print("")
print("")
def split_non_alnum(haystack, strip_enable=True, skip_keywords_enable=True):
    global independent_list
    global function_names
    global module_list
    results = list()
    index = 0
    start_index = 0
    while index <= len(haystack):
        if index==len(haystack) or not haystack[index].isalnum():
            word = haystack[start_index:index]
            if (not skip_keywords_enable) or (word not in keyword.kwlist and word not in function_names and word not in independent_list and word not in module_list):
                if strip_enable:
                    results.append(word.strip())
                else:
                    results.append(word)
            start_index = index+1
        index += 1
    return results

issue_count = 0
file_list = list()
#def is_identifier(needle, dot_continues_enable):
#    result = True
#
#    for index in range(0,len(needle)):
#        if needle[index] not in identifier_chars:
#            result = False
#            break
#    return result

quote_list = "'\""
def split_non_identifier(haystack, strip_enable=True, skip_keywords_enable=True, skip_independent_enable=True, dot_continues_enable=True):
    results = list()
    index = 0
    start_index = 0
    is_in_quote_char = None
    prev_char = None
    escaped_dq_enable = True
    while index <= len(haystack):
        if index<len(haystack) and (is_in_quote_char is None) and (haystack[index] in quote_list):
            is_in_quote_char = haystack[index]
        elif index<len(haystack) and (is_in_quote_char is not None) and (haystack[index]==is_in_quote_char and (prev_char!="\\" or is_in_quote_char!="\"")):
            is_in_quote_char = None
        elif index==len(haystack) or ((is_in_quote_char is None) and not is_identifier_valid(haystack[index], dot_continues_enable)):
            word = haystack[start_index:index]
            if (not skip_keywords_enable) or word not in keyword.kwlist:
                if (not skip_independent_enable) or (word not in independent_list and not endswith_any(word, independent_endswith_list)):
                    if strip_enable:
                        results.append(word.strip())
                    else:
                        results.append(word)
            start_index = index+1
        if index<len(haystack):
            prev_char = haystack[index]
        index += 1
    return results

def endswith(haystack, needle, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    if haystack is not None and needle is not None and len(needle)>0 and len(haystack)>=len(needle):
        if case_sensitive_enable:
            if haystack[-len(needle):] == needle:
                #print("haystack[-len(needle):] = "+haystack[-len(needle):]+" in "+haystack)
                result = True
        else:
            if haystack[-len(needle):].lower() == needle.lower():
                #print("haystack[-len(needle):].lower() = "+haystack[-len(needle):].lower()+" in "+haystack)
                result = True
    return result

def startswith(haystack, needle, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    if haystack is not None and needle is not None and len(needle)>0 and len(haystack)>=len(needle):
        if case_sensitive_enable:
            if haystack[:len(needle)] == needle:
                result = True
        else:
            if haystack[:len(needle)].lower() == needle.lower():
                result = True
    return result

def any_endswith(haystacks, needle, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    for haystack in haystacks:
        if endswith(haystack, needle, case_sensitive_enable):
            result = True
            break
    return result

def endswith_any(haystack, needles, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    for needle in needles:
        if endswith(haystack, needle, case_sensitive_enable):
            result = True
            break
    return result

def any_startswith(haystacks, needle, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    for haystack in haystacks:
        if startswith(haystack, needle, case_sensitive_enable):
            result = True
            break
    return result

def startswith_any(haystack, needles, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    for needle in needles:
        if startswith(haystack, needle, case_sensitive_enable):
            result = True
            break
    return result

def endswith_any(haystack, needles, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    for needle in needles:
        if endswith(haystack, needle, case_sensitive_enable):
            result = True
            break
    return result

#only works on strings IF case_sensitive_enable, since then would do lower() on each element of haystacks
def in_any_string(needle, haystacks, case_sensitive_enable=False):
    if global_case_sensitive_enable is not None:
        case_sensitive_enable = global_case_sensitive_enable
    result = False
    if needle is not None and len(needle)>0:
        for haystack in haystacks:
            if haystack is not None and len(haystack)>0:
                if case_sensitive_enable:
                    if needle in haystack:
                        result = True
                        break
                else:
                    if needle.lower() in haystack.lower():
                        result = True
                        break
    return result


min_indent = ""

def increase_indent():
    global min_indent
    min_indent+="  "

def decrease_indent():
    global min_indent
    if len(min_indent)>=2:
        min_indent = min_indent[:-2]

def check_coord_mismatch(file_path):
    global file_list
    global issue_count
    global module_list
    print("Running check_coord_mismatch on "+file_path+"...")
    global function_list
    if (file_path not in file_list):
        file_list.append(file_path)
    line_counting_number = 1
    ins = open(file_path, 'r')
    line = True
    global min_indent
    is_imported = False
    problematic_line_count = 0
    inline_comment_delimiter = "#"
    inline_line_break = None
    file_path_lower = file_path.lower()
    if len(file_path)>3 and (file_path_lower[-3:]==".cs"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(file_path)>2 and (file_path_lower[-2:]==".c"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(file_path)>2 and (file_path_lower[-2:]==".h"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(file_path)>4 and (file_path_lower[-4:]==".hpp"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(file_path)>4 and (file_path_lower[-4:]==".cpp"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(file_path)>4 and (file_path_lower[-4:]==".php"):
        inline_comment_delimiter = "//"
        inline_line_break = ";"
    elif len(file_path)>3 and (file_path_lower[-3:]==".py"):
        inline_comment_delimiter = "#"
    elif len(file_path)>4 and (file_path_lower[-4:]==".pyw"):
        inline_comment_delimiter = "#"
    else:
        answer=raw_input("what is the inline comment delimiter for the sourcecode file type of "+file_path+" [blank for "+inline_comment_delimiter+"]? ")
        if len(answer)>0:
            inline_comment_delimiter = answer

    dup_ignore_list = function_names+independent_list+module_list
    while line:
        line = ins.readline()
        prev_issue_count = issue_count
        if line:
            line_strip = line.strip()
            comment_index = find_unquoted_MAY_BE_COMMENTED(line_strip, inline_comment_delimiter)
            if comment_index>-1:
                line_strip = line_strip[:comment_index]
            sublines = list()


            if inline_line_break is not None:
                remaining_string = line_strip
                while True:
                    inline_line_break_index = find_unquoted_MAY_BE_COMMENTED(remaining_string, inline_line_break)  # do NOT check for INLINE COMMENT since already removed it using detected delimiter above
                    if inline_line_break_index<0:
                        break
                    sublines.append(remaining_string[:inline_line_break_index])
                    remaining_string = remaining_string[inline_line_break_index+1:]

                if len(remaining_string)>0:
                    sublines.append(remaining_string)
            else:
                sublines.append(line_strip)
            for subline in sublines:
                line_strip = subline
                if (len(line_strip)>0) and (line_strip[0]!="#"):
                    ao_index = line_strip.find("=")
                    import_string = "import "
                    from_string = "from "
                    import_index = -1
                    if line_strip[:len(import_string)]==import_string:
                        import_index = 0
                    elif line_strip[:len(from_string)]==from_string:
                        import_string = from_string
                        import_index = line_strip.find(import_string)
                    if import_index>=0:
                        module_string = line_strip[import_index+len(import_string):].strip()
                        space_index = module_string.find(" ")
                        if space_index>-1:
                            module_string = module_string[:space_index]
                        if module_string not in module_list:
                            module_list.append(module_string)
                            try:
                                #tmp_tuples = list()
                                import_string = "import "+module_string
                                #exec exec_string
                                try_enable = False
                                outs = open('expertmmregressiontmp.py','w')
                                outs.write("def get_module_contents():"+"\n")
                                outs_indent = "    "
                                outs.write(outs_indent+"results = None"+"\n")
                                if try_enable:
                                    outs.write(outs_indent+"try:"+"\n")
                                    outs_indent = "        "
                                outs.write(outs_indent+"import inspect"+"\n")
                                outs.write(outs_indent+import_string+"\n")
                                exec_string = "tmp_tuples = inspect.getmembers("+module_string+", inspect.isroutine)"
                                outs.write(outs_indent+exec_string+"\n")
                                outs.write(outs_indent+"results = list()"+"\n")
                                outs.write(outs_indent+"for function_tuple in tmp_tuples:"+"\n")
                                outs.write(outs_indent+"    results.append(function_tuple[0])"+"\n")

                                outs_indent = "    "
                                if try_enable:
                                    outs.write(outs_indent+"except:"+"\n")
                                    outs_indent = "        "
                                    outs.write(outs_indent+"print(\"Could not finish get_module_contents\")"+"\n")
                                outs_indent = "    "
                                outs.write(outs_indent+"return results"+"\n")
                                outs.write("\n")
                                outs.close()
                                if is_imported:
                                    reload(expertmmregressiontmp)
                                else:
                                    import expertmmregressiontmp
                                tmp_list = expertmmregressiontmp.get_module_contents()
                                os.remove("expertmmregressiontmp.py")
                                new_list = None
                                if tmp_list is not None:
                                    new_list = list()
                                    for routine_string in tmp_list:
                                        if routine_string not in function_list:
                                            new_list.append(routine_string)
                                if new_list is not None:
                                    function_list += new_list
                                    print("Found "+str(len(new_list))+" new method(s) from '"+module_string+"' to ignore: "+','.join(new_list))
                                    if len(new_list)>0:
                                        dup_ignore_list = function_names+independent_list+module_list
                                else:
                                    print("unable to import module named '"+module_string+"', so some routines may not be successfully ignored:")
                                del expertmmregressiontmp
                            except:
                                print("Could not finish importing module named '"+module_string+"', so some routines may not be successfully ignored:")
                                view_traceback()
                    if ao_index<0:
                        ao_index = line_strip.find(">")
                    if ao_index<0:
                        ao_index = line_strip.find("<")
                    if ao_index<0:
                        ao_index = line_strip.find(" in ")




                    if ao_index>0:  # intentionally >0 instead of =
                        increase_indent()
                        names_string = line_strip[:ao_index].strip()
                        values_string = line_strip[ao_index+1:].strip()
                        name_list = split_non_identifier(names_string)
                        value_list = split_non_identifier(values_string)
                        message = None

                        message_prefix = " WARNING: "
                        this_start_index = 0
                        names_string = line_strip[:ao_index].strip()
                        values_string = line_strip[ao_index+1:].strip()
                        name_list = split_non_identifier(names_string)
                        value_list = split_non_identifier(values_string)

                        #while True:
                            #this_chunk_len = get_operation_chunk_len(line_strip,this_start_index,1,line_counting_number)
                            #if this_chunk_len<1:
                                #break
                            #partial_string = line_strip[this_start_index:this_start_index+this_chunk_len]
                            #this_start_index += this_chunk_len

                        duplicate_index = find_dup(name_list,ignore_numbers_enable=True)
                        if duplicate_index>-1:
                            if name_list[duplicate_index] not in dup_ignore_list:
                                if is_dependend_variable(name_list[duplicate_index]):
                                    name_index = line.find(name_list[duplicate_index])
                                    message_prefix = " WARNING: "
                                    issue_count += 1
                                    message = (file_path+" ("+str(line_counting_number)+","+str(name_index)+")"+message_prefix+"name '"+name_list[duplicate_index]+"' is used twice (perhaps other coord should have been used)")
                                    print(message)
                                    break
                        duplicate_index = find_dup(value_list)
                        if duplicate_index>-1:
                            if value_list[duplicate_index] not in dup_ignore_list:
                                if is_dependend_variable(value_list[duplicate_index]):
                                    name_index = line.find(value_list[duplicate_index])
                                    message_prefix = " WARNING: "
                                    issue_count += 1
                                    message = (file_path+" ("+str(line_counting_number)+","+str(name_index)+")"+message_prefix+"value '"+value_list[duplicate_index]+"' is used twice (perhaps other coord should have been used)")
                                    print(message)
                                    break

                        message = None

                        for regression_mismatch in regression_mismatches:
                            both_present = False
                            only_mismatched_coord_is_present_string = " ERROR (only has mismatch): "

                            message_prefix = " WARNING: "
                            if regression_mismatch.startswith_enable:
                                if (any_startswith(name_list,regression_mismatch.side_a_string) and not any_startswith(name_list,regression_mismatch.side_b_string)) and any_startswith(value_list,regression_mismatch.side_b_string):
                                    name_index = line.find(regression_mismatch.side_a_string) + 1
                                    if not both_present:
                                        both_present = any_startswith(value_list,regression_mismatch.side_a_string)
                                        message_prefix = only_mismatched_coord_is_present_string
                                    #if message is None:
                                    message = (file_path+" ("+str(line_counting_number)+","+str(name_index)+")"+message_prefix+"name starts with "+regression_mismatch.side_a_string+", but "+regression_mismatch.side_b_string+" on right in check/assignment")
                                    print(message)
                                    issue_count += 1
                                    break

                                elif (any_startswith(name_list,regression_mismatch.side_b_string) and not any_startswith(name_list,regression_mismatch.side_a_string)) and any_startswith(value_list,regression_mismatch.side_a_string):
                                    name_index = line.find(regression_mismatch.side_b_string) + 1
                                    if not both_present:
                                        both_present = any_startswith(value_list,regression_mismatch.side_b_string)
                                        message_prefix = only_mismatched_coord_is_present_string
                                    #if message is None:
                                    message = (file_path+" ("+str(line_counting_number)+","+str(name_index)+")"+message_prefix+"name starts with "+regression_mismatch.side_b_string+", but "+regression_mismatch.side_a_string+" on right in check/assignment")
                                    print(message)
                                    issue_count += 1
                                    break
                            elif regression_mismatch.endswith_enable:
                                if (any_endswith(name_list,regression_mismatch.side_a_string) and not any_endswith(name_list,regression_mismatch.side_b_string)) and any_endswith(value_list,regression_mismatch.side_b_string):
                                    name_index = line.find(regression_mismatch.side_a_string) + 1
                                    if not both_present:
                                        both_present = any_endswith(value_list,regression_mismatch.side_a_string)
                                        message_prefix = only_mismatched_coord_is_present_string
                                    #if message is None:
                                    message = (file_path+" ("+str(line_counting_number)+","+str(name_index)+")"+message_prefix+"name ends with "+regression_mismatch.side_a_string+", but "+regression_mismatch.side_b_string+" on right in check/assignment")
                                    print(message)
                                    issue_count += 1
                                    break

                                elif (any_endswith(name_list,regression_mismatch.side_b_string) and not any_endswith(name_list,regression_mismatch.side_a_string)) and any_endswith(value_list,regression_mismatch.side_a_string):
                                    name_index = line.find(regression_mismatch.side_b_string) + 1
                                    if not both_present:
                                        both_present = any_endswith(value_list,regression_mismatch.side_b_string)
                                        message_prefix = only_mismatched_coord_is_present_string
                                    if message is None:
                                        message = (file_path+" ("+str(line_counting_number)+","+str(name_index)+")"+message_prefix+"name ends with "+regression_mismatch.side_b_string+", but "+regression_mismatch.side_a_string+" on right in check/assignment")
                                    print(message)
                                    issue_count += 1
                                    break

                            else:
                                if (in_any_string(regression_mismatch.side_a_string, name_list) and not in_any_string(regression_mismatch.side_b_string, name_list)) and in_any_string(regression_mismatch.side_b_string, value_list):
                                    value_index = line.find(regression_mismatch.side_a_string) + 1
                                    if not both_present:
                                        both_present = in_any_string(regression_mismatch.side_a_string, value_list)
                                        message_prefix = only_mismatched_coord_is_present_string
                                    #if message is None:
                                    message = (file_path+" ("+str(line_counting_number)+","+str(value_index)+")"+message_prefix+"name contains "+regression_mismatch.side_a_string+", but "+regression_mismatch.side_b_string+" on right in check/assignment")
                                    print(message)
                                    issue_count += 1
                                    break
                                elif (in_any_string(regression_mismatch.side_b_string, name_list) and not in_any_string(regression_mismatch.side_a_string, name_list)) and in_any_string(regression_mismatch.side_a_string, value_list):
                                    value_index = line.find(regression_mismatch.side_b_string) + 1
                                    if not both_present:
                                        both_present = in_any_string(regression_mismatch.side_b_string, value_list)
                                        message_prefix = only_mismatched_coord_is_present_string
                                    #if message is None:
                                    message = (file_path+" ("+str(line_counting_number)+","+str(value_index)+")"+message_prefix+"name contains "+regression_mismatch.side_b_string+", but "+regression_mismatch.side_a_string+" on right side of check/assignment")
                                    print(message)
                                    issue_count += 1
                                    break
        if issue_count>prev_issue_count:
            print("line "+str(line_counting_number)+": "+line.strip())
            if verbose_enable:
                print("  ao_index:"+str(ao_index))
                print("  names: "+','.join(name_list))
                print("  values: "+','.join(value_list))
            print("")
            problematic_line_count += 1
        line_counting_number += 1
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
independent_list.append("line_strip")
independent_list.append("self.chunks")
independent_list.append("self.mapvars")
independent_list.append(".metadata")
independent_list.append("\" \\\"\"")
independent_list.append("\" \"")
independent_list.append("player_position_tuple")

print("  (Ignoring the following independent variables:")
print(','.join(independent_list)+")")

#verbose_enable = True
check_coord_mismatch("generator.py")
check_coord_mismatch(os.path.join("web","chunkymap.php"))
print("Found "+str(issue_count)+" issue(s) in "+str(len(file_list))+" file(s)")
if (issue_count>0):
    print("Please run again after these issues are fixed to check for more on same lines.")
raw_input("Press enter to exit...")
