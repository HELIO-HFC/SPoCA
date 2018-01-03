#! /bin/bash

# Script to load environment variables 
# required by SPOCA HFC (prod. version).
#
# To load this script:
# >source spoca_hfc_env_setup.ias.sh
#
# X.Bonnin, 23-OCT-2014
# Y.TAOUFIQ, July2016/July2017
# C. Renie 15-12-2017

source "/home/crenie/ias/env-spoca-ar/bin/activate"

export HFC_DIR=/home/crenie/ias/hfc/prod
export SPOCA_HOME_DIR=$HFC_DIR/features/frc/spoca
export SPOCA_HFC_DIR=$SPOCA_HOME_DIR/hfc/prod
export SPOCA_HFC_DB_DIR=$SPOCA_HFC_DIR/db
#export IDL_DIR=/usr/local/exelis/idl

#Append spoca hfc library path to $PYTHONPATH

PYTHONPATH=$PYTHONPATH:$SPOCA_HFC_DIR/src
PYTHONPATH=$PYTHONPATH:$SPOCA_HOME_DIR/lib/python
export PYTHONPATH

# Add spoca library to LD_LIBRARY_PATH
LD_LIBRARY_PATH="$SPOCA_HOME_DIR/sidc/releases/current/SPoCA/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH
