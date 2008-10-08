from deseb.builder import get_field_default
from deseb.common import SQL, fixed_sql_model_create as model_create
from deseb.meta import DBSchema
from deseb.meta import DBTable
from django.db.models.loading import get_models
from deseb.common import NotProvided

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
    
    def get_create_index_sql(self, table, index):
        "Returns the CREATE INDEX SQL statement for a single field"
        from django.db import connection
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        output = SQL()
        if not (index.pk or index.unique):
            unique = index.unique and 'UNIQUE ' or ''
            output.append(
                kw('CREATE %sINDEX' % unique) + ' ' + 
                self.style.SQL_TABLE(qn('%s_%s' % (table.name, index.name))) + ' ' + 
                kw('ON') + ' ' + 
                self.style.SQL_TABLE(qn(table.name)) + ' ' + 
                "(%s)" % self.style.SQL_FIELD(qn(index.name)) + 
                ";"
           )
        return output
        
    def get_column_index_rebuild_needed(self, table, left, right, updates):
        return False

    def get_change_column_def_effect(self, table, left, right, updates):
        for i,f in enumerate(table.fields):
            if f.name == right.name:
                table.fields[i] = right #no rename
        if 'coltype' in updates:
            #we created new column
            table.get_index(right.name)

    def get_change_column_name_effect(self, table, left, right):
        del table.fields[left.name]
        table.fields[right.name] = right
        drop = [x for x in table.fields if not x.name == left.name]
        for i,f in enumerate(drop):
            if f.name == right.name:
                table.fields[i] = right #no rename

    def get_drop_index_sql(self, table, index):
        qn = self.connection.ops.quote_name
        kw = self.style.SQL_KEYWORD
        tqn = lambda s: self.style.SQL_TABLE(qn(s))
        return SQL(kw('DROP INDEX ') + tqn(index.full_name) + ';')

    def sql_for_inline_foreign_key_references(self, field, known_models, style):
        "Return the SQL snippet defining the foreign key reference for a field"
        return [], False
        
        qn = self.connection.ops.quote_name
        if field.rel.to in known_models:
            output = [style.SQL_KEYWORD('REFERENCES') + ' ' + \
                style.SQL_TABLE(qn(field.rel.to._meta.db_table)) + ' (' + \
                style.SQL_FIELD(qn(field.rel.to._meta.get_field(field.rel.field_name).column)) + ')' +
                self.connection.ops.deferrable_sql()
            ]
            pending = False
        else:
            # We haven't yet created the table to which this field
            # is related, so save it for later.
            output = []
            pending = True

        return output, pending

    def get_create_table_sql(self, table):
        #known_models = {}
        style = self.style
        qn = self.connection.ops.quote_name
        table_output = []
        #pending_references = {}
        for f in table.fields.values():
            col_type = f.coltype.dbtype
            tablespace = None # f.db_tablespace or table.db_tablespace
            if col_type is None:
                # Skip ManyToManyFields, because they're not represented as
                # database columns in this table.
                continue
            # Make the definition (e.g. 'foo VARCHAR(30)') for this field.
            field_output = [style.SQL_FIELD(qn(f.name)),
                style.SQL_COLTYPE(col_type)]
            field_output.append(style.SQL_KEYWORD('%sNULL' % (not f.allow_null and 'NOT ' or '')))
            if f.primary_key:
                field_output.append(style.SQL_KEYWORD('PRIMARY KEY'))
            elif f.unique:
                field_output.append(style.SQL_KEYWORD('UNIQUE'))
            if tablespace and f.unique:
                # We must specify the index tablespace inline, because we
                # won't be generating a CREATE INDEX statement for this field.
                field_output.append(self.connection.ops.tablespace_sql(tablespace, inline=True))
            #ForeignKey support
            #if f.rel:
            #    ref_output, pending = self.sql_for_inline_foreign_key_references(f, known_models, style)
            #    if pending:
            #        pass#pr = pending_references.setdefault(f.rel.to, []).append((model, f))
            #    else:
            #        field_output.extend(ref_output)
            table_output.append(' '.join(field_output))
        #if opts.order_with_respect_to:
        #    table_output.append(style.SQL_FIELD(qn('_order')) + ' ' + \
        #        style.SQL_COLTYPE(models.IntegerField().db_type()) + ' ' + \
        #        style.SQL_KEYWORD('NULL'))
        #for field_constraints in opts.unique_together:
        #    table_output.append(style.SQL_KEYWORD('UNIQUE') + ' (%s)' % \
        #        ", ".join([style.SQL_FIELD(qn(opts.get_field(f).column)) for f in field_constraints]))

        full_statement = [style.SQL_KEYWORD('CREATE TABLE') + ' ' + style.SQL_TABLE(qn(table.name)) + ' (']
        final_output = SQL()
        for i, line in enumerate(table_output): # Combine and add commas.
            full_statement.append('    %s%s' % (line, i < len(table_output)-1 and ',' or ''))
        full_statement.append(')')
        #if table.db_tablespace:
        #    full_statement.append(self.connection.ops.tablespace_sql(opts.db_tablespace))
        full_statement.append(';')
        final_output.append('\n'.join(full_statement))

        #currently for Oracle only
        #if opts.has_auto_field:
        #    # Add any extra SQL needed to support auto-incrementing primary keys.
        #    auto_column = opts.auto_field.db_column or opts.auto_field.name
        #    autoinc_sql = self.connection.ops.autoinc_sql(opts.db_table, auto_column)
        #    if autoinc_sql:
        #        for stmt in autoinc_sql:
        #            final_output.append(stmt)

        return final_output
    
    def get_create_table_indexes_sql(self, table):
        sql = SQL()
        for index in table.indexes.values():
            sql.extend(self.get_create_index_sql(table, index))
        return sql
    
    def get_rebuild_table_sql(self, left, right, renames):
        """
        Renames: right => left
        """
        old_names = left.fields.keys()
        
        #print "Renames:", renames

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
        for f in right.fields.values():
            if f.name in renames:
                updated.append(fqn(renames[f.name])) # copy renamed column
            elif f.name in old_names:
                updated.append(fqn(f.name)) # copy column
            else:
                default = NotProvided
                if f.allow_null:
                    default = None
                elif f.primary_key:
                    default = '0'
                elif f.coltype.coltype in ['int', 'bool', 'tinyint']:
                    default = '0' 
                elif f.coltype.coltype in ['varchar', 'text']:
                    default = ''
                default = get_field_default(f, default) # add column with default value set
                if default is None:
                    updated.append('NULL')
                else:
                    updated.append(fqv(default))

        sql.append(kw('INSERT INTO ') + 
                   tqn(right.name) + 
                   kw(' SELECT ') + 
                   fld(','.join(updated)) + 
                   kw(' FROM ') + 
                   tqn(tmp_table_name) +';')
        
        sql.extend(self.get_drop_table_sql(temp))
        
        sql.extend(self.get_create_table_indexes_sql(right))
        
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
                    table.indexes.extend(self.get_indexes(cursor, table_name))
                except IndexError:
                    pass
        return schema
            
    def get_indexes(self, cursor, table_name):
        raise NotImplementedError()
        
    def get_table(self, cursor, table_name):
        raise NotImplementedError()
