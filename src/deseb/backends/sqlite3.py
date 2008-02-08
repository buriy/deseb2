import deseb.schema_evolution

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

model_create = deseb.schema_evolution.fixed_sql_model_create

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
        model = self.get_model_from_table_name(table_name)
        output = []
        output.append('-- FYI: so we create a new ' + qn(table_name) +' and delete the old ')
        output.append('-- FYI: this could take a while if you have a lot of data') 
    
        tmp_table_name = table_name + '_1337_TMP' # unlikely to produce a namespace conflict
        output.extend(self.get_change_table_name_sql(tmp_table_name, table_name))
        output.extend(model_create(model, self.get_all_models_in_app_from_table_name(table_name), self.style)[0])
    
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
    
    def get_change_column_name_sql( self, table_name, indexes, old_col_name, new_col_name, col_type, f ):
        # sqlite doesn't support column modifications, so we fake it
        qn = self.connection.ops.quote_name
        model = self.get_model_from_table_name(table_name)
        if not model: 
            return ['-- model not found']
        output = []
        output.append('-- FYI: sqlite does not support renaming columns')
        return output

    def get_change_column_def_sql(self, table_name, col_name, col_type, f, column_flags, f_default, updates):
        # sqlite doesn't support column modifications, so we fake it
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fld = self.style.SQL_FIELD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        model = self.get_model_from_table_name(table_name)
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

    def get_all_models_in_app_from_table_name(self, table_name):
        #print 'table_name', table_name
        from django.db import models
        for app in models.get_apps():
            app_name = app.__name__.split('.')[-2]
            if table_name.startswith(app_name):
                for model in models.get_models(app):
                    if model._meta.db_table == table_name:
                        return set(models.get_models(app))
        return set()

    
class DatabaseIntrospection:
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint(self, cursor, app):
        """it's important that the output of these methods don't change, otherwise the hashes they
        produce will be inconsistent (and detection of existing schemas will fail.  unless you are 
        absolutely sure the outout for ALL valid inputs will remain the same, you should bump the version by creating a new method"""
        return self.get_schema_fingerprint_fv1(cursor, app)
    
    def get_schema_fingerprint_fv1(self, cursor, app):
        from django.db import models
        app_name = app.__name__.split('.')[-2]
    
        schema = ['app_name := '+ app_name]
    
        cursor.execute("select * from sqlite_master where type='table' order by name;")
        for row in cursor.fetchall():
            table_name = row[1]
            if not table_name.startswith(app_name):
                continue    # skip tables not in this app
            table_description = [ s.strip() for s in row[4].split('\n')[1:-1] ]
            table_description.sort()
            schema.append('table_name := '+ table_name)
            for s in table_description:
                schema.append('\t'+s)
        
        schema_string = '\n'.join(schema)
        #print 'schema_string', schema_string
        return 'fv1:'+ str(schema_string.__hash__())

    def get_columns(self, cursor, table_name):
        try:
            qn = self.connection.ops.quote_name
            cursor.execute("PRAGMA table_info(%s)" % qn(table_name))
            return [row[1] for row in cursor.fetchall()]
        except:
            return []
        
    def get_known_column_flags(self, cursor, table_name, column_name):
        import django.db.models.fields
        qn = self.connection.ops.quote_name
        cursor.execute("PRAGMA table_info(%s)" % qn(table_name))
        dict = {}
        dict['primary_key'] = False
        dict['foreign_key'] = False
        dict['unique'] = False
        dict['allow_null'] = True
        
        for row in cursor.fetchall():
    #        print row
            if row[1] == column_name:
                col_type = row[2]
    
                # maxlength check goes here
                if row[2][0:7]=='varchar':
                    dict['max_length'] = row[2][8:len(row[2])-1]
                    dict['coltype'] = 'varchar'
                else:
                    dict['coltype'] = col_type
                # f_default flag check goes here
                dict['allow_null'] = row[3]==0
                
        cursor.execute("select sql from sqlite_master where name=%s;" % qn(table_name))
        for row in cursor.fetchall():
            table_description = [ s.strip() for s in row[0].split('\n')[1:-1] ]
            for column_description in table_description:
                if column_description.startswith('"'+column_name+'"'):
                    dict['primary_key'] = column_description.find('PRIMARY KEY')>-1
        
    #    print dict
        return dict
