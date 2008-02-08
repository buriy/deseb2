
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
