@echo off
REM First argument is settings file for your backend without .py extension
REM set PYTHONPATH=../src;%PYTHONPATH%
if "%1"=="" echo No settings file name given
if "%1"=="" goto END
IF NOT EXIST %1.py echo Oops... settings file %1.py is not found
IF NOT EXIST %1.py goto END
REM IF EXIST settings.py echo Warning: settings.py will be removed!
copy %1.py settings.py > nul
call realtest.py %2
REM del settings.py > nul
:END
