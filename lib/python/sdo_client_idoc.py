#! /usr/bin/python
"""
This script has been designed to give python programmers an easy way to interrogate medoc sitools2 interface.
You can make a search with the following entries : a date range , a wavelenghth or multiple wavelengths , a cadence.
You will have as a result a list of Sdo_data objets on which you can apply the method display() that will give you for each 
the recnum, the sunum, the date_obs, the wavelength, the ias_location, the exptime and t_rec_index 
For each result you will be able to call metadata_search() method in order to have the metadata information.
@author: Pablo ALINGERY for IAS 28-08-2012
"""
__version__ = "0.9"
__license__ = "GPL"
__author__ ="Pablo ALINGERY"
__credit__=["Pablo ALINGERY", "Elie SOUBRIE"]
__maintainer__="Pablo ALINGERY"
__email__="pablo.alingery.ias.u-psud.fr"


from pySitools2_idoc import *


def search(DATES=None,WAVES=['94','131','171','193','211','304','335','1600','1700'],CADENCE=['1 min'],NB_RES_MAX=-1,**kwds):
	"""Use the generic search() from pySitools2 library for Sitools2 SDO instance located at IAS
	Parameters available are DATES, WAVES, CADENCE and NB_RES_MAX
	DATES is the interval of dates within you wish to make a research, it must be specifed and composed of 2 datetime elements d1 d2, with d2 >d1
	WAVES is the wavelength (in Angstrom), it must be a list of wave and wave must be in the list ['94','131','171','193','211','304','335','1600','1700']
	if WAVES is not specified WAVES values ['94','131','171','193','211','304','335','1600','1700']
	CADENCE is the cadence with you with to make a research, it must be a string and in list ['1 min', '2 min', '5 min', '10 min', '30 min', '1 h', '2 h', '6 h', '12 h' , '1 day']
	if CADENCE is not specified, CADENCE values '1 min'
	NB_RES_MAX is the nbr of results you wish to display from the results 
	it must be an integer and if specified must be >0
	"""
#Allow lower case entries
	for k,v  in kwds.iteritems():
		if k not in ['dates','waves','cadence','nb_res_max']:
			sys.exit("Error in search():\n'%s' entry for the search function is not allowed" % k) 
		elif k=='dates':
			DATES=v
		elif k=='waves':
			WAVES=v
		elif k=='cadence':
			CADENCE=v
		elif k=='nb_res_max':
			NB_RES_MAX=v
		
	sitools_url='http://medoc-sdo.ias.u-psud.fr'
#	sitools_url='http://localhost:8182'
	print "Loading medoc-sdo Sitools2 client : ",sitools_url
	sdo_dataset=Sdo_IAS_SDO_dataset(sitools_url+"/webs_IAS_SDO_dataset")
	DATES_OPTIM=[]
	if DATES is None:
		sys.exit("Error in search():\nDATES entry must be specified")
	if type(DATES).__name__!='list' :
			mess_err="Error in search():\nentry type for DATES is : %s\nDATES must be a list type" % type(DATES).__name__
			sys.exit(mess_err)
	if len(DATES)!=2:
		mess_err="Error in search() : %d elements specified for DATES\nDATES param must be specified and a list of 2 elements" %len(DATES)
		sys.exit(mess_err)
	for date in DATES :
		if type(date).__name__!='datetime' :
			mess_err="Error in search() : type for DATES element is %s \nDATES list element must be a datetime type" % type(date).__name__
			sys.exit(mess_err)
		else :
			DATES_OPTIM.append(str(date.strftime("%Y-%m-%dT%H:%M:%S")))
	if DATES[1]<= DATES[0]:
		mess_err="Error in search():\nd1=%s\nd2=%s\nfor DATES =[d1,d2] d2 should be > d1" %(DATES[1].strftime("%Y-%m-%dT%H:%M:%S"),DATES[2].strftime("%Y-%m-%dT%H:%M:%S"))
		sys.exit(mess_err)
	dates_param=[[sdo_dataset.fields_list[4]],DATES_OPTIM,'DATE_BETWEEN']
	WAVES_allowed_list=['94','131','171','193','211','304','335','1600','1700']
	if type(WAVES).__name__!='list' :
			mess_err="Error in search():\nentry type for WAVES is : %s\nWAVES must be a list type" % type(WAVES).__name__
			sys.exit(mess_err)
	for wave in WAVES :
		if type(wave).__name__!='str' :
			mess_err="Error in search():\nEntry type for WAVES element is %s\nlist element for WAVES must be a string type" % type(wave).__name__
			sys.exit(mess_err)
		if wave not in WAVES_allowed_list:
			mess_err="Error in search():\nWAVES= %s not allowed\nWAVES must be in list %s" % (WAVES,WAVES_allowed_list)
			sys.exit(mess_err)
	wave_param=[[sdo_dataset.fields_list[5]],WAVES,'IN']
	CADENCE_allowed_list={'1m':'1 min', '2m':'2 min', '5m':'5 min', '10m':'10 min', '30m': '30 min', '1h' :'1 h', '2h':'2 h', '6h': '6 h', '12h':'12 h' , '1d': '1 day'}
	if type(CADENCE).__name__!='list' :
			mess_err="Error in search():\nentry type for CADENCE is : %s\nCADENCE must be a list type" % type(CADENCE).__name__
			sys.exit(mess_err)
	if len(CADENCE)!=1 :
		mess_err="Error in search():\n%d elements specified for CADENCE\nCADENCE param must be specified and a list of only one element" % len(DATES)
		sys.exit(mess_err)
	for cadence in CADENCE:
		if (cadence not in CADENCE_allowed_list.keys()) and (cadence not in CADENCE_allowed_list.values()) :
			mess_err="Error in search():\nCADENCE= %s not allowed\nCADENCE must be in list %s" % (CADENCE,CADENCE_allowed_list)
			sys.exit(mess_err)
		else :
			CADENCE=[CADENCE_allowed_list[cadence]]
	cadence_param=[[sdo_dataset.fields_list[10]],CADENCE,'CADENCE']
	if type(NB_RES_MAX).__name__!='int' :
			mess_err="Error in search():\nentry type for NB_RES_MAX is : %s\nNB_RES_MAX must be a int type" % type(NB_RES_MAX).__name__
			sys.exit(mess_err)
	if NB_RES_MAX!=-1 and  NB_RES_MAX<0 :
		mess_err="Error in search():\nNB_RES_MAX= %s not allowed\nNB_RES_MAX must be >0" % NB_RES_MAX
		sys.exit(mess_err)
	output_options=[sdo_dataset.fields_list[0],sdo_dataset.fields_list[1],sdo_dataset.fields_list[2],sdo_dataset.fields_list[4],sdo_dataset.fields_list[5],sdo_dataset.fields_list[7],sdo_dataset.fields_list[8],sdo_dataset.fields_list[9]]

