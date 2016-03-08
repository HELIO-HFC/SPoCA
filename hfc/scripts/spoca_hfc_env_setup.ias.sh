#! /bin/bash

# Script to load environment variables 
# required by SPOCA HFC (prod. version).
#
# To load this script:
# >source spoca_hfc_env_setup.ias.sh
#
# X.Bonnin, 09-NOV-2015


export SPOCA_HOME_DIR=/usr/local/hfc/prod/features/frc/spoca
export SPOCA_HFC_DIR=$SPOCA_HOME_DIR/hfc
export SPOCA_HFC_DB_DIR=$SPOCA_HFC_DIR/db
export SPOCA_HFC_META_DIR=$SPOCA_HFC_DIR/metadata

# Append spoca hfc library path to $PYTHONPATH
PYTHONPATH=$PYTHONPATH:$SPOCA_HFC_DIR/src
PYTHONPATH=$PYTHONPATH:$SPOCA_HOME_DIR/lib/python
export PYTHONPATH

# Add spoca library to LD_LIBRARY_PATH
LD_LIBRARY_PATH="$SPOCA_HOME_DIR/src/sidc/releases/current/SPoCA/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH
