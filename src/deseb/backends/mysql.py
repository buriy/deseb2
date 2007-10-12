
try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 


class DatabaseOperations:
    
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
    
    pk_requires_unique = False

    def get_change_table_name_sql( self, table_name, old_table_name ):
        return [self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(old_table_name)) +self.style.SQL_KEYWORD(' RENAME TO ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) + ';']
    
    def get_change_column_name_sql( self, table_name, indexes, old_col_name, new_col_name, col_type, f ):
        pk_name = None
        for key in indexes.keys():
            if indexes[key]['primary_key']: pk_name = key
        output = []
        col_def = col_type +' '+ self.style.SQL_KEYWORD('%sNULL' % (not f.null and 'NOT ' or ''))
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name))
                       +self.style.SQL_KEYWORD(' CHANGE COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(old_col_name)) 
                       +' '+ self.style.SQL_FIELD(self.connection.ops.quote_name(new_col_name)) +' '
                       + self.style.SQL_KEYWORD(col_def) + ';' )
        return output
    
    def get_change_column_def_sql( self, table_name, col_name, col_type, f, column_flags ):
        output = []
        col_def = col_type +' '+ self.style.SQL_KEYWORD('%sNULL' % (not f.null and 'NOT ' or ''))
        if f.unique:
            col_def += ' '+ self.style.SQL_KEYWORD('UNIQUE')
        if f.primary_key:
            col_def += ' '+ self.style.SQL_KEYWORD('PRIMARY KEY')
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' MODIFY COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +' '+ col_def + ';' )
        if f.default and str(f.default) != 'django.db.models.fields.NOT_PROVIDED' and f.default!=column_flags['default']:
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ALTER COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) + self.style.SQL_KEYWORD(' SET DEFAULT ')+ "'" + str(f.default) + '\';' )
        elif column_flags['default'] and (not f.default or str(f.default) == 'django.db.models.fields.NOT_PROVIDED'):
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ALTER COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) + self.style.SQL_KEYWORD(' DROP DEFAULT') +';' )
        return output
    
    def get_add_column_sql( self, table_name, col_name, col_type, null, unique, primary_key, default ):
        output = []
        field_output = []
        field_output.append(self.style.SQL_KEYWORD('ALTER TABLE'))
        field_output.append(self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)))
        field_output.append(self.style.SQL_KEYWORD('ADD COLUMN'))
        field_output.append(self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)))
        field_output.append(col_type)
        field_output.append(self.style.SQL_KEYWORD(('%sNULL' % (not null and 'NOT ' or ''))))
        if unique:
            field_output.append(self.style.SQL_KEYWORD('UNIQUE'))
        if primary_key:
            field_output.append(self.style.SQL_KEYWORD('PRIMARY KEY'))
        if default and str(default) != 'django.db.models.fields.NOT_PROVIDED':
            field_output.append(self.style.SQL_KEYWORD('DEFAULT'))
            if col_type=='integer':
                field_output.append(self.style.SQL_KEYWORD(str(default)))
            else:
                field_output.append((self.connection.ops.quote_name(str(default))))
        output.append(' '.join(field_output) + ';')
        return output
    
    def get_drop_column_sql( self, table_name, col_name ):
        output = []
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' DROP COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) + ';' )
        return output
    
    def get_drop_table_sql( self, delete_tables):
        return []

    def get_autoinc_sql(self, table):
        return None
    

class DatabaseIntrospection:
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint( self, cursor, app):
        """it's important that the output of these methods don't change, otherwise the hashes they
        produce will be inconsistent (and detection of existing schemas will fail.  unless you are 
        absolutely sure the outout for ALL valid inputs will remain the same, you should bump the version by creating a new method"""
        return self.get_schema_fingerprint_fv1(cursor, app)
    
    def get_schema_fingerprint_fv1( self, cursor, app):
        from django.db import models
        app_name = app.__name__.split('.')[-2]
    
        schema = ['app_name := '+ app_name]
    
        cursor.execute('SHOW TABLES;')
        for table_name in [row[0] for row in cursor.fetchall()]:
            if not table_name.startswith(app_name):
                continue    # skip tables not in this app
            schema.append('table_name := '+ table_name)
            cursor.execute("describe %s" % self.connection.ops.quote_name(table_name))
            for row in cursor.fetchall():
                tmp = []
                for x in row:
                    tmp.append(str(x))
                schema.append( '\t'.join(tmp) )
            cursor.execute("SHOW INDEX FROM %s" % self.connection.ops.quote_name(table_name))
            for row in cursor.fetchall():
                schema.append( '\t'.join([ str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5]), str(row[9]), ]) )
            
        return 'fv1:'+ str('\n'.join(schema).__hash__())

    def get_columns( self, cursor, table_name):
        try:
            cursor.execute("describe %s" % self.connection.ops.quote_name(table_name))
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
        
    def get_known_column_flags( self, cursor, table_name, column_name ):
        cursor.execute("describe %s" % self.connection.ops.quote_name(table_name))
        dict = {}
        for row in cursor.fetchall():
            if row[0] == column_name:
    
                # maxlength check goes here
                if row[1][0:7]=='varchar':
                    dict['maxlength'] = row[1][8:len(row[1])-1]
                
                # default flag check goes here
                if row[2]=='YES': dict['allow_null'] = True
                else: dict['allow_null'] = False
                
                # primary/foreign/unique key flag check goes here
                if row[3]=='PRI': dict['primary_key'] = True
                else: dict['primary_key'] = False
                if row[3]=='FOR': dict['foreign_key'] = True
                else: dict['foreign_key'] = False
                if row[3]=='UNI': dict['unique'] = True
                else: dict['unique'] = False
                
                # default value check goes here
                # if row[4]=='NULL': dict['default'] = None
                # else: dict['default'] = row[4]
                dict['default'] = row[4]
                
        # print table_name, column_name, dict
        return dict
