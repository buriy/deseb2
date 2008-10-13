from deseb.meta import DBField
from django.db.models.fields import AutoField
from django.db.models.fields.related import ForeignKey
from deseb.meta import DBSchema
from deseb.meta import DBTable
from deseb.meta import DBIndex
from deseb.common import NotProvided, get_app_models
from django.contrib.contenttypes.generic import GenericRelation
from deseb.storage import get_model_aka, get_field_aka
from deseb.dbtypes import get_field_type

def get_field_default(column, empty=NotProvided):
    if column.default is NotProvided:
        return empty
    if callable(column.default): 
        return empty
    return column.default

#def compare_field_length(f, column_flags):
#    from django.db.models.fields import CharField, SlugField
#    f_maxlength = str(getattr(f, 'maxlength', getattr(f, 'max_length', None)))
#    db_maxlength = str(column_flags.traits.get('max_length', 64000))
#    return(not f.primary_key and isinstance(f, CharField) and db_maxlength!= f_maxlength) or \
#          (not f.primary_key and isinstance(f, SlugField) and db_maxlength!= f_maxlength)

def build_model_flags(model, f):
    info = DBField(
        name = f.attname,
        allow_null = f.null and not f.primary_key,
        default = get_field_default(f),
        coltype = get_field_type(f),
        foreign_key = None,#isinstance(f, ForeignKey) or None,
        primary_key = f.primary_key,
        unique = f.unique and not f.primary_key,
        aka = get_field_aka(model, f.name))
    return info

def build_model_table(_app, model):
    table_name = model._meta.db_table
    table = DBTable(name = table_name, aka = get_model_aka(model))
    for f in model._meta.local_fields:
        #existing_relations = introspection.get_relations(cursor,db_table)
        flags = build_model_flags(model, f)
        from django.conf import settings
        if settings.DATABASE_ENGINE.startswith('postgres') and isinstance(f, AutoField):
            flags.sequence = table.name+"_"+f.column+"_seq"
        table.fields.append(flags)
        if f.db_index and not f.primary_key and not f.unique:
            #name = '%s_%s' % (table_name, f.column)
            table.indexes.append(DBIndex(name=f.column,
                                         full_name = table_name + '_' + f.column))
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
        flags = build_model_flags(model, f)
        table.fields.append(flags)
        from django.conf import settings
        if settings.DATABASE_ENGINE.startswith('postgres') and isinstance(f, AutoField):
            flags.sequence = table.name+"_"+column+"_seq"

    return table

def build_model_schema(app):
    app_models = get_app_models(app)
    
    schema = DBSchema('Actual '+app.__name__)
    revised = []

    while app_models:
        model = app_models.pop()
        if model._meta.db_table:
            table = build_model_table(app, model)
            schema.tables.append(table)
        for f in model._meta.local_many_to_many:
            if isinstance(f, GenericRelation): continue
            if not hasattr(f.rel, 'through'): continue # < v1.0
            m2m = f.rel.through
            if m2m and not m2m in revised and not m2m in app_models:
                app_models.append(m2m)
            if not m2m:
                table = build_m2m_table(app, f, model)
            schema.tables.append(table)
   
    return schema
