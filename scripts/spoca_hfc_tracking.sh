#!/bin/sh

# Script to launch spoca_hfc_tracking.py

##Set paths
SRC_DIR=/obs/helio/hfc/frc/spoca 
WORK_DIR=/travail/helio/hfc/frc/spoca
PRODUCT_DIR=/obs/helio/hfc/frc/spoca/products
MAP_DIR=/obs/helio/hfc/frc/spoca/data

##Append extra python modules' path to $PYTHONPATH
PYTHONPATH=$PYTHONPATH:$SRC_DIR/lib/python
export PYTHONPATH

#Input arguments (edit this part)
CONFIG_FILE=$SRC_DIR/config/AIA_AR.tracking.config
HISTORY_FILE=$PRODUCT_DIR/spoca_hfc_tracking.history
LOG_FILE=$PRODUCT_DIR/spoca_hfc_tracking.log
STARTTIME=2011-01-01T00:00:00
ENDTIME=2011-01-31T23:59:59

SCRIPT=$SRC_DIR/lib/python/spoca_hfc_tracking.py
echo "Running $SCRIPT..."
time python $SCRIPT -V -D -C -s $STARTTIME -e $ENDTIME \
    -m $MAP_DIR -o $PRODUCT_DIR \
    -h $HISTORY_FILE \
    -l $LOG_FILE $CONFIG_FILE 
echo "Running $SCRIPT...done"



