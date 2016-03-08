#! /usr/bin/env python

"""
This python module extracts the date and time of a list of spoca map files
X.Bonnin (LESIA) 
"""

__author__="Xavier Bonnin"
__version__="1.0.0"

import os, sys
import argparse, glob
from datetime import datetime


MAP_TFORMAT="%Y%m%dT%H%M%S"
OUTPUT_TFORMAT="%Y-%m-%dT%H:%M:%S"

def extract_date(mapfiles,quiet=False):
    
    dates=[]    
    for current_map in mapfiles:
        items = os.path.basename(current_map).split("_")
        if (len(items) != 4):
            if not (quiet): print "Wrong input file format: %s!" % (current_map)
            sys.exit(1)
        dates.append(datetime.strptime(items[2],MAP_TFORMAT))

    return dates

if (__name__ == "__main__"):

	parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('mapfiles',nargs='*',
                            help="List of map files")
	parser.add_argument('-n','--newest',action='store_true',
			    help="Print newest date")
 	parser.add_argument('-o','--oldest',action='store_true',
			    help="Print oldest date")    
        parser.add_argument('-Q','--Quiet',action='store_true',
                            help="Quiet mode")
	args = parser.parse_args()

        mapfiles = args.mapfiles
	dates = extract_date(mapfiles,quiet=args.Quiet)

        if (args.newest):
            print max(dates).strftime(OUTPUT_TFORMAT)
        elif (args.oldest):
            print min(dates).strftime(OUTPUT_TFORMAT)
        else:
            for current_date in dates:
                print current_date.strftime(OUTPUT_TFORMAT)
