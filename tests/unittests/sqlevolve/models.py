"""
Schema Evolution Tests
"""

from django.db import models, connection
from django.conf import settings
import deseb

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
)

class Person(models.Model):
    name = models.CharField(maxlength=20, default="")
    gender = models.CharField(maxlength=1, choices=GENDER_CHOICES, default=False)
    gender2 = models.CharField(maxlength=1, choices=GENDER_CHOICES, aka='gender_old')
    ssn = models.IntegerField(default=111111111)

    def __unicode__(self):
        return self.name
    
    class Meta:
        aka = ('PersonOld', 'OtherBadName')

class Muebles(models.Model):
    tipo = models.CharField(maxlength=40, default="woot")
    # new fields
    fecha_publicacion = models.DateTimeField('date published', null=True)

class C(models.Model):
    "all with akas"
    c001 = models.AutoField(primary_key=True, aka='xxx')
    c002 = models.BooleanField(aka='xxx')
    c003 = models.CharField(maxlength='256', aka='xxx')
    c004 = models.CommaSeparatedIntegerField(maxlength='256', aka='xxx')
    c005 = models.DateField(aka='xxx')
    c006 = models.DateTimeField(aka='xxx')
    if deseb.version == 'trunk':
        c007 = models.DecimalField(decimal_places=5, max_digits=10, aka='xxx') # not in v0.96
    c008 = models.EmailField(aka='xxx')
    c010 = models.FileField(upload_to='/tmp', aka='xxx')
    c011 = models.FilePathField(aka='xxx')
    if deseb.version == '0.96':
        c012 = models.FloatField(aka='xxx', decimal_places=5, max_digits=10) # for v0.96
    else:
        c012 = models.FloatField(aka='xxx')
    c013 = models.IPAddressField(aka='xxx')
    c014 = models.ImageField(upload_to='/tmp', aka='xxx')
    c015 = models.IntegerField(aka='xxx')
    c016 = models.NullBooleanField(aka='xxx')
#   c017 = models.OrderingField(maxlength='256')
    c018 = models.PhoneNumberField(aka='xxx')
    c019 = models.PositiveIntegerField(aka='xxx')
    c020 = models.PositiveSmallIntegerField(aka='xxx')
    c021 = models.SlugField(aka='xxx')
    c022 = models.SmallIntegerField(aka='xxx')
    c023 = models.TextField(aka='xxx')
    c024 = models.TimeField(aka='xxx')
    c025 = models.URLField(aka='xxx')
    c026 = models.USStateField(aka='xxx')
    c027 = models.XMLField(aka='xxx')

from django.core.management.color import color_style
import deseb.schema_evolution

style = color_style()
ops, introspection = deseb.schema_evolution.get_operations_and_introspection_classes(style)
import pprint

def print_schema_evolution(app):
    sql = deseb.schema_evolution.get_sql_evolution(app, style, notify=False)
    return pprint.pprint(sql)

def silent_execute(cursor, command): 
    cursor.execute(command)
    
def print_and_execute(cursor, sql, execute=True): 
    #print pprint.pformat(sql).replace('\\\\n', '\\n')
    raise Exception(pprint.pformat(sql).replace('\\\\n', '\\n'))
    if not execute: return #this option is useful for debugging
    for command in sql: 
        if command[:2] == '--': continue
        cursor.execute(command)
        
def print_and_evolve(cursor, app, execute=True):
    try:
        sql = deseb.schema_evolution.get_sql_evolution(app, style, notify=False)
        print_and_execute(cursor, sql, execute=execute)
    except:
        import traceback
        traceback.print_exc()
        raise

