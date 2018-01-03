#! /usr/bin/env python
# -*- coding: ASCII -*-

"""
HFC wrapper module to run the SPoCA classification program.
@author: Xavier Bonnin (CNRS, LESIA)
@modified by: Ymane TAOUFIQ (Obs.Paris)
@modified by: Christian RENIE (Obs.Paris, LESIA)
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
import time
import spoca_hfc_classes
import spoca_hfc_methods
#from memory_profiler import profile
#import ordereddict


#psutil.phymem_usage()
#cpu1        = psutil.cpu_percent(interval=0, percpu=True)
#cpu1c       = psutil.cpu_count(logical=True)
#mcpu1c      = multiprocessing.cpu_count()
#vm1         = psutil.virtual_memory().percent
#vm11        = psutil.virtual_memory()
#vm11.total >> 20
#swap_mem1   = psutil.swap_memory()
#swap_mem1.total >> 20
#disk_usage1 = psutil.disk_usage('/')
# Import spoca hfc global variables

from spoca_hfc_globals import VERSION, LOG, TODAY, \
    INPUT_TFORMAT, DATA_DIRECTORY, OUTPUT_DIRECTORY, \
    BATCH_DIRECTORY, CADENCE, JOBS, \
    HOSTNAME, MAX_RUNTIME, DB_FILE

# Import classes for spoca hfc
try:
    from spoca_hfc_classes import spoca_hfc
except:
    sys.exit("Import failed in module spoca_hfc_classification :\
             \n\tspoca_hfc_classes module is required!")
# Import methods for spoca hfc
try:
    from spoca_hfc_methods import setup_logging, build_filelist
except:
    sys.exit("Import failed in module spoca_hfc_classification :\
             \n\tspoca_hfc_methods module is required!")


__version__ = VERSION
__license__ = "GPL"
__author__ = "Xavier Bonnin (CNRS, LESIA)"
__credit__ = "Xavier Bonnin"
__maintainer__ = ["Xavier Bonnin", "Christian Renie"]
__email__ = "xavier.bonnin@obspm.fr"
__date__ = "03-MAR-2015"

# File basename
BASENAME = os.path.basename(__file__)

# Starting Date/time
LAUNCH_TIME = time.time()

ENDTIME = TODAY.strftime(INPUT_TFORMAT)
STARTTIME = (TODAY - timedelta(days=31)).strftime(INPUT_TFORMAT)


# Memory profiling stored in logfile
#os.remove('memory_profiler.log')
#fp=open('memory_profiler.log','w')
#@profile(stream=fp)

# Module to setup spoca_hfc
def setup_spoca_hfc(config_file, starttime, endtime,
                    cadence=None,
                    data_directory=DATA_DIRECTORY,
                    output_directory=OUTPUT_DIRECTORY,
                    batch_directory=BATCH_DIRECTORY,
                    centers_file=None,
                    db_file=DB_FILE,
                    write_qlk=True,
                    overwrite=False,
                    debug=False,
                    local=False):

    spoca_job = spoca_hfc(
        write_qlk=write_qlk,
        overwrite=overwrite, debug=debug)

    setattr(spoca_job, "data_directory", data_directory)
    setattr(spoca_job, "output_directory", output_directory)
    setattr(spoca_job, "batch_directory", batch_directory)

    if (centers_file is not None):
        setattr(spoca_job, "centers_file", centers_file)

    spoca_job.load_parameters(config_file)
    ok, reason = spoca_job.test_parameters()
    if ok:
        LOG.debug("Spoca HFC parameters in file %s seem ok", config_file)
        LOG.debug(reason)
    else:
        LOG.warn("Spoca HFC parameters in file %s could be wrong", config_file)
        LOG.warn(reason)

    setattr(spoca_job.hfc, "outfnroot",
            spoca_job.code.lower()
            + "-" + spoca_job.feature.lower()
            + "_" + "".join(spoca_job.version.split(".")))

    if not (spoca_job.load_metadata(db_file)):
        LOG.error("Something goes wrong \
                  with local database file %s, please check!", db_file)
        sys.exit(1)

    LOG.info("Dataseries --> %s/%s %s",
             spoca_job.observatory, spoca_job.instrument,
             str(spoca_job.wavelength))
    LOG.info("Feature --> %s", spoca_job.hfc.feature_name)
    LOG.info(
        "Time range --> [%s, %s]",
        starttime.strftime(INPUT_TFORMAT),
        endtime.strftime(INPUT_TFORMAT))
    if (cadence):
        LOG.info("Detection cadence --> %s sec.", str(cadence))
    LOG.info("SPoCA classification config. file --> %s",
             spoca_job.class_config)
    LOG.info("SPoCA classification executable --> %s", spoca_job.class_exe)
    LOG.info("SPoCA get map config. file --> %s", spoca_job.getmap_config)
    LOG.info("SPoCA get map executable --> %s", spoca_job.getmap_exe)    
    LOG.info("Output_directory --> %s", output_directory)
    LOG.info("Data_directory --> %s", data_directory)
    if (centers_file):
        LOG.info("Centers_file --> %s", centers_file)

    # Set arguments and get file list
    LOG.info("Loading list of files to process...")
    ttop = time.time()
    filelist = build_filelist(spoca_job.observatory, spoca_job.instrument,
                              spoca_job.wavelength,
                              starttime, endtime,
                              cadence=cadence,
                              local=local)
    LOG.info("Loading list of files to process...done    (took "
             + str(int(time.time() - ttop)) + " sec.)")
    nfile = len(filelist)

    if (nfile == 0):
        LOG.warning("List of files to process is empty.")
        sys.exit(0)
    else:
        LOG.info(
            "%i set(s) found for dataseries %s/%s [%s]",
            nfile, spoca_job.observatory, spoca_job.instrument,
            ",".join([str(w) for w in spoca_job.wavelength]))

    # Initialize the list of jobs to run
    LOG.info("Building list of spoca jobs to run...")
    ttop = time.time()
    joblist = []
    for i, current_fileset in enumerate(filelist):
        current_job = spoca_hfc(job_id=i + 1,
                                write_qlk=write_qlk,
                                overwrite=overwrite,
                                debug=debug)

        current_job.set_parameter("fileset", current_fileset)
        current_job.set_parameter("db_file", db_file)
        current_job.set_parameter("data_directory", spoca_job.data_directory)
        current_job.set_parameter("output_directory",
                                  spoca_job.output_directory)
        current_job.set_parameter("batch_directory", spoca_job.batch_directory)
        current_job.set_parameter("centers_file", spoca_job.centers_file)
        current_job.load_parameters(config_file)
        setattr(current_job.hfc, "outfnroot",
                spoca_job.code.lower()
                + "-" + spoca_job.feature.lower()
                + "_" + "".join(spoca_job.version.split(".")))
        current_job.load_metadata(db_file)

        if (current_job.isprocessed(setid=True, offset=i)):
            LOG.warning(
                "%s/%s observations on %s have already been processed:",
                current_job.observatory, current_job.instrument,
                str(current_fileset[0]["time_start"]))
            if (overwrite):
                LOG.warning("Existing output files will be overwritten!")
            else:
                LOG.warning("Skipping job #%i!", current_job.job_id)
                continue

        joblist.append(current_job)

    LOG.info("Building list of spoca jobs to run...done    (took "
             + str(int(time.time() - ttop)) + " seconds)")

    return joblist


# Main script

if (__name__ == "__main__"):

    # Get the arguments
    parser = argparse.ArgumentParser(
        description='Run spoca classification for the \
        HFC in a given time range.',
        conflict_handler='resolve', add_help=True)
    parser.add_argument('config_file', nargs=1,
                        help='HFC configuration filepath')
    parser.add_argument(
        '-s', '--starttime', nargs='?',
        default=STARTTIME,
        help="First date and time to process [" +
        STARTTIME + "]")
    parser.add_argument(
        '-e', '--endtime', nargs='?',
        default=ENDTIME,
        help="Last date and time to process [" +
        ENDTIME + "]")
    parser.add_argument(
        '-c', '--cadence', nargs='?',
        default=CADENCE,
        help="Cadence of observations in seconds")
    parser.add_argument(
        '-o', '--output_dir', nargs='?',
        default=OUTPUT_DIRECTORY,
        help='Output directory path [' + OUTPUT_DIRECTORY + ']')
    parser.add_argument(
        '-d', '--data_dir', nargs='?',
        default=DATA_DIRECTORY,
        help='Data directory path [' + DATA_DIRECTORY + ']')
    parser.add_argument(
        '-td', '--temp_dir', nargs='?',
        default=BATCH_DIRECTORY,
        help='Temporary batch directory path [' + BATCH_DIRECTORY + ']')
    parser.add_argument(
        '-j', '--jobs', nargs='?', default=JOBS, type=int,
        help='Number of job to launch in parallel [' + str(JOBS) + ']')
    parser.add_argument(
        '-f', '--centers', nargs='?', default="", help="Class center filepath")
    parser.add_argument(
        '-b', '--db_file', nargs='?', default=DB_FILE,
        help='Spoca hfc sqlite3 database filepath.')
    parser.add_argument(
        '-l', '--log', nargs='?', default=None,
        help="Log filepath")
    parser.add_argument(
        '-Q', '--Quicklook', action='store_true',
        help='Produce quicklook images')
    parser.add_argument(
        '-D', '--Clean_data', action='store_true',
        help='Delete data files after processing')
    parser.add_argument(
        '-B', '--Clean_batch', action='store_true',
        help='Delete batch files after processing')
    parser.add_argument(
        '-M', '--Clean_map', action='store_true',
        help='Delete the SPoCA maps after processing')
    parser.add_argument(
        '-P', '--Clean_prep', action='store_true',
        help='Delete the prep-processed data after processing')
    parser.add_argument(
        '-V', '--Verbose', action='store_true',
        help='Set the logging level to verbose at the screen')
    parser.add_argument(
        '-O', '--Overwrite', action='store_true',
        help="Overwrite existing file(s).")
    parser.add_argument(
        '-D', '--Debug', action='store_true',
        help='Set the logging level to debug for the log file')
    parser.add_argument(
        '-L', '--Local', action='store_true',
        help='Get local data files (AIA only)')
    args = parser.parse_args()
    config_file = args.config_file[0]
    output_directory = os.path.abspath(args.output_dir)
    data_directory = os.path.abspath(args.data_dir)
    starttime = datetime.strptime(args.starttime, INPUT_TFORMAT)
    endtime = datetime.strptime(args.endtime, INPUT_TFORMAT)
    cadence = args.cadence
    pjobs = args.jobs
    db_file = args.db_file
    centers_file = args.centers
    log_file = args.log
    write_qlk = args.Quicklook
    clean_data = args.Clean_data
    clean_map = args.Clean_map
    clean_prep = args.Clean_prep
    verbose = args.Verbose
    overwrite = args.Overwrite
    debug = args.Debug
    local = args.Local

    if (cadence is not None):
        cadence = float(cadence)
    if (cadence < 0):
        cadence = None

    # Setup the logging
    setup_logging(
        filename=log_file, quiet=False,
        verbose=verbose, debug=debug)

    LOG.info("Starting %s on %s (%s)", BASENAME,
             HOSTNAME, TODAY.strftime(INPUT_TFORMAT))

    # Check configuration file existence
    if not (os.path.isfile(config_file)):
        LOG.error("%s does not exist!", config_file)
        sys.exit(1)
    # Check output directory existence
    if not (os.path.isdir(output_directory)):
        LOG.error("%s does not exist!", output_directory)
        sys.exit(1)
    # Check data directory existence
    if not (os.path.isdir(data_directory)):
        LOG.error("%s does not exist!", data_directory)
        sys.exit(1)

    # Check database file existence
    if not (os.path.isfile(db_file)):
        LOG.error("%s does not exist!", db_file)
        sys.exit(1)

    if (starttime > endtime):
        LOG.error("starttime is older than endtime!")
        sys.exit(1)

    # Setup spoca hfc jobs
    LOG.info("Building spoca_hfc job(s)...")
    ttop = time.time()
    batch_directory = ""
    spoca_jobs = setup_spoca_hfc(
        config_file, starttime, endtime,
        cadence=cadence,
        data_directory=data_directory,
        output_directory=output_directory,
        batch_directory=batch_directory,
        centers_file=centers_file,
        db_file=db_file,
        write_qlk=write_qlk,
        overwrite=overwrite,
        debug=debug,
        local=local)
    LOG.info("Building spoca_hfc job(s)...done    (took "
             + str(int(time.time() - ttop)) + " seconds)")
    njob = len(spoca_jobs)
    if (njob == 0):
        LOG.warning("No spoca_hfc job to run for the given time range.")
        sys.exit(0)
    else:
        LOG.info("%i spoca_hfc job(s) to run", njob)

    # Run spoca_hfc jobs
    running = []
    npending = njob
    for current_job in spoca_jobs:

        LOG.info(
            "Starting job #%i for %s/%s observations on %s",
            current_job.job_id,
            current_job.observatory, current_job.instrument,
            str(current_job.fileset[0]["time_start"]))
        current_job.start()
        running.append(current_job)
        npending -= 1
        LOG.info("%i/%i current running/pending job(s).",
                 len(running), npending)
        time.sleep(3)

        i = 0
        while(True):
            if (time.time() - running[i].timer > MAX_RUNTIME):
                running[i].setTerminated(True)
                LOG.warning("Execution of job #%i is too long, aborting!",
                            current_job.job_id)

            if (running[i].terminated):
                if (running[i].success):
                    info_msg = "Job #%i has ended correctly" \
                        % (running[i].job_id)
                    LOG.info(info_msg)
                    running[i].comment = info_msg
                    running[i].status = "OK"
                    if (running[i].update_db()):
                        LOG.info("Database in %s updated.", running[i].db_file)
                    else:
                        LOG.error("Something goes wrong "
                                  "with the database file: %s!",
                                  running[i].db_file)
                        sys.exit(1)
                else:
                    LOG.warning("Job #%i has failed!",
                                running[i].job_id)
                running[i].clean(
                    data=clean_data,
                    prep=clean_prep,
                    map=clean_map)
                running.remove(running[i])

            nrun = len(running)
            if (npending > pjobs) and (nrun < pjobs):
                break
            if (nrun == 0):
                break
            i = (i + 1) % nrun

    LOG.info("Total elapsed time: %f minutes",
             (time.time() - LAUNCH_TIME) / 60.0)


#cpu2        = psutil.cpu_percent(interval=0, percpu=True)
#cpu2c       = psutil.cpu_count(logical=True)
#mcpu2c      = multiprocessing.cpu_count()
#vm2         = psutil.virtual_memory().percent
#vm22        = psutil.virtual_memory()
#vm22.total>>20
#swap_mem2   = psutil.swap_memory()
#swap_mem2.total>>20
#disk_usage2 = psutil.disk_usage('/')

#print('cpu_count 1 and 2 :',cpu1c,cpu2c)
#print('cpu_percent 1 and 2  :', cpu1,cpu2)
#print('mcpu 1 and 2 :', mcpu1c, mcpu2c)
#print('psutil.virtual_memory().percent  1 and 2 :',vm1,vm2)
#print('psutil.virtual_memory()  1 and 2 :',vm11,vm22)
#print('swap_memory 1 and 2 :', swap_mem1,swap_mem2)
#print('disk_usage 1 and 2 :', disk_usage1,disk_usage2)
#h = hpy()
#print h.heap()
