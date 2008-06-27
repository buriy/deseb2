from deseb.dbmodel import DBField
from deseb.actions import NotNullColumnNeedsDefaultException
from deseb.dbmodel import DBSchema
from deseb.dbmodel import DBTable
from deseb.dbmodel import DBIndex

class DatabaseOperations:
    
    def quote_value(self, s):
        if type(s) is bool:
            if s: return "'f'"
            else: return "'t'"
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
            kw('ALTER TABLE ')+ tqn(old_table_name) +
            kw(' RENAME TO ')+ tqn(table_name) + ';')
        return output
    
    def get_change_column_name_sql(self, table_name, indexes, old_col_name, new_col_name, col_type, f):
        pk_name = None
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        for key in indexes.keys():
            if indexes[key]['primary_key']: pk_name = key
        output = []
        col_def = fct(col_type)
        if not f.primary_key:
            col_def += ' ' + kw(not f.null and 'NOT NULL' or 'NULL')
        output.append(
            kw('ALTER TABLE ')+ tqn(table_name) +
            kw(' CHANGE COLUMN ')+ fqn(old_col_name) + ' ' +
            fqn(new_col_name) + ' ' + kw(col_def) + ';')
        return output
    
    def get_change_column_def_sql(self, table_name, col_name, col_type, f, column_flags, f_default, updates):
        from django.db.models.fields import NOT_PROVIDED
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fct = self.style.SQL_COLTYPE
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        output = []

        if updates['update_null'] or updates['update_type']:
            if str(f_default)==str(NOT_PROVIDED) and not f.null: 
                details = 'column "%s" of table "%s"' % (col_name, table_name)
                raise NotNullColumnNeedsDefaultException("when modified " + details)
            if str(f_default)!=str(NOT_PROVIDED) and not f.null: 
                output.append(
                    kw('UPDATE ') + tqn(table_name) +
                    kw(' SET ') + fqn(col_name) + ' = ' + fqv(f_default) + 
                    kw(' WHERE ') + fqn(col_name) + kw(' IS NULL;'))

        col_def = fct(col_type)
        if not f.primary_key:
            col_def += ' ' + kw(not f.null and 'NOT NULL' or 'NULL')
        #if f.unique:
        #    col_def += ' ' + kw('UNIQUE')
        #if f.primary_key:
        #    col_def += ' ' + kw('PRIMARY KEY')
        output.append(
            kw('ALTER TABLE ')+ tqn(table_name) +
            kw(' MODIFY COLUMN ')+ fqn(col_name) + ' '+ col_def + ';')
        
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
        field_output = []
        field_output.append(
            kw('ALTER TABLE ') + tqn(table_name) +
            kw(' ADD COLUMN ') + fqn(col_name) + ' ' + fct(col_type))
        if unique:
            field_output.append(kw('UNIQUE'))
        if primary_key:
            field_output.append(kw('PRIMARY KEY'))
        output.append(' '.join(field_output) + ';')
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
            col_def = fct(col_type) + kw(not null and ' NOT NULL' or '')
            #if unique:
            #    col_def += ' '+ kw('UNIQUE')
            #if primary_key:
            #    col_def += ' '+ kw('PRIMARY KEY')
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) +
                kw(' MODIFY COLUMN ') + fqn(col_name) + ' '+
                kw(col_def+';'))
        if unique:
            output.append(
                kw('ALTER TABLE ') + tqn(table_name) + kw(' ADD CONSTRAINT ') +
                table_name + '_' + col_name + '_unique_constraint'+
                kw(' UNIQUE(') + fqn(col_name) + kw(')')+';')
        return output
    
    def get_drop_column_sql(self, table_name, col_name):
        output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        output.append(
             kw('ALTER TABLE ')+ tqn(table_name) 
            +kw(' DROP COLUMN ')+ fqn(col_name) + ';')
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
    

class DatabaseIntrospection:
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint(self, cursor, app_name):
        """it's important that the output of these methods don't change, otherwise
        the hashes they produce will be inconsistent (and detection of existing
        schemas will fail.  unless you are absolutely sure the output for ALL
        valid inputs will remain the same, you should bump the version"""
        schema = self.get_schema(cursor, app_name)
        return 'fv2:'+ schema.get_hash()

    def get_schema(self, cursor, app_name):
        cursor.execute('SHOW TABLES;')
        schema = DBSchema('DB schema')
        table_names = [row[0] for row in cursor.fetchall()]
        for table_name in table_names:
            if not table_name.startswith(app_name):
                continue    # skip tables not in this app
            table = self.get_table(self, cursor, table_name)
            schema.tables.append(table)
            table.indexes += self.get_indexes(cursor, table_name)
        return schema
            
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
                coltype = row[1], 
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
            if row[3]=='FOR': dict['foreign_key'] = True
            if row[3]=='UNI': dict['unique'] = True
            table.fields.append(info)
        # print table_name, column_name, dict
        return table
