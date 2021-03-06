#! /usr/bin/env python
# -*- coding: ASCII -*-

"""
Methods called by the spoca_hfc_processing and spoca_hfc_classes modules.
@author: Xavier Bonnin (CNRS, LESIA)
@modified by: Christian RENIE (Obs.Paris, LESIA)
"""

import os
import sys
import time
from datetime import datetime, timedelta
import csv
import re
import cStringIO
import urllib2
import sqlite3
import suds
import copy
import tempfile
#import pyfits
import PIL
from PIL import ImageEnhance
import numpy as np
from sunpy.net import vso
from ssw import tim2jd
from astropy.io.votable import parse, is_votable
from astropy.io import fits
from scipy import ndimage
#sys.path.append('/home/ytaoufiq/SPOCA-IAS/SPOCA-AR/spoca/hfc/src/')
import sunpy
import sunpy.map
import sunpy.map.sources
import sunpy.instr
import sunpy.instr.aia
#from memory_profiler import profile
import sdo_client_idoc
import logging
from bs4 import BeautifulSoup
from jsoc_client import jsoc




# Import spoca hfc global variables
try:
    from spoca_hfc_globals import LOG, MEDOC_HQI_WSDL, \
        HFC_TFORMAT, MEDOC_TFORMAT, AIA_WAVES, \
        VSO_TFORMAT, SDAC_URL, TODAY, JSOC_IN_TFORMAT, \
        JSOC_OUT_TFORMAT, JSOC_URL, SAIO_URL, SAIO_TFORMAT, \
        INPUT_TFORMAT, DATA_DIRECTORY, OUTPUT_DIRECTORY, \
        MEDOC_URL, VSO_URL, BATCH_DIRECTORY, SDO_URL, \
        FITS_TFORMAT
except:
    sys.exit("Import failed in module spoca_hfc_methods :\
             \n\tspoca_hfc_globals module is required!")

# Import sdo_client_idoc variables
try:
    from sdo_client_idoc import search
except:
    sys.exit("Import failed in module spoca_hfc_methods :\
             \n\tsdo_client_idoc module is required!")


# Path definition
CURRENT_DIRECTORY = os.getcwd()


def query_medoc(instrument,
                tstart=None, tend=None,
                sample=None,
                min_wave=None, max_wave=None):

    """
    This method allows to query the MEDOC HELIO Interface.
    """

    instrument = instrument.upper()
    if (instrument == "EIT"):
        table = "soho_view"

        where_clause = "instrument," + instrument
        if (min_wave):
            where_clause += ";wavemin," + str(min_wave) + "/"
        if (max_wave):
            where_clause += ";wavemax,/" + str(max_wave)

        if (tstart):
            starttime = tstart.strftime(HFC_TFORMAT)
        if (tend):
            endtime = tend.strftime(HFC_TFORMAT)

        medoclist = []
        try:
            client = suds.client.Client(MEDOC_HQI_WSDL)
        except:
            LOG.error("Can not query MEDOC HQI!")
        else:
            votable = getattr(client.service, "Query")(
                STARTTIME=starttime,
                ENDTIME=endtime,
                FROM=table,
                WHERE=where_clause)
            medoc_header, medoc_data = parse_votable(votable)
            # print medoc_data
        for current_row in medoc_data:
            if ('T' in current_row['date_obs']):
                current_time_start = datetime.strptime(
                    current_row['date_obs'],
                    HFC_TFORMAT)
            else:
                datetime.strptime(current_row['date_obs'], MEDOC_TFORMAT)

            current_dict = {'fileid': current_row['address'],
                            'time_start': current_time_start,
                            'provider': "MEDOC",
                            'filename':
                            os.path.basename(
                                current_row['address']),
                            'min_wave': current_row['wavemin'],
                            'max_wave': current_row['wavemax']}
            if (medoclist.count(current_dict) == 0):
                medoclist.append(current_dict)
    return medoclist


# Method to query idoc server (only for AIA 1 min data)
def query_idoc(tstart, tend, cadence=['1 min'],
               waves=AIA_WAVES, local=False):

    """
    This method allows to query the IDOC SDO server.
    """

    # Case where input cadence is in seconds (int)
    if (type(cadence[0]) == int):
        cadence = cadence[0] / 60
        if (cadence <= 30):
            cadence = [str(cadence) + "m"]
        elif (cadence > 30) and (cadence <= 12 * 60):
            cadence = [str(cadence / 60) + "h"]
        else:
            cadence = [str(cadence / (60 * 24)) + "d"]
        # LOG.info("Cadence is %s",cadence[0])

    idoclist = []
    sdo_data_list = search(DATES=[tstart, tend],
                           WAVES=waves,
                           CADENCE=cadence)
    
    # Modif Pablo 2014-10-23 - Xavier 2015-03-05
    for current_row in sdo_data_list:
        if (local):
            date_str = str(current_row.date_obs).split()[0]
            time_str = str(current_row.date_obs).split()[1]
            if '.' in time_str:
                ms = time_str.split(".")[1]
                time_str = time_str.split(".")[0]
                ms_str = ms[0:2]
            else:
                ms_str = '00'
                
            current_fileid = current_row.ias_location + \
                "/S00000/image_lev1.fits"
            current_outputfilename = 'aia.lev1.' + str(current_row.wave) + \
                'A_' + date_str + 'T' + time_str + "." + \
                str(ms_str) + 'Z.image_lev1.fits'
        else:
            current_fileid = current_row.url
            current_outputfilename = None

