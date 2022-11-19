from __future__ import print_function
import platform
import urllib2
import sys
import subprocess
import os
import traceback
# import os.path

from urllib import FancyURLopener
# TODO: make urllib imports compatible with Python 2 and 3

try:
    input = raw_input
except NameError:
    pass  # Python 3


def view_traceback():
    ex_type, ex, tb = sys.exc_info()
    traceback.print_tb(tb)
    del tb


mta_repo = "https://github.com/poikilos/mtanalyze/archive/master.zip"

# as per Pedro Lobito on <http://stackoverflow.com/questions/802134/
#   changing-user-agent-on-urllib2-urlopen>:


class MyOpener(FancyURLopener, object):
    version = ('Mozilla/5.0 (Windows; U; Windows NT 5.1; it;'
               ' rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11')


def web_get(url, file_name):
    myopener = MyOpener()
    print("Downloading "+url+"...")
    myopener.retrieve(url, file_name)


# as per <http://stackoverflow.com/questions/22676/
#   how-do-i-download-a-file-over-http-using-python>
# but FAILS (404 Error) since user agent is not recognized, and setting
# user agent string does not fix it. use web_get above instead.
def web_get_DEPRECATED(url, file_name):
    print("This function probably will not work since settings user"
          " agent doesn't work with urllib2 request object (user agent"
          " is not recognized, and 404 error is usually the result)."
          " Try web_get instead.")
    file_name = None
    # url = "http://download.thinkbroadband.com/10MB.zip"

    # file_name = url.split('/')[-1]

    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        fmt = r"%10d  [%3.2f%%]"
        status = fmt % (file_size_dl,
                        file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()
    # TODO: Test to find specific exceptions and handle them.
    return file_name


python_folder_path = os.path.dirname(sys.executable)

print("")
print("This script will install numpy and PIL wheels into "
      + python_folder_path
      + " on Windows. If this doesn't sound like something you should"
      " do, please press Ctrl C and terminate this script.")

os_bits = "64"
print(platform.architecture()[0])
is_detected = False
if "32" in platform.architecture()[0]:
    os_bits = "32"
    is_detected = True
elif "64" in platform.architecture()[0]:
    os_bits = "64"
    is_detected = True
detected_msg = " (shown above)"
if is_detected:
    detected_msg = " (detected above)"

print("")
answer = input("Enter #of bits in your PYTHON architecture (may be"
               " different from #of bits of Windows) [blank for "
               + os_bits+detected_msg + "]: ")
print("Attempting to update pip...")
# ^ since display is blank for a while otherwise
if answer is not None:
    answer = answer.strip()
    if len(answer) > 0:
        os_bits = answer
pip_update_cmd_string = (sys.executable
                         + " -m pip install"
                         " --upgrade pip wheel setuptools")
subprocess.call(pip_update_cmd_string)

dl_numpy_name = None
downloaded_pillow_name = None
remote_numpy_path = None

if os_bits == "32":
    dl_numpy_name = "numpy-1.10.4+mkl-cp27-cp27m-win32.whl"
    downloaded_pillow_name = "Pillow-3.1.1-cp27-none-win32.whl"
elif os_bits == "64":
    dl_numpy_name = "numpy-1.10.4+mkl-cp27-cp27m-win_amd64.whl"
    downloaded_pillow_name = "Pillow-3.1.1-cp27-none-win_amd64.whl"

pythonlibs_url = "http://www.lfd.uci.edu/~gohlke/pythonlibs/djcobkfp"
remote_numpy_path = pythonlibs_url + "/" + dl_numpy_name
remote_pillow_path = pythonlibs_url + "/" + downloaded_pillow_name

profile_path = None
if os.path.sep == "\\":
    profile_path = os.environ.get("USERPROFILE")
# elif os.path.sep=="/":
#     profile_path=os.environ.get("HOME")
if profile_path is not None and os.path.isdir(profile_path):
    downloads_path = os.path.join(profile_path, "Downloads")
else:
    downloads_path = "."

dl_pillow_path = os.path.join(downloads_path,
                              downloaded_pillow_name)
downloaded_numpy_path = os.path.join(downloads_path,
                                     dl_numpy_name)

download_test_enable = True

if download_test_enable:
    if not os.path.isfile(downloaded_numpy_path):
        web_get(remote_numpy_path, downloaded_numpy_path)
        if os.path.isfile(downloaded_numpy_path):
            print("Successfully downloaded '" + downloaded_numpy_path
                  + "'")
    else:
        print(dl_pillow_path+" is present")
    if not os.path.isfile(dl_pillow_path):
        web_get(remote_pillow_path, dl_pillow_path)
        if os.path.isfile(dl_pillow_path):
            print("Successfully downloaded '" + dl_pillow_path
                  + "'")
    else:
        print(dl_pillow_path + " is present")


python_folder_name = os.path.basename(python_folder_path)
if python_folder_name.lower()[:7] != "python3":
    is_python_version_confirmed = False
    if python_folder_name.lower()[:7] == "python2":
        is_python_version_confirmed = True
    if not is_python_version_confirmed:
        confirm_string = "n"
        answer = input("You are running this script from '"
                       + python_folder_path + "' which does not appear"
                       " to be a python folder. Are you sure you REALLY"
                       " sure you want to install Python 2 wheels and"
                       " chunkymap there y/[n]? ")
        if answer is not None:
            answer = answer.strip()
        else:
            answer = ""
        if answer.lower() == "y" or answer.lower() == "yes":
            is_python_version_confirmed = True
        else:
            print("Installation of chunkymap was cancelled by the"
                  " user.")
    if is_python_version_confirmed:
        python_Lib_path = os.path.join(python_folder_path, "Lib")
        python_Lib_site_packages_path = os.path.join(python_Lib_path,
                                                     "site-packages")
        if os.path.isdir(python_Lib_site_packages_path):

            ins_numpy_path = os.path.join(
                python_Lib_site_packages_path,
                "numpy"
            )
            if not os.path.isdir(ins_numpy_path):
                # downloaded_numpy_path = os.path.join(
                #     downloads_path,
                #     dl_numpy_name
                # )
                install_numpy_cmd_string = (sys.executable
                                            + " -m pip install \""
                                            + downloaded_numpy_path
                                            + "\"")
                if not os.path.isfile(downloaded_numpy_path):
                    print("Trying to download " + remote_numpy_path
                          + "...")
                    web_get(remote_numpy_path, downloaded_numpy_path)
                else:
                    print("Detected previously-downloaded '"
                          + downloaded_numpy_path + "'")

                if os.path.isfile(downloaded_numpy_path):
                    subprocess.call(install_numpy_cmd_string)

            if os.path.isdir(ins_numpy_path):
                print("Numpy was detected at '" + ins_numpy_path
                      + "'. Checking for PIL...")
                ins_pillow_path = os.path.join(
                    python_Lib_site_packages_path,
                    "PIL"
                )
                if not os.path.isdir(ins_pillow_path):
                    # dl_pillow_path = os.path.join(
                    #     downloads_path,
                    #     downloaded_pillow_name
                    # )
                    install_pillow_cmd_string = (sys.executable
                                                 + " -m pip install \""
                                                 + dl_pillow_path
                                                 + "\"")
                    if not os.path.isfile(dl_pillow_path):
                        print("")
                        print("Trying to download "
                              + remote_pillow_path
                              + "...")
                        web_get(remote_pillow_path, dl_pillow_path)
                    else:
                        print("Detected previously-downloaded '"
                              + dl_pillow_path + "'")
                    if os.path.isfile(dl_pillow_path):
                        subprocess.call(install_pillow_cmd_string)
                if os.path.isdir(ins_pillow_path):
                    print("Pillow was detected at '" + ins_pillow_path
                          + "'")
                    dl_mta_name = "chunkymap.zip"
                    dl_mta_path = os.path.join(
                        downloads_path,
                        dl_mta_name
                    )
                    run_py_path = "generator.py"

                    if not os.path.isfile(run_py_path):
                        if not os.path.isfile(dl_mta_path):
                            web_get(mta_repo, dl_mta_path)
                            if os.path.isfile(dl_mta_path):
                                print("Successfully downloaded "
                                      + dl_mta_name)
                            else:
                                print("Failed to download or detect "
                                      + run_py_path
                                      + " -- please download "
                                      + mta_repo)
                        print("(You must right-click on " + dl_mta_path
                              + " then click Extract All, then you can"
                              " run this file from that folder to"
                              " re-detect a compatible python and write"
                              " that python to " + run_bat_path)
                    else:
                        print("Now you can run " + run_py_path
                              + " using: ")
                        print("  " + sys.executable + " " + run_py_path)
                        run_bat_path = "chunkymap-generator.bat"
                        if os.path.isfile(run_bat_path):
                            os.remove(run_bat_path)
                        outs = open(run_bat_path, 'w')
                        outs.write(sys.executable + " " + run_py_path
                                   + "\n")
                        outs.close()
                        print("  OR by double-clicking")
                        print("  " + run_bat_path)
                    input("Press enter to exit.")
                else:
                    input("Cannot detect nor install " + ins_pillow_path
                          + " so installation cannot continue. Try"
                          " downloading " + downloaded_pillow_name
                          + " to '" + downloads_path
                          + "' then run this script again."
                          " Press enter to exit.")
            else:
                input("Cannot detect nor install "
                      + ins_numpy_path + " so installation cannot"
                      " continue. Try downloading " + dl_numpy_name
                      + " to '" + downloads_path + "' then run this"
                      " script again. Press enter to exit.")
        else:
            input("Cannot detect a site-packages folder in python"
                  " installation of current python executable "
                  + sys.executable + " so installation cannot continue."
                  " Press enter to exit.")
else:
    input("This installer does not know the correct wheels for python 3"
          " (detected at " + python_folder_path + "). Please run this"
          " script with python 2 instead. Please see README.md for"
          " manual installation, but download and install Python 3"
          " wheels instead of the example wheels listed in README.md."
          " Press enter to exit.")
