#!/bin/bash

# Bash script to launch spoca_hfc_classificatiob.py
# (dev. version).
# X.Bonnin (LESIA, CNRS), 14-MAY-2014

##Set environment variables and paths
if [ -z "$SPOCA_HOME_DIR" ]
then
	#SPOCA_HOME_DIR=/obs/helio/hfc/frc/spoca # Tycho.obspm.fr spoca path
	SPOCA_HOME_DIR=/usr/local/hfc/frc/spoca
fi
source $SPOCA_HOME_DIR/hfc/devtest/spoca_hfc_env_setup.dev.sh

PRODUCT_DIR=$SPOCA_HOME_DIR/products
DATA_DIR=$SPOCA_HOME_DIR/data
BATCH_DIR=$SPOCA_HFC_DIR/scripts/batch

# Input arguments (edit this part)
DATASET=AIA_AR
CONFIG_FILE=$SPOCA_HFC_DIR/config/HFC_$DATASET.classification.dev.config
CENTER_FILE=$PRODUCT_DIR/HFC_$DATASET.segmentation.dev.centers
LOG_FILE=$SPOCA_HOME_DIR/logs/HFC_$DATASET.segmentation.dev.log
DB_FILE=$SPOCA_HFC_DIR/db/spoca_hfc.dev.db
JOBS=1
STARTTIME=2012-07-20T18:00:00
ENDTIME=2012-07-20T20:00:00
CADENCE=7200

SCRIPT=$SPOCA_HFC_DIR/src/spoca_hfc_classification.py

CMD="python $SCRIPT --Debug --Quicklook --Overwrite \
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
