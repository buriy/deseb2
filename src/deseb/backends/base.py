from deseb.builder import get_field_default
from deseb.common import SQL, fixed_sql_model_create as model_create
from deseb.meta import DBSchema
from deseb.meta import DBTable
from django.db.models.loading import get_models

class BaseDatabaseOperations(object):
    def __init__(self, connection, style):
        self.connection = connection
        self.style = style
        
    def get_create_table_sql_old(self, table):
        app, model = self.get_model_from_table_name(table.name)
        if not model:
            raise Exception("Model for table %s was not found" % table.name)
        referenced_tables = app and set(get_models(app)) or set()
        return SQL(model_create(model, referenced_tables, self.style)[0])
    
    def get_create_table_sql(self, table):
        from django.db import models
        known_models = {}
        style = self.style
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fld = self.style.SQL_FIELD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        final_output = []
        table_output = []
        pending_references = {}
        for f in opts.local_fields:
            col_type = f.db_type()
            tablespace = f.db_tablespace or opts.db_tablespace
            if col_type is None:
                # Skip ManyToManyFields, because they're not represented as
                # database columns in this table.
                continue
            # Make the definition (e.g. 'foo VARCHAR(30)') for this field.
            field_output = [style.SQL_FIELD(qn(f.column)),
                style.SQL_COLTYPE(col_type)]
            field_output.append(style.SQL_KEYWORD('%sNULL' % (not f.null and 'NOT ' or '')))
            if f.primary_key:
                field_output.append(style.SQL_KEYWORD('PRIMARY KEY'))
            elif f.unique:
                field_output.append(style.SQL_KEYWORD('UNIQUE'))
            if tablespace and f.unique:
                # We must specify the index tablespace inline, because we
                # won't be generating a CREATE INDEX statement for this field.
                field_output.append(self.connection.ops.tablespace_sql(tablespace, inline=True))
            if f.rel:
                ref_output, pending = self.sql_for_inline_foreign_key_references(f, known_models, style)
                if pending:
                    pass#pr = pending_references.setdefault(f.rel.to, []).append((model, f))
                else:
                    field_output.extend(ref_output)
            table_output.append(' '.join(field_output))
        #if opts.order_with_respect_to:
        #    table_output.append(style.SQL_FIELD(qn('_order')) + ' ' + \
        #        style.SQL_COLTYPE(models.IntegerField().db_type()) + ' ' + \
        #        style.SQL_KEYWORD('NULL'))
        #for field_constraints in opts.unique_together:
        #    table_output.append(style.SQL_KEYWORD('UNIQUE') + ' (%s)' % \
        #        ", ".join([style.SQL_FIELD(qn(opts.get_field(f).column)) for f in field_constraints]))

        full_statement = [style.SQL_KEYWORD('CREATE TABLE') + ' ' + style.SQL_TABLE(qn(opts.db_table)) + ' (']
        for i, line in enumerate(table_output): # Combine and add commas.
            full_statement.append('    %s%s' % (line, i < len(table_output)-1 and ',' or ''))
        full_statement.append(')')
        if opts.db_tablespace:
            full_statement.append(self.connection.ops.tablespace_sql(opts.db_tablespace))
        full_statement.append(';')
        final_output.append('\n'.join(full_statement))

        if opts.has_auto_field:
            # Add any extra SQL needed to support auto-incrementing primary keys.
            auto_column = opts.auto_field.db_column or opts.auto_field.name
            autoinc_sql = self.connection.ops.autoinc_sql(opts.db_table, auto_column)
            if autoinc_sql:
                for stmt in autoinc_sql:
                    final_output.append(stmt)

        return final_output
    
    def get_rebuild_table_sql(self, left, right, renames):
        """
        Renames: right => left
        """
        old_names = [f.name for f in left.fields]

        # used instead of column renames, additions and removals
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        fld = self.style.SQL_FIELD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        fqn = lambda s: self.style.SQL_FIELD(qn(s))
        fqv = lambda s: self.style.SQL_FIELD(self.quote_value(s))
        sql = SQL('-- FYI: next few lines could take a while if you have a lot of data') 
    
        tmp_table_name = right.name + '_1337_TMP' # unlikely to produce a namespace conflict
        temp = DBTable(tmp_table_name)
        sql.extend(self.get_change_table_name_sql(left, temp))
        sql.extend(self.get_create_table_sql(right))
        updated = []
        for f in right.fields:
            if f.name in renames:
                updated.append(fqn(renames[f.name])) # copy renamed column
            elif f.name in old_names:
                updated.append(fqn(f.name)) # copy column
            else:
                default = get_field_default(f, '') # add column with default value set
                updated.append(fqv(default))

        sql.append(kw('INSERT INTO ') + 
                   tqn(right.name) + 
                   kw(' SELECT ') + 
                   fld(','.join(updated)) + 
                   kw(' FROM ') + 
                   tqn(tmp_table_name) +';')
        sql.append(self.get_drop_table_sql(temp))
        return sql
        
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
                try:
                    table.indexes += self.get_indexes(cursor, table_name)
                except IndexError:
                    pass
        return schema
            
    def get_indexes(self, cursor, table_name):
        raise NotImplementedError()
        
    def get_table(self, cursor, table_name):
        raise NotImplementedError()
