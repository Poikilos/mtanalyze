#!/usr/bin/env python
from __future__ import print_function

import os

myPath = os.path.realpath(__file__)
myPackage = os.path.split(myPath)[0]
myRepo = os.path.split(myPackage)[0]
repos = os.path.split(myRepo)[0]
me = 'pythoninfo.py'

try:
    try:
        from parsing import *
    except ImportError as ex:
        from pycodetool.parsing import *
except ImportError:
    print("This script requires parsing from poikilos/pycodetool")
    print("Try (in a Terminal):")
    print()
    print("cd \"{}\"".format(repos))
    print("git clone https://github.com/poikilos/pycodetool.git"
          " pycodetool")
    print()
    print()
    exit(1)


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
