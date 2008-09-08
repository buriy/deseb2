from deseb.common import get_operations_and_introspection_classes
from deseb.common import management
from deseb.common import version
from django.conf import settings
from deseb.builder import compare_field_length, get_field_type, build_model_flags,\
    get_field_default, build_model_schema
from deseb.meta import TreeDiff
from deseb.meta import DBIndex
from deseb.meta import DBField

DEBUG = False

def get_introspection_module():
    from django.db import connection
    return connection.introspection

class NotNullColumnNeedsDefaultException(Exception): pass
class MultipleRenamesPossibleException(Exception): pass

def get_sql_indexes_for_field(model, f, style):
    "Returns the CREATE INDEX SQL statement for a single field"
    from django.db import backend, connection
    output = []
    if f.db_index and not (f.primary_key or f.unique):
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
            style.SQL_KEYWORD('CREATE %sINDEX' % unique) + ' ' + 
            style.SQL_TABLE(connection.ops.quote_name('%s_%s' % (model._meta.db_table, f.column))) + ' ' + 
            style.SQL_KEYWORD('ON') + ' ' + 
            style.SQL_TABLE(connection.ops.quote_name(model._meta.db_table)) + ' ' + 
            "(%s)" % style.SQL_FIELD(connection.ops.quote_name(f.column)) + 
            "%s;" % tablespace_sql
       )
    return output
    
def get_sql_evolution_check_for_new_fields(model, old_table_name, style):
    "checks for model fields that are not in the existing data structure"
    from django.db import connection

    ops, introspection = get_operations_and_introspection_classes(style)
    
    #data_types = connection.creation.data_types
    cursor = connection.cursor()
#    introspection = ops = get_ops_class(connection)
    opts = model._meta
    output = []
    db_table = model._meta.db_table
    if old_table_name: 
        db_table = old_table_name
    existing_fields = introspection.get_table(cursor,db_table).fields
    for f in opts.fields:
        if f.column not in existing_fields and (not f.aka or f.aka not in existing_fields and len(set(f.aka) & set(existing_fields))==0):
            col_type = f.db_type()
            if col_type is not None:
                output.extend(ops.get_add_column_sql(model._meta.db_table, f.column, style.SQL_COLTYPE(col_type), f.null, f.unique, f.primary_key, f.default))
                output.extend(get_sql_indexes_for_field(model, f, style))
    return output

def get_sql_evolution_check_for_changed_model_name(klass, style):
    from django.db import connection

    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
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
    from django.db import connection
    
    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
    opts = klass._meta
    output = []
    db_table = klass._meta.db_table
    if old_table_name: 
        db_table = old_table_name
    for f in opts.fields:
        existing_fields = introspection.get_table(cursor,db_table).fields
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
                output.extend(ops.get_change_column_name_sql(klass._meta.db_table, introspection.get_indexes(cursor,db_table), old_col, f.column, col_type_def, f))
    return output
    
def get_sql_evolution_rebuild_table(klass, old_table_name, style):
    from django.db import connection
    
    ops, introspection = get_operations_and_introspection_classes(style)

    cursor = connection.cursor()
    opts = klass._meta
    output = []
    db_table = klass._meta.db_table
    if old_table_name: 
        db_table = old_table_name

    existing_fields = introspection.get_table(cursor,db_table).fields
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
    
    output.extend(ops.get_rebuild_table_sql(klass._meta.db_table, introspection.get_indexes(cursor,db_table), existing_fields, renamed_fields))
    return output
    