#        current_dict = {'fileid': ,
        current_dict = {'fileid': current_fileid,
                        'time_start': current_row.date_obs,
                        'provider': "IDOC", 'filename': None,
                        'min_wave': current_row.wave,
                        'max_wave': current_row.wave,
                        'output_filename': current_outputfilename}

        if (idoclist.count(current_dict) == 0):
            idoclist.append(current_dict)

    return idoclist


def query_vso(instrument=None,
              tstart=None, tend=None,
              sample=None, pixels=None,
              resolution=1,
              min_wave=None, max_wave=None,
              unit_wave="Angstrom",
              nday=20):

    """
    This method allows to query the VSO server.
    """

    vsolist = []

    # Query vso
    client = vso.VSOClient()

    current_tstart = tstart
    loop = True
    while (loop):

        current_tend = current_tstart + timedelta(days=nday)
        # LOG.info(str(current_tstart)+" - "+str(current_tend))
        # Get file list at the first wavelength
        try:
            vso_resp = client.query(vso.attrs.Time(current_tstart,
                                    current_tend),
                                    vso.attrs.Instrument(instrument),
                                    vso.attrs.Sample(sample),
                                    vso.attrs.Resolution(resolution),
                                    vso.attrs.Pixels(pixels),
                                    vso.attrs.Wave(min_wave, max_wave,
                                                   waveunit=unit_wave))
        except:
            LOG.error("Querying vso server has failed!")
            loop = False
        else:
            if (vso_resp):
                tstart_i = []
                for resp in vso_resp:
                    time_start = datetime.strptime(resp.time.start,
                                                   VSO_TFORMAT)
                    if (time_start > tend):
                        loop = False
                        break

            if (float(resp.wave.wavemax) != float(max_wave)) or \
                    (float(resp.wave.wavemin) != float(min_wave)):
                continue
            current_row = {'fileid': SDAC_URL + resp.fileid,
                           'time_start': time_start,
                           'provider': resp.provider, 'filename': None,
                           'min_wave': resp.wave.wavemax,
                           'max_wave': resp.wave.wavemin}
            if (vsolist.count(current_row) == 0):
                vsolist.append(current_row)
                tstart_i.append(time_start)
            if (len(tstart_i) > 0):
                if (max(tstart_i) > current_tstart):
                    current_tend = max(tstart_i)

        current_tstart = current_tend

    if (current_tstart >= tend):
        loop = False

    return vsolist


def query_jsoc(ds, starttime, endtime,
               wavelength=None,
               timeout=180):

    """
    This method allows to query the JSOC AIA server.
    """

    # Define starttime and endtime (in jsoc cgi time format)
    #stime = starttime - timedelta(seconds=10)  # starttime - 10 sec.
    #etime = endtime + timedelta(seconds=10)  # endtime + 10 sec.
    stime = starttime
    etime = endtime
    stime = stime.strftime(JSOC_IN_TFORMAT)
    etime = etime.strftime(JSOC_IN_TFORMAT)

    if (ds == "aia.lev1"):
        ds_id = "aia__lev1"

    url = JSOC_URL + "/cgi-bin/ajax/show_info"
    url = url + "?ds=" + ds + "[" + stime + "-" + etime + "]"
    if (wavelength):
        url = url + "[?WAVELNTH=" + str(wavelength) + "?]"
    url = url + "&key=T_REC_index%2CT_OBS%2CWAVELNTH"

    try:
        LOG.info("Querying " + url)
        f = urllib2.urlopen(url, None, timeout)
    except urllib2.URLError, e:
        LOG.error("Can not open %s", url)
        LOG.error(e)
        return []
    else:
        flist = f.read().split("\n")[1:-1]

    jsoclist = []
    for current_row in flist:
        current_items = current_row.split()
        current_outputfilename = ds + '.' + str(current_items[2]) + \
                'A_' + str(current_items[1]) + '.image_lev1.fits'
        current_fileid = VSO_URL + "/cgi-bin/netdrms/drms_export.cgi?series="+ds_id
        current_fileid+=";compress=rice"
        record = str(current_items[2]) + '_' + str(current_items[0])+"-"+str(current_items[0])
        current_fileid = current_fileid+";record="+record
        
        if (wavelength):
            if (float(current_items[2]) != float(wavelength)):
                continue
            jsoclist.append({'fileid': current_fileid, 'filename': None,
                             'time_start':
                            datetime.strptime(current_items[1],
                                              JSOC_OUT_TFORMAT),
                             'provider': "JSOC",
                             'min_wave': current_items[2],
                             'max_wave': current_items[2],
                             'output_filename': current_outputfilename})
    return jsoclist

