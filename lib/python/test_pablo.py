#! /usr/bin/env python

import os
import sys
import time
from datetime import datetime, timedelta
import re
import subprocess

try:
    from sdo_client_idoc import search
except:
    sys.exit("Import failed :\
             \n\tsdo_client_idoc module is required!")




d1 = datetime(2011,01,01,0,0,0)
d2 = d1 + timedelta(minutes=5)
sdo_data_list =search( DATES=[d1,d2], WAVES=['335','193'], CADENCE=['1m'], nb_res_max=2 )
print sdo_data_list
for data in sdo_data_list :
	date_str= str(data.date_obs).split()[0]
        hour_str=str(data.date_obs).split()[1]
	ms=hour_str.rsplit(".")[1]
	print ms[:2]

