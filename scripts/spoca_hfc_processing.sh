#!/bin/sh

# Script to launch spoca_hfc_processing.py

##Set paths
SRC_DIR=/obs/helio/hfc/frc/spoca 
WORK_DIR=/travail/helio/hfc/frc/spoca
PRODUCT_DIR=$SRC_DIR/products
DATA_DIR=$SRC_DIR/data

##Append extra python modules' path to $PYTHONPATH
PYTHONPATH=$PYTHONPATH:$SRC_DIR/lib/python
export PYTHONPATH

##SSW environment variable required
SSW=/obs/helio/library/idl/ssw
export SSW
SSW_ONTOLOGY=$SSW/vobs/ontology
export SSW_ONTOLOGY
SSWDB=$SSW/sswdb
export SSWDB
SSW_EIT_RESPONSE=$SSW/soho/eit/response
export SSW_EIT_RESPONSE

# Input arguments (edit this part)
CONFIG_FILE=$SRC_DIR/config/hfc/HFC_EIT_AR.segmentation.config
CENTER_FILE=$PRODUCT_DIR/spoca-ar_hfc_centers.txt
HISTORY_FILE=$PRODUCT_DIR/spoca-ar_hfc_history.txt
LOG_FILE=$PRODUCT_DIR/spoca-ar_hfc_processing.log
NPROC=3
STARTTIME=2002-12-20T00:00:00
ENDTIME=2002-12-30T23:59:59
#CADENCE=7200

SCRIPT=$SRC_DIR/lib/python/spoca_hfc_processing.py
echo "Running $SCRIPT..."
time python $SCRIPT --Verbose --Quicklook \
            -s $STARTTIME -e $ENDTIME -p $NPROC \
            -d $DATA_DIR -o $PRODUCT_DIR \
            -b $CENTER_FILE -h $HISTORY_FILE \
            -l $LOG_FILE $CONFIG_FILE 
echo "Running $SCRIPT...done"



