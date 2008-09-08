from deseb.actions import NotNullColumnNeedsDefaultException
from deseb.meta import DBField
from deseb.meta import DBIndex
from deseb.meta import DBTable
from deseb.backends.base import BaseDatabaseIntrospection

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

    def get_change_table_name_sql(self, table_name, old_table_name):
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        output.append(
            kw('ALTER TABLE ') + tqn(old_table_name) +
            kw(' RENAME TO ') + tqn(table_name) + ';')
        return output
    
    def get_change_column_name_sql(self, table_name, indexes, old_col_name, new_col_name, col_type, f):
        # TODO: only supports a single primary key so far
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        for key in indexes.keys():
            if indexes[key]['primary_key']: pk_name = key
        output = []
        output.append(
            kw('ALTER TABLE ') + tqn(table_name)
            + kw(' RENAME COLUMN ') + fqn(old_col_name)
            + kw(' TO ') + fqn(new_col_name) + ';')
        return output

    def get_change_column_def_sql(self, db_flags, model_flags, updates, table_name, f_default):
        col_name = model_flags.name
        col_type = model_flags.coltype
        from django.db.models.fields import NOT_PROVIDED
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        if updates['update_type']:
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ADD COLUMN ') + fqn(col_name+'_tmp') + ' ' + fct(col_type) + ';')
            output.append(
                kw('UPDATE ') + tqn(table_name) + 
                kw(' SET ') + fqn(col_name+'_tmp') + 
                ' = ' + fqn(col_name) + ';')
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' DROP COLUMN ') + fqn(col_name) + ';')
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' RENAME COLUMN ') + fqn(col_name+'_tmp') + 
                kw(' TO ') + fqn(col_name) + ';')
        elif updates['update_length']:
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + 
                kw(' ALTER COLUMN ') + fqn(col_name) + 
                kw(' TYPE ')+ fct(col_type) + ';')

        if updates['update_sequences'] and db_flags and db_flags.traits.has_key('sequence'):
            seq_name = db_flags.sequence
            seq_name_correct = model_flags.sequence
            if seq_name != seq_name_correct:
                output.append(
                    kw('ALTER TABLE ') + tqn(seq_name) +
                    kw(' RENAME TO ') + tqn(seq_name_correct)+';')
                output.append(
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + tqn(col_name) + 
                    kw(' SET DEFAULT nextval(')+
                    fqv(seq_name_correct)+'::regclass);')

        if updates['update_null']:
            if str(f_default)==str(NOT_PROVIDED) and not model_flags.allow_null: 
                details = 'column "%s" of table "%s"' % (col_name, table_name)
                raise NotNullColumnNeedsDefaultException("when modified " + details)
            if str(f_default)!=str(NOT_PROVIDED) and not model_flags.allow_null: 
                output.append(
                    kw('UPDATE ') + tqn(table_name) +
                    kw(' SET ') + fqn(col_name) + ' = ' + fqv(f_default) + 
                    kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))
            if not model_flags.allow_null:
                output.append(
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + fqn(col_name) +
                    kw(' SET NOT NULL;'))
            elif not updates['update_type']:
                output.append(
                    kw('ALTER TABLE ') + tqn(table_name) +
                    kw(' ALTER COLUMN ') + fqn(col_name) +
                    kw(' DROP NOT NULL;'))

        if updates['update_unique'] and model_flags.unique:
            output.append(kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';')
            
        return output
    
    def get_add_column_sql(self, table_name, col_name, col_type, null, unique, primary_key, f_default):
        from django.db.models.fields import NOT_PROVIDED
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE 
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        output.append(
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' ADD COLUMN ') + fqn(col_name) + ' ' + fct(col_type) + ';')
        if primary_key: return output
        if str(f_default)==str(NOT_PROVIDED) and not null: 
            details = 'column "%s" into table "%s"' % (col_name, table_name)
            raise NotNullColumnNeedsDefaultException("when added " + details)
        if str(f_default)!=str(NOT_PROVIDED) and not null: 
            output.append(
                kw('UPDATE ') + tqn(table_name) +
                kw(' SET ') + fqn(col_name) + ' = ' + fqv(f_default) +
                kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))
        if not null:
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' ALTER COLUMN ') + fqn(col_name) +
                kw(' SET NOT NULL;'))
        if unique:
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';')
        return output
    
    def get_drop_column_sql(self, table_name, col_name):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        output = []
        output.append(
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' DROP COLUMN ') + fqn(col_name) + ';')
        return output
    
    def get_drop_table_sql(self, delete_tables):
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        for table_name in delete_tables:
            output.append(
                kw('DROP TABLE ')+ tqn(table_name) + ' CASCADE;')
        return output
    
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
                allow_null = False,
                max_length = None
            )
            table.fields.append(column)
            col = column.traits
            col['allow_null'] = not row[3]
            col['coltype'] = row[1]
            if row[1][0:17]=='character varying':
                col['max_length'] = int(row[1][18:-1])
                col['coltype'] = 'varchar'
            if row[1][0:7]=='varchar':
                col['max_length'] = int(row[1][8:-1])
                col['coltype'] = 'varchar'
            elif row[1][0:4]=='text':
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
