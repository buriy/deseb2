from django.core.exceptions import ImproperlyConfigured
from optparse import OptionParser
from django.utils import termcolors
from django.conf import settings

import os, re, shutil, sys, textwrap, datetime, traceback
try:
    import django.core.management.sql as management
    from django.core.management import color
    version = 'trunk'
except ImportError:
    # v0.96 compatibility
    import django.core.management as management
    management.installed_models = management._get_installed_models
    class color_class:
        def color_style(self):
            return management.style
        def no_style(self):
            class no_style:
                def __getattr__(self, attr):
                    return lambda x: x
            return no_style()
    color = color_class()
    version = '0.96'

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

class NotNullColumnNeedsDefaultException(Exception): pass
class MultipleRenamesPossibleException(Exception): pass

DEBUG = False

def get_operations_and_introspection_classes(style):
    from django.db import backend, connection

    try: # v0.96 compatibility
        v0_96_quote_name = backend.quote_name
        class dummy: pass
        setattr(connection, 'ops', dummy())
        setattr(connection.ops, 'quote_name', v0_96_quote_name)
    except:
        pass
    
    backend_type = str(connection.__class__).split('.')[3]
    if backend_type=='mysql': import deseb.backends.mysql as backend
    elif backend_type=='postgresql': import deseb.backends.postgresql as backend 
    elif backend_type=='postgresql_psycopg2': import deseb.backends.postgresql_psycopg2 as backend 
    elif backend_type=='sqlite3': import deseb.backends.sqlite3 as backend
    else: raise Exception('backend '+ backend_type +' not supported yet - sorry!')
    ops = backend.DatabaseOperations(connection, style)
    introspection = backend.DatabaseIntrospection(connection)
    return ops, introspection

def get_sql_indexes_for_field(model, f, style):
    "Returns the CREATE INDEX SQL statement for a single field"
    from django.db import backend, connection
    output = []
    if f.db_index and not ((f.primary_key or f.unique) and backend.autoindexes_primary_keys):
        unique = f.unique and 'UNIQUE ' or ''
        try:
            tablespace = f.db_tablespace or model._meta.db_tablespace
        except: # v0.96 compatibility
            tablespace = None
        if tablespace and backend.supports_tablespaces:
            tablespace_sql = ' ' + backend.get_tablespace_sql(tablespace)
        else:
            tablespace_sql = ''
        output.append(
            style.SQL_KEYWORD('CREATE %sINDEX' % unique) + ' ' + \
            style.SQL_TABLE(connection.ops.quote_name('%s_%s' % (model._meta.db_table, f.column))) + ' ' + \
            style.SQL_KEYWORD('ON') + ' ' + \
            style.SQL_TABLE(connection.ops.quote_name(model._meta.db_table)) + ' ' + \
            "(%s)" % style.SQL_FIELD(connection.ops.quote_name(f.column)) + \
            "%s;" % tablespace_sql
       )
    return output
    
def get_sql_evolution_check_for_new_fields(model, old_table_name, style):
    "checks for model fields that are not in the existing data structure"
    from django.db import connection

    ops, introspection = get_operations_and_introspection_classes(style)
    
    data_types = connection.creation.data_types
    cursor = connection.cursor()
#    introspection = ops = get_ops_class(connection)
    opts = model._meta
    output = []
    db_table = model._meta.db_table
    if old_table_name: 
        db_table = old_table_name
    existing_fields = introspection.get_columns(cursor,db_table)
    for f in opts.fields:
        if f.column not in existing_fields and (not f.aka or f.aka not in existing_fields and len(set(f.aka) & set(existing_fields))==0):
            col_type = f.db_type()
            if col_type is not None:
                output.extend(ops.get_add_column_sql(model._meta.db_table, f.column, style.SQL_COLTYPE(col_type), f.null, f.unique, f.primary_key, f.default))
                output.extend(get_sql_indexes_for_field(model, f, style))
    return output

