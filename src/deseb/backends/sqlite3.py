import deseb.schema_evolution

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

model_create = deseb.schema_evolution._get_sql_model_create

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
    
    pk_requires_unique = True

    def get_change_table_name_sql( self, table_name, old_table_name ):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tbl = lambda s: self.style.SQL_TABLE(qn(s))
        return [kw('ALTER TABLE ')+ tbl(old_table_name) +
                kw(' RENAME TO ') + tbl(table_name) + ';']
    
    def get_change_column_name_sql( self, table_name, indexes, old_col_name, new_col_name, col_def, f ):
        # sqlite doesn't support column renames, so we fake it
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fld = self.style.SQL_FIELD
        tbl = lambda s: self.style.SQL_TABLE(qn(s))
        model = self.get_model_from_table_name(table_name)
        output = []
        output.append( '-- FYI: sqlite does not support renaming columns, so we create a new '
                       + qn(table_name) 
                       +' and delete the old  (ie, this could take a while)' )
    
        tmp_table_name = table_name + '_1337_TMP' # unlikely to produce a namespace conflict
        output.extend( self.get_change_table_name_sql( tmp_table_name, table_name ) )
        output.extend( model_create(model, set(), self.style)[0] )
    
        old_cols = []
        for f in model._meta.fields:
            if f.column != new_col_name:
                old_cols.append( qn(f.column) )
            else: 
                old_cols.append( qn(old_col_name) )
    
        output.append( kw('INSERT INTO ')+ tbl(table_name) +kw(' SELECT ')
                       + fld(','.join(old_cols)) +kw(' FROM ')+ tbl(tmp_table_name) +';' )
        output.append( kw('DROP TABLE ')+ tbl(tmp_table_name) +';' )
    
        return output
    
    def get_change_column_def_sql( self, table_name, col_name, col_type, f, column_flags, f_default, updates ):
        # sqlite doesn't support column modifications, so we fake it
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fld = self.style.SQL_FIELD
        tbl = lambda s: self.style.SQL_TABLE(qn(s))
        model = self.get_model_from_table_name(table_name)
        if not model: 
            return ['-- model not found']
        output = []
        output.append( '-- FYI: sqlite does not support changing columns, so we create a new '
                       + qn(table_name) +' and delete the old '
                       +'(ie, this could take a while)' )
    
        tmp_table_name = table_name + '_1337_TMP' # unlikely to produce a namespace conflict
        output.extend( self.get_change_table_name_sql( tmp_table_name, table_name ) )
        output.extend( model_create(model, set(), self.style)[0] )
    
        old_cols = []
        for f in model._meta.fields:
            old_cols.append( qn(f.column) )
    
        output.append( kw('INSERT INTO ')+ tbl(table_name) +kw(' SELECT ')
                       + fld(','.join(old_cols)) +kw(' FROM ')+ tbl(tmp_table_name) +';' )
        output.append( kw('DROP TABLE ')+ tbl(tmp_table_name) +';' )
    
        return output
    
    def get_add_column_sql( self, table_name, col_name, col_type, null, unique, primary_key, f_default ):
        output = []
        field_output = []
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tbl = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        field_output.append(kw('ALTER TABLE') + tbl(table_name))
        field_output.append(kw('ADD COLUMN') + fqn(col_name))
        field_output.append(col_type)
        field_output.append(kw('%sNULL' % (not null and 'NOT ' or '')))
        if unique or primary_key:
            field_output.append(kw('UNIQUE'))
        if primary_key:
            field_output.append(kw('PRIMARY KEY'))
        if f_default!=None and str(f_default) != 'django.db.models.fields.NOT_PROVIDED':
            field_output.append(kw('DEFAULT'))
            field_output.append(qn(str(f_default)))
        output.append(' '.join(field_output) + ';')
        return output
    
    def get_drop_column_sql( self, table_name, col_name ):
        model = self.get_model_from_table_name(table_name)
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tbl = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        output = []
        output.append( '-- FYI: sqlite does not support deleting columns, so we create a new '
                       + qn(table_name) +' and delete the old  (ie, this could take a while)' )
        tmp_table_name = table_name + '_1337_TMP' # unlikely to produce a namespace conflict
        output.extend( self.get_change_table_name_sql( tmp_table_name, table_name ) )
        output.extend( model_create(model, set(), self.style)[0] )
        new_cols = []
        for f in model._meta.fields:
            new_cols.append( qn(f.column) )
        output.append(
            kw('INSERT INTO ')+ tbl(table_name) +
            kw(' SELECT ') + fqn(','.join(new_cols)) +
            kw(' FROM ')+ tbl(tmp_table_name) +';' )
        output.append( 
            kw('DROP TABLE ')+ tbl(tmp_table_name) +';' )
        return output
    
    def get_drop_table_sql( self, delete_tables):
        return []

    def get_autoinc_sql(self, table):
        return None
    
    def get_model_from_table_name(self, table_name):
        from django.db import models
        for app in models.get_apps():
            app_name = app.__name__.split('.')[-2]
            if table_name.startswith(app_name):
                for model in models.get_models(app):
                    if model._meta.db_table == table_name:
                        return model
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
            qn = self.connection.ops.quote_name
            cursor.execute("PRAGMA table_info(%s)" % qn(table_name))
            return [row[1] for row in cursor.fetchall()]
        except:
            return []
        
    def get_known_column_flags( self, cursor, table_name, column_name ):
        import django.db.models.fields
        qn = self.connection.ops.quote_name
        cursor.execute("PRAGMA table_info(%s)" % qn(table_name))
        dict = {}
        dict['primary_key'] = False
        dict['foreign_key'] = False
        dict['unique'] = False
        dict['default'] = ''
        dict['allow_null'] = True
    
        for row in cursor.fetchall():
    #        print row
            if row[1] == column_name:
                col_type = row[2]
    
                # maxlength check goes here
                if row[2][0:7]=='varchar':
                    dict['maxlength'] = row[2][8:len(row[2])-1]
                    dict['coltype'] = 'varchar'
                else:
                    dict['coltype'] = col_type
                # f_default flag check goes here
                dict['allow_null'] = row[3]==0
                
                # f_default value check goes here
                dict['default'] = row[4]
                if not dict['default']:
                    dict['default'] = django.db.models.fields.NOT_PROVIDED
    
        cursor.execute("PRAGMA index_list(%s)" % qn(table_name))
        index_names = []
        for row in cursor.fetchall():
            index_names.append(row[1])
        for index_name in index_names:
            cursor.execute("PRAGMA index_info(%s)" % qn(index_name))
            for row in cursor.fetchall():
                if row[2]==column_name:
                    if col_type=='integer': dict['primary_key'] = True  # sqlite3 does not distinguish between unique and pk; all 
                    else: dict['unique'] = True                         # unique integer columns are treated as part of the pk.
    
                # primary/foreign/unique key flag check goes here
                #if row[3]=='PRI': dict['primary_key'] = True
                #else: dict['primary_key'] = False
                #if row[3]=='FOR': dict['foreign_key'] = True
                #else: dict['foreign_key'] = False
                #if row[3]=='UNI': dict['unique'] = True
                #else: dict['unique'] = False
                
    
    #    print dict
        return dict
