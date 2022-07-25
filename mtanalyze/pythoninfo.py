#!/usr/bin/env python
from __future__ import print_function

import os
import sys
me = 'pythoninfo.py'

MY_PATH = os.path.realpath(__file__)
MY_MODULE_PATH = os.path.split(MY_PATH)[0]
MY_REPO_PATH = os.path.split(MY_MODULE_PATH)[0]
REPOS_PATH = os.path.split(MY_REPO_PATH)[0]

def get_python3_exe_path():
    result = "python3"
    alt_path = "C:\\Python38\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python37\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python36\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python35\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python34\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
        # else may be in path--assume installer worked
    return result


def get_python2_exe_path():
    result = "python2"
    alt_path = "C:\\Python28\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python27\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python26\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python25\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    alt_path = "C:\\Python24\\python.exe"
    if os.path.isfile(alt_path):
        return alt_path
    # else may be in path--assume installer worked
    return result


def get_python_exe_path():
    return get_python3_exe_path()


python_exe_path = get_python_exe_path()
