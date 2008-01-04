@echo off
set PYTHONPATH=../src;%PYTHONPATH%
REM Comment out backends you don't want to run
call modeltests.bat settings_sqlite3
REM call modeltests.bat settings_mysql
REM call modeltests.bat settings_postgresql
REM call modeltests.bat settings_postgresql_psycopg2
