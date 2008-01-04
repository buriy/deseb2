from django.conf import settings

# list of all known schema fingerprints, in order
mysql_fingerprints = [
    'fv1:1742830097',
#    'fv1:907953071',
    'fv1:xxxxxxxxx',
    'fv1:yyyyyyyyy',
    # add future fingerprints here
]

# all of your evolution scripts, mapping the from_version and to_version 
# to a list if sql commands
mysql_evolutions = {
    # ('from_fingerprint','to_fingerprint'): ['-- some sql'],
    ('fv1:1742830097','fv1:907953071'): [
        '-- some list of sql statements, constituting an upgrade',
        '-- some list of sql statements, constituting an upgrade',
        '-- some list of sql statements, constituting an upgrade',
        '-- some list of sql statements, constituting an upgrade',
    ],
    ('fv1:907953071','fv1:xxxxxxxxx'): [
        '-- another list of sql statements, constituting a second upgrade',
        '-- another list of sql statements, constituting a second upgrade',
    ],
    ('fv1:xxxxxxxxx','fv1:yyyyyyyyy'): [
        '-- another list of sql statements, constituting a third upgrade',
    ],
    ('fv1:yyyyyyyyy','fv1:xxxxxxxxx'): [
        '-- downgrades are supported too',
    ],
    ('fv1:907953071','fv1:yyyyyyyyy'): [
        '-- an example of the graph nature of upgrades....someone on',
        '-- fv1:907953071 can upgrade directly to fv1:yyyyyyyyy if you',
        '-- have some weird situation / requirement.  priority is given to',
        '-- the greater upgrade (ie how many indices in fingerprints it jumps)',
    ],
}

fingerprints = []; evolutions = {}
if settings.DATABASE_ENGINE == 'mysql':
    fingerprints = mysql_fingerprints
    evolutions = mysql_evolutions