def query_jsoc2(ds, starttime, endtime,
               wavelength=None,
               timeout=180):

    """
    This method allows to query the JSOC AIA server.
    """

    stime = starttime
    etime = endtime
    stime = stime.strftime(JSOC_IN_TFORMAT)
    etime = etime.strftime(JSOC_IN_TFORMAT)

    j_soc = jsoc(ds, realtime=True, starttime=starttime, endtime=endtime, wavelength = wavelength, notify='christian.renie@obspm.fr')
    info = j_soc.show_info(key=["T_REC_index", "T_REC", "WAVELNTH"])

    jsoclist = []
    for current_row in info.split("\n")[1:-1]:
        current_items = current_row.split()
        current_outputfilename = ds + '.' + str(current_items[2]) + 'A_' + str(current_items[1]) + '.image_lev1.fits'
        
        if (wavelength):
            if (float(current_items[2]) != float(wavelength)):
                continue
            jsoclist.append({'fileid': None, 'filename': None,
                             'time_start':
                            datetime.strptime(current_items[1],
                                              '%Y-%m-%dT%H:%M:%SZ'),
                             'provider': "JSOC",
                             'min_wave': current_items[2],
                             'max_wave': current_items[2],
                             'output_filename': current_outputfilename})
    return jsoclist

def query_AIA_RT_data(wavelength=None, timeout=180):

    """
    This method allows to query the LMSAL AIA server for real time AIA data
    """

    urlBase = "http://sdowww.lmsal.com/sdomedia/SunInTime/mostrecent/"
    # build all YYYY/MM/DD string from between start and end time

    if (wavelength):
        extension = "_%04d.fits" % (wavelength)
    else:
        extension = '.fits'

    fileList = []
    try:
        url = urlBase
        LOG.info("Querying " + url)
        f = urllib2.urlopen(url, None, timeout)
    except urllib2.URLError, e:
        LOG.error("Can not open %s", url)
        LOG.error(e)
    else:
        soup = BeautifulSoup(f, 'html.parser')
        tmp =  [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(extension)]
        for f in tmp:
            fileList.append(f)

    # find the most recent file
    currentTime = datetime(1950, 1, 1)
    latestFile = ''
    for current_row in fileList:
        current_outputfilename = os.path.basename(current_row)
        time_start = datetime.strptime(current_outputfilename, 'AIA%Y%m%d_%H%M%S' + extension)
        if time_start > currentTime:
               latestFile = current_row
        
    lmsalList = []
    current_outputfilename = os.path.basename(latestFile)
    current_fileid = latestFile
    time_start = datetime.strptime(current_outputfilename, 'AIA%Y%m%d_%H%M%S' + extension)
    # build target filename which will be used for download
    filename = 'aia.lev1.' + str(int(wavelength)) + 'A_' + time_start.strftime('%Y-%m-%dT%H:%M:%S') + '.image_lev1.fits'
    lmsalList.append({'fileid': current_fileid,
                         'filename': filename,
                         'time_start': time_start,
                         'provider': urlBase,
                         'min_wave': wavelength,
                         'max_wave': wavelength,
                         'output_filename': filename})
#                         'output_filename': current_outputfilename})
    
    return lmsalList

def query_AIA_lmsal(starttime, endtime,
               wavelength=None,
               timeout=180):

    """
    This method allows to query the LMSAL AIA server for real time AIA data
    """

    stime = starttime
    etime = endtime

    urlBase = "http://sdowww.lmsal.com/sdomedia/SunInTime/"
    # build all YYYY/MM/DD string from between start and end time
    datePartList = []
    delta = timedelta(days=1)
    while stime <= etime:
        datePartList.append("%4s/%2s/%2s" % (stime.strftime("%Y"), stime.strftime("%m"), stime.strftime("%d")))
        stime = stime + delta 

    if (wavelength):
        extension = "_%04d.fits" % (wavelength)
    else:
        extension = '.fits'

    fileList = []
    for dt in datePartList:
        try:
            url = urlBase + dt
            print("Querying " + url)
            LOG.info("Querying " + url)
            f = urllib2.urlopen(url, None, timeout)
        except urllib2.URLError, e:
            LOG.error("Can not open %s", url)
            LOG.error(e)
        else:
            soup = BeautifulSoup(f, 'html.parser')
            tmp =  [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(extension)]
            for f in tmp:
                fileList.append(f)

    lmsalList = []
    for current_row in fileList:
        current_outputfilename = os.path.basename(current_row)
        current_fileid = current_row
        lmsalList.append({'fileid': current_fileid,
                         'filename': current_outputfilename,
                         'time_start': datetime.strptime(current_outputfilename, 'AIA%Y%m%d_%H%M%S' + extension),
                         'provider': urlBase,
                         'min_wave': wavelength,
                         'max_wave': wavelength,
                         'output_filename': current_outputfilename})
    
    return lmsalList

