import os
def run(cmd, *args):
    _in, out, err = os.popen3("%s %s" % (cmd, " ".join(args)))
    return out.readlines(), err.readlines()
