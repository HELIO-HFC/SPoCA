#!/bin/bash

# Script to download the latest version of the Spoca source code from its Git repository.
#
# IMPORTANT:
#   Make sure that the git software is installed on your system,
#   and that the $SPOCA_HOME_DIR env. variable is set correctly.
#
#
# X.Bonnin (LESIA, Observatoire de Paris - CNRS), 08-MAR-2016

if [ -z $SPOCA_HOME_DIR ];then
    echo "$SPOCA_HOME_DIR is not defined!"
    exit -1
fi

currentdir=`pwd`
spoca_source_dir=$SPOCA_HOME_DIR/src/

cd $spoca_source_dir
git https://github.com/bmampaey/SPoCA.git

cd $currentdir
exit 0