def query_saio(instrument="EIT",
               begindate=(TODAY - timedelta(days=1)),
               enddate=TODAY,
               min_wave=171.0, max_wave=171.0,
               resolution=1024,
               return_type="VOTABLE"):

    """
    Method to query the SAIO server, visit:
    http://ssa.esac.esa.int/ssa/aio/html/home_main.shtml
    """

    url_prod = SAIO_URL + "/product-action?"

    url_meta = SAIO_URL + "/metadata-action?"
    url_meta += "RESOURCE_CLASS=OBSERVATION&SELECTED_FIELDS=OBSERVATION"
    url_meta += "&QUERY=INSTRUMENT.NAME=%s" % (quote(instrument.upper(),
                                               single=True))
    url_meta += "+AND+OBSERVATION.BEGINDATE>=" \
        + quote(begindate.strftime(SAIO_TFORMAT), single=True)
    url_meta += "+AND+OBSERVATION.ENDDATE<=" \
        + quote(enddate.strftime(SAIO_TFORMAT), single=True)
    url_meta += "&RETURN_TYPE=%s" % (return_type.upper())

    LOG.info("Reaching %s", url_meta)
    buff = download_file(url_meta, get_buffer=True)

    tmp = tempfile.NamedTemporaryFile()
    try:
        tmp.write(buff.getvalue())
        tmp.seek(0)
        if (is_votable(tmp)):
            data = parse(tmp)
        else:
            data = read_csv(tmp.name, delimiter=",", quotechar="\"")
    finally:
        tmp.close()

    saiolist = []
    for row in data:
        if (row["SCIENCE_OBJECT.NAME"] != "Full Sun/Full Disk"):
            continue

        if ((float(row["OBSERVATION.WAVELENGTHRANGE"]) >= float(min_wave)) and
                (float(row["OBSERVATION.WAVELENGTHRANGE"])
                 <= float(max_wave))):
            current_fileid = url_prod \
                + "OBSERVATION.ID=%s" % (row["OBSERVATION.ID"])
            current_fileid += "&RETRIEVALTYPE=PRODUCTS&RESOLUTION=%i" \
                % (int(resolution))
            current_filename = row["OBSERVATION.FILENAME"]
            current_date = row["OBSERVATION.BEGINDATE"]

#            print current_fileid

            saiolist.append({'fileid': current_fileid,
                            'filename': current_filename,
                            'time_start': datetime.strptime(current_date,
                                                            MEDOC_TFORMAT),
                            'provider': "ESAC",
                            'min_wave': float(min_wave),
                            'max_wave': float(max_wave),
                            'output_filename': None})
    return saiolist


def sort_list(datalist, date_obs=None, dt_max=7200):

    """
    Method to sort one or two lists of dataset
    finding the nearest dates and times.
    """

    newlist = []
    if (type(datalist) is not list):
        LOG.error("Input argument datalist must be a list!")
        return None
    nlist = len(datalist)

    if (nlist == 1) and (date_obs is None):
        return list(datalist)
    elif (nlist == 1) and (date_obs is not None):
        for current_date in date_obs:
            dt = []
            for current_row in datalist[0]:
                dt.append(abs(total_sec(current_row['time_start']
                                        - current_date)))
            if (min(dt) < dt_max):
                index = dt.index(min(dt))
                newset = [datalist[0][index]]
                if (newlist.count(newset) == 0):
                    newlist.append(newset)
    elif (nlist == 2):
        jd1 = []
        jd2 = []
        if (date_obs is None) or (len(date_obs) == 0):
            date_obs = []
            for current_row in datalist[0]:
                date_obs.append(current_row['time_start'])
                jd1.append(sum(tim2jd(current_row['time_start'])))
        else:
            for current_row in datalist[0]:
                jd1.append(sum(tim2jd(current_row['time_start'])))

        for current_row in datalist[1]:
            jd2.append(sum(tim2jd(current_row['time_start'])))

        jd1 = np.array(jd1)
        jd2 = np.array(jd2)

        for current_date in date_obs:
            current_jd = np.array(sum(tim2jd(current_date)))

            dt1 = np.abs(current_jd - jd1)
            dt2 = np.abs(current_jd - jd2)

            dt1_min = np.min(dt1)
            dt2_min = np.min(dt2)
            # Time difference between two observations must
            # not exceed dt_min (in seconds)
            if (dt1_min * 24. * 3600 <= dt_max) \
                    and (dt2_min * 24. * 3600 <= dt_max):
                index1 = list(dt1).index(dt1_min)
                index2 = list(dt2).index(dt2_min)
                newset = [datalist[0][index1], datalist[1][index2]]
                if (newlist.count(newset) == 0):
                    newlist.append(newset)
    else:
        LOG.error("Empty datalist!")

    return newlist


