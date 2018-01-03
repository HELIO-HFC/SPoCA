#!/bin/bash

# Bash script to launch spoca_hfc_classification.py
# X.Bonnin (LESIA, CNRS), 23-OCT-2014
# Y.TAOUFIQ (OBS.PARIS), last modification , July 2017 
# C. RENIE (LESIA, Obs. Paris), DEC-2017


display_usage() { 
	echo "Bash script to launch spoca_hfc_classification.py" 
	echo -e "\nUsage:\n source setup-daily-spoca.sh [-v visualize_AR_contours] \n"
}

# if more than one argument supplied, display usage  
if [  $# -gt 1 ]
then 
    display_usage
    exit 1
fi

#pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
echo $SCRIPTPATH
#popd > /dev/null
source spoca_hfc_env_setup.solpcr2.sh

if [ $VIRTUAL_ENV ]
then
    printf  '\n\ virtual environment exists for this project at : $VIRTUAL_ENV\n'
else
    printf '\n\n\t*******************************************************************\n'
    printf '\t***  NOTE! Must run this script in tf-env virtual environment!  ***\n'
    printf 'please install virtual-env with this file : installing_virtual_env_for_spoca.csh'
    printf '\t*******************************************************************'
    exit
fi

# Input arguments [for bash env. and for spoca_hfc_classification.py]   
DATA_DIR=$SPOCA_HOME_DIR/data                           
BATCH_DIR=$SPOCA_HOME_DIR/tmp
HFC_HOME_DIR=$SPOCA_HOME_DIR/hfc
HFC_LOG_DIR=$SPOCA_HOME_DIR/logs
DATA_DIR=$SPOCA_HOME_DIR/products/
PRODUCT_DIR=$SPOCA_HOME_DIR/products
LOG_FILE=$HFC_LOG_DIR/hfc_upload_frc.ias.log
SCRIPT=$SPOCA_HFC_DIR/src/spoca_hfc_classification.py


if [[ -n $(find $PRODUCT_DIR/ -name 'aia.lev1.171A_*') ]]
then find $PRODUCT_DIR/ -name 'aia.lev1.171A_*' -delete
fi
if [[ -n $(find $PRODUCT_DIR/ -name 'aia.lev1.193A_*') ]]
then find $PRODUCT_DIR/ -name 'aia.lev1.193A_*' -delete
fi
if [[ -n $(find $PRODUCT_DIR/ -name 'spoca-ar_*.fits') ]]
then find $PRODUCT_DIR/ -name 'spoca-ar_*.fits' -delete
fi
if [[ -n $(find $PRODUCT_DIR/ -name 'spoca-ar_*_feat.csv') ]]
then find $PRODUCT_DIR/ -name 'spoca-ar_*_feat.csv' -delete
fi
if [[ -n $(find $PRODUCT_DIR/ -name 'spoca-ar_*_init.csv') ]]
then find $PRODUCT_DIR/ -name 'spoca-ar_*_init.csv' -delete
fi


#******
DATASET=AIA_AR
#******
CONFIG_FILE=$SPOCA_HFC_DIR/config/HFC_$DATASET.classification.solpcr2.config
CENTER_FILE=$PRODUCT_DIR/HFC_$DATASET.segmentation.dev.centers
LOG_FILE=$SPOCA_HOME_DIR/logs/HFC_$DATASET.segmentation.dev.log
DB_FILE=$SPOCA_HFC_DIR/db/spoca_hfc_db.ias.sql
#******
JOBS=1
#******

#******
CADENCE=7200
#******
#fixed date
STARTTIME=2017-12-12T00:00:00
ENDTIME=2017-12-12T23:59:00
#------------------------------
#date for daily routine
#STARTTIME=$(date +"%Y-%m-%dT00:00:00")
#ENDTIME=$(date -d "+1 days" +"%Y-%m-%dT00:00:00")
#------------------------------
#date for 2 days and more
#STARTTIME=$(date +"2014-%m-%dT00:00:00")
#ENDTIME=$(date -d "+2 days" +"2014-%m-%dT00:00:00")
#******


# LAUNCH spoca_hfc_classification.py
#CMD="kernprof -l $SCRIPT --Local --Debug --Quicklook --Overwrite -s $STARTTIME -e $ENDTIME -j $JOBS \
#CMD="kernprof -l $SCRIPT --Debug --Quicklook --Overwrite -s $STARTTIME -e $ENDTIME -j $JOBS \
CMD="python $SCRIPT --Debug --Quicklook --Overwrite -s $STARTTIME -e $ENDTIME -j $JOBS \
-d $DATA_DIR -o $PRODUCT_DIR \
-f $CENTER_FILE -td $BATCH_DIR \
-c $CADENCE -b $DB_FILE \
-l $LOG_FILE $CONFIG_FILE"

CURRENT_DATE=`date +%Y-%m-%dT%H:%M:%S`
echo "[$CURRENT_DATE]: Running $SCRIPT..."
echo "Time for COMMAND ONE"
echo $CMD
time $CMD

# VISUALIZE spoca AR contour images
if [ $1 = "-v" ]
then
    echo "Visualization"
    LIST_RES=`ls $DATA_DIR'aia.lev1.171'*'.jpg'`
    if [[-z $LIST_RES]]
    then
	echo "No images in $DATA_DIR"
	exit 1
    else
	for image in $LIST_RES
	do
	    echo $image
	    yr=${image:(-43):(-39)}
	    echo $yr
	    mth=${image:(-38):(-36)}
	    echo $mth
	    day=${image:(-35):(-33)}
	    echo $day
	    tmeh=${image:(-32):(-30)}
	    echo $tmeh
	    tmem=${image:(-29):(-27)}
	    echo $tmem
	    tmes=${image:(-26):(-24)}
	    echo $tmes
	    python $SPOCA_HFC_DIR/frc_preview/frc_preview.py -f $SPOCA_HOME_DIR/products/spoca-ar_301_"$yr$mth$day"T"$tmeh$tmem$tmes"_sdo_feat.csv -i $image $SPOCA_HOME_DIR/products/spoca-ar_301_"$yr$mth$day"T"$tmeh$tmem$tmes"_sdo_init.csv
	done
    fi
fi

CURRENT_DATE=`date +%Y-%m-%dT%H:%M:%S`
echo "[$CURRENT_DATE]: Running $SCRIPT...done -(if option -v : images viewed with preview tool)- and uploaded into ftp server."


