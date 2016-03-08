#!/bin/sh

# Script to launch spoca_hfc_tracking.py

##Set paths
SRC_DIR=/obs/helio/hfc/frc/spoca 
WORK_DIR=/travail/helio/hfc/frc/spoca
PRODUCT_DIR=/data/helio/hfc/frc/spoca-ar
MAP_DIR=/poubelle/helio/hfc/frc/spoca-ar

##Append extra python modules' path to $PYTHONPATH
PYTHONPATH=$PYTHONPATH:$SRC_DIR/lib/python
export PYTHONPATH

## Check if maps have been already processed on the local disk
## If it does, then start the tracking at the oldest date of these files
## (This allows to keep the same track ids).
PYSCRIPT=$SRC_DIR/lib/python/extract_map_date.py
STARTTIME=`python $PYSCRIPT -o -Q $MAP_DIR/spoca-ar_*_soho.ARMap.fits`
if [ -z "$STARTTIME" ]; then
  STARTTIME=`date --date '1 month ago' '+%Y-%m-%dT%H:%M:%S'` 
fi
ENDTIME=`date '+%Y-%m-%dT%H:%M:%S'`

#Input arguments (edit this part)
CONFIG_FILE=$SRC_DIR/config/EIT_AR.tracking.config
HISTORY_FILE=$PRODUCT_DIR/spoca-ar-soho_hfc_tracking.history
LOG_FILE=$PRODUCT_DIR/spoca-ar-soho_hfc_tracking.log

SCRIPT=$SRC_DIR/lib/python/spoca_hfc_tracking.py
echo "Running $SCRIPT..."
time python $SCRIPT -V -D -C -s $STARTTIME -e $ENDTIME \
    -m $MAP_DIR -o $PRODUCT_DIR \
    -h $HISTORY_FILE \
    -l $LOG_FILE $CONFIG_FILE 
echo "Running $SCRIPT...done"



