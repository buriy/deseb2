from deseb.actions import NotNullColumnNeedsDefaultException
from deseb.backends.base import BaseDatabaseIntrospection
from deseb.backends.base import BaseDatabaseOperations
from deseb.builder import get_field_type
from deseb.common import SQL, NotProvided
from deseb.meta import DBField
from deseb.meta import DBIndex
from deseb.meta import DBTable

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
    
    def get_change_column_name_sql(self, table, left, right):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        col_def = fct(right.dbtype)
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

        if 'null' in updates or 'type' in updates:
            if right.default is NotProvided and not right.allow_null: 
                details = 'column "%s" of table "%s"' % (col_name, table_name)
                raise NotNullColumnNeedsDefaultException("when modified " + details)
            if not right.default is NotProvided and not right.allow_null: 
                sql.append(
                    kw('UPDATE ') + tqn(table_name) +
                    kw(' SET ') + fqn(col_name) + ' = ' + fqv(right.default) + 
                    kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))

        col_def = fct(right.dbtype)
        if not right.primary_key:
            col_def += ' ' + kw(not right.allow_null and 'NOT NULL' or 'NULL')
        #if right.unique:
        #    col_def += ' ' + kw('UNIQUE')
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
            kw(' ADD COLUMN ') + fqn(column.name) + ' ' + fct(column.type))
        if column.unique:
            field_output.append(kw('UNIQUE'))
        if column.primary_key:
            field_output.append(kw('PRIMARY KEY'))
        sql.append(' '.join(field_output) + ';')
        if column.primary_key: return sql
        if default is NotProvided and not column.allow_null: 
            details = 'column "%s" into table "%s"' % (col_name, table_name)
            raise NotNullColumnNeedsDefaultException("when added " + details)
        if not default is NotProvided and not column.allow_null:
            sql.append(
                kw('UPDATE ') + tqn(table_name) +
                kw(' SET ') + fqn(col_name) + ' = ' + fqv(default) +
                kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))
        if not column.allow_null:
            col_def = fct(column.type) + kw(not column.allow_null and ' NOT NULL' or '')
            #if unique:
            #    col_def += ' '+ kw('UNIQUE')
            #if primary_key:
            #    col_def += ' '+ kw('PRIMARY KEY')
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' MODIFY COLUMN ') + fqn(col_name) + ' '+
                kw(col_def+';'))
        if column.unique:
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) + kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';')
        return sql
    
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
            index = DBIndex(name=row[0])
            indexes.append(index)
        return indexes
        
    def get_table(self, cursor, table_name):
        table = DBTable(name=table_name)
        cursor.execute("describe %s" % self.connection.ops.quote_name(table_name))
        for row in cursor.fetchall():
            column_name = row[0]
            info = DBField(
                name = column_name,
                dbtype = row[1],
                coltype = get_field_type(row[1]), 
                primary_key = False,
                foreign_key = False,
                unique = False,
                allow_null = False,
                max_length = None
            )
            dict = info.traits
            # maxlength check goes here
            if row[1][0:7]=='varchar':
                dict['max_length'] = int(row[1][8:len(row[1])-1])
            elif row[1]=='text':
                dict['max_length'] = 65534
            elif row[1]=='longtext':
                dict['max_length'] = 100000000
            
            # f_default flag check goes here
            if row[2]=='YES': dict['allow_null'] = True
            else: dict['allow_null'] = False
            
            # primary/foreign/unique key flag check goes here
            if row[3]=='PRI': dict['primary_key'] = True
            #if row[3]=='FOR': dict['foreign_key'] = True
            if row[3]=='UNI': dict['unique'] = True
            table.fields.append(info)
        # print table_name, column_name, dict
        return table
