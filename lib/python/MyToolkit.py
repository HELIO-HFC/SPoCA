#! /usr/bin/env python
# -*-coding:ASCII -*

"""
Module containing useful recurrent methods.
X.Bonnin (LESIA, CNRS), 11-JUL-2013
"""

import os
import sys
import urllib2
import socket
import time
import cStringIO
import csv
import sqlite3

def sqlite_get(sqlite_file,cmd):

    """Method to query a sqlite db"""
    if (sqlite_file is None):
        return None

    if not (os.path.isfile(sqlite_file)): 
        return None

    conn=sqlite3.connect(sqlite_file)
    c=conn.cursor()
    try:
        c.execute(cmd)
        c.close()
        response=[]
        for row in c: response.append(row)
    except:
        return False

    return response

def uniq(seq):

    """
    Method to remove replicated items for a list preserving order.
    """

    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]


def setup_logging(filename = None, quiet = False, verbose = False, debug = False):

    """Method to setup a logging instance"""

    import logging
    
    if debug:
        logging.basicConfig(level = logging.DEBUG, format='%(levelname)-8s: %(message)s')
    elif verbose:
        logging.basicConfig(level = logging.INFO, format='%(levelname)-8s: %(message)s')
    else:
        logging.basicConfig(level = logging.CRITICAL, format='%(levelname)-8s: %(message)s')
	
    if quiet:
        logging.root.handlers[0].setLevel(logging.CRITICAL + 10)
    elif verbose:
        logging.root.handlers[0].setLevel(logging.INFO)
    else:
        logging.root.handlers[0].setLevel(logging.CRITICAL)
	
    if filename:
        import logging.handlers
        fh = logging.FileHandler(filename, delay=True)
        fh.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(funcName)-12s %(message)s', 
                                          datefmt='%Y-%m-%d %H:%M:%S'))
        if debug:
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)
		
        logging.root.addHandler(fh)
        
def indices(alist,value):

    """
    Returns the indices for a given value in a list
    """
    
    ind = [item for item in range(len(alist)) if alist[item] == value]
    return ind


def read_csv(file,
             delimiter=';',
             quotechar=';',
             quiet=False):

    """
    Method to read a csv format file.
    """
    
    if (file.startswith("http:")) or \
        (file.startswith("ftp:")):
        try:
            stream = urllib2.urlopen(file).read()
            buff = cStringIO.StringIO(stream)
        except urllib2.HTTPError, e:
            print e.code
            return None
        except urllib2.URLError, e:
            print e.args
            return None
    else:
        if not (os.path.isfile(file)):
            if not (quiet): print "%s does not exists!" % (file)
            return None
        buff = open(file,'rb')
        
    reader = csv.DictReader(buff,delimiter=delimiter)
    data = []
    for row in reader:
        data.append(row)

    return data


def write_csv(content,output_file,fieldnames=None,
              delimiter=';',quotechar='"',overwrite=False):

    """
    Method to write a csv format file
    providing data as a list of dictionnary.
    """

    if (os.path.isfile(output_file)):
        if (overwrite):
            os.remove(output_file)
        else:
            print "%s already exist!" % (output_file)
            return output_file
    
    islist = isinstance(content,list)
    if not (islist):
        content = [content]

    if (fieldnames is None): fieldnames = content[0].keys()

    header={}
    for name in fieldnames: header[name] = name

    try:
        with open(output_file,"wb") as fw:
            writer = csv.DictWriter(fw,fieldnames,
                                    delimiter=delimiter,
                                    quotechar=quotechar,
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writerow(header)
            for row in content: 
                writer.writerow(row)
    except ValueError:
        return False
    else:
        return True


def download_file(url,
                  target_directory=".",
                  filename="",
                  tries=3,wait=3,
                  timeout=None,
                  quiet=False,
                  get_stream=False,
                  user=None,
                  passwd=None):

    """
    Method to download a file.
    """
    if user is not None and passwd is not None:
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        # this creates a password manager
        passman.add_password(None, url, user, passwd)
        # because we have put None at the start it will always
        # use this username/password combination for  urls
        # for which `url` is a super-url

        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        # create the AuthHandler

        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
	
    target = ""
    for i in range(tries):
        try:
            connect = urllib2.urlopen(url,None,timeout)
        except urllib2.HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code
            time.sleep(wait)
            continue
        except urllib2.URLError,e:
            if not (quiet): print "Can not reach %s: %s [%s]" % (url,e,tries-i)
            time.sleep(wait)
            continue
        except socket.timeout, e:
            if not (quiet): print "Timeout %s: %s [%s]" % (url,e,tries-i)
            time.sleep(wait)
            continue
        else:
            if (get_stream):
                content = connect.read()
                return content

            if not (filename):
                if (connect.info().has_key('Content-Disposition')):
                    filename = connect.info()['Content-Disposition'].split('filename=')[1]
                    if (filename.startswith("'")) or (filename.startswith("\"")):
                        filename=filename[1:-1]
                    else:
                        filename=os.path.basename(url)
                else:
                    filename=os.path.basename(url)
            target=os.path.join(target_directory,filename)
            if not (os.path.isfile(target)):
                try:
                    fw = open(target,'wb')
                    fw.write(connect.read())
                except IOError as e:
                    if not (quiet): print "Can not download %s!" % (url)
                    break
                else:
                    fw.close()
                    break
            else:
                if not (quiet): print "%s already exists" % (target)
                break
    return target


def add_quote(string,double=False):
    if (double):
        return "\"" + string + "\""
    else:
        return "\'" + string + "\'"
