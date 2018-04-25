import os
from poikilos import *


def get_python3_exe_path():
    result = "python3"
    try:
        alt_path = "C:\\Python38\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python37\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python36\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python35\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python34\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        #else may be in path--assume installer worked
    except:
        pass  # do nothing
    return result

def get_python2_exe_path():
    result = "python2"
    try:
        alt_path = "C:\\Python28\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python27\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python26\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python25\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        alt_path = "C:\\Python24\python.exe"
        if os.path.isfile(alt_path):
            return alt_path
        #else may be in path--assume installer worked
    except:
        pass  # do nothing
    return result


def get_python_exe_path():
    return get_python3_exe_path()

python_exe_path = get_python_exe_path()
