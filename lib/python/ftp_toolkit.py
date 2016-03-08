#!/usr/bin/env python
# -*-coding:Utf-8 -*

import sys, os, shutil
import csv
import ftplib

class connect():

	def __init__(self,ftpServer,user="",password=""):
				self.conn = ftplib.FTP(ftpServer,user,password)
				self.frcName = None

	# Method to return the list of directories contain in the ftpPath
	def retDir(self,ftpPath="",FULL_PATH=False):
		
		try:
			if (len(ftpPath) > 0):
				#Get current directory path
				curPath = self.conn.pwd()
				#Change to ftpDir
				self.conn.cwd(ftpPath)
			
			#Get Directory list
			itemList=[]
			self.conn.retrlines('LIST',itemList.append)
			dirList=[]
			for current_item in itemList:
				if (current_item[0] == "d"):
					if (FULL_PATH):
						dirList.append(ftpPath + "/" + current_item.split()[-1])
					else:
						dirList.append(current_item.split()[-1])
			
			if (len(ftpPath) > 0):		
				#Return to initial path
				self.conn.cwd(curPath)
		except ftplib.error_perm,e:
			return []
		else:	
			return dirList

	# Method to return the list of files contain in the ftpPath
	def retFile(self,ftpPath="",FULL_PATH=False):
		
		if (len(ftpPath) > 0):
			#Get current directory path
			curPath = self.conn.pwd()
			#Change to ftpDir
			self.conn.cwd(ftpPath)
		
		#Get file list
		itemList=[]
		self.conn.retrlines('LIST',itemList.append)
		fileList=[]
		for current_item in itemList:
			if (current_item[0] != "d"):
				if (FULL_PATH):
					fileList.append(ftpPath + "/" + current_item.split()[-1])
				else:
					fileList.append(current_item.split()[-1])
		
		if (len(ftpPath) > 0):
			#Return to initial path
			self.conn.cwd(curPath)
		
		return fileList

	# Method to test directory existence on a distance ftpPath 
	def isdir(self,dirname,ftpPath=""):
		
		if ((len(ftpPath) == 0) and 
			("/" in dirname)):
			ftpPath = ("".join(cdir+"/" for cdir in dirname.split("/")[0:-1]))[0:-1]

		dirList = connect.retDir(self,ftpPath,FULL_PATH=True)	
		
		if (dirList.count(dirname) == 0): 
			return False
		else:
			return True

	# Method to test file existence on a distance ftpPath 
	def isfile(self,filename,ftpPath=""):
		
		fileList = connect.retFile(self,ftpPath,FULL_PATH=True)	
		
		if (fileList.count(filename) == 0): 
			return False
		else:
			return True
	
	# Method to upload a file 
	def put(self,source,target,ASCII=False):
		
		#Get current directory path
		curPath = self.conn.pwd()
		
		try:
			self.conn.cwd(target)
		except ftplib.error_perm,e:
			print "Can not change directory from %s to %s!" % (curPath,target)
			print e
			return False
			
		if (ASCII):
			try:
				with open(source,'r') as fw:
					self.conn.storlines('STOR '+os.path.basename(source),fw)
			except ftplib.error_perm,e:
				print "Can not upload "+os.path.basename(source)+" to "+target+"!"
				print e
				return False
		else:
			try:
				with open(source,'rb') as fw:
					self.conn.storbinary('STOR '+os.path.basename(source),fw)
			except ftplib.error_perm,e:
				print "Can not upload "+os.path.basename(source)+" to "+target+"!"
				print e
				return False
		fw.close()
		
		self.conn.cwd(curPath)
		
		return True
	
	# Method to make a directory
	def mkdir(self,dirname):

		try:
			self.conn.mkd(dirname)
		except ftplib.error_perm,e:
			return False
		
		return True			

	# Method to delete a file
	def delete(self,filename):
			
		try:
			self.conn.delete(filename)
		except ftplib.error_perm,e:
			return False
		return True
		
	# Method to close the ftp connection
	def quit(self):
		self.conn.quit()
	