#Sort date_obs ASC, wave ASC
	sort_options=[[sdo_dataset.fields_list[5],'ASC'],[sdo_dataset.fields_list[4],'ASC']]
	Q1=Query(dates_param)
	Q2=Query(wave_param)
	Q3=Query(cadence_param)
	query_list=[Q1,Q2,Q3]
	result=sdo_dataset.search(query_list,output_options,sort_options,limit_to_nb_res_max=NB_RES_MAX)
	sdo_data_list=[]
	if len(result) !=0 :
		for i, data in enumerate(result) :
			sdo_data_list.append(Sdo_data(data))
	print "%s results returned" % len(sdo_data_list)
	return sdo_data_list

def metadata_info():
	"""Displays information concerning the metadata dataset webs_aia_dataset 
	For example if you need the list of the fields in aia_dataset use it  
	"""
	ds_aia_lev1=Sdo_aia_dataset("http://medoc-sdo.ias.u-psud.fr/webs_aia_dataset")
	return ds_aia_lev1.display()

def singleton(class_def):
    instances = {}
    def get_instance(Class_heritage):
        if class_def not in instances:
            instances[class_def] = class_def(Class_heritage)
        return instances[class_def]
    return get_instance

#This following classes will only have one instance 
@singleton
class Sdo_aia_dataset(Dataset):
	"""Definition de la classe Sdo_aia_dataset that heritates of Dataset"""

	def __init__(self,url):
		Dataset.__init__(self,url)

#This following classes will only have one instance 
@singleton
class Sdo_IAS_SDO_dataset(Dataset):
	"""Definition de la classe Sdo_IAS_SDO_dataset that heritates of Dataset"""

	def __init__(self,url):
		Dataset.__init__(self,url)


class Sdo_data():
	"""Definition de la classe Sdo_data """

	def __init__(self,data):
		self.url=''
		self.recnum=0
		self.sunum=0
		self.date_obs=''
		self.wave=0
		self.ias_location=''
		self.exptime=0
		self.t_rec_index=0
		self.compute_attributes(data)

	def compute_attributes(self, data) :
		self.url=data['get']
		self.recnum=data['recnum']
		self.sunum=data['sunum']
		self.date_obs=data['date__obs']
		self.wave=data['wavelnth']
		self.ias_location=data['ias_location']
		self.exptime=data['exptime']
		self.t_rec_index=data['t_rec_index']
			

	def display(self):
		print self.__repr__()

        def __repr__(self):
            return ("url : %s,recnum : %d, sunum : %d, date_obs : %s, wave : %d, ias_location : %s, exptime : %s, t_rec_index : %d\n" %(self.url,self.recnum,self.sunum,self.date_obs,self.wave,self.ias_location,self.exptime,self.t_rec_index))

	def get_file(self, DECOMPRESS=False, FILENAME=None, TARGET_DIR=None, QUIET=False, **kwds ):
		"""This method is used to retrieve the data on the client side 
		   DECOMPRESS is set by default to False so compressed file are downloaded, to get uncompressed files set DECOMPRESS=True
		   FILENAME is by design aia.lev1.waveA_date_obs.image_lev1.fits you can change it providing a FILENAME  
		   TARGET_DIR the path of the targetted directory, by design the files are downloaded in the current dir
		   QUIET output active or not, by design the output is active , for a quiet get_file process set QUIET=True 
		"""

