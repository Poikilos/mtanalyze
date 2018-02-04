import os
from expertmm import *

python_exe_path = get_python_exe_path()

def get_python_exe_path():
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
