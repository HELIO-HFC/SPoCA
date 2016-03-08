#!/usr/bin/env python
# -*-coding:Utf-8 -*

import sys, argparse
import httplib, urllib
import csv, re

class connect:

	def __init__(self,db,host,server,
		     	host_port=3306,server_port=8080,
		     	user="",passwd=""):
		self.db = db
		self.server = server
		self.host = host
		self.server_port = server_port
		self.user = user
		self.passwd = passwd
		self.host_port = host_port
        
                #Build url
		jdbc = "jdbc:mysql://" + host + ":" + str(host_port) + "/" + db
		url = "http://"+ server + ":" + str(server_port)
		url = url + "/stilts/task/sqlclient?db="+jdbc
		url = url + "&user=" + user + "&password=" + passwd
		self.jdbc = jdbc
		self.url = url

	def getAttrib(self):
		print "db = "+self.db
		print "host = "+self.host
		print "host_port = "+str(self.host_port)
		print "server = "+self.server
		print "server_port = "+str(self.server_port)
		print "user = "+self.user
		print "passwd = "+self.passwd
		
	def query(self,sql_cmd,ofmt="text",
		  	  VERBOSE=False):
		
        #Build query
		url = self.url + "&sql=" + sql_cmd 
		if (len(ofmt) !=0): url = url + "&ofmt=" + ofmt
		
		if (VERBOSE):print "query --> "+url
		try:
			f = urllib.urlopen(url)
			s = f.read()
			f.close()
		except IOError,e:
			return None
		else:
			return s

	def show_tables(self,ofmt="text",
					VERBOSE=True):

		sql_cmd = "SHOW TABLES"
		resp = connect.query(self,sql_cmd,ofmt=ofmt,VERBOSE=VERBOSE)
		print resp

	def describe_table(self,table,ofmt="text",
			   		   VERBOSE=True):

		sql_cmd = "DESCRIBE "+table
		resp = connect.query(self,sql_cmd,ofmt=ofmt,VERBOSE=VERBOSE)
		print resp

	def get_tablelist(self):
		resp = connect.query(self,"SHOW TABLES",ofmt='csv')
		resp = resp.split("\n")
		return resp[2:-3]

	def get_fieldlist(self,table):
		
		sql_cmd = "SHOW FULL COLUMNS FROM " + table
		resp = connect.query(self,sql_cmd,ofmt='csv')
		resp = resp.split("\n")[2:-3]
		fields = []
		for current_row in resp:
			fields.append(current_row.split(","))
		return fields
	
	def import_csv(self,sql_cmd,
				   output_file="outputs.csv",
				   delimiter=",",
				   quotechar='"'):
						
		resp = connect.query(self,sql_cmd,ofmt='csv')
		resp = resp.split("\n")[1:-3]
		header = resp[0]
		content = resp[1:]
		
		with open(output_file,'w') as fw:
			fw.write(delimiter.join(header.split(","))+"\n")
			spamWriter = csv.writer(fw,delimiter=delimiter,
									quotechar=quotechar,
									quoting=csv.QUOTE_MINIMAL)
			for current_row in content:
				data = re.split(''',(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', current_row)
				spamWriter.writerow(data)
			fw.close()

		
		
