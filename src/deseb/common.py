try:
    import django.core.management.sql as management
    from django.core.management import color
    version = 'trunk'
except ImportError:
    # v0.96 compatibility
    import django.core.management as management
    management.installed_models = management._get_installed_models
    class color_class:
        def color_style(self):
            return management.style
        def no_style(self):
            class no_style:
                def __getattr__(self, attr):
                    return lambda x: x
            return no_style()
    color = color_class()
    version = '0.96'

try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 

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
        return connection.creation.sql_create_model(model, style, known_models)
        return management.sql_model_create(model, style, known_models)
    else:
        return management._get_sql_model_create(model, known_models)

if __name__ == "__main__":
    import doctest
    doctest.testmod