import django.core.management

"""
    django has its own internal set of commands (stored in django.core.management.commands).
    this function adds our commands to django's own.
"""

def add_management_commands(func):
    def inner(*args, **kwargs):
        print 'real woot'
        rv = func(*args, **kwargs)
        rv['sqlevolve'] = 'deseb'
        add_aka_support()
        return rv
    return inner

django.core.management.get_commands = add_management_commands(django.core.management.get_commands)

added_aka_support = False

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
            self.aka = None
            if kwargs.has_key('aka'):
                self.aka = kwargs['aka']
                if self.aka.__class__.__name__=='str':
                    self.aka = (self.aka)
                del kwargs['aka']
            func(self, *args, **kwargs)
        return inner
    
    django.db.models.Field.__init__ = set_field_aka(django.db.models.Field.__init__)
    django.db.models.CharField.__init__ = set_field_aka(django.db.models.CharField.__init__)
    django.db.models.IntegerField.__init__ = set_field_aka(django.db.models.IntegerField.__init__)
    django.db.models.DateField.__init__ = set_field_aka(django.db.models.DateField.__init__)
    
    def set_model_aka(func):
        def inner(self, cls, name):
            self.aka = None
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
    
