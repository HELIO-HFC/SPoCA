#! /usr/bin/env python

import sys
import subprocess
import argparse

def pycurl(url, QUIET=False, *args, **kwargs):

    cmd = "curl"

    if (args):
        for arg in args:
            cmd += " "+arg
    
    if (kwargs):
        for k,v in kwargs.iteritems():
            if (len(k) == 1):
                if (v): cmd += " -"+k+" "+v
            elif (len(k) > 1):
                if (v): cmd += " --"+k+" "+v
                
    cmd += " "+url

    if not (QUIET): print cmd
    proc = subprocess.Popen(cmd,shell=True,
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, error = proc.communicate()
    proc.wait()
    return output, error

if (__name__ == "__main__"):
    
    parser = argparse.ArgumentParser()
    parser.add_argument('url',nargs=1,help="url to fetch")
    Namespace = parser.parse_args()

    url = Namespace.url[0]
    del Namespace.url
    keys = {}
    
    for k,v in Namespace.__dict__.items(): keys[k] = v
    output, error = pycurl(url,**keys)
    print "output:"
    print output
    print "error:"
    print error

