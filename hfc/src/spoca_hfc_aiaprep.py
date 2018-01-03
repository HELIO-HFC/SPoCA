#!/usr/bin/python

import sys
import pyfits
import sunpy
import astropy.utils.compat.odict
#import ordereddict
import sunpy.instr
import sunpy.instr.aia



def aia_preprocessing(file_name):
    print(file_name)
    hdulist = pyfits.open(file_name)
    print(hdulist.info())
    hdulist[1].verify("fix")
    map=sunpy.map.sources.AIAMap(hdulist[1].data, hdulist[1].header)
    type(map.data)
    new_map=sunpy.instr.aia.aiaprep(map)
    print(new_map.data)
    print(new_map.meta)
    return new_map


new_map = aia_preprocessing(file_name)
