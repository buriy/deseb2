from deseb.actions import NotNullColumnNeedsDefaultException
from deseb.meta import DBField
from deseb.meta import DBIndex
from deseb.meta import DBTable
from deseb.backends.base import BaseDatabaseIntrospection
from deseb.common import SQL, NotProvided
from deseb.builder import get_field_type

class DatabaseOperations:
    def quote_value(self, s):
        if type(s) is bool:
            if s: return "'t'"
            else: return "'f'"
        if type(s) is int:
            return str(s)
        else:
            return u"'%s'" % unicode(s).replace("'","\'")
    
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
    
    pk_requires_unique = False

    def get_change_table_name_sql(self, left, right):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(
            kw('ALTER TABLE ') + tqn(left.name) +
            kw(' RENAME TO ') + tqn(right.name) + ';')
    
    def get_change_column_name_sql(self, table, left, right):
        # TODO: only supports a single primary key so far
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        return SQL(
            kw('ALTER TABLE ') + tqn(table.name)
            + kw(' RENAME COLUMN ') + fqn(left.name)
            + kw(' TO ') + fqn(right.name) + ';')

    def get_change_column_def_sql(self, table, left, right, updates):
        table_name = table.name
        col_name = right.name
        sql = SQL()
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        if 'coltype' in updates:
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ADD COLUMN ') + fqn(col_name+'_tmp') + ' ' + fct(right.dbtype) + ';')
            sql.append(
                kw('UPDATE ') + tqn(table_name) + 
                kw(' SET ') + fqn(col_name+'_tmp') + 
                ' = ' + fqn(col_name) + ';')
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' DROP COLUMN ') + fqn(col_name) + ';')
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' RENAME COLUMN ') + fqn(col_name+'_tmp') + 
                kw(' TO ') + fqn(col_name) + ';')
        elif left.max_length != right.max_length:
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' ALTER COLUMN ') + fqn(col_name) + 
                kw(' TYPE ')+ fct(right.dbtype) + ';')
        if 'sequence' in updates:
            seq_name = left.sequence
            seq_name_correct = right.sequence
            if seq_name != seq_name_correct:
                sql.append(
                    kw('ALTER TABLE ') + tqn(seq_name) +
                    kw(' RENAME TO ') + tqn(seq_name_correct)+';')
                sql.append(
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + tqn(col_name) + 
                    kw(' SET DEFAULT nextval(')+
                    fqv(seq_name_correct)+'::regclass);')

        if 'null' in updates:
            if right.default is NotProvided and not right.allow_null: 
                details = 'column "%s" of table "%s"' % (col_name, table_name)
                raise NotNullColumnNeedsDefaultException("when modified " + details)
            if not right.default is NotProvided and not right.allow_null: 
                sql.append(
                    kw('UPDATE ') + tqn(table_name) +
                    kw(' SET ') + fqn(col_name) + ' = ' + fqv(right.default) + 
                    kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))
            if not right.allow_null:
                sql.append(
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + fqn(col_name) +
                    kw(' SET NOT NULL;'))
            elif not 'update_type' in updates:
                sql.append(
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + fqn(col_name) +
                    kw(' DROP NOT NULL;'))

        if 'unique' in updates and right.unique:
            sql.append(kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';')
            
        return sql
    
    def get_add_column_sql(self, table, column):
        # versions >= sqlite 3.2.0, see http://www.sqlite.org/lang_altertable.html
        table_name = table.name, 
        col_name = column.name
        sql = SQL()
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        sql.append(
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' ADD COLUMN ') + fqn(col_name) + ' ' + fct(column.dbtype) + ';')
        if column.primary_key: 
            return sql
        if column.default is NotProvided and not column.allow_null: 
            details = 'column "%s" into table "%s"' % (col_name, table_name)
            raise NotNullColumnNeedsDefaultException("when added " + details)
        if not column.default is NotProvided and not column.allow_null: 
            sql.append(
                kw('UPDATE ') + tqn(table_name) +
                kw(' SET ') + fqn(col_name) + ' = ' + fqv(column.default) +
                kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))
        if not column.allow_null:
            sql.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ALTER COLUMN ') + fqn(col_name) +
                kw(' SET NOT NULL;'))
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
            kw('ALTER TABLE ') + tqn(table.name) +
            kw(' DROP COLUMN ') + fqn(column.name) + ';')
    
    def get_drop_table_sql(self, table):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(kw('DROP TABLE ')+ tqn(table.name) + ' CASCADE;')
    
    def get_autoinc_sql(self, table):
        return None
    

