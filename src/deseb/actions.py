from deseb.backends.sqlite3 import RebuildTableNeededException
from deseb.builder import build_model_schema
from deseb.common import SQL
from deseb.common import get_operations_and_introspection_classes
from deseb.meta import DBField, DBIndex, TreeDiff, DBTable, DBEntity, DBSchema
from deseb.storage import get_table_aka

DEBUG = False

class NotNullColumnNeedsDefaultException(Exception): pass
class MultipleRenamesPossibleException(Exception): pass

#def get_introspection_module():
#    from django.db import connection
#    return connection.introspection

#def get_creation_module():
#    from django.db import connection
#    return connection.creation

class Actions(object):
    parents = DBEntity
    def __init__(self, parent, style):
        if self.parents and not isinstance(parent, self.parents):
            raise Exception("Not compatible parent passed")
        self.object = parent #DBTable
        self.style = style
        
    def process(self, changes):
        commands = []
        for change in changes:
            if DEBUG: print ' ', repr(change) 
            method = getattr(self, 'do_'+change.action())
            output = method(change)
            if output is None: 
                raise Exception("Method %s.%s returned nothing." % (self.__class__.__name__, method.__name__))
            if isinstance(output, SQL):
                commands.append((change, output))
            else:
                commands.extend(output)
                
        return commands

class PropertyActions(Actions):
    parents = DBField
    def do_add(self, change):            
        return SQL('-- add property')
    def do_remove(self, change):
        return SQL('-- remove property')
    def do_change(self, change):
        return SQL('-- update property')
    def do_rename(self, change):
        return SQL('-- rename property')

class FieldActions(Actions):
    parents = DBTable 
    def __init__(self, table, style):
        super(FieldActions, self).__init__(table, style)
        self.ops, _introspection = get_operations_and_introspection_classes(style)
        self.side_effects = []
    
    def do_add(self, change):
        return self.ops.get_add_column_sql(self.object, change.right)

    def do_update(self, change):
        #print 'update fields:\n', unicode(change)
        updates = set()
        for attr in change.nested:
            updates.add(attr.klass)
        if self.ops.get_column_index_rebuild_needed(self.object, change.left, change.right, updates):
            self.side_effects.append(('REMOVED INDEX', change.left.name))
        sql = self.ops.get_change_column_def_sql(self.object, change.left, change.right, updates)
        return sql
        
    def do_rename(self, change):
        #print 'rename fields:\n', unicode(change)
        sql = self.ops.get_change_column_name_sql(self.object, change.left, change.right)
        if change.nested and self.ops.smart_rename_available:
            sql.extend(self.do_update(change))
        return sql
        
    def do_remove(self, change):
        self.side_effects.append(('REMOVED INDEX', change.left.name))
        return self.ops.get_drop_column_sql(self.object, change.left)

class IndexActions(Actions):
    parents = DBTable 
    def __init__(self, table, style):
        super(IndexActions, self).__init__(table, style)
        self.ops, _introspection = get_operations_and_introspection_classes(style)
    
    def do_add(self, change):
        if not self.object.get_field(change.right.name):
            #print "can't add index %s_%s" % (self.object.name, change.right.name)
            return SQL()
        return self.ops.get_create_index_sql(self.object, change.right)

    def do_remove(self, change):
        #if not self.object.get_field(change.left.name):
        #    print "can't remove index %s_%s" % (self.object.name, change.left.name)
        #    return SQL()
        return self.ops.get_drop_index_sql(self.object, change.left)

    def do_rename(self, change):
        sql = self.do_remove(change)
        sql.extend(self.do_add(change))
        return sql
        
    def do_update(self, change):
        return self.do_rename(change)

