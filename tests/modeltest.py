from shutil import copy
import sys
import os

SHOW_CMD = False

def run(cmd, *args, **kw):
    os.environ['PATH'] = '../src:'+os.environ['PATH']
    runnable = "%s %s" % (cmd, " ".join(args))
    if SHOW_CMD: print runnable
    if os.name == 'nt' and runnable.startswith('python '):
        runnable = runnable[7:]
    _in, out, err = os.popen3(runnable)
    return out.read(), err.read()

def copy_models(dir, version):
    copy(dir+"/models.py."+version, dir+"/models.py")

def runpe(cmd, *args):
    out, err = run(cmd, *args)
    if err: print err
    return out

def runpoe(cmd, *args):
    out, err = run(cmd, *args)
    if out: print out
    if err: print err

def modeltest(app):
    #First argument is test application name
    if not app:
        raise Exception("No test name given")
    if not os.path.exists('settings.py'):
        raise Exception('Oops... file settings.py does not exist! Please copy your settings there!')
    print "Test %s" % app
    #reset on post state and pre state
    copy_models(app, 'pre')
    runpoe("manage.bat", "reset", app, "--noinput")
    #runpoe("manage.bat", "evolvedb", app, "--noinput --dont-save --dont-notify")
    copy_models(app, 'post')
    print "Planned changes:"
    runpoe("manage.bat", "sqlevolve", app, "--dont-notify")
    #runpoe("manage.bat", "evolvedb", app, "--noinput --dont-save --dont-notify")
    #Write all sqlevolve output to stderr
    errors = runpe("manage.bat sqlevolve", app, "--dont-notify 1>&2")
    if errors.strip():
        return "Error: %s lines of sqlevolve" % len(errors.strip().split('\n'))
    else:
        return "Ok, test passed."

if __name__ == "__main__":
    if len(sys.argv)<2 or len(sys.argv)>2:
        print "Usage: modeltest.py <test_name>"
    else:
        print modeltest(*sys.argv[1:])
