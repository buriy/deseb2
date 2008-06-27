from deseb.dbmodel import DBSchema
from deseb.dbmodel import DBTable
from deseb.dbmodel import DBField
from deseb.dbmodel import DBIndex
from django.db.models.fields.related import ForeignKey

try:
    import django.core.management.sql as management
    from django.core.management import color
    version = 'trunk'
except ImportError:
    # v0.96 compatibility
    import django.core.management as management
    management.installed_models = management._get_installed_models

def build_model_flags(f, coltype):
    info = DBField(
        name = f.attname,
        allow_null = f.null,
        coltype = coltype,
        foreign_key = isinstance(f, ForeignKey),
        primary_key = f.primary_key,
        unique = f.unique,
        max_length = f.max_length,
        aka = f.aka)
    return info

def get_field_type(f):
    #if f in ['timestamp with time zone']: return f
    f = f.split('(')[0]
    if f in ['serial']: return 'integer'
    if f in ['tinyint']: return 'bool'
    if f in ['decimal']: return 'numeric'
    return f    

def build_model_table(app, model):
    table_name = model._meta.db_table
    table = DBTable(name = table_name)
    for f in model._meta.fields:
        #existing_relations = introspection.get_relations(cursor,db_table)
        f_col_type = get_field_type(f.db_type())
        flags = build_model_flags(f, f_col_type)
        table.fields.append(flags)
        if f.db_index:
            name = '%s_%s' % (table_name, f.column)
            table.indexes.append(DBIndex(name=name))
    return table

def build_model_schema(app):
    from django.db import models

    # get the existing models, minus the models we've just created
    app_models = models.get_models(app)
            
    schema = DBSchema('Model schema') 
    for model in app_models:
        if model._meta.db_table:
            table = build_model_table(app, model=model)
            schema.tables.append(table)
    
    return schema