#Allow lower case entries
		for k,v  in kwds.iteritems():
			if k not in ['decompress','filename','target_dir','quiet']:
				sys.exit("Error get_file():\n'%s' entry for the search function is not allowed" % k) 
			elif k=='decompress':
				DECOMPRESS=v
			elif k=='filename':
				FILENAME=v
			elif k=='target_dir':
				TARGET_DIR=v
			elif k=='quiet':
				QUIET=v

		if FILENAME is None :
			FILENAME="aia.lev1."+str(self.wave)+"A_"+self.date_obs.strftime('%Y-%m-%dT%H:%M:%S.')+"image_lev1.fits" #if not specified this is the default name
		if TARGET_DIR is not None:
			if not os.path.isdir(TARGET_DIR) :
				sys.exit("Error get_file():\nCheck the parameter TARGET_DIR, '%s' directory does not exist." % TARGET_DIR)
			if TARGET_DIR[-1].isalnum():
				FILENAME=TARGET_DIR+'/'+FILENAME
			elif TARGET_DIR[-1]=='/':
				FILENAME=TARGET_DIR+FILENAME
			else :
				sys.exit("Error get_file():\nCheck the param TARGET_DIR, special char %s at the end of TARGET_DIR is not allowed." % TARGET_DIR[-1])
		if not DECOMPRESS :
			self.url=self.url+";compress=rice"
		try :	
			urllib.urlretrieve(self.url, FILENAME)
		except :
			print "Error downloading %s " % FILENAME
		else :
			if not QUIET :
				print "Download file %s completed" % FILENAME

	def metadata_search(self, KEYWORDS=[], RECNUM_LIST=[], **kwds):
		"""Use search() results (the field recnum) in order to provide metadata information from the dataset webs_aia_dataset
		KEYWORDS is the list of names of metadata that you wish to have in the output THAT MUST BE SPECIFIED 
		RECNUM_LIST by designed values self.recnum 
		"""
#Allow lower case entries
		for k,v  in kwds.iteritems():
			if k not in ['keywords','recnum_list']:
				sys.exit("Error get_file():\n'%s' entry for the search function is not allowed" % k) 
			elif k=='keywords':
				KEYWORDS=v
			elif k=='recnum_list':
				RECNUM_LIST=v

		if len(KEYWORDS)==0 :
			sys.exit("Error metadata_search():\nkeywords must be specified")
		if type(KEYWORDS).__name__!='list' :
			mess_err="Error in metadata_search():\nentry type for KEYWORDS is : %s\nKEYWORDS must be a list type" % type(KEYWORDS).__name__
			sys.exit(mess_err)
		ds_aia_lev1=Sdo_aia_dataset("http://medoc-sdo.ias.u-psud.fr/webs_aia_dataset")
		if len(RECNUM_LIST)==0 :
			RECNUM_LIST=[str(self.recnum)]
		param_query_aia=[[ds_aia_lev1.fields_list[0]],RECNUM_LIST,'IN']
		Q_aia=Query(param_query_aia)
		O1_aia=[]
		for key in KEYWORDS :
			if ds_aia_lev1.fields_dict.has_key(key):
				O1_aia.append(ds_aia_lev1.fields_dict[key])
			else :
				sys.exit("Error metadata_search(): %s keyword does not exist" % key)
		S1_aia=[[ds_aia_lev1.fields_list[18],'ASC']]#sort by date_obs ascendant
		return ds_aia_lev1.search([Q_aia],O1_aia,S1_aia)[0]


def main():
	d1=datetime(2012,8,10,0,0,0)
	d2=d1+timedelta(days=1)
	sdo_data_list=search(DATES=[d1,d2],waves=['335'],cadence=['1h'],nb_res_max=10)
	for data in sdo_data_list :
		data.get_file(target_dir='results')

	for item in sdo_data_list:
		my_meta_search=item.metadata_search(keywords=['quality','cdelt1','cdelt2','crval1'])
		print my_meta_search
if __name__ == "__main__":
	main()
