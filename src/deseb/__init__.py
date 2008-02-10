import django.core.management
try:
    import django.core.management.sql
    version = 'trunk'
except ImportError:
    version = '0.96'
"""
    django has its own internal set of commands (stored in django.core.management.commands).
    this function adds our commands to django's own.
"""

added_aka_support = False

def db_type(self):
    from django.db import get_creation_module
    from django.db.models.fields.related import ForeignKey
    data_types = get_creation_module().DATA_TYPES
    internal_type = self.get_internal_type()
    if internal_type in ['ForeignKey']:
        return db_type(self.rel.to._meta.pk)
    assert internal_type in data_types.keys(), "No such django type. Please send this error to maintainer."
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
                if self.aka.__class__.__name__=='str':
                    self.aka = (self.aka,)
                del kwargs['aka']
            if version == 'trunk' and kwargs.has_key('maxlength'):
                kwargs['max_length'] = kwargs['maxlength']
                del kwargs['maxlength']
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
            if self.meta:
                meta_attrs = self.meta.__dict__
                if meta_attrs.has_key('aka'):
                    self.aka = meta_attrs['aka']
                    if self.aka.__class__.__name__=='str':
                        self.aka = (self.aka,)
                    del meta_attrs['aka']
            func(self, cls, name)
        return inner
    
    django.db.models.options.Options.contribute_to_class = set_model_aka(django.db.models.options.Options.contribute_to_class)
    
def add_management_commands(func):
    def inner(*args, **kwargs):
        add_aka_support()
        rv = func(*args, **kwargs)
        rv['evolvedb'] = 'deseb'
        rv['sqlevolve'] = 'deseb'
        rv['fingerprint'] = 'deseb'
        return rv
    return inner

PASS_ARGS = {'--dont-save':'do_save', '--dont-notify':'do_notify', '--noinput': 'interactive', '--managed-upgrades-only':'managed_upgrade_only'}
HIDE_ARGS = ['--dont-save', '--dont-notify']

def get_additional_args():
    import sys
    kwargs = {}
    for k,v in PASS_ARGS.items(): 
        if k in sys.argv: kwargs[v] = False
    return kwargs

def management_command_evolvedb_v0_96():
    def inner(*args, **kwargs):
        "Interactively runs the SQL statements to bring your schema up to date with your models."
        import schema_evolution
        kwargs.update(get_additional_args())
        return schema_evolution.run_sql_evolution_v0_96(*args, **kwargs)
    inner.args = '[--noinput] [--dont-notify] [--dont-save] ' + django.core.management.APP_ARGS
    return inner

def management_command_sqlevolve_v0_96():
    def inner(*args, **kwargs):
        "Output the SQL ALTER statements to bring your schema up to date with your models."
        import schema_evolution
        kwargs.update(get_additional_args())
        return schema_evolution.get_sql_evolution_v0_96(*args, **kwargs)
    inner.args = '[--noinput] [--dont-notify] ' + django.core.management.APP_ARGS
    return inner

def management_command_sqlfingerprint_v0_96():
    def inner(*args, **kwargs):
        "Prints the app fingerprints."
        import schema_evolution
        kwargs.update(get_additional_args())
        return schema_evolution.get_sql_fingerprint_v0_96(*args, **kwargs)
    inner.args = '' + django.core.management.APP_ARGS
    return inner

def execute_from_command_line_v0_96(func):
    def inner(action_mapping, argv):
        add_aka_support()
        if argv is None: import sys; argv = sys.argv
        return func(action_mapping, [c for c in argv if not c in HIDE_ARGS])
    return inner

try:
    django.core.management.get_commands = add_management_commands(django.core.management.get_commands)
except:
    django.core.management.DEFAULT_ACTION_MAPPING['evolvedb'] = management_command_evolvedb_v0_96()
    django.core.management.DEFAULT_ACTION_MAPPING['sqlevolve'] = management_command_sqlevolve_v0_96()
    django.core.management.DEFAULT_ACTION_MAPPING['fingerprint'] = management_command_sqlfingerprint_v0_96()
    django.core.management.NO_SQL_TRANSACTION = tuple(['evolvedb', 'sqlevolve', 'fingerprint']+list(django.core.management.NO_SQL_TRANSACTION))
    django.core.management.execute_from_command_line = execute_from_command_line_v0_96(django.core.management.execute_from_command_line)
    
