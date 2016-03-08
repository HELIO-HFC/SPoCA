#! /usr/bin/env python
# -*- coding: ASCII -*-

"""
Contains global variables for spoca_hfc_processing, spoca_hfc_classes,
and spoca_hfc_methods modules.
@author: Xavier Bonnin (CNRS, LESIA)
"""

import os
import sys
import socket
from datetime import datetime
import logging

global CODE, VERSION, HOSTNAME, TODAY, \
    MAX_RUNTIME, SPOCA_HOME_DIR, \
    DATA_DIRECTORY, OUTPUT_DIRECTORY, \
    BATCH_DIRECTORY, \
    INPUT_TFORMAT, JSOC_TFORMAT, FITS_TFORMAT, \
    HFC_TFORMAT, CPT_TFORMAT, HELIO_TFORMAT, \
    VSO_TFORMAT, JSOC_IN_TFORMAT, JSOC_OUT_TFORMAT, \
    MEDOC_TFORMAT, IDOC_TFORMAT, SQL_TFORMAT, \
    LOG, DB_FILE, DB_TABLES, FTP_URL, \
    VSO_URL, SDO_URL, JSOC_URL, SDAC_URL, \
    MEDOC_URL, MEDOC_HQI_WSDL, JOBS, \
    AIA_WAVES, EIT_WAVES, \
    RSUN_KM, DSUN_KM, ARCSEC2DEG

# Code name
CODE = "SPOCA"

# Spoca release version
VERSION = "3.01"

# Hostname
HOSTNAME = socket.gethostname()

# today
TODAY = datetime.today()

# Maximum time in seconds after which a running job is automatically closed
MAX_RUNTIME = 3600

# Number of running jobs in parallel
JOBS = 1

# Default path definition (defined here for tycho.obspm.fr)
if ("SPOCA_HOME_DIR" in os.environ):
    SPOCA_HOME_DIR = os.environ['SPOCA_HOME_DIR']
else:
    # SPOCA_HOME_DIR=os.path.realpath(__file__)
    sys.exit("SPOCA_HOME_DIR: Undefined variable.")

if ("SPOCA_HFC_DIR" in os.environ):
    SPOCA_HFC_DIR = os.environ['SPOCA_HFC_DIR']
else:
    sys.exit("SPOCA_HFC_DIR: Undefined variable.")
    # SPOCA_HFC_DIR=os.path.join(SPOCA_HOME_DIR,"hfc")

if ("SPOCA_HFC_DB_DIR" in os.environ):
    DB_DIR = os.environ['SPOCA_HFC_DB_DIR']
else:
    sys.exit("SPOCA_HFC_DB_DIR: Undefined variable.")

OUTPUT_DIRECTORY = os.path.join(SPOCA_HOME_DIR, "products")
DATA_DIRECTORY = os.path.join(SPOCA_HOME_DIR, "data")
BATCH_DIRECTORY = os.path.join(SPOCA_HOME_DIR, "tmp")

# Date and time formats
INPUT_TFORMAT = '%Y-%m-%dT%H:%M:%S'
JSOC_TFORMAT = '%Y.%m.%d_%H:%M:%S'
FITS_TFORMAT = "%Y-%m-%dT%H:%M:%S"
HFC_TFORMAT = "%Y-%m-%dT%H:%M:%S"
CPT_TFORMAT = "%Y%m%d%H%M%S"
HELIO_TFORMAT = "%Y-%m-%dT%H:%M:%S"
VSO_TFORMAT = "%Y%m%d%H%M%S"
JSOC_IN_TFORMAT = "%Y.%m.%d_%H:%M:%S"
JSOC_OUT_TFORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
MEDOC_TFORMAT = "%Y-%m-%d %H:%M:%S.%f"
IDOC_TFORMAT = "%Y-%m-%d %H:%M:%S.%f"
SAIO_TFORMAT = "%Y-%m-%d"
SQL_TFORMAT = '%Y-%m-%d %H:%M:%S'

# Name of the logger for spoca_hfc
LOGGER = "spoca_hfc"
LOG = logging.getLogger(LOGGER)

# SPOCA HFC SQLITE3 database info
DB_TABLES = {"HISTORY": "PROCESSING_HISTORY",
                        "FRC_INFO": "FRC_INFO",
                        "OBSERVATORY": "OBSERVATORY"}
DB_FILE = os.path.join(DB_DIR, "spoca_hfc_db.sql")

# HFC distant FTP server url
FTP_URL = "ftp://ftpbass2000.obspm.fr/pub/helio"

# data provider server urls
VSO_URL = "http://vso2.tuc.noao.edu"
SDO_URL = "http://sdo4.nascom.nasa.gov"
JSOC_URL = "http://jsoc.stanford.edu"
SDAC_URL = "http://sohodata.nascom.nasa.gov"
MEDOC_URL = "http://medoc.ias.u-psud.fr"
SAIO_URL = "http://ssa.esac.esa.int/ssa/aio"
MEDOC_HQI_WSDL = "http://helio-hqi.ias.u-psud.fr/helio-soho/HelioService?wsdl"

# SDO AIA wavelength list
AIA_WAVES = ["171", "193"]

# SoHO EIT wavelength list
EIT_WAVES = ["171", "195"]

# Default cadence (None=Full res)
CADENCE = None

# Global variables
RSUN_KM = 6.955e5  # solar radius in km
DSUN_KM = 150.0e6  # Sun-Earth average distance in km
ARCSEC2DEG = 1. / 3600.
