import django.db.models 
import django.core.management

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
django.db.models.DateTimeField.__init__ = set_field_aka(django.db.models.DateTimeField.__init__)

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


