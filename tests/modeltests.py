from shutil import copy
from modeltest import modeltest
from modeltest import runpe
import sys
import os

def modeltests(app, test=None):
    if not os.path.exists(app+".py"):
        raise Exception("Oops... settings file %s.py is not found" % app)
    copy(app+".py", "settings.py")
    if test:
        print modeltest(test)
    else:
        dirs = runpe("ls -1d case* issue*")
        for t in dirs.strip().split('\n'):
            print modeltest(t.strip())
    os.unlink("settings.py")

if __name__ == "__main__":
    if len(sys.argv)<2 or len(sys.argv)>3:
        print "Usage: modeltests.py <settings file without .py> [<test name>]"
    else:
        modeltests(*sys.argv[1:])
