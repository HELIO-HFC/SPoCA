#! /usr/bin/env python

"""
HFC wrapper software for SPoCA tracking code
"""

import sys, os, socket
import logging, subprocess
import argparse
import glob
from datetime import datetime, timedelta
import time
import ftplib
import numpy as np
from math import sqrt

try:
    from spoca_hfc_globals import *
except:
    sys.exit("Import failed in module spoca_hfc_tracking :\n\tspoca_hfc_globals module is required!")

# Import classes for spoca hfc
try:
    from spoca_hfc_classes import tracking, hfc
except:
    sys.exit("Import failed in module spoca_hfc_tracking :\n\tspoca_hfc_classes module is required!")

# Import methods for spoca hfc
try:
    from spoca_hfc_methods import setup_logging, parse_configfile, \
                                write_csv, read_csv, output_date, ordered_dict, \
                                check_history, update_history, download_file
except:
    sys.exit("Import failed in module spoca_hfc_tracking :\n\tspoca_hfc_methods module is required!")


__author__ = "Xavier Bonnin"
__version__ = "1.10"
__date__ = "17-DEC-2013"

# Institut information
INSTITUT = "OBSPM"
PERSON = "Xavier Bonnin"
CONTACT = "xavier.bonnin@obspm.fr"
REFERENCE = "doi:10.1051/0004-6361/200811416"

# SPOCA version
VERSION = 3.01

# Hostname
HOSTNAME = socket.gethostname()

# Path definitions (defined for helio@siolino.obspm.fr)
EIT_CCP_BIN="/obs/helio/hfc/frc/spoca/bin/spoca_eit/tracking.x" # directory containing spoca executables for eit
#AIA_AR_CCP_BIN="/obs/helio/hfc/frc/spoca/bin/spoca_ar_aia/tracking.x" # directory containing spoca executables for aia/ar
AIA_AR_CCP_BIN="/data/renie/SPOCA-IAS/SPOCA-AR/spoca/src/sidc/releases/current/SPoCA/bin2/tracking.x" # directory containing spoca executables for aia/ar
AIA_CH_CCP_BIN="/obs/helio/hfc/frc/spoca/bin/spoca_ch_aia/tracking.x" # directory containing spoca executables for aia/ch

# Time inputs
LAUNCH_TIME = time.time()
TODAY = datetime.today()
HFC_TFORMAT="%Y-%m-%dT%H:%M:%S"
INPUT_TFORMAT = '%Y-%m-%dT%H:%M:%S'
CPT_TFORMAT="%Y%m%d%H%M%S"

# Default values for input parameters
STARTTIME = (TODAY - timedelta(days=10)).strftime(INPUT_TFORMAT) #starttime
ENDTIME = TODAY.strftime(INPUT_TFORMAT) #endtime
OUTPUT_DIRECTORY = "/obs/helio/hfc/frc/spoca/products"
MAP_DIRECTORY=OUTPUT_DIRECTORY

# Method to setup spoca_hfc_tracking
def setup_spoca_hfc(configfile, 
		    data_directory=MAP_DIRECTORY,
		    output_directory=OUTPUT_DIRECTORY):
	
	tracking_instance = tracking()
	tracking_instance.load_parameters(configfile)
	tracking_instance.set_parameter("version",VERSION)
	tracking_instance.set_parameter("data_directory",data_directory)
	tracking_instance.set_parameter("output_directory",output_directory)
        tracking_instance.set_parameter('observatory', tracking_instance.args["OBSERVATORY"])
        tracking_instance.set_parameter('bin', tracking_instance.args["CLASS_EXE"])
        tracking_instance.set_parameter('code', tracking_instance.args["CODE"])
	# Set SPOCA/EIT input parameters
       	#if (tracking_instance.args["imageType"] == "EIT"):
	#	tracking_instance.set_parameter("observatory","SoHO")
	#	tracking_instance.set_parameter("bin",EIT_CCP_BIN)
	#	if (tracking_instance.args["maps"] == "A"):
	#		tracking_instance.set_parameter("code","spoca-ar")
	#	elif (tracking_instance.args["maps"] == "C"):
	#		tracking_instance.set_parameter("code","spoca-ch")
	#	else:
	#		log.error("Unknown type of map: "+tracking_instance.args["maps"])
	#		sys.exit(1)
	# Set SPOCA/AIA input parameters		
	#elif (tracking_instance.args["imageType"] == "AIA"):
	#	tracking_instance.set_parameter("observatory","SDO")
	#	if (tracking_instance.args["maps"] == "A"):
	#		tracking_instance.set_parameter("bin", AIA_AR_CCP_BIN)
	#		tracking_instance.set_parameter("code", "spoca-ar")
	#	elif (tracking_instance.args["maps"] == "C"):
	#		tracking_instance.set_parameter("bin", AIA_CH_CCP_BIN)
	#		tracking_instance.set_parameter("code", "spoca-ch")
	#	else:
	#		log.error("Unknown type of map: "+tracking_instance.args["maps"])
	#		sys.exit(1)
	#else:
	#	log.error("Unknown imageType: "+tracking_instance.args["imageType"])
	#	sys.exit(1)

	ok, reason = tracking_instance.test_parameters()
	if ok:
		log.info("Spoca parameters in file %s seem ok", configfile)
		log.debug(reason)
	else:
		log.warn("Spoca parameters in file %s could be wrong", configfile)
		log.warn(reason)
	
	return tracking_instance

