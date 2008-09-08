from deseb.meta import DBSchema

class BaseDatabaseIntrospection(object):
    def __init__(self, connection):
        self.connection = connection
    
    def get_schema_fingerprint(self, cursor, app_name, add_tables):
        """it's important that the output of these methods don't change, otherwise
        the hashes they produce will be inconsistent (and detection of existing
        schemas will fail.  unless you are absolutely sure the output for ALL
        valid inputs will remain the same, you should bump the version"""
        schema = self.get_schema(cursor, app_name, add_tables)
        return 'fv2:'+ schema.get_hash()

    def get_table_names(self, cursor):
        raise NotImplementedError()
    
    def get_schema(self, cursor, app_name, add_tables):
        schema = DBSchema('DB schema')
        table_names = self.get_table_names(cursor)
        for table_name in table_names:
            if table_name.startswith(app_name+"_") or table_name in add_tables:
                table = self.get_table(cursor, table_name)
                schema.tables.append(table)
                table.indexes += self.get_indexes(cursor, table_name)
        return schema
            
    def get_indexes(self, cursor, table_name):
        raise NotImplementedError()
        
    def get_table(self, cursor, table_name):
        raise NotImplementedError()