def get_sql_evolution_check_for_changed_model_name(klass, style):
    from django.db import get_introspection_module, connection

    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
    introspection = get_introspection_module()
#    ops = get_ops_class(connection)
    table_list = introspection.get_table_list(cursor)
    if klass._meta.db_table in table_list:
        return [], None
    aka_db_tables = set()
    if klass._meta.aka:
        for x in klass._meta.aka:
            aka_db_tables.add("%s_%s" % (klass._meta.app_label, x.lower()))
    matches = list(aka_db_tables & set(table_list))
    if len(matches)==1:
        return ops.get_change_table_name_sql(klass._meta.db_table, matches[0]), matches[0]
    else:
        return [], None
    
def get_sql_evolution_check_for_changed_field_name(klass, old_table_name, style):
    from django.db import get_introspection_module, connection
    
    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
    opts = klass._meta
    output = []
    db_table = klass._meta.db_table
    if old_table_name: 
        db_table = old_table_name
    for f in opts.fields:
        existing_fields = introspection.get_columns(cursor,db_table)
        if f.column in existing_fields:
            old_col = f.column
        elif f.aka and len(set(f.aka).intersection(set(existing_fields)))==1:
            old_col = set(f.aka).intersection(set(existing_fields)).pop()
        elif f.aka and len(set(f.aka).intersection(set(existing_fields)))>1:
            details = 'column "%s" of table "%s"' % (f.column, klass._meta.db_table)
            raise MultipleRenamesPossibleException("when renamed " + details)
        else:
            continue
        if old_col != f.column:
            col_type = f.db_type()
            col_type_def = style.SQL_COLTYPE(col_type)
            if col_type is not None:
                col_def = style.SQL_COLTYPE(col_type) +' '+ style.SQL_KEYWORD('%sNULL' % (not f.null and 'NOT ' or ''))
                if f.unique and not f.primary_key:
                    col_def += style.SQL_KEYWORD(' UNIQUE')
                if f.primary_key:
                    col_def += style.SQL_KEYWORD(' PRIMARY KEY')
                output.extend(ops.get_change_column_name_sql(klass._meta.db_table, get_introspection_module().get_indexes(cursor,db_table), old_col, f.column, col_type_def, f))
    return output
    
def get_sql_evolution_rebuild_table(klass, old_table_name, style):
    from django.db import get_introspection_module, connection
    
    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
    opts = klass._meta
    output = []
    db_table = klass._meta.db_table
    if old_table_name: 
        db_table = old_table_name

    existing_fields = introspection.get_columns(cursor,db_table)
    renamed_fields = {}
    
    for f in opts.fields:
        if f.column in existing_fields:
            old_col = f.column
        elif f.aka and len(set(f.aka).intersection(set(existing_fields)))==1:
            old_col = set(f.aka).intersection(set(existing_fields)).pop()
        elif f.aka and len(set(f.aka).intersection(set(existing_fields)))>1:
            details = 'column "%s" of table "%s"' % (f.column, klass._meta.db_table)
            raise MultipleRenamesPossibleException("when renamed " + details)
        else:
            continue
        if old_col != f.column:
            renamed_fields[f.column] = old_col
    
    output.extend(ops.get_rebuild_table_sql(klass._meta.db_table, get_introspection_module().get_indexes(cursor,db_table), existing_fields, renamed_fields))
    return output
    
def get_field_default(f):
    from django.db.models.fields import NOT_PROVIDED
    if callable(f.default): return NOT_PROVIDED
    return f.default

def get_field_type(f):
    f = f.split('(')[0].split(' ')[0]
    if f in ['integer', 'serial']: return 'int'
    if f in ['tinyint']: return 'bool'
    if f in ['decimal']: return 'numeric'
    return f    

def compare_field_length(f, column_flags):
    from django.db.models.fields import CharField, SlugField, AutoField
    f_maxlength = str(getattr(f, 'maxlength', getattr(f, 'max_length', None)))
    db_maxlength = str(column_flags.get('max_length', 64000))
    return(not f.primary_key and isinstance(f, CharField) and db_maxlength!= f_maxlength) or \
          (not f.primary_key and isinstance(f, SlugField) and db_maxlength!= f_maxlength)