if settings.DATABASE_ENGINE == 'mysql':
    def test_mysql():
        """
    >>> app = models.get_apps()[8]
    >>> auth_app = models.get_apps()[1]
    >>> app.__name__
    'unittests.sqlevolve.models'
    >>> auth_app.__name__
    'django.contrib.auth.models'
    
    >>> cursor = connection.cursor()

    # the table as it is supposed to be
    >>> create_table_sql = deseb.schema_evolution.get_sql_all(auth_app, color_style())
    
    # make sure we don't evolve an unedited table
    >>> print_and_evolve(cursor, auth_app) #m1
    []
    
    # the table as it is supposed to be
    >>> create_table_sql = deseb.schema_evolution.get_sql_all(app, color_style())
    
    # make sure we don't evolve an unedited table
    >>> print_and_evolve(cursor, app) #m2
    []
    
    # delete a column, so it looks like we've recently added a field
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_person', 'gender' ))
    ['ALTER TABLE `sqlevolve_person` DROP COLUMN `gender`;']
    >>> print_and_evolve(cursor, app) #m3
    ['ALTER TABLE `sqlevolve_person` ADD COLUMN `gender` varchar(1);',
 "UPDATE `sqlevolve_person` SET `gender` = 't' WHERE `gender` IS NULL;",
 'ALTER TABLE `sqlevolve_person` MODIFY COLUMN `gender` varchar(1) NOT NULL;']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])

    # add a column, so it looks like we've recently deleted a field
    >>> silent_execute(cursor, 'ALTER TABLE `sqlevolve_person` ADD COLUMN `gender_nothere` varchar(1) NOT NULL;')
    >>> print_and_evolve(cursor, app) #m4
    ['-- warning: the following may cause data loss',
 u'ALTER TABLE `sqlevolve_person` DROP COLUMN `gender_nothere`;',
 '-- end warning']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])

    # rename column, so it looks like we've recently renamed a field
    >>> silent_execute(cursor, 'ALTER TABLE `sqlevolve_person` CHANGE COLUMN `gender2` `gender_old` varchar(1) NOT NULL;')
    >>> print_and_evolve(cursor, app) #m5
    ['ALTER TABLE `sqlevolve_person` CHANGE COLUMN `gender_old` `gender2` varchar(1) NOT NULL;']
    
    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])
    
    # rename table, so it looks like we've recently renamed a model
    >>> silent_execute(cursor, 'ALTER TABLE `sqlevolve_person` RENAME TO `sqlevolve_personold`')
    >>> print_and_evolve(cursor, app) #m6
    ['ALTER TABLE `sqlevolve_personold` RENAME TO `sqlevolve_person`;']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])
    
    # change column flags, so it looks like we've recently changed a column flag
    >>> silent_execute(cursor, 'ALTER TABLE `sqlevolve_person` MODIFY COLUMN `name` varchar(10) NULL;')
    >>> print_and_evolve(cursor, app) #m7
    [u"UPDATE `sqlevolve_person` SET `name` = '' WHERE `name` IS NULL;",
 'ALTER TABLE `sqlevolve_person` MODIFY COLUMN `name` varchar(20) NOT NULL;']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])

    # delete a datetime column, so it looks like we've recently added a datetime field
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_muebles', 'fecha_publicacion' ))
    ['ALTER TABLE `sqlevolve_muebles` DROP COLUMN `fecha_publicacion`;']
    >>> print_and_evolve(cursor, app) #m8
    ['ALTER TABLE `sqlevolve_muebles` ADD COLUMN `fecha_publicacion` datetime;']
    
    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_muebles;'); silent_execute(cursor, create_table_sql[1])
    
    # delete a column with a default value, so it looks like we've recently added a column
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_muebles', 'tipo' ))
    ['ALTER TABLE `sqlevolve_muebles` DROP COLUMN `tipo`;']
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_person', 'ssn' ))
    ['ALTER TABLE `sqlevolve_person` DROP COLUMN `ssn`;']
    >>> print_and_evolve(cursor, app) #m9
    ['ALTER TABLE `sqlevolve_person` ADD COLUMN `ssn` integer;',
 'UPDATE `sqlevolve_person` SET `ssn` = 111111111 WHERE `ssn` IS NULL;',
 'ALTER TABLE `sqlevolve_person` MODIFY COLUMN `ssn` integer NOT NULL;',
 'ALTER TABLE `sqlevolve_muebles` ADD COLUMN `tipo` varchar(40);',
 u"UPDATE `sqlevolve_muebles` SET `tipo` = 'woot' WHERE `tipo` IS NULL;",
 'ALTER TABLE `sqlevolve_muebles` MODIFY COLUMN `tipo` varchar(40) NOT NULL;']
        """

