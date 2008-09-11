from deseb.meta import DBField
from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignKey
from deseb.meta import DBSchema
from deseb.meta import DBTable
from deseb.meta import DBIndex
from deseb.meta import TreeDiff
from deseb.common import get_operations_and_introspection_classes
from django.contrib.contenttypes.generic import GenericRelation
from deseb.storage import get_model_aka, get_field_aka

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

def get_max_length(f):
    if isinstance(f, ForeignKey):
        type = f.db_type()
        if '(' in type and ')' in type:
            return int(f.db_type().split('(')[1].split(')')[0])
    return f.max_length

def compare_field_length(f, column_flags):
    from django.db.models.fields import CharField, SlugField, AutoField
    f_maxlength = str(getattr(f, 'maxlength', getattr(f, 'max_length', None)))
    db_maxlength = str(column_flags.traits.get('max_length', 64000))
    return(not f.primary_key and isinstance(f, CharField) and db_maxlength!= f_maxlength) or \
          (not f.primary_key and isinstance(f, SlugField) and db_maxlength!= f_maxlength)

def build_model_flags(model, f):
    info = DBField(
        name = f.attname,
        allow_null = f.null,
        coltype = get_field_type(f.db_type()),
        foreign_key = isinstance(f, ForeignKey),
        primary_key = f.primary_key,
        unique = f.unique and not f.primary_key,
        max_length = get_max_length(f),
        aka = get_field_aka(model, f.name))
    return info

def build_model_table(_app, model):
    table_name = model._meta.db_table
    table = DBTable(name = table_name, aka = get_model_aka(model))
    for f in model._meta.local_fields:
        #existing_relations = introspection.get_relations(cursor,db_table)
        flags = build_model_flags(model, f)
        table.fields.append(flags)
        if f.db_index and not f.primary_key and not f.unique:
            name = '%s_%s' % (table_name, f.column)
            table.indexes.append(DBIndex(name=name))
    return table

def get_m2m_fields(model, f):
    return [
        ('id', AutoField(primary_key=True)),
        (f.m2m_column_name(), ForeignKey(model)),
        (f.m2m_reverse_name(), ForeignKey(f.rel.to)),
    ]

def build_m2m_table(app, m2m_field, model):
    table_name = m2m_field.m2m_db_table()
    table = DBTable(name = table_name)
    for column, f in get_m2m_fields(model, m2m_field):
        #existing_relations = introspection.get_relations(cursor,db_table)
        f.attname = column
        flags = build_model_flags(f)
        table.fields.append(flags)
    return table

def build_model_schema(app):
    from django.db import models

    # get the existing models, minus the models we've just created
    app_models = models.get_models(app)
            
    schema = DBSchema('Actual '+app.__name__)
    revised = []

    while app_models:
        model = app_models.pop()
        if model._meta.db_table:
            table = build_model_table(app, model)
            schema.tables.append(table)
        for f in model._meta.local_many_to_many:
            if isinstance(f, GenericRelation): continue
            m2m = f.rel.through
            if m2m and not m2m in revised and not m2m in app_models:
                app_models.append(m2m)
            if not m2m:
                table = build_m2m_table(app, f, model)
            schema.tables.append(table)
   
    return schema
