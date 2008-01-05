from django.conf import settings

# all of your evolution scripts, mapping the from_version and to_version 
# to a list if sql commands
mysql_evolutions = [
    # [('from_fingerprint','to_fingerprint'), ['-- some sql'],
    [('fv1:1742830097','fv1:907953071'),
        '-- some list of sql statements, constituting an upgrade',
        '-- some list of sql statements, constituting an upgrade',
        '-- some list of sql statements, constituting an upgrade',
        '-- some list of sql statements, constituting an upgrade',
    ],
    [('fv1:907953071','fv1:xxxxxxxxx'),
        '-- another list of sql statements, constituting a second upgrade',
        '-- another list of sql statements, constituting a second upgrade',
    ],
    [('fv1:xxxxxxxxx','fv1:yyyyyyyyy'),
        '-- another list of sql statements, constituting a third upgrade',
    ],
    [('fv1:yyyyyyyyy','fv1:xxxxxxxxx'),
        '-- downgrades are supported too',
    ],
    [('fv1:907953071','fv1:yyyyyyyyy'),
        '-- an example of the graph nature of upgrades....someone on',
        '-- fv1:907953071 can upgrade directly to fv1:yyyyyyyyy if you',
        '-- have some weird situation / requirement.  priority is given to',
        '-- the greater upgrade (ie how many indices in fingerprints it jumps)',
    ],
]

# all of your evolution scripts, mapping the from_version and to_version to a list if sql commands
mysql_evolutions = [
    [('fv1:-1020759453','fv1:-1020759453'), # generated 2008-01-05 08:17:24.312000
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `question` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `author` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `choice` varchar(200) NOT NULL;",
    ],
    [('fv1:-1020759453','fv1:-1020759453'), # generated 2008-01-05 08:17:34.562000
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `question` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `author` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `choice` varchar(200) NOT NULL;",
    ],
    [('fv1:-1020759453','fv1:-1020759453'), # generated 2008-01-05 08:18:02.171000
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `question` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `author` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `choice` varchar(200) NOT NULL;",
    ],
    [('fv1:-1020759453','fv1:-1020759453'), # generated 2008-01-05 08:19:10.234000
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `question` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `author` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `choice` varchar(200) NOT NULL;",
    ],
    [('fv1:-1020759453','fv1:-1020759453'), # generated 2008-01-05 08:22:48.359000
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `question` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `author` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `choice` varchar(200) NOT NULL;",
    ],
    [('fv1:-1020759453','fv1:-1020759453'), # generated 2008-01-05 08:31:42.609000
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `question` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_poll` MODIFY COLUMN `author` varchar(200) NOT NULL;",
        "ALTER TABLE `case01_add_field_choice` MODIFY COLUMN `choice` varchar(200) NOT NULL;",
    ],
] # don't delete this comment! ## mysql_evolutions_end ##