class TableActions(Actions):
    parents = DBSchema 
    def __init__(self, schema, style):
        super(TableActions, self).__init__(schema, style)
        self.ops, _introspection = get_operations_and_introspection_classes(style)

    def do_add(self, change):
        sql = self.ops.get_create_table_sql(change.right)
        sql.extend(self.ops.get_create_table_indexes_sql(change.right))
        return sql
    def do_remove(self, change):
        return self.ops.get_drop_table_sql(change.left)
    
    def do_rebuild(self, change):
        renames = {}
        for nest in change.nested:
            if nest.action() == 'rename' and issubclass(nest.get_type(), DBField):
                renames[nest.right.name] = nest.left.name
        return self.ops.get_rebuild_table_sql(change.left, change.right, renames)
    
    def do_try_update(self, change):
        flds = [c for c in change.nested if issubclass(c.get_type(), DBField)]
        fld_acts = FieldActions(change.right, self.style)
        fld_cmds = fld_acts.process(flds)
        idxs_removed = set([n for op, n in fld_acts.side_effects if op == 'REMOVED INDEX'])
        #print 'removed for', change.left.name, '->', change.right.name, ':', idxs_removed
        real_indexes = DBTable(name = change.left.name, aka = change.left.aka)
        for n, idx in change.left.indexes.items():
            if not n in idxs_removed:
                real_indexes.indexes.append(idx)
        idxs_diff = TreeDiff(real_indexes, change.right)
        #print 'Indexes diff:', unicode(idxs_diff.changes)
        if idxs_diff:
            idxs = [c for c in idxs_diff.changes if issubclass(c.get_type(), DBIndex)]
            #print 'diff:', [c.left.full_name for c in idxs if c.left]
        idx_cmds = IndexActions(change.right, self.style).process(idxs)
        return fld_cmds + idx_cmds

    def do_update(self, change):
        try:
            return self.do_try_update(change)
        except RebuildTableNeededException:
            return self.do_rebuild(change)

    def do_rename(self, change):
        try:
            sql = SQL()
            sql.extend(self.ops.get_change_table_name_sql(change.left, change.right))
            if change.nested:
                commands = [(change, sql)]
                commands.extend(self.do_try_update(change))
                return commands
        except RebuildTableNeededException:
            return self.do_rebuild(change)
        return sql

#app_models = get_possible_app_models(cursor, app_name)
#def get_possible_app_models(cursor, app_name):
#    table_list = get_introspection_module().get_table_list(cursor)
#    seen_models = get_installed_models(table_list)
#    app_models = []
#    for m in seen_models:
#        if m._meta.app_label == app_name and m._meta.db_table:
#            app_models.append(m._meta.db_table)
#            app_models.extend(get_model_aka(m)) 
#    return app_models

def get_installed_tables(app, model_schema):
    app_name = app.__name__.split('.')[-2]
    if model_schema is None: raise Exception("No model_schema given")
    add_tables = set()
    for name, _model in model_schema.tables.items():
        add_tables.add(name)
        add_tables.update(get_table_aka(app_name, name))
    return add_tables

def get_schemas(cursor, app, style, db_schema=None, model_schema=None):
    _ops, introspection = get_operations_and_introspection_classes(style)
    app_name = app.__name__.split('.')[-2]
    if model_schema is None:
        model_schema = build_model_schema(app)
    add_tables = get_installed_tables(app, model_schema)
    if db_schema is None:
        db_schema = introspection.get_schema(cursor, app_name, add_tables)
        db_schema.name = 'Current DB'
    return db_schema, model_schema

def show_evolution_plan(cursor, app, style, db_schema, model_schema):
    diff = TreeDiff(db_schema, model_schema)
    return unicode(diff)

def get_introspected_evolution_options(app, style, db_schema, model_schema):
    app_name = app.__name__.split('.')[-2]
    if DEBUG: print '-'*55
    if DEBUG: print 'Application "%s":' % app_name
    diff = TreeDiff(db_schema, model_schema)
    output = []
    actions = TableActions(model_schema, style).process(diff.changes)
    for _change, sql in actions:
        output.extend(sql.actions)
    return output
