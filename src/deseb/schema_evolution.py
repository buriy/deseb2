from deseb.actions import get_introspected_evolution_options, show_evolution_plan
from deseb.common import color
from deseb.common import get_operations_and_introspection_classes
from deseb.common import management
from deseb.builder import build_model_schema
from deseb.storage import get_model_aka
import os, sys, datetime, traceback

DEBUG = False

def get_sql_evolution(app, style, notify=False):
    "Returns SQL to update an existing schema to match the existing models."
    return get_sql_evolution_detailed(app, style, notify)[2]

def get_installed_tables(app):
    model_schema = build_model_schema(app)
    add_tables = set()
    for model in model_schema.tables:
        add_tables.add(model.name)
        add_tables.update(get_model_aka(model))
    return add_tables

def get_sql_all(app, style):
    return management.sql_all(app, style)

def get_sql_evolution_detailed(app, style, notify):
    "Returns SQL to update an existing schema to match the existing models."
    
    from django.db import connection
    cursor = connection.cursor()
    #show_evolution_plan(cursor, app, style)

    ops, introspection = get_operations_and_introspection_classes(style)
    app_name = app.__name__.split('.')[-2]
    
    final_output = []

    schema_fingerprint = introspection.get_schema_fingerprint(cursor, app_name, get_installed_tables(app))
    schema_recognized, all_upgrade_paths, available_upgrades, best_upgrade \
        = get_managed_evolution_options(app, schema_fingerprint, style, notify)
    if schema_recognized:
        if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (recognized)\n" % (app_name, schema_fingerprint)))
        final_output.extend(best_upgrade[2])
        return schema_fingerprint, False, final_output
    else:
        if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (unrecognized)\n" % (app_name, schema_fingerprint)))

    final_output.extend(get_introspected_evolution_options(app, style))
        
    return schema_fingerprint, True, final_output

def get_fingerprints_evolutions_from_app(app, style, notify):
    from django.conf import settings
    try:
        app_name = app.__name__.split('.')[-2]
        app_se = __import__(app_name +'.schema_evolution').schema_evolution
        evolutions_list = app_se.__getattribute__(settings.DATABASE_ENGINE+'_evolutions')
        evolutions = {}
        fingerprints = []
        end_fingerprints = []
        for x in evolutions_list:
            if evolutions.has_key(x[0]):
                if notify: sys.stderr.write(style.NOTICE("Warning: Fingerprint mapping %s is defined twice in %s.schema_evolution\n" % (str(x[0]),app_name)))
            else:
                evolutions[x[0]] = x[1:]
                if x[0][0] not in fingerprints:
                    fingerprints.append(x[0][0])
                if x[0][1] not in fingerprints and x[0][1] not in end_fingerprints:
                    end_fingerprints.append(x[0][1])
        fingerprints.extend(end_fingerprints)
        return fingerprints, evolutions
    except:
        return [], {}

def get_sql_fingerprint(app, style, notify=True):
    "Returns the fingerprint of the current schema, used in schema evolution."
    from django.db import connection
    # This should work even if a connecton isn't available
    try:
        cursor = connection.cursor()
    except:
        cursor = None

    ops, introspection = get_operations_and_introspection_classes(style)

    app_name = app.__name__.split('.')[-2]
    schema_fingerprint = introspection.get_schema_fingerprint(cursor, app_name, get_installed_tables(app))
    try:
        fingerprints, evolutions = get_fingerprints_evolutions_from_app(app, style, notify)
        # is this a schema we recognize?
        schema_recognized = schema_fingerprint in fingerprints
        if schema_recognized:
            if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (recognized)\n" % (app_name, schema_fingerprint)))
        else:
            if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (unrecognized)\n" % (app_name, schema_fingerprint)))
    except:
        traceback.print_exc()
        if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (no schema_evolution module found)\n" % (app_name, schema_fingerprint)))
    return

def get_managed_evolution_options(app, schema_fingerprint, style, notify):
    # return schema_recognized, available_upgrades, best_upgrade
#    try:
        # is this a schema we recognize?
        fingerprints, evolutions = get_fingerprints_evolutions_from_app(app, style, notify)
        schema_recognized = schema_fingerprint in fingerprints
        if schema_recognized:
            available_upgrades = []
            all_upgrade_paths = set()
            for (vfrom, vto), upgrade in evolutions.iteritems():
                all_upgrade_paths.add((vfrom, vto))
                if vfrom == schema_fingerprint:
                    distance = fingerprints.index(vto)-fingerprints.index(vfrom)
                    available_upgrades.append((vfrom, vto, upgrade, distance) )
            if len(available_upgrades):
                best_upgrade = available_upgrades[0]
                for an_upgrade in available_upgrades:
                    if an_upgrade[3] > best_upgrade[3]:
                        best_upgrade = an_upgrade
                return schema_recognized, all_upgrade_paths, available_upgrades, best_upgrade
            else:
                return schema_recognized, all_upgrade_paths, available_upgrades, None
        else:
            return False, set(), [], None
#    except:
#        print sys.exc_info()[0]
#        return False, [], None

