from deseb.dbmodel import DBField
from deseb.dbmodel import DBSchema
from deseb.dbmodel import DBTable
import deseb.actions

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

model_create = deseb.actions.fixed_sql_model_create

class DatabaseOperations:
    def quote_value(self, s):
        if type(s) is bool:
            if s: return "'t'"
            else: return "'f'"
        if type(s) is int:
            return str(s)
        else:
            return u"'%s'" % unicode(s).replace("'", "\'")
    
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
    
    pk_requires_unique = True

    def get_change_table_name_sql(self, table_name, old_table_name):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return [kw('ALTER TABLE ') + tqn(old_table_name) +
                kw(' RENAME TO ') + tqn(table_name) + ';']
    
    def get_rebuild_table_sql(self, table_name, indexes, old_columns, renamed_columns):
        # sqlite doesn't support column renames, so we fake it
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fld = self.style.SQL_FIELD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        app, model = self.get_model_from_table_name(table_name)
        assert model, "Model for table %s was not found" % table_name
        output = []
        output.append('-- FYI: so we create a new ' + qn(table_name) +' and delete the old ')
        output.append('-- FYI: this could take a while if you have a lot of data') 
    
        tmp_table_name = table_name + '_1337_TMP' # unlikely to produce a namespace conflict
        output.extend(self.get_change_table_name_sql(tmp_table_name, table_name))
        from django.db import models
        referenced_tables = app and set(models.get_models(app)) or set()
        output.extend(model_create(model, referenced_tables, self.style)[0])
        old_cols = []
        for f in model._meta.fields:
            if f.column in old_columns:
                old_cols.append(fqn(f.column))
            elif f.column in renamed_columns:
                old_cols.append(fqn(renamed_columns[f.column]))
            else:
                NOT_PROVIDED = 'django.db.models.fields.NOT_PROVIDED'
                default = f.default
                if default is None or str(default) == NOT_PROVIDED or callable(default):
                    default = ''
                old_cols.append(fqv(default))

        output.append(kw('INSERT INTO ') + tqn(table_name) + 
                      kw(' SELECT ') + fld(','.join(old_cols)) + 
                      kw(' FROM ') + tqn(tmp_table_name) +';')
        output.append(kw('DROP TABLE ') + tqn(tmp_table_name) +';')
    
        return output
    
    def get_change_column_name_sql(self, table_name, indexes, old_col_name, new_col_name, col_type, f):
        # sqlite doesn't support column modifications, so we fake it
        model = self.get_model_from_table_name(table_name)
        if not model: 
            return ['-- model not found']
        output = []
        output.append('-- FYI: sqlite does not support renaming columns')
        return output

    def get_change_column_def_sql(self, table_name, col_name, col_type, f, column_flags, f_default, updates):
        # sqlite doesn't support column modifications, so we fake it
        app, model = self.get_model_from_table_name(table_name)
        if not model: 
            return ['-- model not found']
        output = []
        output.append('-- FYI: sqlite does not support changing columns')
        return output
    
    def get_add_column_sql(self, table_name, col_name, col_type, null, unique, primary_key, default):
        # versions >= sqlite 3.2.0, see http://www.sqlite.org/lang_altertable.html
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        if unique or primary_key or not null:
            output.append('-- FYI: sqlite does not support adding primary keys or unique or not null fields')
        else:
            output.append(' '.join(
            [ kw('ALTER TABLE'), tqn(table_name), 
              kw('ADD COLUMN'), fqn(col_name), fct(col_type), 'NULL']))
        return output
    
    def get_drop_column_sql(self, table_name, col_name):
        output = []
        output.append('-- FYI: sqlite does not support deleting columns')
        return output
    
    def get_drop_table_sql(self, delete_tables):
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        for table_name in delete_tables:
            output.append(
                kw('DROP TABLE ')+ tqn(table_name) + ';')
        return output

    def get_autoinc_sql(self, table):
        return None
    
    def get_model_from_table_name(self, table_name):
        from django.db import models
        for app in models.get_apps():
            app_name = app.__name__.split('.')[-2]
            for model in models.get_models(app):
                if model._meta.db_table == table_name:
                    return app, model
        return None, None
    
class DatabaseIntrospection:
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint(self, cursor, app_name):
        schema = self.get_schema(cursor, app_name)
        return 'fv2:'+ schema.get_hash()
    
    def get_schema(self, cursor, app_name):
        schema = DBSchema('DB schema')
        cursor.execute("select * from sqlite_master where type='table' order by name;")
        table_names = [row[1] for row in cursor.fetchall()]
        for table_name in table_names:
            if not table_name.startswith(app_name):
                continue    # skip tables not in this app
            table = self.get_table(cursor, table_name)
            schema.tables.append(table)
            #table.indexes += self.get_indexes(cursor, table_name)
        return schema

    def get_table(self, cursor, table_name):
        table = DBTable(name = table_name)
        qn = self.connection.ops.quote_name
        cursor.execute("PRAGMA table_info(%s)" % qn(table_name))
        for row in cursor.fetchall():
            column = DBField(
                name = row[1], 
                primary_key = False, 
                foreign_key = False, 
                unique = False, 
                allow_null = False, 
                max_length = None
            )
            table.fields.append(column)
            col = column.traits
            col_type = row[2]
    
                # maxlength check goes here
            col['coltype'] = col_type
            if row[2][0:7]=='varchar':
                col['max_length'] = int(row[2][8:-1])
                col['coltype'] = 'varchar'

                # f_default flag check goes here
            col['allow_null'] = (row[3]==0)
                
        cursor.execute("select sql from sqlite_master where name=%s;" % qn(table_name))
        for row in cursor.fetchall():
            table_description = [ s.strip() for s in row[0].split('\n')[1:-1] ]
            for column_description in table_description:
                #print table_name, "::", column_description
                if not column_description.startswith('"'): continue
                colname = column_description.split('"',2)[1]
                col = table.get_field(colname).traits
                col['primary_key'] = ' PRIMARY KEY' in column_description
                col['foreign_key'] = ' REFERENCES ' in column_description
                col['unique'] = ' UNIQUE' in column_description
        return table
