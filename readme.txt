 SPoCA software for the HFC
 ==========================

 Introduction
 ------------

 This directory contains the SPoCA detection code
 developed and maintained by the SIDC in Belgium.

 In the present case, SPoCA is used in the framework of the HFC,
 a service of the HELIO Virtual Observatory, to populate the HFC
 database with active regions and coronal holes information. 

 For more information about the SPoCA code, please visit:
 	http://sdoatsidc.oma.be/web/sdoatsidc/SoftwareSPoCA/

 Content of the directory
 ------------------------

 This directory contains the following items:
	
	/config		can be used to store configuration files for SPoCA
	/data		can be used to store input data files
	/doc		contains documentation for SPoCA
	/hfc		a Python wrapper to produce SPoCA output files in the HFC format 
	/lib		common libraries 
	/logs		can be used to store log files
	/products	can be used to store output files
	/scripts	contains scripts 
	/setup		contains shell scripts to setup the environment variables
        /src            contains the SPoCA source code

 SPoCA execution in the HFC framework
 ------------------------------------

 To produce SPoCA output files in the HFC format, please use the dedicated python wrapper provided in the /hfc directory. 
 
 PLEASE NOTE THAT THE PYTHON WRAPPER SHALL BE ABLE TO CALL THE SPOCA EXECUTABLE BINARY FILES SAVED 
 IN THE src/sidc/releases/current/bin1 and src/sidc/releases/current/bin2 DIRECTORIES!

 SPoCA source code
 -----------------

 The SPoCA source code is stored in the src/sidc directory.
 All of the releases, including the current one, shall be saved in specific folder 'YYYY-MM-DD/SPoCA', 
 where 'YYYY', 'MM' and 'DD' are respectively the year, month and day of the release.

 A symbolic link 'src/sidc/releases/current --> src/sidc/releases/YYYY-MM-DD' shall then be created 
 in order to allow the python wrapper for HFC to call SPoCA.  

 From the 'YYYY-MM-DD' directory, to retrieve the source code using GIT, use the following command:
        git clone https://github.com/bmampaey/SPoCA SPoCA

 Bibliography 
 ------------ 

 * The SPoCA-suite: Software for extraction, characterization, and tracking of active regions and coronal holes on EUV images,
	C. Verbeeck, V. Delouille, B. Mampaey, R. De Visscher (2014) Astronomy & Astrophysics, 561, A29, 
	doi: 10.1051/0004-6361/20132124

 * Barra, V., Delouille, V., Hochedez, J.-F., & Chainais, P.:2005 
	`Segmentation of EIT Images Using Fuzzy Clustering: a Preliminary Study', 
	ESA Special Publication, 600, 77.1.
