#! /usr/bin/env python
# -*- coding: ASCII -*-

"""
Classes called by the spoca_hfc_processing module.
@author: Xavier Bonnin (CNRS, LESIA)
@modified by: Christian RENIE (Obs.Paris, LESIA)
"""

import os
import sys
import glob
import subprocess
import threading
import time
from datetime import datetime, timedelta
from math import radians
import ftplib
import numpy as np
#from numba import jit
#import ordereddict
#import pyfits
from astropy.io import fits
from improlib import image2chain, poly_area
from wcs import convert_hpc_hg
from ssw import tim2carr, get_sun
#from memory_profiler import profile
import gc
from gc import *
import spoca_hfc_methods
from jsoc_client import jsoc

# Import spoca hfc global variables
try:
    from spoca_hfc_globals import CODE, VERSION, LOG, \
        DATA_DIRECTORY, OUTPUT_DIRECTORY, BATCH_DIRECTORY, \
        DB_TABLES, HFC_TFORMAT, FTP_URL, \
        CPT_TFORMAT, RSUN_KM, DSUN_KM, TODAY
except:
    sys.exit("Import failed in module spoca_hfc_classes :\
             \n\tspoca_hfc_globals module is required!")

# Import methods for spoca hfc
try:
    from spoca_hfc_methods import parse_configfile, \
        download_file, write_csv, read_csv, run_prep, output_date, load_fits, \
        fits2img, hfc_date, ordered_dict, quote, \
        sqlite_query, sqlite_getcolname, compute_feat_stats
except:
    sys.exit("Import failed in module spoca_hfc_classes :\
             \n\tspoca_hfc_methods module is required!")


