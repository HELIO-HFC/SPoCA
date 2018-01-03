#! /usr/bin/env python

import os, sys
from suds.client import Client
import logging
import urllib
import subprocess
from PIL import Image

# Paths's definitions
qlk_dir = os.getcwd()

# url of hfc web service
wsdl_url = "http://voparis-helio.obspm.fr/hfc-hqi/HelioService?wsdl"

def parse_votable(votable):
    resource = votable.RESOURCE[0]
    
    # Add service's description to the header
    header = {'DESCRIPTION':resource.DESCRIPTION}
    
    # Add query's info to the header
    info = []
    for current_row in resource.INFO:
        current_info = {}
        if (hasattr(current_row, "_value")):
            current_info['VALUE'] = current_row._value
        if (hasattr(current_row, "value")):
            current_info['VALUE'] = current_row.value
        if (hasattr(current_row, "_name")):
            current_info['NAME'] = current_row._name
        if (hasattr(current_row, "name")):
            current_info['NAME'] = current_row.name
        info.append(current_info)
    header['INFO'] = info
    
    # Add fields' info to the header
    field = []
    if (hasattr(resource.TABLE[0],"FIELD")):
            for current_row in resource.TABLE[0].FIELD:
                current_field = {}
                current_field['NAME'] = current_row._name
                current_field['DATATYPE'] = current_row._datatype
                if (hasattr(current_row,"_ucd")):
                    current_field['UCD'] = current_row._ucd
                if (hasattr(current_row,"_utype")):
                    current_field['UTYPE'] = current_row._utype
                if (hasattr(current_row,"_arraysize")):
                    current_field['ARRAYSIZE'] = current_row._arraysize
                field.append(current_field)
            header['FIELD'] = field

    # Add data to the tabledata list
    tabledata = []
    if (hasattr(resource.TABLE[0].DATA[0],"TR")):
        for current_row in resource.TABLE[0].DATA[0].TR:
            current_tabledata = {}
            for i,current_td in enumerate(current_row.TD):
                current_tabledata[header['FIELD'][i]['NAME']]=current_td
                tabledata.append(current_tabledata)

    return header, tabledata

def query_hfc(STARTTIME=None,
              ENDTIME=None,
              TABLE="FRC_INFO",
              WHERE=None):
    
    client = Client(wsdl_url)
    response = client.service.Query(STARTTIME=STARTTIME,
                                    ENDTIME=ENDTIME,
                                    FROM=TABLE,
                                    WHERE=WHERE)
    return response

def show(quicklook_directory=qlk_dir,
         DELETE_QUICKLOOK=False,
         VERBOSE=True):

    #logging.basicConfig(level=logging.INFO)
    #logging.getLogger('suds.client').setLevel(logging.DEBUG

    starttime="2001-01-01T00:00:00"
    endtime="2001-01-10T23:59:59"
    table="VIEW_CH_HQI"

    if (VERBOSE): print "Querying HFC..."
    votable = query_hfc(TABLE=table,
                        STARTTIME=starttime,
                        ENDTIME=endtime)
    header, data = parse_votable(votable)
    if (VERBOSE): print str(len(data))+" feature(s) found."

    if (VERBOSE): print "Getting list of quicklooks..."
    qlkList = []
    for row in data:
        current_qlk = row['QCLK_URL']+"/"+row["QCLK_FNAME"]
        if not (current_qlk in qlkList):
            qlkList.append(current_qlk)
    if (VERBOSE): print str(len(qlkList))+" image(s) found."   

    # show image + contour of features
    imageFiles = []
    for current_image in qlkList:
        local_fname = os.path.join(quicklook_directory,
                                   os.path.basename(current_image))
        if not (os.path.isfile(local_fname)):
            if (VERBOSE): print "Downloading "+current_image+"..."
            ok = urllib.urlretrieve (current_image, local_fname)
            if not (os.path.isfile(local_fname)):
                print "Downloading "+current_image+" has failed!"
                continue
        imageFiles.append(local_fname)
            
                                    
    
        
if (__name__ == "__main__"):
    show()