def get_sql_evolution_check_for_changed_field_flags(klass, old_table_name, style):
    ops, introspection = get_operations_and_introspection_classes(style)
    
    from django.db import connection
    data_types = connection.creation.data_types
    cursor = connection.cursor()
#    introspection = ops = get_ops_class(connection)
    opts = klass._meta
    output = []
    db_table = klass._meta.db_table
    if old_table_name: 
        db_table = old_table_name
    for f in opts.fields:
        existing_fields = introspection.get_columns(cursor,db_table)
        #existing_relations = introspection.get_relations(cursor,db_table)
        cf = None # current field, ie what it is before any renames
        if f.column in existing_fields:
            cf = f.column
            f_col_type = f.db_type()
        elif f.aka and len(set(f.aka).intersection(set(existing_fields)))==1:
            cf = set(f.aka).intersection(set(existing_fields)).pop()
            #hack
            tempname = f.column
            f.column = cf
            f_col_type = f.db_type()
            f.column = tempname
        else:
            continue # no idea what column you're talking about - should be handled by get_sql_evolution_check_for_new_fields())
        data_type = f.get_internal_type()
        if data_types.has_key(data_type):
            #print cf, data_type, f_col_type
            is_postgresql = settings.DATABASE_ENGINE in ['postgresql', 'postgresql_psycopg2']
            column_flags = introspection.get_known_column_flags(cursor, db_table, cf)
            update_length = compare_field_length(f, column_flags)
            update_type = get_field_type(column_flags['coltype']) != get_field_type(f_col_type)
            if DEBUG and update_type:
                print get_field_type(column_flags['coltype']), '->', get_field_type(f_col_type)
            update_unique = (column_flags['unique']!=f.unique and not (is_postgresql and f.primary_key))
            update_null = column_flags['allow_null'] != f.null and not f.primary_key
            update_primary = column_flags['primary_key']!=f.primary_key
            update_sequences = False
            if column_flags.has_key('sequence'):
                correct_seq_name = klass._meta.db_table+"_"+cf+'_seq'
                update_sequences = column_flags['sequence'] != correct_seq_name
            #if DEBUG and update_length: 
            #    print f_col_type, column_flags['coltype'], column_flags['maxlength']
            if update_type or update_null or update_length or update_unique or update_primary or update_sequences:
                #print "cf, f.default, column_flags['default']", cf, f.default, column_flags['default'], f.default.__class__
                f_default = get_field_default(f)
                updates = {
                    'update_type': update_type,
                    'update_length': update_length,
                    'update_unique': update_unique,
                    'update_null': update_null,
                    'update_primary': update_primary,
                    'update_sequences': update_sequences,
                }
                output.extend(ops.get_change_column_def_sql(klass._meta.db_table, cf, f_col_type, f, column_flags, f_default, updates))
    return output

def get_sql_evolution_check_for_dead_fields(klass, old_table_name, style):
    from django.db import connection
    
    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
#    introspection = ops = get_ops_class(connection)
    opts = klass._meta
    output = []
    db_table = klass._meta.db_table
    if old_table_name: 
        db_table = old_table_name
    suspect_fields = set(introspection.get_columns(cursor,db_table))
#    print 'suspect_fields = ', suspect_fields
    for f in opts.fields:
#        print 'f = ', f
#        print 'f.aka = ', f.aka
        suspect_fields.discard(f.column)
        suspect_fields.discard(f.aka)
        if f.aka: suspect_fields.difference_update(f.aka)
    if len(suspect_fields)>0:
        output.append('-- warning: the following may cause data loss')
        for suspect_field in suspect_fields:
            output.extend(ops.get_drop_column_sql(klass._meta.db_table, suspect_field))
        output.append('-- end warning')
    return output

