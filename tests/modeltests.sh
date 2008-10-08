#Comment out backends you don't want to run
cp settings_sqlite3.py settings.py; echo "sqlite3:"; python realtest.py $1
cp settings_mysql.py settings.py; echo "MySQL:"; python realtest.py $1
#cp settings_postgresql.py settings.py; echo "PostgreSQL:"; python realtest.py $1
cp settings_postgresql_psycopg2.py settings.py; echo "PostgreSQL+psycopg2:"; python realtest.py $1