def find_updates(column_flags, model_flags, f, table_name):
    f_col_type = model_flags.coltype
    is_postgresql = settings.DATABASE_ENGINE in ['postgresql', 'postgresql_psycopg2']
    update_length = compare_field_length(f, column_flags)
    update_type = get_field_type(column_flags.coltype) != get_field_type(f_col_type)
    if DEBUG and update_type:
        print get_field_type(column_flags.coltype), '->', get_field_type(f_col_type)
    update_unique = (column_flags.unique != f.unique and not (is_postgresql and f.primary_key))
    update_null = column_flags.allow_null != f.null and not f.primary_key
    update_primary = column_flags.primary_key != f.primary_key
    update_sequences = False
    if column_flags.traits.has_key('sequence'):
        correct_seq_name = table_name+"_"+model_flags.name+'_seq'
        update_sequences = column_flags.sequence != correct_seq_name
    updates = {
        'update_type': update_type,
        'update_length': update_length,
        'update_unique': update_unique,
        'update_null': update_null,
        'update_primary': update_primary,
        'update_sequences': update_sequences,
    }
    return updates

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
        existing_fields = introspection.get_table(cursor,db_table).fields
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
            db_flags = introspection.get_known_column_flags(cursor, db_table, cf)
            model_flags = build_model_flags(f, f_col_type)
            if db_flags.traits.has_key('sequence'):
                model_flags.sequence = klass._meta.db_table+"_"+cf+'_seq' 
            if set(db_flags.items()) != set(model_flags.items()): 
                updates = find_updates(db_flags, model_flags, f, db_table) 
                f_default = get_field_default(f)
                output.extend(ops.get_change_column_def_sql(db_flags, model_flags, updates, db_table, f_default))
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
    suspect_fields = set(introspection.get_table(cursor,db_table).fields)
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

def fixed_sql_model_create(model, known_models, style):
    from django.db import connection
    if version == 'trunk':
        return connection.creation.sql_create_model(model, style, known_models)
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
        if tablespace and backend.supports_tablespaces:
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

def show_evolution_plan(cursor, app, style):
    ops, introspection = get_operations_and_introspection_classes(style)

    model_schema = build_model_schema(app)
    app_name = app.__name__.split('.')[-2]
    table_list = get_introspection_module().get_table_list(cursor)
    seen_models = get_introspection_module().installed_models(table_list)
    app_models = [m._meta.db_table for m in seen_models if m._meta.app_label == app_name and m._meta.db_table]
    db_schema = introspection.get_schema(cursor, app_name, app_models)
    db_schema.name = 'Current DB'
    #print unicode(db_schema)
    #print unicode(model_schema)
    diff = TreeDiff(db_schema, model_schema)
    #print unicode(db_schema)
    #print unicode(model_schema)
    if diff:
        print unicode(diff)
    #import sys
    #sys.exit()

def update_traits(changes, table, style):
    ops, introspection = get_operations_and_introspection_classes(style)
    commands = []
    _app, model = ops.get_model_from_table_name(table.name)
    for change in changes:
        print '   ', repr(change) 
        action = change.action()
        if action == 'add':
            commands.append(
                (change, '[add property]')
            )
        elif action == 'remove':
            commands.append(
                (change, '[remove property]')
#               (change, ops.get_drop_column_sql([change.left.name]))
            )
        elif action == 'update':
            raise 'What?!'
        elif action == 'change':
            commands.append(
                (change, '[update property]')
            )
#        elif action == 'rename':
#            commands.append(
#                (change, ops.get_change_column_sql(change.left.name, change.right.name))
#            )
#            if change.nested:
#                commands.append(
#                    update_table(change.nested, style)
#                )
    return commands    

def update_table(changes, table, style):
    ops, introspection = get_operations_and_introspection_classes(style)
    commands = []
    _app, model = ops.get_model_from_table_name(table.name)
    for change in changes:
        print ' ', repr(change) 
        action = change.action()
        if action == 'add':
            if isinstance(change.right, DBField):
                commands.append(
                    (change, '[add field]')
                )
            elif isinstance(change.right, DBIndex):
#                commands.append(
#                    (change, '[add index]')
#                )
                pass
        elif action == 'remove':
            commands.append(
                (change, '[remove field]')
#               (change, ops.get_drop_column_sql([change.left.name]))
            )
        elif action == 'update':
            if change.nested:
                commands.extend(
                    update_traits(change.nested, change.left, style)
                )
        elif action == 'change':
            commands.append(
                (change, '[update field]')
            )
