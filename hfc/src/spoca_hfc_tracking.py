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
                                write_csv, output_date, ordered_dict, \
                                check_history, update_history
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
VERSION = 2.00

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

    # Check map directory existence
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
