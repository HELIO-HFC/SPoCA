#!/usr/bin/env python
# -*- coding: ASCII -*-

"""
Read and display info in a SPoCA map
@author: X.Bonnin (LESIA, CNRS)
"""

import os
import sys
import pyfits
import argparse
import numpy

map_type = None

if (__name__ == "__main__"):

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("map_file", nargs=1, help="Spoca map fits filepath")
    parser.add_argument("-d", "--data", action="store_true",help="print data")
    args = parser.parse_args()
    map_file = args.map_file[0]
    data_flag = args.data

    if not (os.path.isfile(map_file)):
        sys.exit("%s does not exist!", map_file)

    print "Opening %s" % (map_file)
    try:
        fits_data = pyfits.open(map_file)
    except IOError:
        sys.exit("Can not open %s: ", map_file)
    else:
            print "FITS content: "
            for entry in fits_data:
                print "%s ==========" % (entry.name)
                if (entry.name == "SEGMENTEDMAP"):
                    map_type = "MAP"
                elif (entry.name == "ACTIVEREGIONMAP"):
                    map_type = "AR"
                elif (entry.name == "CORONALHOLEMAP"):
                    map_type = "CH"
                print "HEADER:"
                print entry.header
                if (data_flag) :
                    print "DATA:"
                    print entry.data
                if (entry.data is not None) and (type(entry.data) is numpy.ndarray):
                    #print type(entry.data)
                    print numpy.amin(entry.data), numpy.amax(entry.data)
                print ""


    if (map_type is None):
        sys.exit("Unknown type of map: \n %s", map_type)

