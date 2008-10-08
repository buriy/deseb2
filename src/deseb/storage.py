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
            self.rename_model(self, app_label, m, aka) 
        for m, field_aka in getattr(data, 'field_renames', {}).iteritems():
            #FIXME: can contain only app-owned models and fields
            #XXX: no duplicates possible
            if m in self.field_aka: raise Exception("Duplicate field_rename found for model %s" % m)
            for f, aka in field_aka:
                self.rename_field(app_label, m, f, aka)
    
    def rename_model(self, app_label, model_name, aka):
        if isinstance(aka, basestring): aka = set([aka])
        self.model_aka[model_name] = aka    
    
    def rename_field(self, app_label, model_name, field, aka):
        self.field_aka.setdefault(model_name, {})
        if isinstance(aka, basestring): aka = set([aka])
        self.field_aka[model_name][field] = aka 
    
    def get_table(self, app_label, object_name):
        return "%s_%s" % (app_label, object_name.lower())
    
    def get_model_table(self, model):
        return model._meta.db_table
    
    def convert_model_akas_to_tables(self, app_label, akas):
        tables = set()
        for object_name in akas:
            tables.add(self.get_table(app_label, object_name))
        return tables
    
    def update_with_aka(self, app_label):
        from deseb import added_aka_support
        if added_aka_support:
            for model in get_models(get_app(app_label)):
                if model._meta.aka:
                    model_akas = self.convert_model_akas_to_tables(app_label, model._meta.aka)
                    self.rename_model(app_label, model._meta.object_name, model_akas)
                for field in model._meta.fields:
                    if field.aka:
                        self.rename_field(app_label, model._meta.object_name, field.column, field.aka)
            
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
        akas = self.model_aka.get(model._meta.object_name, set())
        #if akas: print "getting_model_aka:", self.get_model_table(model), '->', akas 
        return akas
    
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
