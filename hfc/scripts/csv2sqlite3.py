#!/usr/bin/env python
# -*- coding: ASCII -*-

"""
Module to insert new entries in a database sqlite3 table
providing a csv format file.
@author: Xavier Bonnin (CNRS, LESIA)
"""

import os
import sys
import argparse
import sqlite3
import csv


# Main script
if (__name__ == "__main__"):

    parser = argparse.ArgumentParser(
        description='Insert new entries in a sqlite3 database table',
                    conflict_handler='resolve', add_help=True)
    parser.add_argument('table', nargs=1,
                        help="sqlite3 database table")
    parser.add_argument('db_file', nargs=1,
                        help="sqlite3 database file")
    parser.add_argument('csv_file', nargs=1,
                        help="csv format file with data to insert")
    parser.add_argument('-d', '--delimiter', nargs='?', default=";",
                        help="csv file delimiter for column")
    parser.add_argument('-q', '--quotechar', nargs='?', default="\"",
                        help="csv file quotechar for column")
    parser.add_argument('-O', '--Overwrite', action='store_true',
                        help="overwrite existing entries")
    args = parser.parse_args()

    table = args.table[0]
    db_file = args.db_file[0]
    csv_file = args.csv_file[0]
    delimiter = args.delimiter
    quotechar = args.quotechar
    overwrite = args.Overwrite

    if not (os.path.isfile(db_file)):
        print "%s not found!" % (db_file)
        sys.exit(1)

    if not (os.path.isfile(csv_file)):
        print "%s not found!" % (csv_file)
        sys.exit(1)

    # Get csv fieldnames in the first line
    # (Used to insert values in the correct order)
    with open(csv_file, 'r') as fr:
        fieldnames = fr.readline().rstrip().split(delimiter)

    # read csv file
    with open(csv_file, 'rb') as fr:
        reader = csv.DictReader(fr,
                                delimiter=delimiter, quotechar=quotechar)
        data = []
        for row in reader:
            data.append(row)

    try:
        con = sqlite3.connect(db_file)

        c = con.cursor()
        for row in data:
            values = list()
            for col in fieldnames:
                if (row[col] is None) or (row[col] == ""):
                    row[col] = "NULL"
                elif (type(row[col]) is str):
                    row[col] = "\"" + row[col] + "\""
                values.append(row[col])

            where_clause = "%s = %s" % (fieldnames[0], row[fieldnames[0]])
            sql_cmd = "SELECT * FROM %s WHERE %s" % (table, where_clause)
            c.execute(sql_cmd)
            if (c.fetchall()) and (overwrite):
                sql_cmd = "UPDATE %s " % (table)
                sql_cmd += "SET " + \
                    ", ".join([k + "=" + v for k, v in row.items()]) + " "
                sql_cmd += "WHERE %s " % (where_clause)
            else:
                sql_cmd = "INSERT INTO %s " % (table)
                sql_cmd += "VALUES (" + ", ".join(values) + ")"

            print sql_cmd
            c.execute(sql_cmd)
            con.commit()

    except sqlite3.Error, e:
        print "Error: %s" % e.args[0]
        sys.exit(1)
    finally:
        con.close()
