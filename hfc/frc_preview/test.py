#!/usr/bin/env python3
#encoding: UTF-8

# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

import os, io
from ftplib import FTP
import tkinter as tk
from tkinter import filedialog, LEFT, Menu
import tkinter.scrolledtext as tkst
from ftpBrowsWidget import askFTPfilename
from pycurl import pycurl
import csv
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.misc import fromimage, toimage
from improlib import chain2image, auto_contrast
import urllib
#from tkinter import tkFileDialog

#import Tkinter as ttk

ftp2csv="ftp://ftpbass2000.obspm.fr/pub/helio"
ftp2qlk="ftp://ftpbass2000.obspm.fr/pub/helio"

class App(tk.Tk):    
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry("800x400+200+200")
        self.title("Upload a Program Flyer to the Library Website")
        self.menu = tk.Menu()
        self.config(menu=self.menu)
        self.filemenu = tk.Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Choose a local init or obs CSV file", command=self.launch_file_dialog_box)
        self.filemenu.add_command(label="Browse ftpbass2000", command=self.launch_FTP_dialog_box)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.quit)
        self.zoneTxt = tkst.ScrolledText(
            wrap   = 'word'  # wrap text at full words only            
        )
        self.zoneTxt.pack(fill="both", expand=True)
        self.init_file = ''
    
    def launch_file_dialog_box(self):
        self.init_file = filedialog.askopenfilename()
        if self.isInitCSVfile():
            self.make_plot()
        else:
            self.zoneTxt.insert('insert', self.init_file + " is not a valid init or obs CSV file" + "\n")
    def launch_FTP_dialog_box(self):
        self.init_file = askFTPfilename()
        if self.isInitCSVfile():
            self.make_plot()
        else:
            self.zoneTxt.insert('insert', self.init_file + " is not a valid init or obs CSV file" + "\n")
            
    def isInitCSVfile(self):
        if len(self.init_file):
            if 'obs' in self.init_file or 'init' in self.init_file:
                return True
            else:
                return False
        
    def make_plot(self):
        VERBOSE = True
        PIXELS=True
        QUICKLOOK=True
        fileSet = self.makeFileSet()        
        if fileSet is None:
            print ("No filesetfound for %s!" % self.init_file)
            self.zoneTxt.insert('insert', "No fileset found for " + self.init_file + "\n")
            return
        else:
            if VERBOSE: print("File Set is: ", fileSet)
        
        self.zoneTxt.insert('insert', "Files set is:\n")
        for item in fileSet:
            self.zoneTxt.insert('insert', item + "\n")

        self.plot_feat(fileSet,
             PIXELS=PIXELS,
             GET_QUICKLOOK=QUICKLOOK,VERBOSE=VERBOSE)
        
    def makeFileSet(self):
        """ Build a complete CSV fileset from an observation CSV filename """
        obsFile = self.init_file
        filePath = os.path.dirname(obsFile)
        fileName = os.path.basename(obsFile)

        if fileName.startswith('spoca-ar') or fileName.startswith('sdoss'):
            items = fileName.split("_")
            code = items[0].lower(); version = items[1]; cdate = items[2]
            observat = items[3].lower(); fileType = items[4].lower()
            fileSet = [fileName, fileName.replace('init', 'feat'),
                fileName.replace('init', 'track'),
                "_".join([code, version, observat, "observatory"]) + ".csv",
                "_".join([code, version, observat, "frc_info"]) + ".csv"]
        elif fileName.startswith('SoSoFT') or fileName.startswith('SoSoPro'):
            fileSet = [fileName, fileName.replace('obs', 'pp'),
            fileName.replace('obs', 'feat'), 
            fileName.replace('obs', 'frc')]
        else:
            fileSet = None

        # add path to filename
        if fileSet is not None:
            for i in range (0, len(fileSet)):
                fileSet[i] = os.path.join(filePath, fileSet[i])

        return fileSet
    
    def plot_feat(self, fileSet,
              image_file=None,
              RSUN=True,
              PIXELS=False,
              GET_QUICKLOOK=False,
              VERBOSE=False):

        if ('SoSoFT' in fileSet[0]) or ('SoSoPro' in fileSet[0]):
            init_file, pp_file, feat_file, frc_file = fileSet
            init_data = self.read_csv(pp_file)
            obs_data = self.read_csv(init_file)
            date_obs = obs_data[0]['DATE_OBS']
            qclk_fname = init_data[0]['PR_LOCFNAME'].replace('fits', 'png')

        else:
            init_file, feat_file, track_file, observatory_file, frc_file = fileSet
            init_data = self.read_csv(init_file)
            date_obs = init_data[0]['DATE_OBS']


        items=os.path.basename(init_file).split("_")
        code=items[0].lower() ; version=items[1] ; cdate=items[2]
        observat=items[3].lower() ; fileType=items[4].lower()

        if not (init_data):
            print ("Error reading %s!" % init_file)
            return False

        data_dir = os.path.dirname(init_file)

    #    date_obs = init_data[0]['DATE_OBS']
        naxis1 = int(init_data[0]['NAXIS1'])
        naxis2 = int(init_data[0]['NAXIS2'])
        cdelt1 = float(init_data[0]['CDELT1'])
        cdelt2 = float(init_data[0]['CDELT2'])
        center_x = float(init_data[0]['CENTER_X'])
        center_y = float(init_data[0]['CENTER_Y'])
        rsun = float(init_data[0]['R_SUN'])
    #    filename = init_data[0]['FILENAME']
        if 'URL' in init_data[0]: url = init_data[0]['URL']
        else: url = None
        if 'QCLK_URL' in init_data[0]: qclk_url = init_data[0]['QCLK_URL']
        else: qclk_url = None
        if 'QCLK_FNAME' in init_data[0]: qclk_fname = os.path.basename(init_data[0]['QCLK_FNAME'])
    #    else: qclk_fname = None

        if (GET_QUICKLOOK) and not (image_file):
            print ("Reading quicklook url from %s" % init_file)
            if not (qclk_fname):
                print ("QCLK_FNAME keyword is not provided in %s!" % init_file)
            else:
                if not (qclk_url) or (qclk_url.upper() == 'NULL'):
                    print ("QCLK_URL keyword is not provided in %s!" % init_file)
                    image_file = os.path.join(data_dir,qclk_fname)
                    if (os.path.isfile(image_file)):
                        print ("%s found in %s" % (qclk_fname,data_dir))
                    else:
                    #    year=date_obs.split("-")[0]
                        observatory=None
                        instrument=None
                        if 'SoSoFT' in fileSet[0]:
                            observatory = "meudon"
                            instrument = "Halpha"
                        elif 'SoSoPro' in fileSet[0]:
                            observatory = "meudon"
                            instrument = "K3p"
                        else:
                            id_oby = init_data[0]['OBSERVATORY_ID']
                            year=date_obs.split("-")[0]
                            observatory_file=data_dir.replace("results/"+year, "results/")+"_".join([code,version,"observatory"])+".csv"
                            print ("Trying to reach %s" % observatory_file)
                            oby_data=self.read_csv(observatory_file)
                            if (oby_data):
                                for row in oby_data:
                                    print(id_oby + " " +row['ID_OBSERVATORY'])
                                    if row['ID_OBSERVATORY'] == id_oby:
                                        observatory=row['OBSERVAT'].lower()
                                        instrument=row['INSTRUME'].lower()
                                        break
                        if observatory is not None and instrument is not None:    
                            qclk_url = data_dir.replace("results", "images/full/"+observatory+'/'+instrument)
                            #qclk_url = ftp2qlk + "/".join([observatory,instrument,year])
                            image_file =  qclk_url + "/" + qclk_fname
                        else:
                            print ("Can't build QCLK_URL from %s" % observatory_file)
                else:
                    image_file =  qclk_url + "/" + qclk_fname

        if (VERBOSE):
            print ("NAXIS1 = %s" % naxis1)
            print ("NAXIS2 = %s" % naxis2)
            print ("CDELT1 = %s" % cdelt1)
            print ("CDELT2 = %s" % cdelt2)
    #        print ("FILENAME = %s" % filename)
            print ("URL = %s" % url)
            print ("QCLK_URL = %s" % qclk_url)
            print ("QCLK_FNAME = %s" % qclk_fname)
            print ("Image file = %s" % image_file)

        self.zoneTxt.insert('insert', "Quiclook is " + image_file + "\n")
        
        # Loading feature data
        if (feat_file is None):
            feat_file = init_file.replace("_init.csv","_feat.csv")
        feat_data = self.read_csv(feat_file)
        if not (feat_data):
            print ("Error reading %s!" % feat_file)
            return False   

        if (VERBOSE):
            print ("Number of features = %i" % len(feat_data))
        self.zoneTxt.insert('insert', "Number of features = %i" % len(feat_data) + "\n")
    #    if (os.path.isfile(track_file)):
    #        track_data = read_csv(track_file)
    #        if not (track_data):
    #            print ("Error reading %s!" % track_file)
    #            return False

        plt.figure(figsize=(8,8))
        plt.title(date_obs)

        X = np.arange(naxis1)
        Y = np.arange(naxis2)
        if not (PIXELS):
            X = cdelt1*(X - center_x)
            Y = cdelt2*(np.arange(naxis2) - center_y)

        x=np.linspace(min(X),max(X),6)
        y=np.linspace(min(Y),max(Y),6)
        plt.xticks(x)
        plt.yticks(y)
           
        print ("Loading quiklook file = %s" % image_file)
        buff = self.load_image(image_file)
        if (buff):
            image = fromimage(buff)
            enhanced_image = auto_contrast(image, low=0., high=1.0)
            enhanced_image = np.flipud(enhanced_image)
            plt.imshow(enhanced_image,
                       cmap=plt.cm.gray, origin='lower',
                       extent=[min(X), max(X), min(Y), max(Y)])
            min_val = np.min(image)
            max_val = np.max(image)
        else:
            self.zoneTxt.insert('insert', "Quicklook file not found: " + image_file + "!\n")
        if (RSUN):
            theta = 2.*np.pi*np.array(range(361))/360.0
            xs = rsun*np.cos(theta) + center_x 
            ys = rsun*np.sin(theta) + center_y
            if not (PIXELS):
                xs = cdelt1*(xs - center_x)
                ys = cdelt2*(ys - center_y)
            plt.plot(xs,ys)

        for current_feat in feat_data:
            if 'BLOB_SEPARATOR' in current_feat:
                cc = current_feat['CC'].split(current_feat['BLOB_SEPARATOR'])
                cc_x_pix = current_feat['CC_X_PIX'].split(current_feat['BLOB_SEPARATOR'])
                cc_y_pix = current_feat['CC_Y_PIX'].split(current_feat['BLOB_SEPARATOR'])
            else:
                cc = [current_feat['CC']]
                cc_x_pix = [current_feat['CC_X_PIX']]
                cc_y_pix = [current_feat['CC_Y_PIX']]
            for j in range (len(cc)): 
                cc_x = np.int64(cc_x_pix[j])
                cc_y = np.int64(cc_y_pix[j])
                Xc,Yc = chain2image(cc[j],start_pixel=[cc_x,cc_y],
                                CCLOCKWISE=True)
                if not (PIXELS):
                    for i,Xi in enumerate(Xc):
                        Xc[i] = cdelt1*(Xc[i] - center_x)
                        Yc[i] = cdelt2*(Yc[i] - center_y)
                plt.plot(Xc,Yc)

        plt.show()
           
    def read_csv(self, file):
        if (file.startswith("http:")) or \
            (file.startswith("ftp:")):
            output, error = pycurl(file,"-qO")
            if (len(output) == 0): return []
            buff = io.StringIO(output.decode('utf-8'))
        else:
            if not (os.path.isfile(file)):
                print (file+" does not exists!")
                return []
            buff = open(file,'r')

        reader = csv.DictReader(buff,delimiter=';')
        data = []
        for row in reader:
            data.append(row)
            #print data

        buff.close()
        return data

    def load_image(self, file):
    
        if (file.startswith("http:")) or \
            (file.startswith("ftp:")):
            try:
                req = urllib.request.Request(file)
                resp = urllib.request.urlopen(req)
                buff = resp.read()
                file = io.BytesIO(buff)
            #    buff = urlopen(file).read()
            #    file = cStringIO.StringIO(buff)
            except urllib.error.URLError as e:
                print ("Can not load %s!" % file)
                print('Reason: ', e.reason)
                return None
        else:
            if not (os.path.isfile(file)):
                print (file+" does not exists!")
                return None
        image = Image.open(file)
        return image        
                
app = App()
app.mainloop()