def get_sql_evolution_check_for_dead_models(table_list, safe_tables, app_name, app_models, style):
    from django.db import connection
    
    ops, introspection = get_operations_and_introspection_classes(style)

    if not app_models: return []
    app_label = app_models[0]._meta.app_label
    safe_tables = set(safe_tables)
    for model in app_models:
        for f in model._meta.many_to_many:
            safe_tables.add(f.m2m_db_table())
    try:
        app_se = __import__(app_name +'.schema_evolution').schema_evolution
        for table_name in app_se.protected_tables:
            safe_tables.add(table_name)
            safe_tables.add(app_label +'_'+ table_name)
    except:
        pass
    delete_tables = set()
    for t in table_list:
        if t.startswith(app_label) and not t in safe_tables:
            delete_tables.add(t)
    return ops.get_drop_table_sql(delete_tables)

def get_sql_evolution_v0_96(app, do_notify=True):
    return get_sql_evolution(app, management.style, do_notify)

def run_sql_evolution_v0_96(app, interactive=True, do_save=True, do_notify=True):
    return evolvedb(app, interactive, do_save, do_notify)

def get_sql_evolution(app, style, notify=True):
    "Returns SQL to update an existing schema to match the existing models."
    return get_sql_evolution_detailed(app, style, notify)[2]

def get_sql_evolution_detailed(app, style, notify):
    "Returns SQL to update an existing schema to match the existing models."

    ops, introspection = get_operations_and_introspection_classes(style)
    from django.db import connection
    cursor = connection.cursor()
    app_name = app.__name__.split('.')[-2]

    final_output = []

    schema_fingerprint = introspection.get_schema_fingerprint(cursor, app)
    schema_recognized, all_upgrade_paths, available_upgrades, best_upgrade = get_managed_evolution_options(app, schema_fingerprint, style, notify)
    if schema_recognized:
            if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (recognized)\n" % (app_name, schema_fingerprint)))
            final_output.extend(best_upgrade[2])
            return schema_fingerprint, False, final_output
    else:
        if notify: sys.stderr.write(style.NOTICE("deseb: Current schema fingerprint for '%s' is '%s' (unrecognized)\n" % (app_name, schema_fingerprint)))

    final_output.extend(get_introspected_evolution_options(app, style))
        
    return schema_fingerprint, True, final_output


def fixed_sql_model_create(model, known_models, style):
    if version == 'trunk':
        return management.sql_model_create(model, style, known_models)
    else:
        return management._get_sql_model_create(model, known_models)

