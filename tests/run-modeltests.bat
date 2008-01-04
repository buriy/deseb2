@echo off
set PYTHONPATH=../src;%PYTHONPATH%
REM Comment out backends you don't want to run
REM call modeltests.bat settings_sqlite3
call modeltests.bat settings_mysql
REM call modeltests.bat settings_postgresql
call modeltests.bat settings_postgresql_psycopg2
