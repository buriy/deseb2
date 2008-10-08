from deseb.actions import NotNullColumnNeedsDefaultException
from deseb.backends.base import BaseDatabaseIntrospection
from deseb.backends.base import BaseDatabaseOperations
from deseb.common import SQL, NotProvided
from deseb.meta import DBField
from deseb.meta import DBIndex
from deseb.meta import DBTable
from deseb.dbtypes import get_column_type
from deseb.backends.sqlite3 import RebuildTableNeededException

class DatabaseOperations(BaseDatabaseOperations):
    def quote_value(self, s):
        if type(s) is bool:
            if s: return "'1'"
            else: return "'0'"
        if type(s) is int:
            return str(s)
        else:
            return u"'%s'" % unicode(s).replace("'","\'")

    def get_change_table_name_sql(self, left, right):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(
            kw('ALTER TABLE ')+ tqn(left.name) +
            kw(' RENAME TO ')+ tqn(right.name) + ';')
    
    smart_rename_available = False
    
    def get_change_column_name_sql(self, table, left, right):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        col_def = fct(right.dbtype)
        if right.unique:
            col_def += " UNIQUE"
        if not right.primary_key:
            col_def += ' ' + kw(not right.allow_null and 'NOT NULL' or 'NULL')
        return SQL(
            kw('ALTER TABLE ')+ tqn(table.name) +
            kw(' CHANGE COLUMN ')+ fqn(left.name) + ' ' +
            fqn(right.name) + ' ' + kw(col_def) + ';')
    
    def get_change_column_def_sql(self, table, left, right, updates):
        table_name = table.name
        col_name = right.name

        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        sql = SQL()

        if 'primary_key' in updates and right.coltype.attrs.get('auto_increment',False):
            raise RebuildTableNeededException("mysql can't add auto_increment field")

        if 'null' in updates or 'coltype' in updates:
            if left.allow_null and not right.allow_null:
                if right.default is NotProvided: 
                    details = 'column "%s" of table "%s"' % (col_name, table_name)
                    raise NotNullColumnNeedsDefaultException("when modified " + details)
                sql.append(
                    kw('UPDATE ') + tqn(table_name) +
                    kw(' SET ') + fqn(col_name) +
                    kw(' = ') + fqv(right.default) + 
                    kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))

        col_def = fct(right.dbtype)
        if not right.primary_key:
            col_def += ' ' + kw(not right.allow_null and 'NOT NULL' or 'NULL')
        if right.unique:
            col_def += ' ' + kw('UNIQUE')
        #if right.primary_key:
        #    col_def += ' ' + kw('PRIMARY KEY')
        sql.append(
            kw('ALTER TABLE ')+ tqn(table_name) +
            kw(' MODIFY COLUMN ')+ fqn(col_name) + ' '+ col_def + ';')
        
        return sql
    
    def get_add_column_sql(self, table, column):
        # versions >= sqlite 3.2.0, see http://www.sqlite.org/lang_altertable.html
        table_name = table.name
        col_name = column.name
        default = column.default
        sql = SQL()
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        field_output = []
        field_output.append(
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' ADD COLUMN ') + fqn(column.name) + ' ' + fct(column.dbtype))
        if column.unique:
            field_output.append(kw('UNIQUE'))
        if column.primary_key and column.coltype.attrs.get('auto_increment',False):
            raise RebuildTableNeededException("mysql can't add auto_increment field")
        if column.primary_key:
            field_output.append(kw('PRIMARY KEY'))
        sql.append(' '.join(field_output) + ';')
        if column.primary_key: return sql
        #if default is NotProvided and not column.allow_null: 
        #    details = 'column "%s" into table "%s"' % (col_name, table_name)
        #    raise NotNullColumnNeedsDefaultException("when added " + details)
        if not default is NotProvided and not column.allow_null:
            sql.append(
                kw('UPDATE ') + tqn(table_name) +
                kw(' SET ') + fqn(col_name) + ' = ' + fqv(default) +
                kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))
        if not column.allow_null:
            col_def = fct(column.dbtype) + kw(not column.allow_null and ' NOT NULL' or '')
            #if column.unique:
            #    col_def += ' '+ kw('UNIQUE')
            #if primary_key:
            #    col_def += ' '+ kw('PRIMARY KEY')
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' MODIFY COLUMN ') + fqn(col_name) + ' '+
                kw(col_def+';'))
        #if column.unique:
        #    sql.append(
        #        kw('ALTER TABLE ') + tqn(table_name) + kw(' ADD CONSTRAINT ') +
        #        table_name + '_' + col_name + '_unique_constraint'+
        #        kw(' UNIQUE(') + fqn(col_name) + kw(')')+';')
        return sql
    
    def get_drop_index_sql(self, table, idx):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(
             kw('ALTER TABLE ')+ tqn(table.name) 
            +kw(' DROP INDEX ')+ tqn(idx.full_name) + ';')

    def get_drop_column_sql(self, table, column):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        return SQL(
             kw('ALTER TABLE ')+ tqn(table.name) 
            +kw(' DROP COLUMN ')+ fqn(column.name) + ';')
    
    def get_drop_table_sql(self, table):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(kw('DROP TABLE ')+ tqn(table.name) + ';')

    def get_autoinc_sql(self, table):
        return None
    
class DatabaseIntrospection(BaseDatabaseIntrospection):
    
    def __init__(self, connection):
        self.connection = connection
   
    def get_table_names(self, cursor):
        cursor.execute('SHOW TABLES;')
        return [row[0] for row in cursor.fetchall()]
    
    def get_indexes(self, cursor, table_name):
        indexes = []
        qn = self.connection.ops.quote_name
        cursor.execute("SHOW INDEX FROM %s" % qn(table_name))
        for row in cursor.fetchall():
            #print 'I:', table_name, row
            if row[2] == 'PRIMARY': continue
            if row[1] == 0 and row[2] == row[4]: continue #unique
            index = DBIndex(name=row[4],
                            unique = not row[1],
                            full_name = row[2])
            indexes.append(index)
        return indexes
        
    def get_table(self, cursor, table_name):
        table = DBTable(name=table_name)
        cursor.execute("describe %s" % self.connection.ops.quote_name(table_name))
        for row in cursor.fetchall():
            #print 'T:', table_name, row
            column_name = row[0]
            coltype = row[1]
            if row[5]=='auto_increment':
                coltype += ' AUTO_INCREMENT'
            info = DBField(
                name = column_name,
                coltype = get_column_type(coltype), 
                primary_key = False,
                foreign_key = None,
                unique = False,
                allow_null = False
            )

            if row[2]=='YES': 
                info.allow_null = True
            
            if row[3]=='PRI': info.primary_key = True
            #if row[3]=='FOR': info.foreign_key = True
            if row[3]=='UNI': info.unique = True
            #if row[3]=='UNI': print 'unique:', row
            table.fields.append(info)
        # print table_name, column_name, info.traits
        return table
