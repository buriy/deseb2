from deseb.backends.sqlite3 import RebuildTableNeededException
from deseb.builder import build_model_schema
from deseb.common import fixed_sql_model_create, SQL, management, get_installed_models
from deseb.common import get_operations_and_introspection_classes
from deseb.meta import DBField, DBIndex, TreeDiff, DBTable, DBEntity, DBSchema
from deseb.storage import get_model_aka, get_table_aka

DEBUG = False

class NotNullColumnNeedsDefaultException(Exception): pass
class MultipleRenamesPossibleException(Exception): pass

def get_introspection_module():
    from django.db import connection
    return connection.introspection

def get_creation_module():
    from django.db import connection
    return connection.creation

def get_sql_indexes_for_field(model, f, style):
    "Returns the CREATE INDEX SQL statement for a single field"
    from django.db import backend, connection
    output = SQL()
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
    
class Actions(object):
    types = DBEntity
    def __init__(self, object, style):
        if self.types and not isinstance(object, self.types):
            raise Exception("Not compatible object passed")
        self.object = object #DBTable
        self.style = style
        
    def process(self, changes):
        commands = []
        for change in changes:
            print ' ', repr(change) 
            method = getattr(self, 'do_'+change.action())
            output = method(change)
            if output is None: 
                raise Exception("Method %s.%s returned nothing." % (method.__class__, method.__name__))
            if isinstance(output, SQL):
                commands.append((change, output))
            else:
                commands.extend(output)
                
        return commands

class FieldActions(Actions):
    types = DBField
    def do_add(self, change):            
        return SQL('-- add property')
    def do_remove(self, change):
        return SQL('-- remove property')
#       change, self.ops.get_drop_column_sql([change.left.name])
    def do_change(self, change):
        return SQL('-- update property')
    def do_rename(self, change):
        return SQL('-- rename table')
#       change, self.ops.get_change_column_sql(change.left.name, change.right.name)

class TableActions(Actions):
    types = DBTable 
    def __init__(self, table, style):
        super(TableActions, self).__init__(table, style)
        self.ops, _introspection = get_operations_and_introspection_classes(style)
        _app, self.model = self.ops.get_model_from_table_name(table.name)
    
    def do_add(self, change):
        if isinstance(change.right, DBField):
            #model_field = self.model._meta.get_field(change.right.name)
            #change.right.dbtype = model_field.db_type() 
            #change.right.default = model_field.default
            return self.ops.get_add_column_sql(self.object, change.right)
        elif isinstance(change.right, DBIndex):
            return SQL('-- add index')

    def do_update(self, change):
        updates = set()
        for attr in change.nested:
            updates.add(attr.klass)
        print 'UPD:', updates
        #model_field = self.model._meta.get_field(change.right.name)
        #change.right.dbtype = model_field.db_type() 
        #change.right.default = model_field.default
        return self.ops.get_change_column_def_sql(self.object, change.left, change.right, updates)
        #return FieldActions(change.left, self.style).process(change.nested)
        
    def do_rename(self, change):
        return self.ops.get_change_column_name_sql(self.object, change.left, change.right)
        
    def do_remove(self, change):
        return self.ops.get_drop_column_sql(self.object, change.left.name)

class SchemaActions(Actions):
    types = DBSchema 
    def __init__(self, schema, style):
        super(SchemaActions, self).__init__(schema, style)
        self.ops, _introspection = get_operations_and_introspection_classes(style)

    def do_add(self, change):
        _app, model = self.ops.get_model_from_table_name(change.right.name)
        if model:
            sql, _refs = fixed_sql_model_create(model, {}, self.style)
        else:
            #probably m2m model 
            #raise Exception("Internal error. Model to add is not found")
            print change.right.fields[1]
            
            creation = get_creation_module()
            creation.sql_for_many_to_many_field(self.object,  )
             
        return SQL(sql)

    def do_remove(self, change):
        return self.ops.get_drop_table_sql(change.left)
    
    def do_update(self, change):
        try:
            return TableActions(change.left, self.style).process(change.nested)
        except RebuildTableNeededException:
            renames = {}
            for nest in change.nested:
                if nest.action() == 'rename':
                    renames[nest.right.name] = nest.left.name 
            return self.ops.get_rebuild_table_sql(change.left, change.right, renames)

    def do_rename(self, change):
        sql = self.ops.get_change_table_name_sql(change.left.name, change.right.name)
        if change.nested:
            sql.append(self.do_update(change))
        sql.extend()

def get_possible_app_models(cursor, app_name):
    table_list = get_introspection_module().get_table_list(cursor)
    seen_models = get_installed_models(table_list)
    app_models = []
    for m in seen_models:
        if m._meta.app_label == app_name and m._meta.db_table:
            app_models.append(m._meta.db_table)
            app_models.extend(get_model_aka(m)) 
    return app_models

def show_evolution_plan(cursor, app, style):
    _ops, introspection = get_operations_and_introspection_classes(style)

    model_schema = build_model_schema(app)
    app_name = app.__name__.split('.')[-2]
    app_models = get_possible_app_models(cursor, app_name)
    db_schema = introspection.get_schema(cursor, app_name, app_models)
    db_schema.name = 'Current DB'
    diff = TreeDiff(db_schema, model_schema)
    return unicode(diff)

def get_installed_tables(app, model_schema = None):
    app_name = app.__name__.split('.')[-2]
    if model_schema is None:
        model_schema = build_model_schema(app)
    add_tables = set()
    for model in model_schema.tables:
        add_tables.add(model.name)
        add_tables.update(get_table_aka(app_name, model.name))
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
    output = []
    actions = SchemaActions(model_schema, style).process(diff.changes)
    for _change, sql in actions:
        output.extend(sql.actions)
    return output
