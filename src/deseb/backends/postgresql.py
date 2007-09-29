
try: set 
except NameError: from sets import Set as set   # Python 2.3 fallback 


class DatabaseOperations:
    
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
    
    pk_requires_unique = False

    def get_change_table_name_sql( self, table_name, old_table_name ):
        pass
    
    def get_change_column_name_sql( self, table_name, indexes, old_col_name, new_col_name, col_def ):
        pass
    
    def get_change_column_def_sql( self, table_name, col_name, col_type, null, unique, primary_key, default ):
        pass
    
    def get_add_column_sql( self, table_name, col_name, col_type, null, unique, primary_key, default ):
        pass
    
    def get_drop_column_sql( self, table_name, col_name ):
        pass
    
    def get_drop_table_sql( self, delete_tables):
        pass
    

class DatabaseIntrospection:
    
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint( self, cursor, app):
        pass
    
    def get_schema_fingerprint_fv1( self, cursor, app):
        pass

    def get_columns( self, cursor, table_name):
        pass
        
    def get_known_column_flags( self, cursor, table_name, column_name ):
        pass
