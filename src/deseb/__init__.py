import django.core.management

"""
    django has its own internal set of commands (stored in django.core.management.commands).
    this function adds our commands to django's own.
"""

added_aka_support = False

def db_type(self):
    from django.db import get_creation_module
    data_types = get_creation_module().DATA_TYPES
    internal_type = self.get_internal_type()
    return data_types.get(internal_type,'') % self.__dict__

def add_aka_support():
    global added_aka_support
    if added_aka_support: return
    else: added_aka_support = True

    import django.db.models 
    
    """
    django is picky about unknown attributes on both fields and models, so here
    we preempt their init methods to remove the offending information.
    
    these two methods pull the aka information (used for detecting renames),
    format it properly and store it as a class attribute.  then the original
    __init__() is called as originally planned.
    """
    
    def set_field_aka(func):
        def inner(self, *args, **kwargs):
            try: 
                if not self.aka: self.aka = None
            except:
                self.aka = None
            if kwargs.has_key('aka'):
                self.aka = kwargs['aka']
                del kwargs['aka']
            func(self, *args, **kwargs)
        return inner
    
    django.db.models.CharField.__init__ = set_field_aka(django.db.models.CharField.__init__)
    django.db.models.CommaSeparatedIntegerField.__init__ = set_field_aka(django.db.models.CommaSeparatedIntegerField.__init__)
    django.db.models.DateField.__init__ = set_field_aka(django.db.models.DateField.__init__)
    django.db.models.Field.__init__ = set_field_aka(django.db.models.Field.__init__)
    django.db.models.FloatField.__init__ = set_field_aka(django.db.models.FloatField.__init__)
    django.db.models.IntegerField.__init__ = set_field_aka(django.db.models.IntegerField.__init__)
    django.db.models.PhoneNumberField.__init__ = set_field_aka(django.db.models.PhoneNumberField.__init__)
    django.db.models.PositiveIntegerField.__init__ = set_field_aka(django.db.models.PositiveIntegerField.__init__)
    django.db.models.PositiveSmallIntegerField.__init__ = set_field_aka(django.db.models.PositiveSmallIntegerField.__init__)
    django.db.models.SmallIntegerField.__init__ = set_field_aka(django.db.models.SmallIntegerField.__init__)
    django.db.models.TextField.__init__ = set_field_aka(django.db.models.TextField.__init__)
    django.db.models.USStateField.__init__ = set_field_aka(django.db.models.USStateField.__init__)
    
    try:
        django.db.models.Field.db_type
    except:
        # v0.96 compatibility
        django.db.models.Field.db_type = db_type
    
    def set_model_aka(func):
        def inner(self, cls, name):
            self.aka = None
#            print self.meta.__dict__
            if self.meta:
                meta_attrs = self.meta.__dict__
                if meta_attrs.has_key('aka'):
                    self.aka = meta_attrs['aka']
                    if self.aka.__class__.__name__=='str':
                        self.aka = (self.aka)
                    del meta_attrs['aka']
            func(self, cls, name)
        return inner
    
    django.db.models.options.Options.contribute_to_class = set_model_aka(django.db.models.options.Options.contribute_to_class)
    
def add_management_commands(func):
    def inner(*args, **kwargs):
        add_aka_support()
        rv = func(*args, **kwargs)
        rv['sqlevolve'] = 'deseb'
        rv['sqlfingerprint'] = 'deseb'
        return rv
    return inner

def add_management_command_sqlevolve_v0_96():
    def inner(*args, **kwargs):
        "Output the SQL ALTER statements to bring your schema up to date with your models."
        import schema_evolution
        return schema_evolution.get_sql_evolution_v0_96(*args, **kwargs)
    inner.args = '[--format]' + django.core.management.APP_ARGS
    return inner

def add_management_command_sqlfingerprint_v0_96():
    def inner(*args, **kwargs):
        "Output the SQL ALTER statements to bring your schema up to date with your models."
        import schema_evolution
        return schema_evolution.get_sql_evolution_v0_96(*args, **kwargs)
    inner.args = '[--format]' + django.core.management.APP_ARGS
    return inner

def execute_from_command_line_v0_96(func):
    def inner(*args, **kwargs):
        add_aka_support()
        return func(*args, **kwargs)
    return inner

try:
    django.core.management.get_commands = add_management_commands(django.core.management.get_commands)
except:
    django.core.management.DEFAULT_ACTION_MAPPING['sqlevolve'] = add_management_command_sqlevolve_v0_96()
    django.core.management.DEFAULT_ACTION_MAPPING['sqlfingerprint'] = add_management_command_sqlfingerprint_v0_96()
    django.core.management.execute_from_command_line = execute_from_command_line_v0_96(django.core.management.execute_from_command_line)
    
