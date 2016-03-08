#! /bin/csh
#
# Script to load environment variables 
# required by SPOCA HFC.
#
# To load this script:
# >source spoca_hfc_setup.csh
#
# X.Bonnin, 17-DEC-2013


# Define nrh2d home directory
setenv SPOCA_HOME_DIR $HOME/hfc/frc/spoca

# Append spoca hfc library path to $PYTHONPATH
setenv PYTHONPATH "$PYTHONPATH":$SPOCA_HOME_DIR/hfc/prod
setenv PYTHONPATH "$PYTHONPATH":$SPOCA_HOME_DIR/lib/python