# make a local copy of existing track file for a given fileset of armaps.fits
def get_trackfile(fileset, codeName, observatoryName, trackFileDir, targetDir):

    """
    Copy track files corresponding to the given
    fileset into the target directory.
    """

    LOG.info("Building list of previous track files...")

    if not (os.path.isdir(targetDir)):
        LOG.error("%s does not exist!", targetDir)
        return []
    
    if "spoca-ar" in codeName:
        trackFileDir = trackFileDir + "/spoca-ar/results"
    elif "spoca-ch" in codeName:
        trackFileDir = trackFileDir + "/spoca-ch/results"

    # get years list from filename of fileset
    yearList = []
    for curr_maps in fileset:
        curDate = os.path.basename(curr_maps).split("_")[2]
        curYear = curDate[:4]
        if curYear not in yearList:
            yearList.append(curYear)
            
    # for each year retrieve existing track.csv files  
    ftp_server = trackFileDir.split("/")[2]
    trckFileList = []
    for year in yearList:
        ftp_dir = "/".join(trackFileDir.split("/")[3:])
        ftp_dir = ftp_dir + "/" + year
        print(ftp_dir)
        ftp = ftplib.FTP(ftp_server)
        ftp.login()
        ftp.cwd(ftp_dir)
        current_fileList = []
        #ftp.dir(current_fileList.append);
        ftp.retrlines('LIST *track.csv', current_fileList.append)
        ftp.quit()
        trckFileList.extend(["ftp://" + ftp_server + "/" + ftp_dir + "/" +
                                current_file.split()[-1]
                                for current_file in current_fileList])
                                
    # download previous csv track files    
    trackset = []
    for curr_maps in fileset:
        curDate = os.path.basename(curr_maps).split("_")[2]
        ftpDir = trackFileDir + "/" + curDate[:4]
	curTrackFileName="_".join([codeName, curDate,observatoryName,"track.csv"])
	curTrackFullPath = os.path.join(ftpDir,curTrackFileName)
        if curTrackFullPath in trckFileList:
            if ((curTrackFullPath.startswith("ftp")) or
                (curTrackFullPath.startwidth("http"))):
                target = download_file(
                curTrackFullPath,
                data_directory=targetDir,
                filename=os.path.basename(curTrackFullPath))        
                if (os.path.isfile(target)):
                    trackset.append(target)
        else:
            if (os.path.isfile(curTrackFullPath)):
                if (targetDir != os.path.dirname(curTrackFullPath)):
                    shutil.copy(curTrackFullPath, targetDir)
                trackset.append(target)       

    return trackset

