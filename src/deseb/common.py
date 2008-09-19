from django.db.models.base import Model
try:
    import django.core.management.sql as management
    from django.core.management import color
    version = 'trunk'
except ImportError:
    # v0.96 compatibility
    import django.core.management as management
    class no_style:
        def __getattr__(self, attr):
            return lambda x: x
    class color_class:
        def color_style(self):
            return management.style
        def no_style(self):
            return no_style()
    color = color_class()
    version = '0.96'

def get_installed_models(tables):
    if version == 'trunk':
        from django.db import connection
        return connection.introspection.installed_models(tables)
    elif version == '0.97':
        return management.installed_models(tables)
    else:
        return management._get_installed_models(tables)

try: 
    set 
except NameError: 
    from sets import Set as set   # Python 2.3 fallback 

from django.db.models.fields import NOT_PROVIDED, Field
NotProvided = NOT_PROVIDED

def get_operations_and_introspection_classes(style):
    from django.db import backend, connection

    try: # v0.96 compatibility
        v0_96_quote_name = backend.quote_name
        class dummy: pass
        setattr(connection, 'ops', dummy())
        setattr(connection.ops, 'quote_name', v0_96_quote_name)
    except:
        pass
    
    backend_type = str(connection.__class__).split('.')[3]
    if backend_type=='mysql': 
        import deseb.backends.mysql as backend
    elif backend_type=='postgresql': 
        import deseb.backends.postgresql as backend 
    elif backend_type=='postgresql_psycopg2': 
        import deseb.backends.postgresql_psycopg2 as backend 
    elif backend_type=='sqlite3': 
        import deseb.backends.sqlite3 as backend
    else: 
        raise Exception('backend '+ backend_type +' not supported yet - sorry!')
    ops = backend.DatabaseOperations(connection, style)
    introspection = backend.DatabaseIntrospection(connection)
    return ops, introspection

def fixed_sql_model_create(model, known_models, style):
    from django.db import connection
    if version == 'trunk':
        from django.db import connection
        return connection.creation.sql_create_model(model, style, known_models)
    elif version == '0.97':
        return management.sql_model_create(model, style, known_models)
    else:
        return management._get_sql_model_create(model, known_models)

def get_app_models(app):
    from django.db import models
    return models.get_models(app)

def create_field_from_column(app, field):
    class FakeField(Field):
        def db_type(self):
            return field.dbtype
    field = FakeField()
    return 

def create_model_from_table(app, table):
    class FakeModel:
        class Meta:
            app_label = app
        for f in table.fields:
            eval('%s = %s()' % (f.type, ))
    model = FakeModel()         
    return model 

class SQL(object):
    def __init__(self, actions=None):
        if not actions: 
            actions = []
        if isinstance(actions, basestring):
            actions = actions.split('\n')
        self.actions = list(actions)
    
    def __repr__(self):
        sql = unicode(self)
        if len(sql)>10: sql = sql[:6]+'...'
        return "<SQL: %s>" % sql
    
    def __unicode__(self):
        return '\n'.join(self.actions)
    
    def extend(self, sql):
        if isinstance(sql, SQL):
            self.actions.extend(sql.actions)
        else:
            self.actions.extend(sql)
    
    def append(self, sql):
        self.actions.append(sql)

if __name__ == "__main__":
    import doctest
    doctest.testmod