# Method to return the list of input files to process
def build_filelist(observatory, instrument, wavelength, starttime, endtime,
                   cadence=None, dt_max=43200, local=False):

    observatory = observatory.lower()
    instrument = instrument.lower()

    if (type(wavelength) is not list):
        LOG.error("Input wavelength must be a list!")
        sys.exit(1)

    filelist = []
    datalist = []
    for wave in wavelength:
        if (instrument == "eit"):
            LOG.info("Retrieving list of files from ESAC (wavelength=%i)...",
                     wave)
            current_eit = query_saio(
                instrument=instrument,
                begindate=starttime, enddate=endtime,
                min_wave=wave, max_wave=wave,
                resolution=1024, return_type="CSV")

            if (current_eit):
                LOG.info("%i records returned", len(current_eit))
                datalist.append(current_eit)
            else:
                LOG.error("Can not retrieve list of files from ESAC!")
                return []
        elif (instrument == "aia"):
            if (cadence is None) or (cadence < 60):
                cadence = 60  # seconds
            LOG.info("Retrieving list of files (wavelength=%i)...",
                     wave)
            # use JSOC2 server (for real time data) if starttime in less than one month from today
            if starttime > (datetime.today() - timedelta(days=30)):
                current_jsoc = query_jsoc2("aia.lev1_nrt2", starttime, endtime, wavelength=wave, timeout=180)
            else:
                current_jsoc = query_jsoc("aia.lev1", starttime, endtime,
                wavelength=wave,
                timeout=180)
            if (current_jsoc):
                LOG.info("%i records returned", len(current_jsoc))
                datalist.append(current_jsoc)
            else:
                LOG.error("Can not retrieve list of files!")
                return []

    # If sample is provided, build a list of times
    # else use the full cadence of the first list of files loaded.
    LOG.info("Building list of files ...")
    timelist = None
    if (cadence is not None):
        timelist = []
        currenttime = starttime
        while (currenttime <= endtime):
            timelist.append(currenttime)
            currenttime += timedelta(seconds=int(cadence))

    # Sort the list(s) of files by increasing dates with the given cadence
    filelist = sort_list(datalist, date_obs=timelist, dt_max=dt_max)

    return filelist


def sqlite_query(sqlite_file, cmd, commit=False, fetchall=True):

    if not (os.path.isfile(sqlite_file)):
        LOG.error("Sqlite3 database file %s not found!", sqlite_file)
        sys.exit(1)

    try:
        conn = sqlite3.connect(sqlite_file)
        c = conn.cursor()
        c.execute(cmd)
        if (fetchall):
            resp = c.fetchall()
        else:
            resp = c.fetchone()
    except sqlite3.Error, e:
        LOG.error("Cannot query %s database, please check!",
                  sqlite_file)
        LOG.error("Error returned:\n %s", e)
        sys.exit(1)
    else:
        if (commit):
            conn.commit()
        conn.close()

    return resp


def sqlite_getcolname(db_file, table):

    cmd = "select * from sqlite_master"
    cmd += " where tbl_name = %s and type = \'table\'" % (quote(table))
    resp = sqlite_query(db_file, cmd)
    if (resp):
        colnames = re.findall("`([a-zA-Z0-9_]+)`", resp[0][-1])[1:]
        return colnames
    else:
        return None


def check_history(history_file, inputList):

    """
    Method to check in the given history file if
    data files have been already processed.
    """

    unprocessed = list(inputList)
    if not (os.path.isfile(history_file)):
        LOG.warning(history_file + " does not exist yet!")
        return unprocessed

    # Read checklist file
    fr = open(history_file, 'r')
    fileList = fr.read().split("\n")
    fr.close()

    for i, current_input in enumerate(inputList):
        current_fileid = current_input[0]["filename"]

        if (current_fileid is None):
            current_fileid = os.path.basename(current_input[0]["fileid"])

        if (current_fileid in fileList):
            unprocessed.remove(inputList[i])
            LOG.info(current_fileid + " already processed.")
        else:
            LOG.info(current_fileid + " not processed.")

    return unprocessed


def update_history(history_file, fileset):

    """
    Method to update the history file.
    """

    if (type(fileset) is not list):
        fileset = list(fileset)

    #current_fileset = fileset[0]

    try:
        with (open(history_file, 'a')) as fa:
            #current_fileid = current_fileset["filename"]

            #if (current_fileid is None):
            #    current_fileid = os.path.basename(current_fileset["fileid"])

            #fa.write(os.path.basename(current_fileid) + "\n")
            for current_fileset in fileset:
                fa.write(os.path.basename(current_fileset) + "\n")
        fa.close()        
    except ValueError:
        return False
    else:
        return True


def aia_preprocessing(file_name):
    hdulist = fits.open(file_name)
    hdulist[1].verify("fix")
    map=sunpy.map.sources.AIAMap(hdulist[1].data, hdulist[1].header)
    new_map=sunpy.instr.aia.aiaprep(map)
    del hdulist[1].data
    del hdulist[1].header
    hdulist.close()
    del map
    return new_map

def run_prep(file2prep, imageType,
             output_filename=None,
             data_directory=DATA_DIRECTORY,
             output_directory=OUTPUT_DIRECTORY,
             batch_directory=BATCH_DIRECTORY,
             clean_batch=False,
             overwrite=False):

    """
    Method to pre-process EIT or AIA data files
    calling SSW/EIT or SSW/AIA IDL programs.
    """