if settings.DATABASE_ENGINE == 'postgresql' or settings.DATABASE_ENGINE == 'postgresql_psycopg2' :
    def test_postgresql():
        """
    >>> app = models.get_apps()[8]
    >>> auth_app = models.get_apps()[1]
    >>> app.__name__
    'unittests.sqlevolve.models'
    >>> auth_app.__name__
    'django.contrib.auth.models'

    >>> cursor = connection.cursor()

    # the table as it is supposed to be
    >>> create_table_sql = deseb.schema_evolution.get_sql_all(app, color_style())

    # make sure we don't evolve an unedited table
    >>> print_and_evolve(cursor, app) #p1
    []

    # delete a column, so it looks like we've recently added a field
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_person', 'gender' ))
    ['ALTER TABLE "sqlevolve_person" DROP COLUMN "gender";']
    >>> print_and_evolve(cursor, app) #p2
    ['ALTER TABLE "sqlevolve_person" ADD COLUMN "gender" varchar(1);',
 'UPDATE "sqlevolve_person" SET "gender" = \\'f\\' WHERE "gender" IS NULL;',
 'ALTER TABLE "sqlevolve_person" ALTER COLUMN "gender" SET NOT NULL;']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])

    # add a column, so it looks like we've recently deleted a field
    >>> print_and_execute(cursor, ops.get_add_column_sql('sqlevolve_person', 'gender_nothere', 'varchar(1)', True, False, False, None ))
    ['ALTER TABLE "sqlevolve_person" ADD COLUMN "gender_nothere" varchar(1);']
    >>> print_and_evolve(cursor, app) #p3
    ['-- warning: the following may cause data loss',
 u'ALTER TABLE "sqlevolve_person" DROP COLUMN "gender_nothere";',
 '-- end warning']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])
    
    # rename column, so it looks like we've recently renamed a field
    >>> print_and_execute(cursor, ops.get_change_column_name_sql('sqlevolve_person', {}, 'gender2', 'gender_old', 'varchar(1)', False ))
    ['ALTER TABLE "sqlevolve_person" RENAME COLUMN "gender2" TO "gender_old";']
    >>> print_and_evolve(cursor, app) #p4
    ['ALTER TABLE "sqlevolve_person" RENAME COLUMN "gender_old" TO "gender2";']
    
    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])

    # rename table, so it looks like we've recently renamed a model
    >>> print_and_execute(cursor, ops.get_change_table_name_sql('sqlevolve_personold', 'sqlevolve_person' ))
    ['ALTER TABLE "sqlevolve_person" RENAME TO "sqlevolve_personold";']
    >>> print_and_evolve(cursor, app) #p5
    ['ALTER TABLE "sqlevolve_personold" RENAME TO "sqlevolve_person";']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])
    
    # rename the sequence, so it looks like we renamed the sequence
    >>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" DROP COLUMN "id";')
    >>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" ADD COLUMN "strangename" serial;')
    >>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" RENAME COLUMN "strangename" TO "id";')
    >>> print_and_evolve(cursor, app) #p6.1
    [u'ALTER TABLE "sqlevolve_person_strangename_seq" RENAME TO "sqlevolve_person_id_seq";',
 u'ALTER TABLE "sqlevolve_person" ALTER COLUMN "id" SET DEFAULT nextval(\\'sqlevolve_person_id_seq\\'::regclass);']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])
    
    # remove id and add integer id, so it looks like we removed primary key constraint
    #>>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" DROP COLUMN "id";')
    #>>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" ADD COLUMN "id" integer;')
    #>>> print_and_evolve(cursor, app) #p6.2

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])

    # change column flags, so it looks like we've recently changed a column flag
    >>> from django.db.models.fields import NOT_PROVIDED
    >>> updates = {
    ...     'update_type': False,
    ...     'update_length': True,
    ...     'update_unique': False,
    ...     'update_null': False,
    ...     'update_primary': False,
    ...     'update_sequences': False,
    ... }
    #>>>print_and_execute(cursor, ops.get_change_column_def_sql('sqlevolve_person', 'name', 'varchar(10)', True, False, NOT_PROVIDED, updates ))
    #['ALTER TABLE "sqlevolve_person" ALTER COLUMN "name" TYPE varchar(10);']
    #>>> print_and_evolve(cursor, app) #p7
    #['ALTER TABLE "sqlevolve_person" ALTER COLUMN "name" TYPE varchar(20);']
    >>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" DROP COLUMN "name";')
    >>> silent_execute(cursor, 'ALTER TABLE "sqlevolve_person" ADD COLUMN "name" varchar(10);')
    >>> print_and_evolve(cursor, app) #p8
    ['ALTER TABLE "sqlevolve_person" ALTER COLUMN "name" TYPE varchar(20);',
 u'UPDATE "sqlevolve_person" SET "name" = \\'\\' WHERE "name" IS NULL;',
 'ALTER TABLE "sqlevolve_person" ALTER COLUMN "name" SET NOT NULL;']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;'); silent_execute(cursor, create_table_sql[0])
    
    # delete a datetime column pair, so it looks like we've recently added a datetime field
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_muebles', 'fecha_publicacion' ))
    ['ALTER TABLE "sqlevolve_muebles" DROP COLUMN "fecha_publicacion";']
    >>> print_and_evolve(cursor, app) #p9
    ['ALTER TABLE "sqlevolve_muebles" ADD COLUMN "fecha_publicacion" timestamp with time zone;']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_muebles;'); silent_execute(cursor, create_table_sql[1])

    # delete a column with a default value, so it looks like we've recently added a column
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_muebles', 'tipo' ))
    ['ALTER TABLE "sqlevolve_muebles" DROP COLUMN "tipo";']
    >>> print_and_execute(cursor, ops.get_drop_column_sql('sqlevolve_person', 'ssn' ))
    ['ALTER TABLE "sqlevolve_person" DROP COLUMN "ssn";']
    >>> print_and_evolve(cursor, app) #p10
    ['ALTER TABLE "sqlevolve_person" ADD COLUMN "ssn" integer;',
 'UPDATE "sqlevolve_person" SET "ssn" = 111111111 WHERE "ssn" IS NULL;',
 'ALTER TABLE "sqlevolve_person" ALTER COLUMN "ssn" SET NOT NULL;',
 'ALTER TABLE "sqlevolve_muebles" ADD COLUMN "tipo" varchar(40);',
 u'UPDATE "sqlevolve_muebles" SET "tipo" = \\'woot\\' WHERE "tipo" IS NULL;',
 'ALTER TABLE "sqlevolve_muebles" ALTER COLUMN "tipo" SET NOT NULL;']
    """

