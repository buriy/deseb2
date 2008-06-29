from deseb.meta import DBField
from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignKey
from deseb.meta import DBSchema
from deseb.meta import DBTable
from deseb.meta import DBIndex
from deseb.meta import TreeDiff
from deseb.common import get_operations_and_introspection_classes

try:
    import django.core.management.sql as management
    from django.core.management import color
    version = 'trunk'
except ImportError:
    # v0.96 compatibility
    import django.core.management as management
    management.installed_models = management._get_installed_models

def get_field_default(f):
    from django.db.models.fields import NOT_PROVIDED
    if callable(f.default): return NOT_PROVIDED
    return f.default

def get_field_type(f):
    if not f: return 'unknown'
    #if f in ['timestamp with time zone']: return f
    f = f.split('(')[0].split(' CHECK')[0]
    if f in ['integer', 'serial']: return 'int'
    if f in ['tinyint']: return 'bool'
    if f in ['decimal']: return 'numeric'
    return f    

def compare_field_length(f, column_flags):
    from django.db.models.fields import CharField, SlugField, AutoField
    f_maxlength = str(getattr(f, 'maxlength', getattr(f, 'max_length', None)))
    db_maxlength = str(column_flags.traits.get('max_length', 64000))
    return(not f.primary_key and isinstance(f, CharField) and db_maxlength!= f_maxlength) or \
          (not f.primary_key and isinstance(f, SlugField) and db_maxlength!= f_maxlength)

def build_model_flags(f, coltype):
    info = DBField(
        name = f.attname,
        allow_null = f.null,
        coltype = coltype,
        # foreign_key = isinstance(f, ForeignKey),
        primary_key = f.primary_key,
        unique = f.unique,
        max_length = f.max_length,
        aka = f.aka)
    return info

def build_model_table(app, model):
    table_name = model._meta.db_table
    table = DBTable(name = table_name)
    for f in model._meta.fields:
        #existing_relations = introspection.get_relations(cursor,db_table)
        f_col_type = ''
        if f.db_type():
            f_col_type = get_field_type(f.db_type())
        flags = build_model_flags(f, f_col_type)
        table.fields.append(flags)
        if f.db_index:
            name = '%s_%s' % (table_name, f.column)
            table.indexes.append(DBIndex(name=name))
    return table

def get_m2m_fields(model, f):
    return [
        ('id', AutoField(primary_key=True)),
        (f.m2m_column_name(), ForeignKey(model)),
        (f.m2m_reverse_name(), ForeignKey(f.rel.to)),
    ]

def build_model_m2m_table(app, model, m2m_field):
    table_name = m2m_field.m2m_db_table()
    table = DBTable(name = table_name)
    for column, f in get_m2m_fields(model, m2m_field):
        #existing_relations = introspection.get_relations(cursor,db_table)
        f_col_type = get_field_type(f.db_type())
        f.attname = column
        flags = build_model_flags(f, f_col_type)
        table.fields.append(flags)
    return table

def build_model_schema(app):
    from django.db import models

    # get the existing models, minus the models we've just created
    app_models = models.get_models(app)
            
    schema = DBSchema('Model schema') 
    for model in app_models:
        if model._meta.db_table:
            table = build_model_table(app, model)
            schema.tables.append(table)
            
        for m2m_field in model._meta.many_to_many:
            table = build_model_m2m_table(app, model, m2m_field)
            schema.tables.append(table)
    
    return schema

def show_evolution_plan(cursor, app, style):
    ops, introspection = get_operations_and_introspection_classes(style)

    model_schema = build_model_schema(app)
    app_name = app.__name__.split('.')[-2]
    db_schema = introspection.get_schema(cursor, app_name) 
    #print unicode(db_schema)
    #print unicode(model_schema)
    diff = TreeDiff(db_schema, model_schema)
    #print unicode(db_schema)
    #print unicode(model_schema)
    print unicode(diff)
    #import sys
    #sys.exit()

def show_table_evolution_plan(cursor, app, model, style):
    ops, introspection = get_operations_and_introspection_classes(style)
    model_schema = build_model_table(app, model)
    #app_name = app.__name__.split('.')[-2]
    db_schema = introspection.get_table(cursor, model._meta.db_table) 
    #print unicode(db_schema)
    #print unicode(model_schema)
    diff = TreeDiff(db_schema, model_schema)
    print unicode(diff)
    #raise Exception(unicode(diff))
