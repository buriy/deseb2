from deseb.backends.base import BaseDatabaseIntrospection
from deseb.backends.base import BaseDatabaseOperations
from deseb.common import NotProvided
from deseb.common import SQL
from deseb.meta import DBField
from deseb.meta import DBIndex
from deseb.meta import DBTable
from deseb.dbtypes import get_column_type

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

class RebuildTableNeededException(Exception): pass

class DatabaseOperations(BaseDatabaseOperations):
    def quote_value(self, s):
        if type(s) is bool:
            if s: return u"'t'"
            else: return u"'f'"
        if type(s) is int:
            return unicode(s)
        else:
            return u"'%s'" % unicode(s).replace("'", "\'")
    
    def get_change_table_name_sql(self, left, right):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(kw('ALTER TABLE ') + tqn(left.name) +
                kw(' RENAME TO ') + tqn(right.name) + ';')

    def get_change_column_name_sql(self, table, left, right):
        raise RebuildTableNeededException("sqlite does not support renaming columns")

    def get_change_column_def_sql(self, table, left, right, updates):
        raise RebuildTableNeededException("sqlite does not support altering columns")
    
    def get_add_column_sql(self, table, column):
        # versions >= sqlite 3.2.0, see http://www.sqlite.org/lang_altertable.html
        table_name = table.name
        col_name = column.name
        null = column.allow_null
        unique = column.unique
        primary_key = column.primary_key
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        if unique or primary_key:
            raise RebuildTableNeededException("sqlite does not support adding primary keys or unique fields")
        if (not null) and (column.default is NotProvided):
            raise RebuildTableNeededException("sqlite does not support adding not null fields")
        else:
            null_sql = null and 'NULL' or 'NOT NULL'
            parts = [ 
                kw('ALTER TABLE'), tqn(table_name), 
                kw('ADD COLUMN'), fqn(col_name), fct(column.dbtype), null_sql]
            if not null:
                parts += ['DEFAULT', fqv(column.default)]
        return SQL(' '.join(parts)+';')
    
    def get_drop_column_sql(self, table, column):
        raise RebuildTableNeededException("sqlite does not support deleting columns")
    
    def get_drop_table_sql(self, table):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(
            kw('DROP TABLE ')+ tqn(table.name) + ';')

    def get_autoinc_sql(self, table):
        return None
    
    def get_model_from_table_name(self, table_name):
        from django.db import models
        for app in models.get_apps():
            #app_name = app.__name__.split('.')[-2]
            for model in models.get_models(app):
                if model._meta.db_table == table_name:
                    return app, model
        return None, None
    
class DatabaseIntrospection(BaseDatabaseIntrospection):
    def __init__(self, connection):
        self.connection = connection
    
    def get_table_names(self, cursor):
        cursor.execute("select * from sqlite_master where type='table' order by name;")
        return [row[1] for row in cursor.fetchall()]

    def get_indexes(self, cursor, table_name):
        qn = self.connection.ops.quote_name
        cursor.execute("PRAGMA index_list(%s);" % qn(table_name))
        indexes = []
        for row in cursor.fetchall():
            #print table_name, row
            if row[2] == 1: continue # sqlite_autoindex_* indexes
            cursor.execute("PRAGMA index_info(%s)" % qn(row[1]))
            columns = cursor.fetchall()
            if len(columns)>1: continue
            #print table_name, row, '=>', columns
            index = DBIndex(
                pk = False,
                name = columns[0][2],
                full_name = row[1],
                unique = False
            )
            indexes.append(index)
        return indexes
    
    def get_table(self, cursor, table_name):
        table = DBTable(name = table_name)
        qn = self.connection.ops.quote_name
        
        cursor.execute("PRAGMA table_info(%s)" % qn(table_name))
        for row in cursor.fetchall():
            info = DBField(
                name = row[1], 
                primary_key = False, 
                foreign_key = None,
                unique = False, 
                allow_null = False,
                coltype = get_column_type(row[2])
            )
            table.fields.append(info)
            col = info.traits

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
                #col['foreign_key'] = ' REFERENCES ' in column_description or None
                col['unique'] = ' UNIQUE' in column_description or ' UNIQUE' in column_description  
        return table