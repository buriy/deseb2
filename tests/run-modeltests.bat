@echo off
set PYTHONPATH=../src;%PYTHONPATH%
REM Comment out backends you don't want to run
REM call modeltests.bat settings_sqlite3 %1
REM call modeltests.bat settings_mysql %1
REM call modeltests.bat settings_postgresql %1
call modeltests.bat settings_postgresql_psycopg2 %1
