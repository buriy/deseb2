@echo off
REM First argument is test application name
set PYTHONPATH=../src;%PYTHONPATH%
if "%1"=="" echo No test name given
if "%1"=="" goto END
IF NOT EXIST settings.py echo Oops... file settings.py does not exist! Please copy your settings there!
IF NOT EXIST settings.py goto END
echo Test %1
cd %1/ && del models.py > nul && copy models.py.pre models.py > nul && cd ..
manage.py reset %1 --noinput
cd %1/ && del models.py > nul && copy models.py.post models.py > nul && cd ..
echo Planned changes:
manage.py sqlevolve %1 --dont-notify
manage.py evolvedb %1 --noinput --dont-save --dont-notify
echo Pending changes, if present (written to stderr):
REM Write all sqlevolve output to stderr
manage.py sqlevolve %1 --dont-notify 1>&2
:END