#    instru = imageType.lower()
    if not (os.path.isdir(output_directory)):
        LOG.error("%s output directory does not exist!", output_directory)
        return ""
    if not (os.path.isdir(data_directory)):
        LOG.error("%s data directory does not exist!", data_directory)
        return ""

    prep_file = ""
    if not (os.path.isfile(file2prep)):
        LOG.error("%s does not exist!", file2prep)
        return ""

    if (output_filename is None):
        basename = os.path.basename(file2prep) + ".prep"
    else:
        basename = os.path.basename(output_filename)

    prep_file = os.path.join(output_directory, basename)
    #print('basename  :', basename)
    new_map = aia_preprocessing(file2prep)
    LOG.info("Sucessfully ran aia_preprocessing !")
    #print('New_map quicklook on data !',new_map.data)
    #print('New_map quicklook on data !', new_map.meta)
    fits.writeto(output_directory+'/'+basename, new_map.data, new_map.meta,clobber = True, output_verify='fix')
    prep_file=output_directory+'/'+basename
    del new_map
    return prep_file


def download_file(url,
                  data_directory=".",
                  filename="",
                  timeout=180, tries=3,
                  wait=3,
                  rice_compression=False,
                  get_buffer=False):

    """
    Method to download a file.
    """

    if (rice_compression):
        url += ";compress=rice"

    target = ""
    for i in range(tries):
        try:
            connect = urllib2.urlopen(url, None, timeout)
        except urllib2.URLError, e:
            LOG.warning("Can not reach %s: %s [%s]", url, e, tries - i)
            time.sleep(wait)
            continue
        else:
            if (get_buffer):
                buff = cStringIO.StringIO(connect.read())
                return buff

            if not (filename):
                if ('Content-Disposition' in connect.info()):
                    filename = \
                        connect.info()['Content-Disposition'].split(
                                                                    'filename=')[1]
                    if (filename.startswith("'")) \
                            or (filename.startswith("\"")):
                        filename = filename[1:-1]
                    else:
                        filename = os.path.basename(url)
            target = os.path.join(data_directory, filename)
            if not (os.path.isfile(target)):
                try:
                    fw = open(target, 'wb')
                    fw.write(connect.read())
                except IOError as e:
                    LOG.error("Can not read %s!", target)
                    break
                else:
                    fw.close()
                    break
            else:
                #LOG.info("%s already exists",target)
                break
    return target


# Return a time in the form yyyymmddThhmmss
def output_date(date):
    return date.strftime("%Y%m%dT%H%M%S")


# Return hfc format date and time yyyy-mm-ddThh:mm:ss
def hfc_date(date):
    return date.strftime("%Y-%m-%dT%H:%M:%S")