#        elif action == 'rename':
#            commands.append(
#                (change, ops.get_change_column_sql(change.left.name, change.right.name))
#            )
#            if change.nested:
#                commands.append(
#                    update_table(change.nested, style)
#                )
    return commands    

def update_schema(diff, style):
    ops, introspection = get_operations_and_introspection_classes(style)
    commands = []
    for change in diff.changes:
        action = change.action()
        print repr(change) 
        if action == 'add':
            #print "Adding model "+change.right.name
            _app, model = ops.get_model_from_table_name(change.right.name)
            if not model: continue
            sql, _refs = fixed_sql_model_create(model, {}, style)
            commands.append(
                (change, sql)
            )
        elif action == 'remove':
            _app, model = ops.get_model_from_table_name(change.left.name)
            commands.append(
                (change, ops.get_drop_table_sql([change.left.name]))
            )
        elif action == 'update':
            commands.extend(
                update_table(change.nested, change.left, style)
            )
#        elif action == 'change':
#            commands.append(
#                (change, ops.get_change_column_def_sql)
#            )
        elif action == 'rename':
            commands.append(
                (change, ops.get_change_table_name_sql(change.left.name, change.right.name))
            )
            if change.nested:
                commands.append(
                    update_table(change.nested, style)
                )
    return commands    

def get_installed_tables(app, model_schema = None):
    if model_schema is None:
        model_schema = build_model_schema(app)
    add_tables = set()
    for model in model_schema.tables:
        add_tables.add(model.name)
        add_tables.update(model.aka)
    return add_tables

def get_introspected_evolution_options(app, style):
    from django.db import connection
    _ops, introspection = get_operations_and_introspection_classes(style)
    cursor = connection.cursor()
    app_name = app.__name__.split('.')[-2]
    print '-'*55
    print 'Application "%s":' % app_name

    model_schema = build_model_schema(app)
    
    add_tables = get_installed_tables(app, model_schema)
    
    db_schema = introspection.get_schema(cursor, app_name, add_tables)
    
    diff = TreeDiff(db_schema, model_schema)
    #print unicode(model_schema)
    #print unicode(diff)
    output = []
    for change, sql in update_schema(diff, style):
        output.append(sql)
        #output.extend(sql)
    return output
    
def get_introspected_evolution_options_old(app, style):
    from django.db import models, connection
    ops, introspection = get_operations_and_introspection_classes(style)
    cursor = connection.cursor()
    app_name = app.__name__.split('.')[-2]

    table_list = introspection.get_table_list(cursor)
    seen_models = introspection.installed_models(table_list)
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

        #show_table_evolution_plan(cursor, app, model, style)
        
        output, old_table_name = get_sql_evolution_check_for_changed_model_name(model, style)
        if old_table_name: seen_tables.add(old_table_name)
        final_output.extend(output)
        
        suboutput = []
        output = get_sql_evolution_check_for_changed_field_flags(model, old_table_name, style)
        suboutput.extend(output)
    
        output = get_sql_evolution_check_for_changed_field_name(model, old_table_name, style)
        suboutput.extend(output)
        
        output = get_sql_evolution_check_for_new_fields(model, old_table_name, style)
        suboutput.extend(output)
        
        output = get_sql_evolution_check_for_dead_fields(model, old_table_name, style)
        suboutput.extend(output)
        
        if suboutput and settings.DATABASE_ENGINE == 'sqlite3':
            output = get_sql_evolution_rebuild_table(model, old_table_name, style)
            final_output.extend(suboutput)
            final_output.extend(output)
        else:
            final_output.extend(suboutput)

    for model in app_models + list(created_models):
        for f in model._meta.many_to_many:
            #creating many_to_many table
            if not f.m2m_db_table() in introspection.get_table_list(cursor):
                final_output.extend(_get_many_to_many_sql_for_field(model, f, style))
                seen_tables.add(f.m2m_db_table())
                
    output = get_sql_evolution_check_for_dead_models(table_list, seen_tables, app_name, app_models, style)
    final_output.extend(output)

    return final_output
