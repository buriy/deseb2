
# all of your evolution scripts, mapping the from_version and to_version to a list if sql commands
mysql_evolutions = [
    [('fv1:893820020','fv1:1742830097'), # generated 2008-02-08 19:47:51.415000
        "-- warning: the following may cause data loss",
        "ALTER TABLE `case01_add_field_choice` DROP COLUMN `votes3`;",
        "ALTER TABLE `case01_add_field_choice` DROP COLUMN `votes2`;",
        "ALTER TABLE `case01_add_field_choice` DROP COLUMN `creatorIp`;",
        "ALTER TABLE `case01_add_field_choice` DROP COLUMN `content`;",
        "ALTER TABLE `case01_add_field_choice` DROP COLUMN `hasSomething`;",
        "-- end warning",
    ],
    [('fv1:1742830097','fv1:-1020759453'), # generated 2008-02-08 19:48:31.758000
        "ALTER TABLE `case01_add_field_poll` ADD COLUMN `pub_date2` datetime;",
        "ALTER TABLE `case01_add_field_choice` ADD COLUMN `votes2` integer;",
        "UPDATE `case01_add_field_choice` SET `votes2` = 0 WHERE `votes2` IS NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `votes2` integer NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` ADD COLUMN `hasSomething` bool;",
        "UPDATE `case01_add_field_choice` SET `hasSomething` = 't' WHERE `hasSomething` IS NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `hasSomething` bool NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` ADD COLUMN `creatorIp` char(15);",
        "ALTER TABLE `case01_add_field_choice` ADD COLUMN `votes3` integer;",
        "UPDATE `case01_add_field_choice` SET `votes3` = 5 WHERE `votes3` IS NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `votes3` integer NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` ADD COLUMN `content` longtext;",
        "UPDATE `case01_add_field_choice` SET `content` = '' WHERE `content` IS NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `content` longtext NOT NULL;",
    ],
] # don't delete this comment! ## mysql_evolutions_end ##


# all of your evolution scripts, mapping the from_version and to_version to a list if sql commands
sqlite3_evolutions = [
    [('fv1:501009936','fv1:-1546186035'), # generated 2008-02-11 04:35:13.304000
        "-- warning: the following may cause data loss",
        "-- FYI: sqlite does not support deleting columns",
        "-- end warning",
        "-- FYI: so we create a new \"case08_evolution_poll\" and delete the old ",
        "-- FYI: this could take a while if you have a lot of data",
        "ALTER TABLE \"case08_evolution_poll\" RENAME TO \"case08_evolution_poll_1337_TMP\";",
        "CREATE TABLE \"case08_evolution_poll\" (\n    \"id\" integer NOT NULL PRIMARY KEY,\n    \"question\" varchar(200) NOT NULL,\n    \"pub_date\" datetime NOT NULL,\n    \"author\" varchar(200) NOT NULL\n)\n;",
        "INSERT INTO \"case08_evolution_poll\" SELECT \"id\",\"question\",\"pub_date\",\"author\" FROM \"case08_evolution_poll_1337_TMP\";",
        "DROP TABLE \"case08_evolution_poll_1337_TMP\";",
        "-- warning: the following may cause data loss",
        "-- FYI: sqlite does not support deleting columns",
        "-- FYI: sqlite does not support deleting columns",
        "-- FYI: sqlite does not support deleting columns",
        "-- FYI: sqlite does not support deleting columns",
        "-- FYI: sqlite does not support deleting columns",
        "-- end warning",
        "-- FYI: so we create a new \"case08_evolution_choice\" and delete the old ",
        "-- FYI: this could take a while if you have a lot of data",
        "ALTER TABLE \"case08_evolution_choice\" RENAME TO \"case08_evolution_choice_1337_TMP\";",
        "CREATE TABLE \"case08_evolution_choice\" (\n    \"id\" integer NOT NULL PRIMARY KEY,\n    \"poll_id\" integer NOT NULL REFERENCES \"case08_evolution_poll\" (\"id\"),\n    \"choice\" varchar(200) NOT NULL,\n    \"votes\" integer NOT NULL\n)\n;",
        "INSERT INTO \"case08_evolution_choice\" SELECT \"id\",\"poll_id\",\"choice\",\"votes\" FROM \"case08_evolution_choice_1337_TMP\";",
        "DROP TABLE \"case08_evolution_choice_1337_TMP\";",
    ],
    [('fv1:-1546186035','fv1:501009936'), # generated 2008-02-11 04:26:39.148000
        "ALTER TABLE \"case08_evolution_poll\" ADD COLUMN \"pub_date2\" datetime NULL",
        "-- FYI: so we create a new \"case08_evolution_poll\" and delete the old ",
        "-- FYI: this could take a while if you have a lot of data",
        "ALTER TABLE \"case08_evolution_poll\" RENAME TO \"case08_evolution_poll_1337_TMP\";",
        "CREATE TABLE \"case08_evolution_poll\" (\n    \"id\" integer NOT NULL PRIMARY KEY,\n    \"question\" varchar(200) NOT NULL,\n    \"pub_date\" datetime NOT NULL,\n    \"author\" varchar(200) NOT NULL,\n    \"pub_date2\" datetime NULL\n)\n;",
        "INSERT INTO \"case08_evolution_poll\" SELECT \"id\",\"question\",\"pub_date\",\"author\",'' FROM \"case08_evolution_poll_1337_TMP\";",
        "DROP TABLE \"case08_evolution_poll_1337_TMP\";",
        "-- FYI: sqlite does not support adding primary keys or unique or not null fields",
        "-- FYI: sqlite does not support adding primary keys or unique or not null fields",
        "ALTER TABLE \"case08_evolution_choice\" ADD COLUMN \"creatorIp\" char(15) NULL",
        "-- FYI: sqlite does not support adding primary keys or unique or not null fields",
        "-- FYI: sqlite does not support adding primary keys or unique or not null fields",
        "-- FYI: so we create a new \"case08_evolution_choice\" and delete the old ",
        "-- FYI: this could take a while if you have a lot of data",
        "ALTER TABLE \"case08_evolution_choice\" RENAME TO \"case08_evolution_choice_1337_TMP\";",
        "CREATE TABLE \"case08_evolution_choice\" (\n    \"id\" integer NOT NULL PRIMARY KEY,\n    \"poll_id\" integer NOT NULL REFERENCES \"case08_evolution_poll\" (\"id\"),\n    \"choice\" varchar(200) NOT NULL,\n    \"votes\" integer NOT NULL,\n    \"votes2\" integer NOT NULL,\n    \"hasSomething\" bool NOT NULL,\n    \"creatorIp\" char(15) NULL,\n    \"votes3\" integer NOT NULL,\n    \"content\" text NOT NULL\n)\n;",
        "INSERT INTO \"case08_evolution_choice\" SELECT \"id\",\"poll_id\",\"choice\",\"votes\",0,'f','',5,'' FROM \"case08_evolution_choice_1337_TMP\";",
        "DROP TABLE \"case08_evolution_choice_1337_TMP\";",
    ],
] # don't delete this comment! ## sqlite3_evolutions_end ##
