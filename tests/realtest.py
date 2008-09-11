from shutil import copy
import os
import sys

DEBUG = True

def copy_models(app_name, version):
    copy(app_name+"/models."+version+".py", app_name+"/models.py")

def write_file(fn, contents):
    f = open(fn, 'wt')
    if isinstance(contents, (list, tuple)):
        contents = u'\n'.join(map(unicode, contents)).encode('utf-8') 
    f.write(contents)
    f.close()

def reload_models(app_name, version):
    from django.db.models.loading import cache
    cache.app_models[app_name] = {}
    __import__(app_name+".models_"+version, {}, {}, ['models_'+version])

def run_sql(commands):
    from django.db import connection
    from django.db import transaction
    cursor = connection.cursor()
    for action in commands:
        try:
            cursor.execute(action)
        except:
            print "Error running SQL command:", action
            raise

def modeltest(app_name, use_aka=True):
    if not app_name:
        raise Exception("No test name given")
    if not os.path.exists('settings.py'):
        raise Exception('Oops... file settings.py does not exist! Please copy your settings there!')
    from django.conf import settings
    from django.db.models.loading import get_apps, get_app, get_models
    from django.core.management.sql import sql_reset
    from django.core.management.color import no_style
    from deseb.schema_evolution import evolvediff
    from deseb.actions import get_introspected_evolution_options
    from django.core.management.sql import sql_delete, sql_create
    from django.db.transaction import commit_on_success
    print "Test %s" % app_name
    #reset on post state and pre state
    from deseb import add_aka_support
    if use_aka:
        add_aka_support()
    
    style = no_style()
    settings.INSTALLED_APPS = tuple(list(settings.INSTALLED_APPS[:5]) + [app_name])
    
    write_file(app_name+"/models.py", '') # re-init models.py
    get_apps()
    
    reload_models(app_name, 'pre')    
    app = get_app(app_name)
    create = sql_create(app, style)
    write_file(app_name+"/init.%s.actual" % settings.DATABASE_ENGINE, create)
    #FIXME: compare to init.correct later instead of copying
    write_file(app_name+"/init.%s.planned"% settings.DATABASE_ENGINE, create)
    
    reset = sql_reset(app, style)
    commit_on_success(run_sql)(reset)
    
    reload_models(app_name, 'post')
    if use_aka:
        from deseb.storage import update_with_aka, save_renames
        update_with_aka(app_name)
        save_renames(app_name)
    diff = evolvediff(app)
    write_file(app_name+"/diff.%s.actual" % settings.DATABASE_ENGINE, diff)
    #FIXME: compare to diff.correct later instead of copying
    write_file(app_name+"/diff.planned", diff)
    
    actions = get_introspected_evolution_options(app, style)
    write_file(app_name+"/actions.%s.actual" % settings.DATABASE_ENGINE, actions)
    #FIXME: compare to diff.correct later instead of copying
    write_file(app_name+"/actions.%s.planned" % settings.DATABASE_ENGINE, actions)
    commit_on_success(run_sql)(actions)

    diff = evolvediff(app)
    write_file(app_name+"/misses.%s.actual" % settings.DATABASE_ENGINE, actions)
    if diff:
        print "Errors:"
        print diff.split('\n',1)[1]

    try:
        actions = get_introspected_evolution_options(app, style)
    except Exception:
        actions = ['Was unable to generate error diff SQL commands']
    write_file(app_name+"/errors.%s.actual" % settings.DATABASE_ENGINE, actions)
    #FIXME: compare to diff.correct later instead of copying
    #write_file(app_name+"/errors.%s.planned" % settings.DATABASE_ENGINE, actions)

def alter_paths():
    DIR = os.path.dirname(os.path.abspath(__file__))                                                                        
    SRC = os.path.dirname(DIR)+"/src"                                                                                       
    sys.path.append(DIR)                                                                                                    
    sys.path.append(SRC)                                                                                                    
    os.environ['PYTHONPATH'] = SRC
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'                                                                                          

if __name__ == "__main__":
    alter_paths()
    if DEBUG:
        dirs = [x for x in os.listdir('.') if x.startswith('case') or x.startswith('issue')]
        for t in dirs:
            modeltest(t.strip())
            print '='*55
        sys.exit()
    if len(sys.argv)<2 or len(sys.argv)>2:
        print "Usage: modeltest.py <test_name>"
        sys.exit(1)
    modeltest(*sys.argv[1:])
