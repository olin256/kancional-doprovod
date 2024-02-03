import os

def purify(fname):
    return os.path.splitext(os.path.basename(fname))[0]