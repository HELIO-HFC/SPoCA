#!/bin/bash

# Create the sqlite3 database file for the spoca hfc software.
# X.Bonnin, 16-05-2014

# Usage: bash make_spoca_hfc_db.sh filename [path]
#           , where filename is a string containing the name of the sql database file to create,
#           , and [path] is an optional argument to provide the path of the directory where the file
#           , must be saved

SQL_SCRIPT=make_spoca_hfc_db.sql

if [ $# -lt 1 ]
then
    echo 'Usage: bash make_spoca_hfc_db.sh filename [path]'
    exit 1
fi
FILENAME=$1

if [ $# -gt 1 ]
then
    PATH=$2
else
    if [ -e "$SPOCA_HFC_DB_DIR" ]
    then
        PATH=$SPOCA_HFC_DB_DIR
        echo "Use $PATH as an output directory"
    else
        PATH=.
    fi
fi

if [[ ! -e $SQL_SCRIPT ]]
then
    echo "The sql script "$SQL_SCRIPT" has not been found!"
    exit 1
fi

OUTFILE=$PATH/$FILENAME
/usr/bin/sqlite3  $OUTFILE < $SQL_SCRIPT

if [ -e $OUTFILE ]
then
    echo "$OUTFILE saved"
    exit 0
else
    echo "$OUTFILE has not been saved correctly!"
    exit 1
fi