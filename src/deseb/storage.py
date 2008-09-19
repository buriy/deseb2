from django.db.models.loading import get_app, get_models
import sys

import os

from django.conf import settings
try:
    STORE = settings.MIGRATIONS
except AttributeError:
    STORE = os.path.abspath('')+'/migrations'

class Dummy: pass

class AkaCache(object):
    model_aka = {}
    field_aka = {}
    stores = {}
    
    def get_store(self, app_label, rev='current'):
        name = rev+'.py'
        folder = STORE+'/'+app_label
        if not os.path.exists(folder):
            os.makedirs(folder)
            return Dummy()
        if not os.path.exists(folder+'/'+name):
            return Dummy()
        try:
            if not folder in sys.path[:1]:
                sys.path.insert(0, folder)
            return __import__(rev, {}, {}, [rev])
        finally:
            if folder in sys.path[:1]:
                sys.path = sys.path[1:]
    
    def _load(self, app_label, rev='current'):
        if app_label in self.stores: 
            return 
        data = self.get_store(app_label, rev)
        self.stores[app_label] = data
        for m, aka in getattr(data, 'model_renames', {}).iteritems():
            #FIXME: can contain only app-owned models
            #XXX: no duplicates possible
            if m in self.model_aka: raise Exception("Duplicate model_rename found for model %s" % m)
            if isinstance(aka, basestring): aka = set([aka])
            self.model_aka[m] = aka 
        for m, field_aka in getattr(data, 'field_renames', {}).iteritems():
            #FIXME: can contain only app-owned models and fields
            #XXX: no duplicates possible
            if m in self.field_aka: raise Exception("Duplicate field_rename found for model %s" % m)
            self.field_aka[m] = field_aka 
    
    def rename_model(self, app_label, model, aka):
        pass
    
    def rename_field(self, app_label, model, field, aka):
        pass
    
    def convert_model_to_table(self, model, aka):
        return "%s_%s" % (model._meta.app_label, aka.lower())
    
    def convert_model_akas_to_tables(self, model):
        tables = set()
        for x in model._meta.aka:
            tables.add(self.convert_model_to_table(model, x))
        return tables
    
    def update_with_aka(self, app_label):
        from deseb import added_aka_support
        if added_aka_support:
            for model in get_models(get_app(app_label)):
                if model._meta.aka:
                    self.model_aka[model._meta.object_name] = self.convert_model_akas_to_tables(model)
                for field in model._meta.fields:
                    if field.aka:
                        self.field_aka.setdefault(model._meta.object_name, {})
                        self.field_aka[model._meta.object_name][field.name] = field.aka
            
    def save(self, app_label, rev='current'):
        app_models = [model._meta.object_name for model in get_models(get_app(app_label))]
        output = []
        output.append('model_renames = {')
        for m, aka in self.model_aka.iteritems():
            if m in app_models:
                output.append('    "%s": %s,' % (m, aka))
        output.append('}')
        output.append('field_renames = {')
        for m, fields in self.field_aka.iteritems():
            if m in app_models:
                output.append('    "%s": {' % (m))
                for f, aka in fields.iteritems():
                    output.append('        "%s": %s,' % (f, aka))
                output.append('    },')
        output.append('}')
        name = rev+'.py'
        folder = STORE+'/'+app_label
        if not os.path.exists(folder):
            os.makedirs(folder)
        open(folder+'/'+name, 'wt').write('\n'.join(output))
        if not os.path.exists(folder+'/'+'__init__.py'):
            open(folder+'/'+'__init__.py', 'wt').write('')
        self.stores[app_label] = Dummy()
    
    def get_model_aka(self, model, rev='current'):
        self._load(model._meta.app_label, rev)
        return self.model_aka.get(model._meta.object_name, set())
    
    def get_table_aka(self, app, table, rev='current'):
        self._load(app, rev)
        return self.model_aka.get(table, set())
    
    def get_field_aka(self, model, field, rev='current'):
        self._load(model._meta.app_label, rev)
        renames = self.field_aka.get(model._meta.object_name, {})
        return renames.get(field, set())
        
cache = AkaCache()
        
get_model_aka = cache.get_model_aka
get_table_aka = cache.get_table_aka
get_field_aka = cache.get_field_aka
save_renames = cache.save
update_with_aka = cache.update_with_aka