def save_managed_evolution(app, commands, schema_fingerprint, new_schema_fingerprint):
    from django.conf import settings
    app_name = app.__name__.split('.')[-2]
    
    # find path to app
    se_file = None
    for p in sys.path:
        if os.path.isdir(os.path.join(p, app_name) ) and app_name!='deseb':
            se_file = os.path.join(p, app_name, 'schema_evolution.py')
    
    if os.path.isfile(se_file):
        file = open(se_file, 'r')
        contents = file.readlines()
    else:
        contents = []
        
    insertion_point = None
    for i in range(0, len(contents)):
        if contents[i].strip().endswith("## "+ settings.DATABASE_ENGINE +"_evolutions_end ##"):
            insertion_point = i
    if insertion_point==None:
        contents.extend([
            "\n",
            "# all of your evolution scripts, mapping the from_version and to_version to a list if sql commands\n",
            settings.DATABASE_ENGINE +"_evolutions = [\n",
            "] # don't delete this comment! ## "+ settings.DATABASE_ENGINE +"_evolutions_end ##\n",
        ])
        insertion_point = len(contents) - 1
        
    contents.insert(insertion_point, '    ],\n')
    for i in range(len(commands)-1, -1, -1):
        contents.insert(insertion_point, '        "'+ commands[i].replace('"','\\"').replace('\n','\\n') +'",\n')
    now = datetime.datetime.now()
    line = "    [('%s','%s'), # generated %s\n" % (schema_fingerprint, new_schema_fingerprint, now)
    contents.insert(insertion_point, line)
    
    file = open(se_file, 'w')
    file.writelines(contents)
    
def evolvediff(app, interactive=True, do_save=False, verbose=False, managed_upgrade_only=False):
    from django.db import connection
    cursor = connection.cursor()
    style = color.no_style()
    return show_evolution_plan(cursor, app, style)

def evolvedb(app, interactive=True, do_save=False, verbose=False, managed_upgrade_only=False):
    from django.db import connection
    cursor = connection.cursor()

    style = color.no_style()
    ops, introspection = get_operations_and_introspection_classes(style)
    app_name = app.__name__.split('.')[-2]
    
    seen_schema_fingerprints = set()
    
    fingerprints, evolutions = get_fingerprints_evolutions_from_app(app, style, verbose)
    if fingerprints and evolutions:
        if verbose:
            print 'deseb: %s.schema_evolution module found (%i fingerprints, %i evolutions)' % \
                    (app_name, len(fingerprints), len(evolutions))

    while True:
        commands = []
        commands_color = []
    
        schema_fingerprint = introspection.get_schema_fingerprint(cursor, app_name, get_installed_tables(app))
        schema_recognized, all_upgrade_paths, available_upgrades, best_upgrade = \
                    get_managed_evolution_options(app, schema_fingerprint, style, verbose)
        if fingerprints and evolutions:
            if schema_recognized:
                if verbose or interactive: 
                    print "deseb: fingerprint for '%s' is '%s' (recognized)" % (app_name, schema_fingerprint)
            else:
                if verbose or interactive: 
                    print "deseb: fingerprint for '%s' is '%s' (unrecognized)" % (app_name, schema_fingerprint)
        managed_upgrade = schema_recognized and available_upgrades and best_upgrade and best_upgrade[3]>0
        if managed_upgrade:
            if verbose or interactive: 
                print "\t and a managed schema upgrade to '%s' is available:" % best_upgrade[1], best_upgrade[3]
            commands_color = commands = best_upgrade[2]
        elif not managed_upgrade_only:
            commands = get_introspected_evolution_options(app, style)
            commands_color = get_introspected_evolution_options(app, color.color_style())
            if interactive:
                if commands:
                    print '%s: the following schema upgrade is available:' % app_name
    #            else:
    #                print '%s: schema is up to date' % app_name
            
        if commands:
            if interactive or DEBUG:
                for cmd in commands_color:
                    print cmd
        else:
                break
    
        if interactive:
            confirm = raw_input("do you want to run the preceeding commands?\ntype 'yes' to continue, or 'no' to cancel: ")
        else:
            confirm = 'yes'
        
        if confirm == 'yes':
            connection._commit() # clean previous commands run state
            for cmd in commands:
                if cmd[:3] != '-- ':
                    cursor.execute(cmd)
            connection._commit() # commit changes
            if interactive: print 'schema upgrade executed'
            new_schema_fingerprint = introspection.get_schema_fingerprint(cursor, app_name, get_installed_tables(app))
            
            if schema_fingerprint==new_schema_fingerprint:
                print "schema fingerprint was unchanged - this really shouldn't happen"
            else:
                if commands and not managed_upgrade and (schema_fingerprint,new_schema_fingerprint) not in all_upgrade_paths:
                    if interactive and do_save:
                        confirm = raw_input("do you want to save these commands in %s.schema_evolution?\n"
                                            "type 'yes' to continue, or 'no' to cancel: " % app_name)
                    else:
                        confirm = 'yes'
                    if do_save and confirm == 'yes':
                        save_managed_evolution(app, commands, schema_fingerprint, new_schema_fingerprint)
            
            if not managed_upgrade: break
        else:
            if interactive: print 'schema not saved'
            break
                
        seen_schema_fingerprints.add(schema_fingerprint)
        schema_fingerprint = new_schema_fingerprint
            
        if managed_upgrade:
            if schema_fingerprint==best_upgrade[1]:
                if verbose: 
                    print '\tfingerprint verification successful'
            else:
                if verbose: 
                    print "\tfingerprint verification failed (is '%s'; was expecting '%s')" % \
                            (schema_fingerprint, best_upgrade[1])
                break
        
        print
    
        if schema_fingerprint in seen_schema_fingerprints:
            break

