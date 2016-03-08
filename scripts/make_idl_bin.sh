#!/bin/sh

# Produce IDL runtime binary files called by the spoca_hfc program.
# Usage : sh make_idl_bin.sh target_directory
# X.Bonnin, 20-11-2012

INSTR=$1

IDL_LIB_DIR=/obs/helio/hfc/frc/spoca/lib/idl/batch
export WAV_IDL_BIN_DIR=$2

case "$INSTR" in  
    eit)
    BATCH_FILE=$IDL_LIB_DIR/make_eit_prep.batch ;;
    aia)
    BATCH_FILE=$IDL_LIB_DIR/make_aia_prep.batch ;;
    *)
	echo "First argument must be aia or eit!"
	exit 0 ;;
esac
idl -queue -e @$BATCH_FILE
