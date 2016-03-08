#! /bin/sh

# Script to load environment variables 
# required by SPOCA HFC (prod. version).
#
# To load this script:
# >source spoca_hfc_env_setup.prod.sh
#
# X.Bonnin, 25-FEB-2014

export SPOCA_HOME_DIR=$HOME/hfc/frc/spoca

export SPOCA_HFC_DIR=$SPOCA_HOME_DIR/hfc/prod

# Append spoca hfc library path to $PYTHONPATH
PYTHONPATH=$PYTHONPATH:$SPOCA_HFC_DIR/prod
PYTHONPATH=$PYTHONPATH:$SPOCA_HOME_DIR/lib/python
export PYTHONPATH
