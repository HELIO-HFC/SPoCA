#!/bin/bash

# Bash script to launch spoca_hfc_classification.py
# for SPOCA-AR-SDO with IAS config.
# X.Bonnin (LESIA, CNRS), 09-NOV-2015

if [ $# -ne 3 ]; then
    echo "Usage: bash run_spoca-ar-sdo_hfc_classification.ias.sh product_dir log_dir tmp_dir"
    exit 1
fi

##Set environment variables and paths
pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null
source $SCRIPTPATH/spoca_hfc_env_setup.ias.sh

PRODUCT_DIR=$1
LOG_DIR=$2
BATCH_DIR=$3
DATA_DIR=$SPOCA_HOME_DIR/data

# Input arguments (edit this part)
DATASET=AIA_AR
CONFIG_FILE=$SPOCA_HFC_DIR/config/HFC_$DATASET.classification.ias.config
CENTER_FILE=$PRODUCT_DIR/HFC_$DATASET.segmentation.centers
LOG_FILE=$SPOCA_HOME_DIR/logs/HFC_$DATASET.segmentation.log
DB_FILE=$SPOCA_HFC_DIR/db/spoca_hfc_db.ias.sql
JOBS=1
STARTTIME=2011-06-09T18:00:00
ENDTIME=2011-06-09T20:00:00
CADENCE=7200

SCRIPT=$SPOCA_HFC_DIR/src/spoca_hfc_classification.py

CMD="python $SCRIPT --Local --Debug --Quicklook --Overwrite \
-s $STARTTIME -e $ENDTIME -j $JOBS \
-d $DATA_DIR -o $PRODUCT_DIR \
-f $CENTER_FILE -t $BATCH_DIR \
-c $CADENCE -b $DB_FILE \
-l $LOG_FILE $CONFIG_FILE"

CURRENT_DATE=`date +%Y-%m-%dT%H:%M:%S`
echo "[$CURRENT_DATE]: Running $SCRIPT..."
echo $CMD
time $CMD
CURRENT_DATE=`date +%Y-%m-%dT%H:%M:%S`
echo "[$CURRENT_DATE]: Running $SCRIPT...done"


exit 0