def _get_many_to_many_sql_for_field(model, f, style):
    from django.db import backend, models, connection
    try:
        from django.contrib.contenttypes import generic
    except: # v0.96 compatibility
        from django.db.models.fields import generic #@UnresolvedImport
        
    ops, introspection = get_operations_and_introspection_classes(style)

    opts = model._meta
    final_output = []
    if not isinstance(f.rel, generic.GenericRel):
        try:
            tablespace = f.db_tablespace or opts.db_tablespace
        except: # v0.96 compatibility
            tablespace = None
        if tablespace and backend.supports_tablespaces and backend.autoindexes_primary_keys:
            tablespace_sql = ' ' + backend.get_tablespace_sql(tablespace, inline=True)
        else:
            tablespace_sql = ''
        table_output = [style.SQL_KEYWORD('CREATE TABLE') + ' ' + \
            style.SQL_TABLE(connection.ops.quote_name(f.m2m_db_table())) + ' (']
        table_output.append('    %s %s %s%s,' % \
            (style.SQL_FIELD(connection.ops.quote_name('id')),
            style.SQL_COLTYPE(models.AutoField(primary_key=True).db_type()),
            style.SQL_KEYWORD('NOT NULL PRIMARY KEY'),
            tablespace_sql))
        table_output.append('    %s %s %s %s (%s)%s,' % \
            (style.SQL_FIELD(connection.ops.quote_name(f.m2m_column_name())),
            style.SQL_COLTYPE(models.ForeignKey(model).db_type()),
            style.SQL_KEYWORD('NOT NULL REFERENCES'),
            style.SQL_TABLE(connection.ops.quote_name(opts.db_table)),
            style.SQL_FIELD(connection.ops.quote_name(opts.pk.column)),
#            backend.get_deferrable_sql()))
            ''))
        table_output.append('    %s %s %s %s (%s)%s,' % \
            (style.SQL_FIELD(connection.ops.quote_name(f.m2m_reverse_name())),
            style.SQL_COLTYPE(models.ForeignKey(f.rel.to).db_type()),
            style.SQL_KEYWORD('NOT NULL REFERENCES'),
            style.SQL_TABLE(connection.ops.quote_name(f.rel.to._meta.db_table)),
            style.SQL_FIELD(connection.ops.quote_name(f.rel.to._meta.pk.column)),
#            backend.get_deferrable_sql()))
            ''))
        table_output.append('    %s (%s, %s)%s' % \
            (style.SQL_KEYWORD('UNIQUE'),
            style.SQL_FIELD(connection.ops.quote_name(f.m2m_column_name())),
            style.SQL_FIELD(connection.ops.quote_name(f.m2m_reverse_name())),
            tablespace_sql))
        table_output.append(')')
        try: 
            if opts.db_tablespace and backend.supports_tablespaces:
                # f.db_tablespace is only for indices, so ignore its value here.
                table_output.append(backend.get_tablespace_sql(opts.db_tablespace))
        except: # v0.96 compatibility
            pass
        table_output.append(';')
        final_output.append('\n'.join(table_output))

        # Add any extra SQL needed to support auto-incrementing PKs
        autoinc_sql = ops.get_autoinc_sql(f.m2m_db_table())
        if autoinc_sql:
            for stmt in autoinc_sql:
                final_output.append(stmt)

    return final_output

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

def get_sql_fingerprint_v0_96(app):
    return get_sql_fingerprint(app, management.style)

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
    schema_fingerprint = introspection.get_schema_fingerprint(cursor, app)
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

def get_sql_all(app, style):
    return management.sql_all(app, style)

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
                    available_upgrades.append((vfrom, vto, upgrade, distance))
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

def get_introspected_evolution_options(app, style):
    ops, introspection = get_operations_and_introspection_classes(style)
    from django.db import models, get_introspection_module, connection
    cursor = connection.cursor()
    app_name = app.__name__.split('.')[-2]

    final_output = []

    table_list = get_introspection_module().get_table_list(cursor)
    seen_models = management.installed_models(table_list)
    created_models = set()
    final_output = []
    
    seen_tables = set()

    model_list = models.get_models(app)
    for model in model_list:
        # Create the model's database table, if it doesn't already exist.
        aka_db_tables = set()
        if model._meta.aka:
            for x in model._meta.aka:
                aka_db_tables.add("%s_%s" % (model._meta.app_label, x.lower()))
        if model._meta.db_table in table_list or len(aka_db_tables & set(table_list))>0:
            continue #renamed
        sql, references = fixed_sql_model_create(model, seen_models, style)
        final_output.extend(sql)
        seen_models.add(model)
        created_models.add(model)
        table_list.append(model._meta.db_table)
        seen_tables.add(model._meta.db_table)

    # get the existing models, minus the models we've just created
    app_models = models.get_models(app)
    for model in created_models:
        if model in app_models:
            app_models.remove(model)

    for model in app_models:
        if model._meta.db_table:
            seen_tables.add(model._meta.db_table)
        output, old_table_name = get_sql_evolution_check_for_changed_model_name(model, style)
        if old_table_name: seen_tables.add(old_table_name)
        final_output.extend(output)
        
        rebuild = False
        output = get_sql_evolution_check_for_changed_field_flags(model, old_table_name, style)
        if output and settings.DATABASE_ENGINE == 'sqlite3': rebuild = True
        final_output.extend(output)
    
        output = get_sql_evolution_check_for_changed_field_name(model, old_table_name, style)
        final_output.extend(output)
        if output and settings.DATABASE_ENGINE == 'sqlite3': rebuild = True
        
        output = get_sql_evolution_check_for_new_fields(model, old_table_name, style)
        if output and settings.DATABASE_ENGINE == 'sqlite3': rebuild = True
        final_output.extend(output)
        
        output = get_sql_evolution_check_for_dead_fields(model, old_table_name, style)
        if output and settings.DATABASE_ENGINE == 'sqlite3': rebuild = True
        final_output.extend(output)
        
        if rebuild:
            output = get_sql_evolution_rebuild_table(model, old_table_name, style)
            final_output.extend(output)

    for model in app_models + list(created_models):
        for f in model._meta.many_to_many:
            #creating many_to_many table
            if not f.m2m_db_table() in get_introspection_module().get_table_list(cursor):
                final_output.extend(_get_many_to_many_sql_for_field(model, f, style))
                seen_tables.add(f.m2m_db_table())
    output = get_sql_evolution_check_for_dead_models(table_list, seen_tables, app_name, app_models, style)
    final_output.extend(output)

    return final_output