# get previous track data from CSV files
def get_prev_trackdata(startDate, endDate, codeName, observatoryName, trackFileDir):

    """
    Return a list with tracking data between startDate and endDate
    """    
    trckFileList = []
    if trackFileDir.startswith('ftp'):
        if "spoca-ar" in codeName:
            trackFileDir = trackFileDir + "/spoca-ar/results"
        elif "spoca-ch" in codeName:
            trackFileDir = trackFileDir + "/spoca-ch/results"

        # get years list from filename of fileset
        startYear = startDate.year
        endYear = endDate.year
        yearList = []
        for i in range(startYear, endYear+1):
            yearList.append(i)
       
        # for each year retrieve existing track.csv files  
        ftp_server = trackFileDir.split("/")[2]
        for year in yearList:
            ftp_dir = "/".join(trackFileDir.split("/")[3:])
            ftp_dir = ftp_dir + "/" + str(year)
            print(ftp_dir)
            ftp = ftplib.FTP(ftp_server)
            ftp.login()
            ftp.cwd(ftp_dir)
            current_fileList = []
            #ftp.dir(current_fileList.append);
            ftp.retrlines('LIST *track.csv', current_fileList.append)
            ftp.quit()
            trckFileList.extend(["ftp://" + ftp_server + "/" + ftp_dir + "/" +
                                current_file.split()[-1]
                                for current_file in current_fileList])
    else:
        trckFileList = glob.glob(trackFileDir + "/*track.csv")
        #trckFileList = glob.glob(os.path.join(trackFileDir, "/*track.csv"))
            
    # load previous tracking data from csv track files 
    prevTrackingData = []
    for trackFileName in trckFileList:
        tmp = os.path.basename(trackFileName).split("_")[2]
        trckDate = datetime.strptime(tmp,'%Y%m%dT%H%M%S')
        if trckDate > startDate and trckDate < endDate:
            curData = read_csv(trackFileName)
            if (curData is None):
                 continue
            for td in curData:
                prevTrackingData.append(
                    {"DATE_OBS": td['DATE_OBS'],
                    "FEAT_X_PIX": td['FEAT_X_PIX'],
                    "FEAT_Y_PIX": td['FEAT_Y_PIX'],
                    "TRACK_ID":td['TRACK_ID'],
                    "TRACK_FILENAME":td['TRACK_FILENAME']})  

    return prevTrackingData

def load_trackid(trackset, feat_data):

    """
    Load track ids from list of
    track files, updating if
    feature matching occurs.
    """

    tdset = []
    tid = []
    for current_file in trackset:
        current_data = read_csv(current_file)
        if (current_data is None):
            continue
        for td in current_data:
            tdset.append([datetime.strptime(td['DATE_OBS'], INPUT_TFORMAT),
                          int(td['FEAT_X_PIX']),
                          int(td['FEAT_Y_PIX'])])
            tid.append(np.int64(td['TRACK_ID']))
    if (len(tid) == 0):
        return []
    max_tid = np.max(tid)

    track_id = []
    count = 1
    for i, curFeat in enumerate(feat_data):
    #for i, current_date in enumerate(feat_data['DATE_OBS']):
        current_set = [
            curFeat['DATE_OBS'],
            curFeat['FEAT_X_PIX'],
            curFeat['FEAT_Y_PIX']]

        if (current_set in tdset):
            index = tdset.index(current_set)
            track_id.append(tid[index])
        else:
            track_id.append(max_tid + count)
            count += 1

    return track_id