if settings.DATABASE_ENGINE == 'sqlite3':
    def test_sqlite():
        """
    >>> app = models.get_apps()[8]
    >>> auth_app = models.get_apps()[1]
    >>> app.__name__
    'unittests.sqlevolve.models'
    >>> auth_app.__name__
    'django.contrib.auth.models'
    
    >>> cursor = connection.cursor()

    # the table as it is supposed to be
    >>> create_table_sql = deseb.schema_evolution.get_sql_all(app, color_style())
    
    # make sure we don't evolve an unedited table
    >>> print_and_evolve(cursor, app) #sq1
    []
    
    # delete a column, so it looks like we've recently added a field
    >>> silent_execute(cursor, 'DROP TABLE "sqlevolve_person";' )
    >>> silent_execute(cursor, '''CREATE TABLE "sqlevolve_person" (
    ...     "id" integer NOT NULL UNIQUE PRIMARY KEY, 
    ...     "name" varchar(20) NOT NULL, 
    ...     "gender" varchar(1) NOT NULL
    ... );''' )
    >>> silent_execute(cursor, 'insert into "sqlevolve_person" values (1,2,3);' )
    >>> print_and_evolve(cursor, app) #sq2
    ['-- FYI: sqlite does not support changing columns',
 '-- FYI: sqlite does not support adding primary keys or unique or not null fields',
 '-- FYI: sqlite does not support adding primary keys or unique or not null fields',
 '-- FYI: so we create a new "sqlevolve_person" and delete the old ',
 '-- FYI: this could take a while if you have a lot of data',
 'ALTER TABLE "sqlevolve_person" RENAME TO "sqlevolve_person_1337_TMP";',
 'CREATE TABLE "sqlevolve_person" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "gender" varchar(1) NOT NULL,
    "gender2" varchar(1) NOT NULL,
    "ssn" integer NOT NULL
    )
    ;',
 u'INSERT INTO "sqlevolve_person" SELECT "id","name","gender",\\'\\',111111111 FROM "sqlevolve_person_1337_TMP";',
 'DROP TABLE "sqlevolve_person_1337_TMP";']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;')
    >>> silent_execute(cursor, create_table_sql[0])
    
    # add a column, so it looks like we've recently deleted a field
    >>> silent_execute(cursor, 'DROP TABLE "sqlevolve_person";' )
    >>> silent_execute(cursor, '''CREATE TABLE "sqlevolve_person" (
    ...     "id" integer NOT NULL UNIQUE PRIMARY KEY, 
    ...     "name" varchar(20) NOT NULL, 
    ...     "gender" varchar(1) NOT NULL,
    ...     "gender2" varchar(1) NOT NULL,
    ...     "gender_new" varchar(1) NOT NULL
    ... );''' )
    >>> silent_execute(cursor, 'insert into "sqlevolve_person" values (1,2,3,4,5);' )
    >>> print_and_evolve(cursor, app) #sq3
    ['-- FYI: sqlite does not support changing columns',
 '-- FYI: sqlite does not support adding primary keys or unique or not null fields',
 '-- warning: the following may cause data loss',
 '-- FYI: sqlite does not support deleting columns',
 '-- end warning',
 '-- FYI: so we create a new "sqlevolve_person" and delete the old ',
 '-- FYI: this could take a while if you have a lot of data',
 'ALTER TABLE "sqlevolve_person" RENAME TO "sqlevolve_person_1337_TMP";',
 'CREATE TABLE "sqlevolve_person" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "gender" varchar(1) NOT NULL,
    "gender2" varchar(1) NOT NULL,
    "ssn" integer NOT NULL
    )
    ;',
 'INSERT INTO "sqlevolve_person" SELECT "id","name","gender","gender2",111111111 FROM "sqlevolve_person_1337_TMP";',
 'DROP TABLE "sqlevolve_person_1337_TMP";']
    
    >>> silent_execute(cursor, 'select * from "sqlevolve_person";')
    >>> cursor.fetchall()[0]
    (1, u'2', u'3', u'4', 111111111)
    
    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;')
    >>> silent_execute(cursor, create_table_sql[0])
    
    # rename column, so it looks like we've recently renamed a field
    >>> silent_execute(cursor, 'DROP TABLE "sqlevolve_person"')
    >>> silent_execute(cursor, '''CREATE TABLE "sqlevolve_person" (
    ...     "id" integer NOT NULL UNIQUE PRIMARY KEY,
    ...     "name" varchar(20) NOT NULL,
    ...     "gender" varchar(1) NOT NULL, 
    ...     "gender_old" varchar(1) NOT NULL
    ... );''')
    >>> silent_execute(cursor, 'insert into "sqlevolve_person" values (1,2,3,4);' )
    >>> print_and_evolve(cursor, app) #sq4
    ['-- FYI: sqlite does not support changing columns',
 '-- FYI: sqlite does not support renaming columns',
 '-- FYI: sqlite does not support adding primary keys or unique or not null fields',
 '-- FYI: so we create a new "sqlevolve_person" and delete the old ',
 '-- FYI: this could take a while if you have a lot of data',
 'ALTER TABLE "sqlevolve_person" RENAME TO "sqlevolve_person_1337_TMP";',
 'CREATE TABLE "sqlevolve_person" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "gender" varchar(1) NOT NULL,
    "gender2" varchar(1) NOT NULL,
    "ssn" integer NOT NULL
    )
    ;',
 'INSERT INTO "sqlevolve_person" SELECT "id","name","gender","gender_old",111111111 FROM "sqlevolve_person_1337_TMP";',
 'DROP TABLE "sqlevolve_person_1337_TMP";']
    >>> silent_execute(cursor, 'select * from "sqlevolve_person";')
    >>> cursor.fetchall()[0]
    (1, u'2', u'3', u'4', 111111111)
    
    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;')
    >>> silent_execute(cursor, create_table_sql[0])
    
    # rename table, so it looks like we've recently renamed a model
    >>> print_and_execute(cursor, ops.get_change_table_name_sql('sqlevolve_personold', 'sqlevolve_person' ))
    ['ALTER TABLE "sqlevolve_person" RENAME TO "sqlevolve_personold";']
    >>> print_and_evolve(cursor, app) #sq5
    ['ALTER TABLE "sqlevolve_personold" RENAME TO "sqlevolve_person";']
    
    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;')
    >>> silent_execute(cursor, create_table_sql[0])
    
    # change column flags, so it looks like we've recently changed a column flag
    >>> silent_execute(cursor, 'DROP TABLE "sqlevolve_person";')
    >>> silent_execute(cursor, 'CREATE TABLE "sqlevolve_person" ("id" integer NOT NULL UNIQUE PRIMARY KEY, "name" varchar(20) NOT NULL, "gender" varchar(1) NOT NULL, "gender2" varchar(1) NULL);')
    >>> print_and_evolve(cursor, app) #sq6
    ['-- FYI: sqlite does not support changing columns',
 '-- FYI: sqlite does not support changing columns',
 '-- FYI: sqlite does not support adding primary keys or unique or not null fields',
 '-- FYI: so we create a new "sqlevolve_person" and delete the old ',
 '-- FYI: this could take a while if you have a lot of data',
 'ALTER TABLE "sqlevolve_person" RENAME TO "sqlevolve_person_1337_TMP";',
 'CREATE TABLE "sqlevolve_person" (
    "id" integer NOT NULL PRIMARY KEY,
    "name" varchar(20) NOT NULL,
    "gender" varchar(1) NOT NULL,
    "gender2" varchar(1) NOT NULL,
    "ssn" integer NOT NULL
    )
    ;',
 'INSERT INTO "sqlevolve_person" SELECT "id","name","gender","gender2",111111111 FROM "sqlevolve_person_1337_TMP";',
 'DROP TABLE "sqlevolve_person_1337_TMP";']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_person;')
    >>> silent_execute(cursor, create_table_sql[0])
    
    # delete a datetime column pair, so it looks like we've recently added a datetime field
    >>> print_and_execute(cursor, ['DROP TABLE sqlevolve_muebles;','CREATE TABLE "sqlevolve_muebles" ("id" integer NOT NULL UNIQUE PRIMARY KEY,"tipo" varchar(40) NOT NULL);'])
    ['DROP TABLE sqlevolve_muebles;',
 'CREATE TABLE "sqlevolve_muebles" ("id" integer NOT NULL UNIQUE PRIMARY KEY,"tipo" varchar(40) NOT NULL);']
    >>> print_and_evolve(cursor, app) #sq7
    ['-- FYI: sqlite does not support changing columns',
 'ALTER TABLE "sqlevolve_muebles" ADD COLUMN "fecha_publicacion" datetime NULL',
 '-- FYI: so we create a new "sqlevolve_muebles" and delete the old ',
 '-- FYI: this could take a while if you have a lot of data',
 'ALTER TABLE "sqlevolve_muebles" RENAME TO "sqlevolve_muebles_1337_TMP";',
 'CREATE TABLE "sqlevolve_muebles" (
    "id" integer NOT NULL PRIMARY KEY,
    "tipo" varchar(40) NOT NULL,
    "fecha_publicacion" datetime NULL
    )
    ;',
 u'INSERT INTO "sqlevolve_muebles" SELECT "id","tipo",\\'\\' FROM "sqlevolve_muebles_1337_TMP";',
 'DROP TABLE "sqlevolve_muebles_1337_TMP";']

    # reset the db
    >>> silent_execute(cursor, 'DROP TABLE sqlevolve_muebles;')
    >>> silent_execute(cursor, create_table_sql[1])
    
    # delete a column with a default value, so it looks like we've recently added a column
    >>> print_and_execute(cursor, ['DROP TABLE sqlevolve_muebles;','CREATE TABLE "sqlevolve_muebles" ("id" integer NOT NULL UNIQUE PRIMARY KEY,"fecha_publicacion" datetime NOT NULL);'])
    ['DROP TABLE sqlevolve_muebles;',
 'CREATE TABLE "sqlevolve_muebles" ("id" integer NOT NULL UNIQUE PRIMARY KEY,"fecha_publicacion" datetime NOT NULL);']
    """
    pass
