#!/usr/bin/env python

import re
import os
import sys
import optparse
import subprocess

PYTHONS = ["2.5"]#["2.3", "2.4", "2.5"]
DBS = ["sqlite3", "postgresql", "postgresql_psycopg2", "mysql"]

p = optparse.OptionParser()
p.add_option("-p", "--python", action="append")
p.add_option("-d", "--db", action="append")
p.add_option("-v", "--verbose", action="store_true")
p.set_defaults(python=[], db=[], verbose=False)
options, args = p.parse_args()

if not options.python: options.python = PYTHONS
if not options.db: options.db = DBS

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(DIR)+"/src"
sys.path.append(DIR)
os.environ['PYTHONPATH'] = SRC

for py in options.python:
    for db in options.db:
        if options.verbose:
            print "#"*80
            print "Running tests using Python %s / %s:" % (py, db)
        pipe = subprocess.Popen(
            ["python%s" % py, "runtests.py", "--settings=settings_%s" % db] + args, 
            stdout  = subprocess.PIPE, 
            stderr  = subprocess.STDOUT, 
            cwd     = DIR
        )
        out, err = pipe.communicate()
        if options.verbose:
            print out
        else:
            outlines = out.split("\n")
            failures = [l for l in outlines if re.match("^(FAIL|ERROR): ", l)]
            lastline = out.split("\n")[-2]
            print "Python %s / %s: %s" % (py, db, lastline)
            if failures:
                for f in failures:
                    print "\t%s" % f
                print