# Main script 
if __name__ == "__main__":  
    
    # Get the arguments
    parser = argparse.ArgumentParser(description='Launch spoca_hfc to track features.',
					 conflict_handler='resolve',
					 add_help=True)
    parser.add_argument('config_file',nargs=1,
			    help='path to the configuration file')
    parser.add_argument('-s','--starttime',nargs='?', 
			    default=STARTTIME,
			    help="start date and time ["+
			    STARTTIME+"]")
    parser.add_argument('-e','--endtime',nargs='?',
			    default=ENDTIME,
			    help="end date and time ["+
			    ENDTIME+"]")	
    parser.add_argument('-m','--map_directory',nargs='?',
	            default=None,help="Directory where spoca map files are stored")
    parser.add_argument('-o','--output_directory',nargs='?',
			    default=OUTPUT_DIRECTORY,
			    help='path to the output directory')
    parser.add_argument('-l','--log_file',nargs='?',default=None,
			help='Pathname of the log file to write')
    parser.add_argument('-h','--history_file',nargs='?',default=None,
			help='pathname of the file containing the history of processed files.')
    parser.add_argument('-C','--Clean_map',action='store_true',
	            help='clean the maps produced by SPOCA code after processing')
    parser.add_argument('-V','--Verbose', action='store_true', 
			    help='set the logging level to verbose at the screen')
    parser.add_argument('-D','--Download_maps', action='store_true', 
			    help='If set, then download map files from the hfc ftp server.')
    args = parser.parse_args()
	
    config_file = args.config_file[0]
    starttime = datetime.strptime(args.starttime,INPUT_TFORMAT)
    endtime = datetime.strptime(args.endtime,INPUT_TFORMAT)
    map_directory=args.map_directory
    output_directory = args.output_directory
    log_file = args.log_file
    history_file = args.history_file
    clean_map = args.Clean_map
    verbose = args.Verbose
    download_maps = args.Download_maps

    # Setup the logging
    setup_logging(filename=log_file,quiet = False, verbose = verbose, 
	              debug = False)	

    # Create a logger
    log = logging.getLogger(LOGGER)
    log.info("Starting spoca_hfc_tracking.py on "+HOSTNAME+" ("+TODAY.strftime(HFC_TFORMAT)+")")

    # Check map directory existence if local
    if not (map_directory.startswith("ftp")):
        if not (os.path.isdir(map_directory)):
	    log.warning("%s does not exist!", map_directory)
	    log.warning("use %s as a map directory",output_directory)
	    map_directory = output_directory

    # Check output directory existence
    if not (os.path.isdir(output_directory)):
	log.error("%s does not exist!", output_directory)
	sys.exit(1)
			
    # Check configuration file existence
    if not (os.path.isfile(config_file)):
	    log.error("%s does not exist!", configfile)
	    sys.exit(1)

    log.info("Setup spoca_hfc_tracking...") ; ttop=time.time()
    spoca_job = setup_spoca_hfc(config_file,
	    		    data_directory=map_directory,
		    	    output_directory=output_directory)
    log.info("Setup spoca_hfc_tracking...done    (took "+str(int(time.time() -ttop))+" seconds)")

    log.info("Setting instrument name --> %s",spoca_job.args['imageType'])
    log.info("Setting type of map to produce --> %s",spoca_job.args['maps'])
    log.info("Setting starttime --> %s",starttime.strftime(INPUT_TFORMAT))
    log.info("Setting endtime --> %s",endtime.strftime(INPUT_TFORMAT))
    log.info("Setting output_directory --> %s",str(output_directory))
    log.info("Setting data_directory --> %s",str(map_directory))    

    # Generage list of map file(s) to load
    mapList = spoca_job.get_maps(starttime,endtime,download_maps=download_maps)
    nmap = len(mapList)
    if (nmap == 0):
        log.warning("Empty map list!")
        sys.exit()
    else:
	log.info("%i map files found",nmap)
        
    # loading previous tracking data
    codeName = "_".join([spoca_job.code.lower(),"".join(str(VERSION).split("."))])
    start = starttime + timedelta(days=-15)
    end = starttime + timedelta(hours=-2)
    prevTrackData = get_prev_trackdata(start, end, codeName, spoca_job.observatory.lower(), map_directory)
    if len(prevTrackData) == 0:
        log.warning("No previous tracking data between %s and %s", starttime, endtime)
    else:
        log.warning("%s previous tracking data have been loaded", len(prevTrackData))
        
    # this array will be used as an history of newly track_id and maaping between old id and new ones
    oldId = []
    newId = []
    for data in prevTrackData:
        oldId.append(int(data["TRACK_ID"]))
        newId.append(int(data["TRACK_ID"]))
    trckIdHistory = {"ori":oldId, "new":newId}
    
    # If history file doesn't exist, create it
    if (history_file is None):
	history_file = os.path.join(output_directory,
				    "spoca_hfc_tracking_"+TODAY.strftime(CPT_TFORMAT)+".history")

    # Run spoca tracking program over maps set
    processed_maps=[]
    width=int(spoca_job.args.pop('max_files'))
    for i in range(nmap-width+1):
	current_set = mapList[i:i+width]
	if (spoca_job.run(current_set)):
	    log.info("Tracking has been done correctly.")
	else:
	    log.error("Tracking has failed, please check!")
            sys.exit(1)
                
        # Extract tracking data from map file and write output csv file	
	log.info("Extracting tracking data from updated maps...")
	for current_map in current_set:
	    current_date = os.path.basename(current_map).split("_")[2]
	    current_output_file="_".join([spoca_job.code.lower(),"".join(str(VERSION).split(".")),
					  current_date,spoca_job.observatory.lower(),"track.csv"])
	    current_output_file = os.path.join(output_directory,current_output_file)
                        
            if (spoca_job.args['maps'] == 'A'):
                spoca_job.hfc.feature_name = "ACTIVE REGIONS"
            else:
                spoca_job.hfc.feature_name = "CORONAL HOLES"
    
	    #urrent_track_data = hfc(spoca_job.args['maps']
	#			     ).map2track(current_map,
	#					 output_file=current_output_file)
            current_track_data = spoca_job.hfc.map2track(current_map, output_file=current_output_file)
	    if not (current_track_data):
		log.warning("%s has not been processed correctly!",current_map)
		continue
	    else:
		log.info("%s processed",current_map)

            # try to connect to previous track_id
            for i, curTrackData in enumerate(current_track_data):
                #first check if this track_id have already matched with an old one
                if curTrackData['TRACK_ID'] in trckIdHistory['ori']:
                    index = trckIdHistory['ori'].index(curTrackData['TRACK_ID'])
                    current_track_data[i]['TRACK_ID'] = trckIdHistory['new'][index]
                    log.info("%s already associated with previous track id %s", trckIdHistory['ori'][index], trckIdHistory['new'][index])
                    continue
                    
                curDate = datetime.strptime(curTrackData['DATE_OBS'],INPUT_TFORMAT)
                curX = curTrackData['FEAT_X_PIX']
                curY = curTrackData['FEAT_Y_PIX']
                minDist = 5000
                possibleMatch = None
                for prevtrckData in prevTrackData:
                    prevDate = datetime.strptime(prevtrckData['DATE_OBS'],INPUT_TFORMAT)                    
                    if (curDate - timedelta(days=2)) < prevDate:
                        prevX = int(prevtrckData['FEAT_X_PIX'])
                        prevY = int(prevtrckData['FEAT_Y_PIX'])
                        dist = sqrt((curX-prevX)**2 + (curY-prevY)**2)
                        if (dist == 0):
                            #log.info("%s match with track_id %s", curTrackData['TRACK_ID'],prevtrckData['TRACK_ID'])
                            possibleMatch = {"id": curTrackData['TRACK_ID'], "x":curX, "y":curY, "prev_id":prevtrckData['TRACK_ID'], "prev_x":prevX, "prev_y":prevY, "dist":dist}                            
                            break
                        if dist < 500 and dist < minDist:
                            #log.info("%s could match with track_id %s with a distance of %s", curTrackData['TRACK_ID'],prevtrckData['TRACK_ID'], dist)
                            #log.info("%s %s  %s %s", curX,prevX, curY, prevY)
                            minDist = dist
                            possibleMatch = {"id": curTrackData['TRACK_ID'], "x":curX, "y":curY, "prev_id":prevtrckData['TRACK_ID'], "prev_x":prevX, "prev_y":prevY, "dist":dist}
                
                # add a new id or create a new one if not match found
                print(possibleMatch)
                if possibleMatch is None:
                    newId = max(trckIdHistory['new']) + 1
                    trckIdHistory['ori'].append(curTrackData['TRACK_ID'])
                    trckIdHistory['new'].append(newId)
                    log.info("New track_id %s created for id %s", newId , curTrackData['TRACK_ID'])
                    current_track_data[i]['TRACK_ID'] = newId                    
                else:
                    log.info("%s matches with %s", curTrackData['TRACK_ID'] , possibleMatch["prev_id"])
                    if (curTrackData['TRACK_ID'] not in trckIdHistory['ori']): 
                        trckIdHistory['ori'].append(curTrackData['TRACK_ID'])
                        trckIdHistory['new'].append(int(possibleMatch["prev_id"]))
                    current_track_data[i]['TRACK_ID'] = int(possibleMatch["prev_id"])              
	    
            fieldnames = current_track_data[0].order()
	    if (write_csv(current_track_data,current_output_file,fieldnames=fieldnames)):
		log.info(current_output_file+" saved")
                if os.path.basename(current_map) not in processed_maps:
		    processed_maps.append(os.path.basename(current_map))
	    
	if (clean_map):
	    map2delete=os.path.join(map_directory,os.path.basename(current_set[0]))
	    if (os.path.isfile(map2delete)):
		os.remove(map2delete)
		log.info("%s deleted",map2delete)

    if (update_history(history_file,processed_maps)):
	log.info("%s has been updated.",history_file)
    else:
	log.error("%s has not been updated correctly!",history_file)
	sys.exit(1)
 
    log.info("Total elapsed time: "+str((time.time() - LAUNCH_TIME)/60.0)+" min.")