def save_managed_evolution(app, commands, schema_fingerprint, new_schema_fingerprint):
    from django.conf import settings
    app_name = app.__name__.split('.')[-2]
    
    # find path to app
    se_file = None
    for p in sys.path:
        if os.path.isdir(os.path.join(p, app_name)) and app_name!='deseb':
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
    contents.insert(insertion_point, "    [('%s','%s'), # generated %s\n" % (schema_fingerprint, new_schema_fingerprint, datetime.datetime.now()))
    
    file = open(se_file, 'w')
    file.writelines(contents)
    
def evolvedb(app, interactive=True, do_save=False, do_notify=True, managed_upgrade_only=False):
    from django.db import connection
    cursor = connection.cursor()

    style = color.no_style()
    ops, introspection = get_operations_and_introspection_classes(style)
    app_name = app.__name__.split('.')[-2]
    
    last_schema_fingerprint = None
    seen_schema_fingerprints = set()
    
    fingerprints, evolutions = get_fingerprints_evolutions_from_app(app, style, do_notify)
    if fingerprints and evolutions:
        if do_notify:
            print 'deseb: %s.schema_evolution module found (%i fingerprints, %i evolutions)' % (app_name, len(fingerprints), len(evolutions))

    while True:
        commands = []
        commands_color = []
    
        schema_fingerprint = introspection.get_schema_fingerprint(cursor, app)
        schema_recognized, all_upgrade_paths, available_upgrades, best_upgrade = get_managed_evolution_options(app, schema_fingerprint, style, do_notify)
        if fingerprints and evolutions:
            if schema_recognized:
                if do_notify or interactive: print "deseb: fingerprint for '%s' is '%s' (recognized)" % (app_name, schema_fingerprint)
            else:
                if do_notify or interactive: print "deseb: fingerprint for '%s' is '%s' (unrecognized)" % (app_name, schema_fingerprint)
        managed_upgrade = schema_recognized and available_upgrades and best_upgrade and best_upgrade[3]>0
        if managed_upgrade:
            if do_notify or interactive: 
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
            new_schema_fingerprint = introspection.get_schema_fingerprint(cursor, app)
            
            if schema_fingerprint==new_schema_fingerprint:
                print "schema fingerprint was unchanged - this really shouldn't happen"
            else:
                if commands and not managed_upgrade and (schema_fingerprint,new_schema_fingerprint) not in all_upgrade_paths:
                    if interactive and do_save:
                        confirm = raw_input("do you want to save these commands in %s.schema_evolution?\ntype 'yes' to continue, or 'no' to cancel: " % app_name)
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
                if do_notify: print '\tfingerprint verification successful'
            else:
                if do_notify: print "\tfingerprint verification failed (is '%s'; was expecting '%s')" % (schema_fingerprint, best_upgrade[1])
                break
        
        print
    
        if schema_fingerprint in seen_schema_fingerprints:
            break

