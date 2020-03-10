import os
from expertmm import *

python_exe_path = "python"

#if os_name=="windows":
try:
    alt_path = "C:\\python27\python.exe"
    if os.path.isfile(alt_path):
        python_exe_path = alt_path
    #else may be in path--assume installer worked
except:
    pass  # do nothing
