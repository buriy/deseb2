import os
import sys

DEBUG = '--debug' in sys.argv
WRITES = not '--skip-log' in sys.argv

#def copy_models(app_name, version):
#    copy(app_name+"/models."+version+".py", app_name+"/models.py")

def write_file(fn, contents):
    if WRITES:
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
    cursor = connection.cursor()
    for action in commands:
        if action.strip().startswith('--'): continue
        try:
            cursor.execute(action)
        except:
            print "Error running SQL command:", action
            raise

def drop_all_tables():
    from django.core.management.color import no_style
    from django.db import connection
    from deseb.meta import DBTable
    from deseb.common import get_operations_and_introspection_classes
    _ops, introspection = get_operations_and_introspection_classes(no_style())
    all_tables = introspection.get_table_names(connection.cursor())
    for table in all_tables:
        run_sql(_ops.get_drop_table_sql(DBTable(table)).actions)

def modeltest(app_name, use_aka=True):
    if not app_name:
        raise Exception("No test name given")
    if not os.path.exists('settings.py'):
        raise Exception('Oops... file settings.py does not exist! Please copy your settings there!')
    from django.conf import settings
    from django.db.models.loading import get_apps, get_app
    from deseb.schema_evolution import evolvediff
    from django.core.management.color import no_style
    from deseb.actions import get_introspected_evolution_options
    from django.core.management.sql import sql_create, sql_indexes
    from django.db.transaction import commit_on_success
    from django.db import connection
    from deseb.actions import get_schemas, show_evolution_plan
    if DEBUG:
        print "Test %s" % app_name
    #reset on post state and pre state
    from deseb import add_aka_support
    if use_aka:
        add_aka_support()
    
    style = no_style()
    settings.INSTALLED_APPS = tuple(list(settings.INSTALLED_APPS[:5]) + [app_name])
    
    write_file(app_name+"/models.py", '') # re-init models.py
    write_file(app_name+"/errdiff.%s.actual" % settings.DATABASE_ENGINE, "")
    write_file(app_name+"/errors.%s.actual" % settings.DATABASE_ENGINE, "")
    get_apps()
    
    drop_all_tables()
    
    reload_models(app_name, 'pre')    
    app = get_app(app_name)
    create = sql_create(app, style) + sql_indexes(app, style)
    write_file(app_name+"/init.%s.actual" % settings.DATABASE_ENGINE, create)
    #FIXME: compare to init.correct later instead of copying
    write_file(app_name+"/init.%s.planned" % settings.DATABASE_ENGINE, create)
    
    reset = sql_create(app, style)
    #print 'SQL:', '\n'.join(reset)
    commit_on_success(run_sql)(reset)
    
    reset_idx = sql_indexes(app, style)
    run_sql(reset_idx)
    
    reload_models(app_name, 'post')
    if use_aka:
        from deseb.storage import update_with_aka, save_renames
        update_with_aka(app_name)
        save_renames(app_name)

    cursor = connection.cursor()
    db_schema, model_schema = get_schemas(cursor, app, style)
    diff = show_evolution_plan(cursor, app, style, db_schema, model_schema)
    write_file(app_name+"/diff.%s.actual" % settings.DATABASE_ENGINE, diff)
    #FIXME: compare to diff.correct later instead of copying
    write_file(app_name+"/diff.%s.planned" % settings.DATABASE_ENGINE, diff)
    
    actions = get_introspected_evolution_options(app, style, db_schema, model_schema)
    write_file(app_name+"/actions.%s.actual" % settings.DATABASE_ENGINE, actions)
    #FIXME: compare to diff.correct later instead of copying
    write_file(app_name+"/actions.%s.planned" % settings.DATABASE_ENGINE, actions)
    try:
        commit_on_success(run_sql)(actions)
    except:
        #print 'changes rolled back'
        from django.db import transaction
        transaction.rollback()
        raise
    #else:
        #print 'changes committed'

    cursor = connection.cursor()
    db_schema, model_schema = get_schemas(cursor, app, style, model_schema=model_schema)
    # due to sqlite3/pysqlite bug, caused deferred index creation, we reget db schema.
    # this is fucking weird, but i've no any explanation, why getting indxes
    # doesn't work correctly first time  
    db_schema, model_schema = get_schemas(cursor, app, style, model_schema=model_schema)
    diff = show_evolution_plan(cursor, app, style, db_schema, model_schema)
    write_file(app_name+"/errdiff.%s.actual" % settings.DATABASE_ENGINE, diff)
    diff1 = diff.split('\n',1)[1]
    if diff1:
        print "Errors:"
        print diff1

    try:
        actions, db_schema, model_schema = get_introspected_evolution_options(app, style, db_schema, model_schema)
    except Exception:
        actions = ['Was unable to generate error diff SQL commands']
    write_file(app_name+"/errors.%s.actual" % settings.DATABASE_ENGINE, actions)
    #FIXME: compare to diff.correct later instead of copying
    #write_file(app_name+"/errors.%s.planned" % settings.DATABASE_ENGINE, actions)
    return diff1

def alter_paths():
    DIR = os.path.dirname(os.path.abspath(__file__))                                                                        
    SRC = os.path.dirname(DIR)+"/src"                                                                                       
    sys.path.append(DIR)                                                                                                    
    sys.path.append(SRC)                                                                                                    
    os.environ['PYTHONPATH'] = SRC
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'                                                                                          

if __name__ == "__main__":
    alter_paths()
    if '--all' in sys.argv:
        dirs = [x for x in os.listdir('.') if x.startswith('case') or x.startswith('issue')]
        for t in dirs:
            try:
                err = modeltest(t.strip())
                if err:
                    print '='*55
            except Exception, err:
                print '-'*55
                import traceback; traceback.print_exc()
                print '='*55
        sys.exit()
    if len(sys.argv)<2 or len(sys.argv)>2:
        print "Usage: modeltest.py <test_name>"
        sys.exit(1)
    modeltest(*sys.argv[1:])
