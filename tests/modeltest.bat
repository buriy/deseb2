@echo off
REM First argument is test application name
set PYTHONPATH=../src;%PYTHONPATH%
if "%1"=="" echo No test name given
if "%1"=="" goto END
IF NOT EXIST settings.py echo Oops... file settings.py does not exist! Please copy your settings there!
IF NOT EXIST settings.py goto END
echo Test %1
REM reset on post state and pre state
cd %1/ && del models.py 1>nul 2>nul && copy models.py.pre models.py > nul && cd ..
manage.py reset %1 --noinput
manage.py evolvedb %1 --noinput --dont-save --dont-notify
cd %1/ && del models.py 1>nul 2>nul && copy models.py.post models.py > nul && cd ..
echo Planned changes:
manage.py sqlevolve %1 --dont-notify
manage.py evolvedb %1 --noinput --dont-save --dont-notify
echo Pending changes (written to stderr, should be empty):
REM Write all sqlevolve output to stderr
manage.py sqlevolve %1 --dont-notify 1>&2
:END