# CLASS TO RUN THE SPOCA SEGMENTATION =============================
class segmentation():

    def __init__(self):

        self.code = CODE
        self.version = VERSION
        self.wavelength = []
        self.config_file = None
        self.fileset = []
        self.localset = []
        self.prepset = []
        self.dataset = []
        self.qlkset = []
        self.batch = []
        self.params = None
        self.classmap = []
        self.featmap = []
        self.centers_file = ""
        self.outfnroot = ""
        self.db_file = None
        self.data_directory = DATA_DIRECTORY
        self.output_directory = OUTPUT_DIRECTORY
        self.batch_directory = BATCH_DIRECTORY
        self.hfc = hfc()

    # Method to load input parameters from configuration file
    def load_parameters(self, config_file):
        LOG.info("Parsing %s ...", config_file)
        self.params = parse_configfile(config_file)

        req_params = ["INSTITUT", "PERSON",
                      "OBSERVATORY", "INSTRUMENT",
                      "WAVELENGTH", "FEATURE",
                      "CLASS_EXE", "CLASS_CONFIG",
                      "GETMAP_EXE", "GETMAP_CONFIG"]

        for p in req_params:
            if not (p in self.params):
                LOG.error("%s parameter is not defined in %s!",
                          p, config_file)
                sys.exit(1)
            LOG.debug("Loading %s = %s", p, self.params[p])
            self.__dict__[p.lower()] = self.params.pop(p)

        self.wavelength = [float(w) for w in self.wavelength.split(",")]

        if not ("FEAT_MAX_AREA_DEG2" in self.params):
            self.params["FEAT_MAX_AREA_DEG2"] = None
        if not ("FEAT_MAX_HG_LONG" in self.params):
            self.params["FEAT_MAX_HG_LONG"] = None

        if (self.feature.upper() == "AR"):
            setattr(self.hfc, "feature_name", "ACTIVE REGIONS")
        elif (self.feature.upper() == "CH"):
            setattr(self.hfc, "feature_name", "CORONAL HOLES")
        else:
            return False, "Unknown feature type: " + self.feature + "!"

        self.config_file = config_file

    def set_parameter(self, parameter, value):

        """Method to set input parameter"""

        if (parameter in self.args):
            self.args[parameter] = value
        else:
            if (parameter in self.__dict__):
                self.__dict__[parameter] = value

    # Method to get input parameter's value
    def get_parameter(self, parameter):
        value = None
        if (parameter in self.args):
            value = self.args[parameter]
        else:
            if (parameter in self.__dict__):
                value = self.__dict__[parameter]
        return value

    def load_metadata(self, db_file):

        """Method to load metadata from HFC local database file"""

        LOG.info("Loading HFC metadata from %s ...", db_file)
        if not (os.path.isfile(db_file)):
            LOG.error("%s does not exist!", db_file)
            sys.exit(1)

        # Load Observatory metadata
        colnames = sqlite_getcolname(db_file, DB_TABLES["OBSERVATORY"])
        cmd = "SELECT %s FROM %s" % (", ".join(colnames),
                                     DB_TABLES["OBSERVATORY"])
        LOG.debug(cmd)
        resp = sqlite_query(db_file, cmd)
	all_obs_info = []
	obs_info = []
        if (resp):
            for row in resp:
                row_i = dict(zip(colnames, row))
                all_obs_info.append(row_i)
                if ((row_i["OBSERVAT"].lower() == self.observatory.lower()) and
                        (row_i["INSTRUME"].lower() == self.instrument.lower()) and
                        (float(row_i["WAVEMIN"]) * 10.0 in self.wavelength)):
                    obs_info.append(row_i)
            setattr(self.hfc, "obs_info", obs_info)
            LOG.info("Observatory metadata loaded")

        if (len(obs_info) == 0):
            LOG.error("No observatory metadata in %s!", db_file)
            sys.exit(1)

        # Load FRC_INFO metadata
        colnames = sqlite_getcolname(db_file, DB_TABLES["FRC_INFO"])
        cmd = "SELECT %s FROM %s " % (", ".join(colnames),
                                      DB_TABLES["FRC_INFO"])
        LOG.debug(cmd)
        resp = sqlite_query(db_file, cmd)
        if (resp):
            all_frc_info = []
            frc_info = []
            for row in resp:
                row_i = dict(zip(colnames, row))
                all_frc_info.append(row_i)
                if ((row_i["INSTITUT"].lower() == self.institut.lower()) and
                        (row_i["PERSON"].lower() == self.person.lower()) and
                        (row_i["FEATURE_NAME"].lower() == self.hfc.feature_name.lower())):
                    frc_info.append(row_i)
            setattr(self.hfc, "frc_info", frc_info)
            LOG.info("frc metadata loaded")

        if (len(frc_info) == 0):
            LOG.error("No frc_info metadata in %s!", db_file)
            sys.exit(1)

        # Copy observatory meta-data  into output csv file
        obs_filepath = os.path.join(self.output_directory,
                                    "_".join([self.hfc.outfnroot, "observatory"])
                                    + ".csv")
        if (write_csv(all_obs_info, obs_filepath,
                      overwrite=self.overwrite)):
            LOG.info("%s saved", obs_filepath)
            setattr(self.hfc, "obs_file", obs_filepath)
        else:
            LOG.error("%s has not been written correctly!", obs_filepath)
            self.terminated = True
            return False

        # Copy frc_info meta-data  into output csv file
        frc_filepath = os.path.join(self.output_directory,
                                    "_".join([self.hfc.outfnroot, "frc_info"])
                                    + ".csv")
        if (write_csv(all_frc_info, frc_filepath,
                      overwrite=self.overwrite)):
            LOG.info("%s saved", frc_filepath)
            setattr(self.hfc, "frc_file", frc_filepath)
        else:
            LOG.error("%s has not been written correctly!", frc_filepath)
            self.terminated = True
            return False

        return True

    # Method to test the validity of input parameters
    def test_parameters(self):

        if not os.path.isdir(self.output_directory):
            return False, "Output directory does not exists: "\
                + str(self.output_directory)
        if not os.access(self.output_directory, os.W_OK):
            return False, "Output directory is not writable: "\
                + str(self.output_directory)
        if not os.path.exists(self.class_exe):
            return False, "Could not find executable: " + str(self.class_exe)
        if not os.path.exists(self.getmap_exe):
            return False, "Could not find executable: " + str(self.getmap_exe)
        if not os.path.exists(self.class_config):
            return False, "Could not find spoca classification config. file: "\
                + str(self.class_config)
        if not os.path.exists(self.getmap_config):
            return False, "Could not find spoca get_map config. file: "\
                + str(self.getmap_config)

        arguments = self.build_arguments(["testfile"], "test")
        if not arguments:
            return False, "Could not create arguments"

        bin_path = os.path.join(self.class_exe)
        if not (os.path.isfile(bin_path)):
            return False, bin_path + " does not exist!"
        test_args = [bin_path] + arguments + ['--help']
        process = subprocess.Popen(
            test_args, shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (output, error) = process.communicate()
        if process.returncode != 0:
            return False, "Arguments could be wrong :" \
                + ' '.join(test_args) + "\nreturned error: " + error
        else:
            return True, ""

    # Method to build the list of input arguments
    # to provide to the classification.x program
    def build_arguments(self, fitsfiles, name,
                        config_file=None, centers_file=None):

        arguments = list()
        if (hasattr(self, "args")):
            for key, value in self.args.items():
                if len(key) > 1:
                    arguments.append("--" + key)
                else:
                    arguments.append("-" + key)
                if value:
                    arguments.append(value)

        arguments.extend(['-O', os.path.join(self.output_directory, name)])

        if not (config_file is None):
            arguments.extend(['-C', config_file])

        if not (centers_file is None):
            arguments.extend(['-c', centers_file])

        for fitsfile in fitsfiles:
            arguments.append(os.path.abspath(fitsfile))

        return arguments

    # Method to run classification
    def run_classification(self, fileList,
                           map_rootname=None,
                           overwrite=False,
                           verbose=True,
                           debug=False):

        """
        Method to run spoca classification program
        """
        output_directory = self.output_directory

        # Check input file list
        if (fileList):
            fileList = list(fileList)
            LOG.info("Running spoca on files %s", " and ".join(fileList))
        else:
            LOG.error("No enough input argument!")
            return None

        # Check existence of output directory
        if not (os.path.isdir(output_directory)):
            LOG.error("%s does not exist!", output_directory)
            return None

        # Build path to spoca executable
        spoca_bin = self.class_exe
        if not (os.path.isfile(spoca_bin)):
            LOG.error("%s does not exist!", spoca_bin)
            return None

        # Build path to spoca config file
        spoca_config = self.class_config
        if not (os.path.isfile(spoca_config)):
            LOG.error("%s does not exist!", spoca_config)
            return None

        # Check that spoca maps for current
        # observations have not already been produced
        if (map_rootname is None):
            map_rootname = "_".join([self.outfnroot.lower(),
                                    "".join(str(self.version).split(".")),
                                    self.observatory.lower()]) + "."
        current_map = os.path.join(output_directory, map_rootname)

        if not (os.path.isfile(current_map)) or (overwrite):
        # Build and run spoca command
            spoca_args = self.build_arguments(
                fileList, current_map,
                config_file=spoca_config,
                centers_file=self.centers_file)
            spoca_cmd = [spoca_bin] + spoca_args
            LOG.debug("Running spoca classification:\
             \n\t" + " ".join(spoca_cmd))
            spoca_process = subprocess.Popen(
                spoca_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False)
            output, errors = spoca_process.communicate()
            if spoca_process.wait() == 0:
                LOG.info("Sucessfully ran spoca command:\
                          \n\t %s, output: %s, errors: %s",
                          ' '.join(spoca_cmd), str(output), str(errors))
            else:
                LOG.error("Error running spoca command:\
                          \n\t %s, output: %s, errors: %s",
                          ' '.join(spoca_cmd), str(output), str(errors))
                current_map = None
            #LOG.info("Running --> "+" ".join(spoca_cmd)+"...done")

        return current_map

    # Method to run classification
    def run_getmap(self, prepfiles, segmap_file,
                   map_rootname=None,
                   overwrite=False,
                   verbose=True,
                   debug=False):

        """
        Method to run spoca get_map program
        """

        output_directory = self.output_directory

        # Check input map file existence
        if not (os.path.isfile(segmap_file)):
            LOG.error("%s does not exist!", segmap_file)
            return None

        # Check existence of output directory
        if not (os.path.isdir(output_directory)):
            LOG.error("%s does not exist!", output_directory)
            return None

        # Build path to spoca executable
        spoca_bin = self.getmap_exe
        if not (os.path.isfile(spoca_bin)):
            LOG.error("%s does not exist!", spoca_bin)
            return None

        # Build path to spoca config file
        spoca_config = self.getmap_config
        if not (os.path.isfile(spoca_config)):
            LOG.error("%s does not exist!", spoca_config)
            return None

        # Check that spoca maps for current observations
        # have not already been produced
        if (map_rootname is None):
            if (self.feature == "ACTIVE REGIONS"):
                ext = "ar"
            elif (self.feature == "CORONAL HOLES"):
                ext = "ch"
            else:
                LOG.error("Unknown feature: %s!", self.feature)
                return None

            map_rootname = "_".join([self.outfnroot.lower(),
                                     "".join(str(self.version).split(".")),
                                     self.observatory.lower()]) \
                + ".%smap.fits" % (ext)
        current_map = os.path.join(output_directory, map_rootname)

        if not (os.path.isfile(current_map)) or (overwrite):
        # Build and run spoca command
            spoca_args = self.build_arguments(
                [segmap_file,prepfiles[0]], current_map,
                config_file=spoca_config)
            spoca_cmd = [spoca_bin] + spoca_args
            LOG.debug("Running SPoCA get map: \n\t" + " ".join(spoca_cmd))
            spoca_process = subprocess.Popen(
                spoca_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False)
            output, errors = spoca_process.communicate()
            if spoca_process.wait() == 0:
                LOG.debug("Sucessfully ran spoca command:\
                          \n\t %s, output: %s, errors: %s",
                          ' '.join(spoca_cmd), str(output), str(errors))
            else:
                LOG.error("Error running spoca command:\
                          \n\t %s, output: %s, errors: %s",
                          ' '.join(spoca_cmd), str(output), str(errors))
                current_map = None
            #LOG.info("Running --> "+" ".join(spoca_cmd)+"...done")
        else:
            LOG.info("%s already exists!", current_map)

        return current_map


# Class to run spoca_hfc job using threading module (segmentation only)
class spoca_hfc(threading.Thread, segmentation):

    def __init__(self,
                 job_id=1,
                 write_qlk=True,
                 overwrite=False,
                 debug=False):

        threading.Thread.__init__(self)
        self.setDaemon(True)
        segmentation.__init__(self)
        self.terminated = False
        self.success = False
        self._stopevent = threading.Event()
        self.job_id = job_id
        self.status = " "
        self.comment = " "
        self.timer = None
        self.write_qlk = write_qlk
        self.overwrite = overwrite
        self.debug = debug

    def set_parameter(self, parameter, value):

        """Method to set input parameter"""

        if (hasattr(self, "args")) and (parameter in self.args):
            self.args[parameter] = value
        else:
            if (parameter in self.__dict__):
                self.__dict__[parameter] = value

    def isprocessed(self, setid=False, offset=0):

        """Method to check in the sqlite3 database
        if the current fileset has been already processed
        or not"""

        if self.fileset[0]["fileid"] is not None:
            fileid = self.fileset[0]["fileid"]
        else:
            fileid = self.fileset[0]["output_filename"]
        # if no db_file provided, then process fileset anyway
        if (self.db_file is None):
            return False

        if not (hasattr(self.hfc, "obs_info")):
            LOG.error("Observatory information have not been loaded!")
            sys.exit(1)
        observatory_id = self.hfc.obs_info[0]["ID_OBSERVATORY"]

        if not (hasattr(self.hfc, "frc_info")):
            LOG.error("FRC information have not been loaded!")
            sys.exit(1)
        frc_info_id = self.hfc.frc_info[0]["ID_FRC_INFO"]

        cmd = "SELECT ID FROM %s " % (DB_TABLES["HISTORY"])
        cmd += " WHERE (OBSERVATORY_ID=%s)" % (observatory_id)
        cmd += " AND (FRC_INFO_ID=%s)" % (frc_info_id)
        cmd += " AND (FILE_ID=%s)" % (quote(fileid))
        LOG.debug(cmd)
        resp = sqlite_query(self.db_file, cmd, fetchall=False)

        if (resp is None) or (len(resp) == 0):
            cmd = "SELECT max(ID) FROM " + DB_TABLES["HISTORY"]
	    LOG.debug(cmd)
	    job_id = sqlite_query(self.db_file,cmd,
                              fetchall=False)[0]
	    if job_id == None:
		job_id = 0	
	    self.job_id = int(job_id) + 1 + offset
            return False
        else:
            self.job_id = int(resp[0])
            return True

    def update_db(self):

        """Method to update the spoca hfc sqlite3 database"""

         # if no db_file provided, then just exit method
        if (self.db_file is None):
            return True

        cmd = "SELECT ID FROM %s" % (DB_TABLES["HISTORY"])
        cmd += " WHERE (ID=%i)" % (self.job_id)
        LOG.debug(cmd)
        if self.fileset[0]["fileid"] is not None:
            fileid = self.fileset[0]["fileid"]
        else:
            fileid = self.fileset[0]["output_filename"]
        isentry = sqlite_query(self.db_file, cmd, fetchall=False)
        if not (isentry):
            cmd2 = ("INSERT INTO %s VALUES "
                "(%i,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")\
                % (
                DB_TABLES["HISTORY"],
                self.job_id,
                self.hfc.obs_info[0]["ID_OBSERVATORY"],
                self.hfc.frc_info[0]["ID_FRC_INFO"],
                quote(self.hfc.init_info[0]["DATE_OBS"]),
                quote(fileid),
                quote(self.classmap),
                quote(self.hfc.init_file),
                quote(self.hfc.feat_file),
                quote("None"),
                quote(TODAY.strftime(HFC_TFORMAT)),
                quote("None"),
                quote(self.status),
                quote(self.comment))
        elif (self.overwrite) and (isentry):
            cmd2 = ("UPDATE %s SET OBSERVATORY_ID=%s,"
                            "FRC_INFO_ID=%s,DATE_OBS=%s, "
                            "FILE_ID=%s,MAP_FILE=%s,INIT_FILE=%s,"
                            "FEAT_FILE=%s,TRACK_FILE=%s, "
                            "FEAT_RUN_DATE=%s,TRACK_RUN_DATE=%s, "
                            "STATUS=%s, COMMENT=%s WHERE ID=%i") \
                % (
                DB_TABLES["HISTORY"],
                self.hfc.obs_info[0]["ID_OBSERVATORY"],
                self.hfc.frc_info[0]["ID_FRC_INFO"],
                quote(self.hfc.init_info[0]["DATE_OBS"]),
                quote(fileid),
                quote(self.classmap),
                quote(self.hfc.init_file),
                quote(self.hfc.feat_file),
                quote("None"),
                quote(TODAY.strftime(HFC_TFORMAT)),
                quote("None"),
                quote(self.status),
                quote(self.comment),
                self.job_id)
        else:
            return True

        LOG.debug(cmd2)
        void = sqlite_query(self.db_file, cmd2, fetchall=False, commit=True)

        cmd = "SELECT ID FROM %s" % (DB_TABLES["HISTORY"])
        cmd += " WHERE (ID=%i)" % (self.job_id)
        LOG.debug(cmd)
        isentry = sqlite_query(self.db_file, cmd, fetchall=False)

        if (isentry):
            return True
        else:
            return False
 #   @profile
    def run(self):

        """Method to run the spoca hfc job"""

        self.timer = time.time()

        fileset = self.fileset

        hfc = self.hfc
        observatory = self.observatory
        instrument = self.instrument
        data_directory = self.data_directory
        output_directory = self.output_directory
        batch_directory = self.batch_directory
        nfile = len(fileset)

        # For SDO data, download RICE compressed files and use jpg
        if (observatory.upper() == "SDO"):
            rice_compression = False
            qlk_ext = ".jpg"
            qlk_quality = 80
        elif (observatory.upper() == "SOHO"):
            rice_compression = False
            qlk_ext = ".jpg"
            qlk_quality = 95

        if (nfile == 0):
            LOG.warning("List of input files is empty.")
            self.terminated = True
            return False

        for i, current_set in enumerate(fileset):
            if current_set["fileid"] is None:
                starttime = current_set["time_start"]
                endtime = current_set["time_start"]
                wavelength = current_set["min_wave"]
                fnParts = current_set["output_filename"].split('.')
                ds = fnParts[0] + '.' + fnParts[1]
                j_soc = jsoc(ds, realtime=True, starttime=starttime, endtime=endtime, wavelength = wavelength, notify='christian.renie@obspm.fr', verbose=True)
                localFile = j_soc.get_fits_url_quick(output_dir=data_directory)
                current_output_filename = current_set["output_filename"]
                current_url = current_set["output_filename"]
                current_file = current_set["output_filename"]
            else:
                current_file = current_set["fileid"]
                current_output_filename = current_set["output_filename"]

                # If input filepaths are urls, then download file
                current_url = ""
                if (current_file.startswith("http:")) or \
                        (current_file.startswith("ftp:")):
                    current_url = current_file

                    LOG.info("Fetching %s...", current_file)
                    localFile = download_file(
                        current_file,
                        filename=current_set["filename"],
                        data_directory=data_directory,
                        rice_compression=rice_compression)                
                else:
                    localFile = current_file
            #if (len(localFile) == 0):
            if localFile is None:
                LOG.error("Downloading %s has failed!", current_file)
                self.terminated = True
                return False
            else:
                LOG.info("%s downloaded", localFile)
            self.localset.append(localFile)

            LOG.info("Pre-processing %s file...", localFile)
            file2process = run_prep(localFile, instrument,
				    output_filename=current_output_filename,
                                    data_directory=data_directory,
                                    output_directory=output_directory,
                                    batch_directory=batch_directory)
            LOG.info("file2process is %s ...", file2process)
            if (len(file2process) == 0):
                LOG.error("Pre-processing %s file...failed", localFile)
                self.terminated = True
                return False
            else:
                LOG.info("%s saved", file2process)
                self.prepset.append(file2process)

            # Load FITS header info for _init.csv file
            current_header, current_data = load_fits(file2process)
            if (current_header is None):
                self.terminated = True
                return False

            self.dataset.append(current_data)
            del current_data
            # Write quicklook image
            current_header['QCLK_FNAME'] = ""
            if (self.write_qlk):
                current_qlkfilename = os.path.basename(file2process)
                if ((current_qlkfilename.endswith(".fits"))
                        or (current_qlkfilename.endswith(".fts"))):
                    current_qlkfilename = \
                        current_qlkfilename.rsplit('.', 1)[0] + qlk_ext
                elif (current_qlkfilename.endswith(".prep")):
                    current_qlkfilename = \
                        current_qlkfilename.rsplit('.', 2)[0] + qlk_ext
                else:
                    current_qlkfilename = current_qlkfilename + qlk_ext
                current_qlk = os.path.join(output_directory,
                                           current_qlkfilename)

                if (fits2img(file2process, current_qlk,
                             normalize=True,
                             quality=qlk_quality)):
                    LOG.info(current_qlk + " saved")
                    current_header['QCLK_FNAME'] = current_qlk
                    self.qlkset.append(current_qlk)
                else:
                    LOG.error("%s has not been saved correctly!", current_qlk)
                    self.terminated = True
                    return False

            obs_id_i = hfc.obs_info[i]["ID_OBSERVATORY"]

            if not (hfc.add_entry(
                "init_info",
               ID_OBSERVATIONS=i + 1,
               OBSERVATORY_ID=obs_id_i,
               DATE_OBS=hfc_date(current_header['DATE-OBS']),
               DATE_END=hfc_date(current_header['DATE_END']),
               JDINT=current_header['JDINT'],
               JDFRAC=current_header['JDFRAC'],
               C_ROTATION=current_header['CAR_ROT'],
               BSCALE=current_header['BSCALE'],
               BZERO=current_header['BZERO'],
               BITPIX=current_header['BITPIX'],
               EXP_TIME=current_header['EXPTIME'],
               NAXIS1=current_header['NAXIS1'],
               NAXIS2=current_header['NAXIS2'],
               CDELT1=current_header['CDELT1'],
               CDELT2=current_header['CDELT2'],
               R_SUN=current_header['R_SUN'],
               CENTER_X=current_header['CENTER_X'],
               CENTER_Y=current_header['CENTER_Y'],
               QUALITY=current_header['QUALITY'],
               FILENAME=os.path.basename(localFile),
               FILE_FORMAT="FITS",
               DATA_TYPE="IMAGE",
               TIME_ORIGIN=observatory.upper(),
               TIME_SCALE="UTC",
               SPATIAL_FRAME_DESC=
               "See JSOC_Keywords_for_metadata.pdf document",
               SPATIAL_FRAME_TYPE="helioprojective-cartesian coordinates",
               SPATIAL_ORIGIN=observatory.upper(),
               PROCESSING_LVL="3",
               #COMMENT=current_header['COMMENT'],
               LOC_FILENAME=localFile,
               URL=current_url,
               QCLK_FNAME=current_header['QCLK_FNAME'],
               QCLK_URL="",
               SOLAR_B0=current_header['SOLAR_B0'],
               D_SUN=current_header['D_SUN'])):
                LOG.error("hfc_instance has no attribute init_info!")
                self.terminated = True
                del current_header
                return False
            gc.collect()
            
        if (len(self.dataset) != nfile):
            LOG.warning("Empty set!")
            self.terminated = True
            return False
        else:
            date_obs = datetime.strptime(hfc.init_info[0]['DATE_OBS'],
                                         HFC_TFORMAT)

        # Write observations meta-data into a csv file
        output_filename = "_".join([hfc.outfnroot,
                                    output_date(date_obs),
                                    observatory.lower(), "init"])\
            + ".csv"
        init_filepath = os.path.join(output_directory, output_filename)
        # Name of fields to write in the csv file (in the right order)

        hfc.init_info[i]["FEAT_FILENAME"] = init_filepath

        if (write_csv(hfc.init_info, init_filepath,  
                      overwrite=self.overwrite)):
            LOG.info("%s saved", init_filepath)
            setattr(hfc, "init_file", init_filepath)
        else:
            LOG.error("%s has not been written correctly!", init_filepath)
            self.terminated = True
            return False

        # Run spoca executable to produce spoca map file (in fits format)
        segmap_rootname = "_".join([hfc.outfnroot,
                                    output_date(date_obs),
                                    observatory.lower()]) \
            + ".map.fits"

        classmap = self.run_classification(
            self.prepset,
            map_rootname=segmap_rootname,
            overwrite=self.overwrite,
            debug=self.debug)

        if (classmap is None) or not (os.path.isfile(classmap)):
            LOG.warning("No segmentation map produced!")
            self.terminated = True
            return False
        else:
            LOG.info("%s saved", classmap)
            self.classmap = classmap

        new_ext = ".%smap.fits" % (self.feature.lower())
        featmap_rootname = classmap.replace(".map.fits", new_ext)

        featmap = self.run_getmap(self.prepset, classmap,
                                  map_rootname=featmap_rootname,
                                  overwrite=self.overwrite)

        if (featmap is None) or not (os.path.isfile(featmap)):
            LOG.warning("No feature map produced!")
            self.terminated = True
            return False
        else:
            LOG.info("%s saved", featmap)
            self.featmap = featmap

        # Extract detected feature(s)
        if (len(featmap) > 0):
            output_filename = "_".join(
                [hfc.outfnroot,
                    output_date(date_obs),
                    observatory.lower(), "feat"]) + ".csv"
            feat_filepath = os.path.join(output_directory,
                                         output_filename)
            if not (os.path.isfile(feat_filepath)) or (self.overwrite):
                featList = hfc.map2feat(featmap, self.dataset[0],
                                        feat_max_area_deg2=
                                        self.params["FEAT_MAX_AREA_DEG2"],
                                        feat_max_hg_long=
                                        self.params["FEAT_MAX_HG_LONG"])

                if (featList is None):
                    LOG.error("Cannot extract features from %s!", featmap)
                    self.terminated = True
                    return False
                elif (len(featList) == 0):
                    LOG.warning("No feature to extract!")
                    self.terminated = True
                    self.success = True
                    return True
                else:
                    # Update feat_filename column
                    for feat in featList:
                        feat["FEAT_FILENAME"] = feat_filepath
                        feat["RUN_DATE"] = TODAY.strftime(HFC_TFORMAT)

                    fieldnames = hfc.feat_info[0].order()
                    if (write_csv(hfc.feat_info, feat_filepath, fieldnames=fieldnames, 
                            overwrite=self.overwrite)):
                        LOG.info("%s saved", feat_filepath)
                        setattr(hfc, "feat_file", feat_filepath)
                    else:
                        LOG.error("%s has not been written correctly!",
                                feat_filepath)
                        self.terminated = True
                        return False
            else:
                LOG.warning("%s already exists!", feat_filepath)
                self.hfc.feat_file = feat_filepath
                self.hfc.feat_info = read_csv(feat_filepath)
            self.success = True
        else:
            LOG.warning("No map produced!")

        self.terminated = True
        return True

    def stop(self):
        self._stopevent.set()

    def setTerminated(self, terminated):
        self.terminated = terminated

    def clean(self,
              data=False,
              prep=False,
              map=False,
              batch=False):
        if (data):
            for f in self.localset:
                if (os.path.isfile(f)):
                    os.remove(f)
                    LOG.info("%s deleted", f)

        if (prep):
            for f in self.prepset:
                if (os.path.isfile(f)):
                    os.remove(f)
                    LOG.info("%s deleted", f)

        if (batch):
            for f in self.batch:
                if (os.path.isfile(f)):
                    os.remove(f)
                    LOG.info("%s deleted", f)

        if (map):
            for f in self.mapset:
                if (os.path.isfile(f)):
                    os.remove(f)
                    LOG.info("%s deleted", f)
        # pour limiter la fuite de memoire            
        del self.dataset            


# CLASS TO RUN THE SPOCA TRACKING =============================
class tracking():
    def __init__(self):

        self.code = "spoca"
        self.version = 2.00
        self.observatory = "SoHO"
        self.args = dict()
        self.map_types = {'A': 'ARMap', 'C': 'CHMap'}
        self.data_directory = "."
        self.output_directory = "."
        self.hfc = hfc()

    # Method to load input parameters from configuration file
    def load_parameters(self, configfile):
        self.args = parse_configfile(configfile)

    # Method to set input parameter
    def set_parameter(self, parameter, value):
        if (parameter in self.args):
            self.args[parameter] = value
        else:
            if (parameter in self.__dict__):
                self.__dict__[parameter] = value

    # Method to get input parameter's value
    def get_parameter(self, parameter):
        value = None
        if (parameter in self.args):
            value = self.args[parameter]
        else:
            if (parameter in self.__dict__):
                value = self.__dict__[parameter]
        return value

    # Method to test the validity of input parameters
    def test_parameters(self):
        if not os.path.isdir(self.output_directory):
            return False, "Output directory does not exists: " \
                + str(self.output_directory)
        if not os.access(self.output_directory, os.W_OK):
            return False, "Output directory is not writable: " \
                + str(self.output_directory)
        if not os.path.exists(self.args["CLASS_EXE"]):
            return False, "Could not find executable: " + str(self.args["bin"])

        for m in self.args["maps"].split(','):
            if m not in self.map_types:
                return False, "Unknown map type " + m

            arguments = self.build_arguments(["testfile"])
            if not arguments:
                return False, "Could not create arguments"

            bin_path = os.path.join(self.args["CLASS_EXE"])
            if not (os.path.isfile(bin_path)):
                return False, bin_path + " does not exist!"
            test_args = [bin_path] + arguments + ['--help']
            process = subprocess.Popen(test_args, shell=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            (output, error) = process.communicate()
            if process.returncode != 0:
                return False, "Arguments could be wrong :" \
                    + ' '.join(test_args) + "\nreturned error: " + error
            else:
                return True, ""

    # Method to build the list of input
    # arguments to provide to the tracking.x program
    # tracking.x -C config_file fitsfiles_list
    def build_arguments(self, fitsfiles):

    #    arguments = list()
    #    for key, value in self.args.items():
    #        if (key == "maps") or (key == "imageType"):
    #            continue

    #        if len(key) > 1:
    #            arguments.append("--" + key)
    #        else:
    #            arguments.append("-" + key)
    #        if value:
    #            arguments.append(value)

        arguments = list()
        arguments.append("-C")
        arguments.append(self.args['CLASS_CONFIG'])
        for fitsfile in fitsfiles:
            arguments.append(os.path.abspath(fitsfile))

        return arguments

    # Method to build list of map files to load
    def get_maps(self, starttime, endtime,
                 download_maps=False):

        code = self.code
        map_type = self.args['maps'].upper()
        obs = self.observatory.lower()
        data_directory = self.data_directory

        if (map_type == "A"):
            #url = FTP_URL + "/spoca-ar"
            #map_type = "ARMap"
            url = data_directory + "/spoca-ar/results"
            map_type = "armap"
        elif (map_type == "C"):
            #url = FTP_URL + "/spoca-ch"
            url = data_directory + "/spoca-ch/results"
            map_type = "CHMap"

        # Years to cover
        startyear = starttime.year
        endyear = endtime.year
        nyear = endyear - startyear + 1
        yearList = [i + startyear for i in range(nyear)]

        # If maps are on a ftp server then download them
        fileList = []
        if (download_maps):
            ftp_server = url.split("/")[2]
            for current_year in yearList:              
                ftp_dir = "/".join(url.split("/")[3:])
                ftp_dir += "/" + str(current_year) + "/maps"                
                ftp = ftplib.FTP(ftp_server)
                ftp.login()
                ftp.cwd(ftp_dir)
                current_fileList = []
                ftp.retrlines('LIST', current_fileList.append)
                ftp.quit()
                fileList.extend(["ftp://" + ftp_server + "/" + ftp_dir + "/" +
                                current_file.split()[-1]
                                for current_file in current_fileList])
        else:
            fileList = glob.glob(os.path.join(data_directory, code + "*" + obs + "." + map_type + ".fits"))
            #fileList = glob.glob(os.path.join(
            #    data_directory, code + "_*_????????T??????_"
            #    + obs + "." + map_type + ".fits"))

        # Extend time range
        stime = starttime - timedelta(seconds=6)
        etime = endtime + timedelta(seconds=6)

        mapList = []
        for current_file in fileList:
            current_basename = os.path.basename(current_file)
            current_items = current_basename.split("_")
            current_obs = current_items[3].split(".")[0].lower()
            if (current_obs != obs):
                continue
            current_date = current_items[2]
            current_date = datetime.strptime(current_date, "%Y%m%dT%H%M%S")
            if (current_date >= stime) and (current_date <= etime):
                mapList.append(current_file)

        return sorted(mapList)

# Method to run the spoca tracking code
# (calling its cpp binary executable)
    def run(self, mapList):
        if (len(mapList) == 0):
            return False

        spoca_bin = self.args['CLASS_EXE']
        spoca_bin_config = self.args['CLASS_CONFIG']
        output_dir = self.output_directory

        # Check that map files exist
        count = 0
        for i, current_map in enumerate(mapList):

            # If the map is on a distant ftp server
            # then download it
            if (current_map.startswith("ftp://") and not os.path.isfile(output_dir+'/'+os.path.basename(current_map))):
                LOG.info("Downloading %s...", current_map)
                current_map = download_file(
                    current_map,
                    data_directory=output_dir,
                    filename=os.path.basename(current_map))
            else:
                current_map = output_dir+'/'+os.path.basename(current_map)
            if not os.path.isfile(current_map):
                LOG.error("%s does not exist, please check!", current_map)
            else:
                mapList[i] = current_map
                count += 1

        # If maps are missing then exit
        if (count != len(mapList)):
            return False

        # Run spoca tracking binary program
        spoca_args = self.build_arguments(mapList)
        spoca_cmd = [spoca_bin] + spoca_args[:]
        #args_part = " ".join(spoca_args)
        #spoca_cmd = spoca_bin + " " + args_part
        LOG.info("Running --> " + " ".join(spoca_cmd) + "...")
        spoca_process = subprocess.Popen(spoca_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        output, errors = spoca_process.communicate()
        if (spoca_process.wait() == 0):
            #LOG.debug("Sucessfully ran spoca command
            #           %s, output: %s, errors: %s",
            #          ' '.join(spoca_cmd), str(output), str(errors))
            return True
        else:
            LOG.error("Error running spoca command %s, output: %s, errors: %s",
                      ' '.join(spoca_cmd), str(output), str(errors))
            #LOG.info("Running --> "+" ".join(spoca_cmd)+"...done")
            return False


# CLASS TO PROCESS HFC DATA =============================
class hfc():
    def __init__(self):

        self.frc_file = ""
        self.obs_file = ""
        self.init_file = ""
        self.feat_file = ""
        self.track_file = ""
        self.obs_info = []
        self.frc_info = []
        self.init_info = []
        self.feat_info = []
        self.feature_name = None
        self.outfnroot = ""

    # Add a row to the HFC table list
    def add_entry(self, table_name, **kwarg):
        table = table_name.lower()

        if (table in self.__dict__):
            current_dict = dict()
            for key, value in kwarg.iteritems():
                current_dict[key.upper()] = value
            self.__dict__[table].append(current_dict)
            return True
        else:
            return False

    # Convert spoca input map into a list containing
    # parameters of the detected features.
    def map2feat(self, mapfile, image,
                 feat_max_area_deg2=None,
                 feat_min_area_deg2=None,
                 feat_max_hg_long=90.0):

        if not (os.path.isfile(mapfile)):
            LOG.error("%s does not exist!", mapfile)
            return []

        header = self.init_info[0]
        feature = self.feat_info

        date_obs = header['DATE_OBS']
        cdelt1 = float(header['CDELT1'])
        cdelt2 = float(header['CDELT2'])
        crpix1 = float(header['CENTER_X'])
        crpix2 = float(header['CENTER_Y'])
        Rsun = RSUN_KM

        if ("SOLAR_B0" in header):
            b0 = header['SOLAR_B0']
        if (b0 == 0):
            ephem = get_sun(datetime.strptime(date_obs, HFC_TFORMAT))
            b0 = ephem[11]
		
        if ("D_SUN" in header):
            Dsun = header['D_SUN']
        if (Dsun == 0.0):
            LOG.warning("D_SUN set to %s by default!", str(DSUN_KM))
            Dsun = DSUN_KM

        l0 = tim2carr(datetime.strptime(date_obs, HFC_TFORMAT))

        try:
            LOG.info("Opening %s", mapfile)
            content = fits.open(mapfile)
        except IOError:
            LOG.error("Can not open %s: ", mapfile)
            return []
        else:
            map_data = {}

        if (self.feature_name == "ACTIVE REGIONS"):
            keymap = "ACTIVEREGIONMAP"
        elif (self.feature_name == "CORONAL HOLES"):
            keymap = "CORONALHOLEMAP"

        for current_content in content:		
            if not (current_content.name.upper() in map_data):
                if (current_content.name.endswith("Stats")):
                    map_data['STATS'] = current_content
                else:
                    map_data[current_content.name.upper()] = current_content

        if not (keymap in map_data):
            LOG.error("No %s table in %s!", keymap, mapfile)
            return []
        if not ("REGIONS" in map_data):
            LOG.error("No REGIONS table in %s!", mapfile)
            return []
        if not ("STATS" in map_data):
            LOG.error("No STATS table in %s!", mapfile)
            return []

        # Number of feature detected
        nfeat = map_data['REGIONS'].header['NAXIS2']
        mask = map_data[keymap].data
        mask = np.transpose(mask)

        # Get image dimensions
        naxis = mask.shape

        pixel_values = np.unique(mask)[1:]
        if (nfeat != len(pixel_values)):
            LOG.error("Incorrect number of feature!")
            return []
        else:
            LOG.info("%i features found in %s", nfeat, mapfile)

        if (nfeat == 0):
            content.close()
            return []

        regions = map_data['REGIONS'].data

        for i, value in enumerate(pixel_values):
            LOG.debug("Extracting HFC parameters for feature #%i ...", i + 1)
            current_date = regions[i][3]

            # Define a sub-image to compute chain code
            x0_pix = sorted([0, regions[i][5] - 2, naxis[0]])[1]
            y0_pix = sorted([0, regions[i][6] - 2, naxis[1]])[1]
            x3_pix = sorted([0, regions[i][7] + 2, naxis[0]])[1]
            y3_pix = sorted([0, regions[i][8] + 2, naxis[1]])[1]
            submask = mask[x0_pix:x3_pix, y0_pix:y3_pix]

            # Make chain code
            cc, locations = image2chain(submask, value,
                                        fill=True,
                                        remove_isolated_pixels=True,
                                        verbose=False)
            if not (cc) or not (locations):
                LOG.warning("Empty chain code for feature %i !", i + 1)
                continue

            for j, iloc in enumerate(locations):
                locations[j][0] += x0_pix
                locations[j][1] += y0_pix

            # Compute some parameters (center of mass, intensity min, max, etc.)
            mask_i = (mask == value)
            stats = compute_feat_stats(mask_i * image)
            stats_sidc = map_data['STATS'].data

            current_feat = ordered_dict()
            # Save some parameters specific to current feature
            if (self.feature_name == "ACTIVE REGIONS"):
                current_feat["ID_AR"] = i + 1
                current_feat["OBSERVATIONS_ID"] = int(self.init_info[0]['ID_OBSERVATIONS'])
                current_feat["OBSERVATIONS_ID_T"] = ""
                current_feat["FEAT_DATE"] = current_date
                current_feat["FEAT_DATE_PREV"] = ""
                current_feat["HELIO_ID"] = ""
                current_feat["FEAT_LENGTH_NL"] = ""
                current_feat["FEAT_LENGTH_SG"] = ""
                current_feat["FEAT_MAX_GRAD"] = ""
                current_feat["FEAT_MEAN_GRAD"] = ""
                current_feat["FEAT_MEDIAN_GRAD"] = ""
                current_feat["FEAT_RVAL"] = ""
                current_feat["FEAT_WLSG"] = ""
            elif (self.feature_name == "CORONAL HOLES"):
                current_feat["ID_CORONALHOLES"] = i + 1
                current_feat["OBSERVATIONS_ID_EIT"] = int(self.init_info[0]['ID_OBSERVATIONS'])
                current_feat["FEAT_DATE"] = current_date
                current_feat["IMAGE_ID"] = ""
                current_feat["IMAGE_GROUP_ID"] = ""
                current_feat["HELIO_ID"] = ""
                current_feat["CHGROUPS_ID"] = ""
                current_feat["FEAT_THRESHOLD"] = ""
                current_feat["FEAT_SKEW_BZ"] = ""
                current_feat["FEAT_WIDTH_X_ARCSEC"] = ""
                current_feat["FEAT_WIDTH_Y_ARCSEC"] = ""
                current_feat["FEAT_WIDTH_X_PIX"] = ""
                current_feat["FEAT_WIDTH_Y_PIX"] = ""
                current_feat["FEAT_WIDTH_HG_LONG_DEG"] = ""
                current_feat["FEAT_WIDTH_HG_LAT_DEG"] = ""
                current_feat["FEAT_WIDTH_CARR_LONG_DEG"] = ""
                current_feat["FEAT_WIDTH_CARR_LAT_DEG"] = ""
            else:
                LOG.error("Unknown type of feature: %s", feature)
                return []

            current_feat["FRC_INFO_ID"] = int(self.frc_info[0]['ID_FRC_INFO'])
            #current_feat["FEAT_X_PIX"] = stats["FEAT_X_PIX"]
            #current_feat["FEAT_Y_PIX"] = stats["FEAT_Y_PIX"]            
            #current_feat["FEAT_X_ARCSEC"] = cdelt1 * (stats["FEAT_X_PIX"] - crpix1)
            #current_feat["FEAT_Y_ARCSEC"] = cdelt2 * (stats["FEAT_Y_PIX"] - crpix2)
            current_feat["FEAT_X_PIX"] = stats_sidc[i][5]
            current_feat["FEAT_Y_PIX"] = stats_sidc[i][6]
            current_feat["FEAT_X_ARCSEC"] = cdelt1*(stats_sidc[i][5] - crpix1)
            current_feat["FEAT_Y_ARCSEC"] = cdelt2*(stats_sidc[i][6] - crpix2)
            current_feat["FEAT_HG_LONG_DEG"], \
                current_feat["FEAT_HG_LAT_DEG"] = \
                convert_hpc_hg(Rsun, Dsun, 'arcsec', 'arcsec', b0, 0.0,
                               current_feat["FEAT_X_ARCSEC"],
                               current_feat["FEAT_Y_ARCSEC"])
            if (np.isnan(current_feat["FEAT_HG_LONG_DEG"])):
                LOG.debug("Feature is on the limb, skipping!")
                continue

            if (feat_max_hg_long is not None) and (abs(current_feat["FEAT_HG_LONG_DEG"]) > abs(float(feat_max_hg_long))):
                LOG.debug("Feature is outside the longitude range, skipping!")
                continue

            current_feat["FEAT_CARR_LONG_DEG"] = \
                current_feat["FEAT_HG_LONG_DEG"] + l0
            current_feat["FEAT_CARR_LAT_DEG"] = current_feat["FEAT_HG_LAT_DEG"]
            current_feat["BR_X0_PIX"] = regions[i][5]
            current_feat["BR_Y0_PIX"] = regions[i][6]
            current_feat["BR_X1_PIX"] = regions[i][5]
            current_feat["BR_Y1_PIX"] = regions[i][8]
            current_feat["BR_X2_PIX"] = regions[i][7]
            current_feat["BR_Y2_PIX"] = regions[i][6]
            current_feat["BR_X3_PIX"] = regions[i][7]
            current_feat["BR_Y3_PIX"] = regions[i][8]
            current_feat["BR_X0_ARCSEC"] = cdelt1 * (float(regions[i][5])
                                                     - crpix1)
            current_feat["BR_Y0_ARCSEC"] = cdelt2 * (float(regions[i][6])
                                                     - crpix2)
            current_feat["BR_X1_ARCSEC"] = cdelt1 * (float(regions[i][5])
                                                     - crpix1)
            current_feat["BR_Y1_ARCSEC"] = cdelt2 * (float(regions[i][8])
                                                     - crpix2)
            current_feat["BR_X2_ARCSEC"] = cdelt1 * (float(regions[i][7])
                                                     - crpix1)
            current_feat["BR_Y2_ARCSEC"] = cdelt2 * (float(regions[i][6])
                                                     - crpix2)
            current_feat["BR_X3_ARCSEC"] = cdelt1 * (float(regions[i][7])
                                                     - crpix1)
            current_feat["BR_Y3_ARCSEC"] = cdelt2 * (float(regions[i][8])
                                                     - crpix2)
            current_feat["BR_HG_LONG0_DEG"], current_feat["BR_HG_LAT0_DEG"] = \
                convert_hpc_hg(Rsun, Dsun, 'arcsec', 'arcsec', b0, 0.0,
                               current_feat["BR_X0_ARCSEC"],
                               current_feat["BR_Y0_ARCSEC"])
            current_feat["BR_HG_LONG1_DEG"], current_feat["BR_HG_LAT1_DEG"] = \
                convert_hpc_hg(Rsun, Dsun, 'arcsec', 'arcsec', b0, 0.0,
                               current_feat["BR_X1_ARCSEC"],
                               current_feat["BR_Y1_ARCSEC"])
            current_feat["BR_HG_LONG2_DEG"], current_feat["BR_HG_LAT2_DEG"] = \
                convert_hpc_hg(Rsun, Dsun, 'arcsec', 'arcsec', b0, 0.0,
                               current_feat["BR_X2_ARCSEC"],
                               current_feat["BR_Y2_ARCSEC"])
            current_feat["BR_HG_LONG3_DEG"], current_feat["BR_HG_LAT3_DEG"] = \
                convert_hpc_hg(Rsun, Dsun, 'arcsec', 'arcsec', b0, 0.0,
                               current_feat["BR_X3_ARCSEC"],
                               current_feat["BR_Y3_ARCSEC"])
            current_feat["BR_CARR_LONG0_DEG"] = \
                current_feat["BR_HG_LONG0_DEG"] + l0
            current_feat["BR_CARR_LAT0_DEG"] = \
                current_feat["BR_HG_LAT0_DEG"]
            current_feat["BR_CARR_LONG1_DEG"] = \
                current_feat["BR_HG_LONG1_DEG"] + l0
            current_feat["BR_CARR_LAT1_DEG"] = \
                current_feat["BR_HG_LAT1_DEG"]
            current_feat["BR_CARR_LONG2_DEG"] = \
                current_feat["BR_HG_LONG2_DEG"] + l0
            current_feat["BR_CARR_LAT2_DEG"] = \
                current_feat["BR_HG_LAT2_DEG"]
            current_feat["BR_CARR_LONG3_DEG"] = \
                current_feat["BR_HG_LONG3_DEG"] + l0
            current_feat["BR_CARR_LAT3_DEG"] = \
                current_feat["BR_HG_LAT3_DEG"]
            current_feat["FEAT_AREA_PIX"] = stats["FEAT_AREA_PIX"]
            cc_hg_x = []
            cc_hg_y = []

            for iloc in locations:
                x_arc_i = cdelt1 * (iloc[0] - crpix1)
                y_arc_i = cdelt2 * (iloc[1] - crpix2)
                hg_x_i, hg_y_i = \
                    convert_hpc_hg(Rsun, Dsun, 'arcsec', 'arcsec', b0, 0.0,
                                   x_arc_i, y_arc_i)
                if (np.isnan(hg_x_i)) or (np.isnan(hg_y_i)):
                    #LOG.debug("Heliographic coordinates cannot be computed!")
                    continue
                cc_hg_x.append(hg_x_i)
                cc_hg_y.append(hg_y_i)

            if (len(cc_hg_x) > 0):
                current_feat["FEAT_AREA_DEG2"] = poly_area(cc_hg_x, cc_hg_y)
                current_feat["FEAT_AREA_MM2"] = \
                    current_feat["FEAT_AREA_DEG2"] * \
                    (radians(1) * RSUN_KM * 1e-3) ** 2
            else:
                current_feat["FEAT_AREA_DEG2"] = ""
                current_feat["FEAT_AREA_MM2"] = ""

            current_feat["FEAT_MIN_INT"] = stats["FEAT_MIN_INT"]
            current_feat["FEAT_MAX_INT"] = stats["FEAT_MAX_INT"]
            current_feat["FEAT_MEAN_INT"] = stats["FEAT_MEAN_INT"]
            current_feat["FEAT_MEAN2QSUN"] = ""
            current_feat["FEAT_MIN_BZ"] = ""
            current_feat["FEAT_MAX_BZ"] = ""
            current_feat["FEAT_MEAN_BZ"] = ""
            current_feat["CC"] = cc
            current_feat["CC_LENGTH"] = len(cc)
            current_feat["CC_X_PIX"] = locations[0][0]
            current_feat["CC_Y_PIX"] = locations[0][1]
            current_feat["CC_X_ARCSEC"] = cdelt1 * (locations[0][0] - crpix1)
            current_feat["CC_Y_ARCSEC"] = cdelt2 * (locations[0][1] - crpix2)
            current_feat["SNAPSHOT_FN"] = ""
            current_feat["SNAPSHOT_PATH"] = ""
            current_feat["FEAT_FILENAME"] = ""

            # Skip too large or too small feature
            if (feat_max_area_deg2):
                if (current_feat["FEAT_AREA_DEG2"] > float(feat_max_area_deg2)):
                    LOG.debug("Feature is too large, skipping!")
                    continue
            if (feat_min_area_deg2):
                if (current_feat["FEAT_AREA_DEG2"] < float(feat_min_area_deg2)):
                    LOG.debug("Feature is too small, skipping!")
                    continue

            self.feat_info.append(current_feat)

        content.close()
        LOG.info("Parameters have "
                 "been extracted for %i feature(s)", len(self.feat_info))

        return self.feat_info

    # Read tracking data from the spoca input map
    def map2track(self, mapfile, output_file=""):

        trackList = []
        if not (os.path.isfile(mapfile)):
            LOG.error("%s does not exist!", mapfile)
            return []

        # Open map file
        content = fits.open(mapfile)
        map_data = {'PRIMARY': [], 'REGIONS': [], 'TRACKINGRELATIONS': [],
                    'STATS': [], 'MAP': [], 'CHAINCODES': []}
        for current_content in content:
            if (current_content.name.endswith("Stats")):
                map_data['STATS'].append(current_content)
            elif (current_content.name.endswith("Map")):
                map_data['MAP'].append(current_content)
            else:
                map_data[current_content.name.upper()].append(current_content)

        if (len(map_data['REGIONS']) == 0):
            LOG.warning("Empty regions dataset in %s!", mapfile)
            return []

#        primary = map_data['PRIMARY'][0]
        regions = map_data['REGIONS'][0]
        stats = map_data['STATS'][0]

        if (regions.data is None):
            LOG.warning("Empty ragions dataset in %s!", mapfile)
            content.close()
            return []

        for i, current_region in enumerate(regions.data):
            #print current_region
            date_obs_i = stats.data[i][1]
            feat_x_pix_i = int(stats.data[i][5])
            feat_y_pix_i = int(stats.data[i][6])

            current_track = ordered_dict()
            if (self.feature_name == "ACTIVE REGIONS"):
                current_track['ID_AR'] = i + 1
                #current_track['TRACK_ID'] = current_region[2]
                current_track['TRACK_ID'] = current_region[11]
            elif (self.feature_name == "CORONAL HOLES"):
                current_track['ID_CH'] = i + 1
                current_track['TRACK_ID'] = current_region[2]

            current_track["DATE_OBS"] = date_obs_i
            current_track["FEAT_X_PIX"] = feat_x_pix_i
            current_track["FEAT_Y_PIX"] = feat_y_pix_i
            current_track['PHENOM'] = "NULL"
            current_track['REF_FEAT'] = "NULL"
            current_track['LVL_TRUST'] = "NULL"
            current_track['TRACK_FILENAME'] = os.path.basename(output_file)
            current_track['FEAT_FILENAME'] = mapfile
            current_track['RUN_DATE'] = TODAY.strftime(HFC_TFORMAT)
            trackList.append(current_track)

        content.close()

        return trackList

if __name__ == "__main__":
	print "spoca_hfc_classes for the spoca_hfc_classification module"
