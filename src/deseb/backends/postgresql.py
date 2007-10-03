
try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 


class DatabaseOperations:
    
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
    
    pk_requires_unique = False

    def get_change_table_name_sql( self, table_name, old_table_name ):
        output = []
        output.append(self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(old_table_name)) +self.style.SQL_KEYWORD(' RENAME TO ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) + ';')
        return output
    
    def get_change_column_name_sql( self, table_name, indexes, old_col_name, new_col_name, col_type, null, unique, primary_key, default ):
        # TODO: only supports a single primary key so far
        pk_name = None
        for key in indexes.keys():
            if indexes[key]['primary_key']: pk_name = key
        output = []
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' RENAME COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(old_col_name)) +self.style.SQL_KEYWORD(' TO ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(new_col_name)) +';' )
        return output
    
    def get_change_column_def_sql( self, table_name, col_name, col_type, null, unique, primary_key, default ):
        output = []
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ADD COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name+'_tmp')) +' '+ self.style.SQL_KEYWORD(col_type) + ';' )
        output.append( self.style.SQL_KEYWORD('UPDATE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' SET ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name+'_tmp')) +' = '+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) + ';' )
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' DROP COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +';' )
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' RENAME COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name+'_tmp')) +self.style.SQL_KEYWORD(' TO ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) + ';' )
        if default and str(default) != 'django.db.models.fields.NOT_PROVIDED':
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ALTER COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +self.style.SQL_KEYWORD(' SET DEFAULT ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(str(default))) +';' )
        if not null:
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ALTER COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +self.style.SQL_KEYWORD(' SET NOT NULL;') )
        if unique:
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ADD CONSTRAINT ')+ table_name +'_'+ col_name +'_unique_constraint'+self.style.SQL_KEYWORD(' UNIQUE(')+ self.style.SQL_FIELD(col_name) +self.style.SQL_KEYWORD(')')+';' )
        
        return output
    
    def get_add_column_sql( self, table_name, col_name, col_type, null, unique, primary_key, default ):
        output = []
        output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ADD COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +' '+ self.style.SQL_KEYWORD(col_type) + ';' )
        if default and str(default) != 'django.db.models.fields.NOT_PROVIDED':
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ALTER COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +self.style.SQL_KEYWORD(' SET DEFAULT ')+ self.connection.ops.quote_name(str(default)) +';' )
        if not null:
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ALTER COLUMN ')+ self.style.SQL_FIELD(self.connection.ops.quote_name(col_name)) +self.style.SQL_KEYWORD(' SET NOT NULL;') )
        if unique:
            output.append( self.style.SQL_KEYWORD('ALTER TABLE ')+ self.style.SQL_TABLE(self.connection.ops.quote_name(table_name)) +self.style.SQL_KEYWORD(' ADD CONSTRAINT ')+ table_name +'_'+ col_name +'_unique_constraint'+self.style.SQL_KEYWORD(' UNIQUE(')+ self.style.SQL_FIELD(col_name) +self.style.SQL_KEYWORD(')')+';' )
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
        pass
    
    def get_schema_fingerprint_fv1( self, cursor, app):
        pass

    def get_columns( self, cursor, table_name):
        try:
            cursor.execute("SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef), a.attnotnull, a.attnum, pg_catalog.col_description(a.attrelid, a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$') AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum" % table_name)
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
        
    def get_known_column_flags( self, cursor, table_name, column_name ):
    #    print "SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef), a.attnotnull, a.attnum, pg_catalog.col_description(a.attrelid, a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$') AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum" % table_name
        cursor.execute("SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod), (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef), a.attnotnull, a.attnum, pg_catalog.col_description(a.attrelid, a.attnum) FROM pg_catalog.pg_attribute a WHERE a.attrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$') AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum" % table_name)
        dict = {}
        dict['primary_key'] = False
        dict['foreign_key'] = False
        dict['unique'] = False
        dict['default'] = ''
        dict['allow_null'] = False
    
        for row in cursor.fetchall():
            if row[0] == column_name:
    
                # maxlength check goes here
                if row[1][0:17]=='character varying':
                    dict['maxlength'] = row[1][18:len(row[1])-1]
                
                # null flag check goes here
                dict['allow_null'] = not row[3]
    
        # pk, fk and unique checks go here
    #    print "select pg_constraint.conname, pg_constraint.contype, pg_attribute.attname from pg_constraint, pg_attribute where pg_constraint.conrelid=pg_attribute.attrelid and pg_attribute.attnum=any(pg_constraint.conkey) and pg_constraint.conname~'^%s'" % table_name 
        unique_conname = None
        shared_unique_connames = set()
        cursor.execute("select pg_constraint.conname, pg_constraint.contype, pg_attribute.attname from pg_constraint, pg_attribute, pg_class where pg_constraint.conrelid=pg_class.oid and pg_constraint.conrelid=pg_attribute.attrelid and pg_attribute.attnum=any(pg_constraint.conkey) and pg_class.relname='%s'" % table_name )
        for row in cursor.fetchall():
    #        print row
            if row[2] == column_name:
                if row[1]=='p': dict['primary_key'] = True
                if row[1]=='f': dict['foreign_key'] = True
                if row[1]=='u': unique_conname = row[0]
            else:
                if row[1]=='u': shared_unique_connames.add( row[0] )
        if unique_conname and unique_conname not in shared_unique_connames:
            dict['unique'] = True
            
                # default value check goes here
        cursor.execute("select pg_attribute.attname, adsrc from pg_attrdef, pg_attribute WHERE pg_attrdef.adrelid=pg_attribute.attrelid and pg_attribute.attnum=pg_attrdef.adnum and pg_attrdef.adrelid = (SELECT c.oid from pg_catalog.pg_class c where c.relname ~ '^%s$')" % table_name )
        for row in cursor.fetchall():
            if row[0] == column_name:
                if row[1][0:7] == 'nextval': continue
                if row[1][0] == "'":
                    dict['default'] = row[1][1:row[1].index("'",1)]
                else:
                    dict['default'] = row[1]                
        return dict
