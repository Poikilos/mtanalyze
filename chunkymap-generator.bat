TRY_PYTHON=C:\Python38\python.exe
IF EXIST "%TRY_PYTHON%" %TRY_PYTHON% generator.py
IF EXIST "%TRY_PYTHON%" GOTO END_SILENT
TRY_PYTHON=C:\Python37\python.exe
IF EXIST "%TRY_PYTHON%" %TRY_PYTHON% generator.py
IF EXIST "%TRY_PYTHON%" GOTO END_SILENT
TRY_PYTHON=C:\Python36\python.exe
IF EXIST "%TRY_PYTHON%" %TRY_PYTHON% generator.py
IF EXIST "%TRY_PYTHON%" GOTO END_SILENT
TRY_PYTHON=C:\Python35\python.exe
IF EXIST "%TRY_PYTHON%" %TRY_PYTHON% generator.py
IF EXIST "%TRY_PYTHON%" GOTO END_SILENT
TRY_PYTHON=C:\Python34\python.exe
IF EXIST "%TRY_PYTHON%" %TRY_PYTHON% generator.py
IF EXIST "%TRY_PYTHON%" GOTO END_SILENT

echo missing Python 3: please download Python 3.4 to theoretical 3.8 (or modify this script) then right-click python3 installer in your Downloads folder, Run as Administrator, install for all users, such that it appears in C:\Python34 to theoretical C:\Python38 (or modify this script)
pause

:END_SILENT