class DatabaseIntrospection(BaseDatabaseIntrospection):
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_table_names(self, cursor):
        cursor.execute('SELECT table_name FROM information_schema.tables')
        return [row[0] for row in cursor.fetchall()]
    
    def get_indexes(self, cursor, table_name):
        # This query retrieves each index on the given table, including the
        # first associated field name
        cursor.execute("""
            SELECT attr.attname, idx.indkey, idx.indisunique, idx.indisprimary
            FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
                pg_catalog.pg_index idx, pg_catalog.pg_attribute attr
            WHERE c.oid = idx.indrelid
                AND idx.indexrelid = c2.oid
                AND attr.attrelid = c.oid
                AND attr.attnum = idx.indkey[0]
                AND c.relname = %s""", [table_name])
        indexes = []
        for row in cursor.fetchall():
            # row[1] (idx.indkey) is stored in the DB as an array. It comes out as
            # a string of space-separated integers. This designates the field
            # indexes (1-based) of the fields that have indexes on the table.
            # Here, we skip any indexes across multiple fields.
            if ' ' in row[1]:
                continue
            if not row[3]:
                index = DBIndex(name = table_name+'_'+row[0], pk=row[3], unique=row[2])
                indexes.append(index)
        return indexes

    def get_table(self, cursor, table_name):
        table = DBTable(name = table_name)
        cursor.execute("SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), "
                       "(SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d "
                       "WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef), "
                       "a.attnotnull, a.attnum, pg_catalog.col_description(a.attrelid, a.attnum) "
                       "FROM pg_catalog.pg_attribute a WHERE a.attrelid = (SELECT c.oid "
                       "from pg_catalog.pg_class c where c.relname ~ '^%s$') "
                       "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum" % table_name)
        for row in cursor.fetchall():
            column = DBField(
                name = row[0], 
                primary_key = False,
                foreign_key = False,
                unique = False,
                dbtype = row[1],
                coltype = get_field_type(row[1]), 
                allow_null = False,
                max_length = None
            )
            table.fields.append(column)
            col = column.traits
            col['allow_null'] = not row[3]
            if row[1][0:17]=='character varying':
                col['max_length'] = int(row[1][18:-1])
            if row[1][0:7]=='varchar':
                col['max_length'] = int(row[1][8:-1])
            elif row[1] == 'text':
                col['max_length'] = 1000000000
                # null flag check goes here
        cursor.execute("""
            select pg_constraint.conname, pg_constraint.contype, pg_attribute.attname 
            from pg_constraint, pg_attribute, pg_class 
            where pg_constraint.conrelid=pg_class.oid and 
            pg_constraint.conrelid=pg_attribute.attrelid and 
            pg_attribute.attnum=all(pg_constraint.conkey) and 
            not(pg_constraint.contype = 'c') and 
            pg_class.relname = %s
            """, [table_name])
        for row in cursor.fetchall():
            col = table.get_field(row[2]).traits
            if row[1]=='p': col['primary_key'] = True
            if row[1]=='f': col['foreign_key'] = True
            if row[1]=='u': col['unique']= True
        for field in table.fields:
            if field.primary_key:
                field.foreign_key = False
        # default value check
        cursor.execute("select pg_attribute.attname, adsrc from pg_attrdef, pg_attribute "
                       "WHERE pg_attrdef.adrelid=pg_attribute.attrelid and "
                       "pg_attribute.attnum=pg_attrdef.adnum and "
                       "pg_attrdef.adrelid = (SELECT c.oid "
                       "from pg_catalog.pg_class c where c.relname ~ '^%s$')" % table_name)
        
        for row in cursor.fetchall():
            col = table.get_field(row[0]).traits
            if row[1][0:7] == 'nextval': 
                if row[1].startswith("nextval('") and row[1].endswith("'::regclass)"):
                    col['sequence'] = row[1][9:-12]
        return table