# Method used in Python 2.6 to compute
# datetime.total_seconds() module operation.
def total_sec(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6


# Method to parse votable returned by the HQI
def parse_votable(votable):

    header = {}
    tabledata = []
    if not hasattr(votable, "RESOURCE"):
        return header, tabledata
    resource = votable.RESOURCE[0]

    # Add service's description to the header
    if (hasattr(resource, "DESCRIPTION")):
        header = {'DESCRIPTION': resource.DESCRIPTION}

    if (hasattr(resource, "INFO")):
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

    if not (hasattr(resource, "TABLE")):
        return header, tabledata

    # Add fields' info to the header
    if (hasattr(resource.TABLE[0], "FIELD")):
        field = []
        for current_row in resource.TABLE[0].FIELD:
            current_field = {}
            current_field['NAME'] = current_row._name
            current_field['DATATYPE'] = current_row._datatype
            if (hasattr(current_row, "_ucd")):
                current_field['UCD'] = current_row._ucd
            if (hasattr(current_row, "_utype")):
                current_field['UTYPE'] = current_row._utype
            if (hasattr(current_row, "_arraysize")):
                current_field['ARRAYSIZE'] = current_row._arraysize
            field.append(current_field)
        header['FIELD'] = field

    # Add data to the tabledata list
    if (hasattr(resource.TABLE[0].DATA[0], "TR")):
        for current_row in resource.TABLE[0].DATA[0].TR:
            current_tabledata = {}
            for i, current_td in enumerate(current_row.TD):
                current_tabledata[header['FIELD'][i]['NAME']] = current_td
                tabledata.append(current_tabledata)

    return header, tabledata


# Method to load input parameters written in the configuration file
def parse_configfile(configfile):
    args = dict()
    try:
            with open(configfile) as f:
                for line in f:
                    param = line.strip()
                    if param and param[0] != '#':
                        params = param.split('=', 1)
                        if len(params) > 1:
                            args[params[0].strip()] = params[1].strip()
                        else:
                            args[params[0].strip()] = None
    except IOError, why:
        raise Exception("Error parsing configuration file "
                        + str(configfile) + ": " + str(why))

    return args


# Method to setup logging
def setup_logging(filename=None,
                  quiet=False, verbose=False, debug=False):

    global logging
    if debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s: %(message)s')
    elif verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)-8s: %(message)s')
    else:
        logging.basicConfig(level=logging.CRITICAL, format='%(levelname)-8s: %(message)s')

    if quiet:
        logging.root.handlers[0].setLevel(logging.CRITICAL + 10)
    elif verbose:
        logging.root.handlers[0].setLevel(logging.INFO)
    elif debug:
        logging.root.handlers[0].setLevel(logging.DEBUG)
    else:
        logging.root.handlers[0].setLevel(logging.CRITICAL)

    if filename:
        import logging.handlers
        fh = logging.FileHandler(filename, delay=True)
        fh.setFormatter(logging.Formatter('%(asctime)s %(name)-\
                        12s %(levelname)-8s %(funcName)-12s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        if debug:
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)

        logging.root.addHandler(fh)


# Method to convert a fits format file to a image format file
# used for several years the convert command of ImageMagick (obsolete adn deleted from here)
# using the convert command of module Wand/Python equivalent to pythonmagick (Nov.2016 YT)

def fits2img(fitsfile, output_filename,
             colorspace=None, colorize=None,
             brightness=None, normalize=None,
             fill=None, tint=None, quality=None,
             overwrite=False, verbose=False):

    if not (os.path.isfile(fitsfile)):
        return False

    if (os.path.isfile(output_filename)) and not (overwrite):
        LOG.info("%s already exist!", output_filename)
        return True

    hdulist = fits.open(fitsfile)
    array=hdulist[0].data
    array_formatted = ((array -np.min(array))* 255 / (np.max(array)-np.min(array))).astype(np.int16)
    img_resu = PIL.Image.fromarray(array_formatted.T)
    #img_rot = img_resu.rotate(90)
    B = ImageEnhance.Brightness(img_resu.rotate(90).convert('RGB'))
    #B.enhance(6).convert('RGB').save(fitsfile[:-5]+'.jpg')
    #output_filename = B.enhance(6)
    try:
        #id = fitsfile.index('fits');
        #fname = fistfile[0:(id+1)]
        #B.enhance(6).convert('RGB').save(fitsfile[:-5]+'.jpg')
        B.enhance(6).convert('RGB').save(output_filename)
    except:   
        ret = False
    else:
        ret = True

    B=0
    del B
    del array
    del array_formatted
    del hdulist[0].data
    hdulist.close()
    del hdulist
    
    return ret

def read_csv(file, delimiter=';', quotechar="\""):

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
            LOG.warning("%s does not exists!", file)
            return None
        buff = open(file, 'rb')

    reader = csv.DictReader(buff, delimiter=delimiter)
    data = []
    for row in reader:
        data.append(row)

    return data


def write_csv(entries, output_file, fieldnames=None,
              delimiter=";", quotechar="\"",
              append_new=False, overwrite=False):

    """
    Method to write a csv format file
    providing data as a list of dictionnary.
    """
    if not (isinstance(entries, list)):
        LOG.error("Input entries must be a list!")
        return False

    if (fieldnames is None):
        fieldnames = entries[0].keys()

    header = {}
    for name in fieldnames:
        header[name] = name

    if (append_new):
        for entry in entries:
            for k, v in entry.iteritems():
                if (v is None):
                    entry[k] = ""
                else:
                    entry[k] = str(v)

    if (os.path.isfile(output_file)):
        LOG.warning("%s already exists!", output_file)
        if not (overwrite) and not (append_new):
            return True
        elif not (overwrite) and (append_new):
            new_entries = copy.copy(entries)
            csv_data = read_csv(output_file,
                                delimiter=delimiter,
                                quotechar=quotechar)
            for row in csv_data:
                if (row in entries):
                    new_entries.remove(row)
                    #LOG.warning("Current entry "
                     #           "already exists in %s: \n\t (%s)",
                      #          output_file, ", ".join(row))
            entries = new_entries

    if (append_new):
        a = "a"
    else:
        a = "wb"

    try:
        with open(output_file, a) as fw:
            writer = csv.DictWriter(fw, fieldnames,
                                    delimiter=delimiter,
                                    quotechar=quotechar,
                                    quoting=csv.QUOTE_MINIMAL,
                                    extrasaction='ignore')
            writer.writerow(header)
            for entry in entries:
                writer.writerow(entry)
    except ValueError:
        return False
    else:
        return True


# Module to get the full url of a soho/eit file providing its fileid
# GET_FILENAME=True --> returns the actual filename instead
def get_eit_url(fileid, provider="SDAC",
                get_filename=False):

    if (get_filename):
        return os.path.basename(fileid)

    provider = provider.upper()
    if (provider == "SDAC"):
        url = SDAC_URL
    elif (provider == "MEDOC"):
        url = MEDOC_URL
    else:
        LOG.error("Unknown data provider: %s", provider)
        return []

    if (fileid.startswith("/")):
        url = url + fileid
    else:
        url = fileid

    return url


# Module to get the url of a sdo file on the vso server providing its fileid
# GET_FILENAME=True --> returns the actual filename instead
def get_aia_url(fileid, provider="JSOC",
                get_filename=False):

    fileid = fileid.split(":")
    if (len(fileid) < 3):
        LOG.error("Wrong fileid format!")
        return ""

    ds = fileid[0]
    wave = fileid[1]
    recnum = fileid[2]

    provider = provider.upper()

    # Build url
    if (provider == "VSO"):
        url = VSO_URL
    elif (provider == "JSOC"):
        url = SDO_URL
    else:
        LOG.error("Unknown data provider: %s", provider)
        return ""

    url = url + "/cgi-bin/drms_export.cgi?series=" \
        + ds + ";compress=rice;record="
    url = url + wave + "_" + recnum + " -" + recnum

    if (get_filename):
        filename = ""
        tries = 3
        for i in range(tries):
            try:
                connect = urllib2.urlopen(url)
            except urllib2.URLError, e:
                LOG.warning("Can not reach %s: %s [%s]", url, e, tries - i)
                continue
            else:
                filename = \
                    connect.info()['Content-Disposition'].split('filename=')[1]
                if (filename.startswith("'")) or (filename.startswith("\"")):
                    filename = filename[1:-1]
                break
        return filename
    else:
        return url

#@profile
def load_fits(fitsfile):

    if not (os.path.isfile(fitsfile)):
        LOG.error("%s does not exist!", fitsfile)
        return None
    else:
	LOG.info("Opening %s ...", fitsfile)

    #hdulist = fits.open(fitsfile)
    #fitsheader = hdulist[0].header
    #data = hdulist[0].data
    fitsheader = fits.getheader(fitsfile)
    data = fits.getdata(fitsfile)

    header = dict(fitsheader)
    del fitsheader
    #del hdulist[0].data
    #hdulist.close()
    #del hdulist

    if (not ("DATE-OBS" in header) or
        not ('NAXIS1' in header) or
            not ('CDELT1' in header)):
        LOG.error("Required keywords are missing in %s!",
                  fitsfile)
        return None

#    if (header['NAXIS1'] != naxis):
#        LOG.error("%s fits file has an incorrect image size (NAXIS1=%i)!",
#                  fitsfile,header['NAXIS1'])
#        return None

    date_obs = header['DATE-OBS'].split(".")[0]
    header['DATE-OBS'] = datetime.strptime(date_obs, FITS_TFORMAT)
    if ('DATE_END' in header):
        date_end = header['DATE_END'].split(".")[0]
        header['DATE_END'] = datetime.strptime(date_end, FITS_TFORMAT)
    else:
        header['DATE_END'] = header['DATE-OBS']

    jdint, jdfrac = tim2jd(header['DATE-OBS'])
    header['JDINT'] = jdint
    header['JDFRAC'] = jdfrac

    if not ('QUALITY' in header):
        header['QUALITY'] = ""
    if not ('BSCALE' in header):
        header['BSCALE'] = 0.0
    if not ('BZERO' in header):
        header['BZERO'] = 0.0

    if not ('CENTER_X' in header):
        if ('CRPIX1' in header):
            header['CENTER_X'] = header['CRPIX1']
            header['CENTER_Y'] = header['CRPIX2']
        else:
            LOG.error("%s fits file has no CENTER_X or CRPIX1 keyword!",
                fitsfile)
            return None

    if not ('EXPTIME' in header):
        if ('EXP_TIME' in header):
            header['EXPTIME'] = header['EXP_TIME']
        else:
            header['EXPTIME'] = 0.0

    if not ('R_SUN' in header):
        if ('SOLAR_R' in header):
            header['R_SUN'] = header['SOLAR_R']
        else:
            header['R_SUN'] = 0.0

    if not ('SOLAR_B0' in header):
        header['SOLAR_B0'] = 0.0

    if ('D_SUN' in header):
        header['D_SUN'] = header['D_SUN'] * 1.0e-3
    elif ("DSUN_OBS" in header):
        header['D_SUN'] = header['DSUN_OBS'] * 1.0e-3
    elif ('HEC_X' in header):
        hec_x = header['HEC_X']
        hec_y = header['HEC_Y']
        hec_z = header['HEC_Z']
        header['D_SUN'] = np.sqrt(hec_x ** 2 + hec_y ** 2 + hec_z ** 2)
    else:
        header['D_SUN'] = 0.0

    return header, data


def quote(string, single=False):
    if (single):
        return "\'" + string + "\'"
    else:
        return "\"" + string + "\""


def compute_feat_stats(mask):

    """
    Compute some feature parameters (center of mass, number of pixels, intensity min/max/mean, etc.)
    """
    stats = {}

    # Getting center of mass coordinates of the feature in pixels
    lbl = ndimage.label(mask)[0]
    feat_xy_pix = ndimage.measurements.center_of_mass(mask, lbl)
    stats["FEAT_X_PIX"] = feat_xy_pix[0]
    stats["FEAT_Y_PIX"] = feat_xy_pix[1]

    # Number of pixels in the feature area
    stats["FEAT_AREA_PIX"] = len(np.where(mask > 0)[1])

    # Intensity min/max/mean
    stats["FEAT_MIN_INT"] = np.min(mask)
    stats["FEAT_MAX_INT"] = np.max(mask)
    stats["FEAT_MEAN_INT"] = np.mean(mask)

    return stats


# Class to use ordered dict (which is not implemented in Python 2.6)
class ordered_dict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._order = self.keys()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._order.remove(key)

    def order(self):
        return self._order[:]

    def ordered_items(self):
        return [(key, self[key]) for key in self._order]


def replace(var, pattern, value):

    if (var is dict):
        for k, v in var.iteritems():
            if (var[k] == pattern):
                var[k] = value
    elif (var is list):
        for i, v in enumerate(var):
            if (v == pattern):
                var[i] = value
    return var

if __name__ == "__main__":
	print "spoca_hfc_methods for spoca_hfc_classification module" 
