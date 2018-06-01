import tkinter as tk
from tkinter import Listbox, Scrollbar, END, RIGHT, Y
from ftplib import FTP

class ftpBrowseWidget(tk.Toplevel):
    def __init__(self, parent, **kw):
        tk.Toplevel.__init__(self, parent, **kw)
        self.wm_title("Browse ftpbass2000")
        self.geometry("800x400+200+200")

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.ftpList = tk.Listbox(self)
        self.ftpList.bind('<Double-1>',self.update_FTP_Dir)
        self.ftpList.pack(side="left",fill="both", expand=True)
        self.ftpList.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.ftpList.yview)
        self.init_file = ''
        self.update_FTP_Dir(self)
        
    def update_FTP_Dir(self, event):
        ##    first thing we do is connect to the ftp host        
        ftp = FTP('ftpbass2000.obspm.fr')
        ftp.login( user = 'anonymous', passwd='')
        ftp.set_pasv(True)
        if hasattr(event, 'type'):
            select=self.ftpList.get(self.ftpList.curselection())
        else:
            select = "pub/helio/"
        
        if select == 'BACK':
            reps = self.curFTPDir.split('/')
            select = '/'.join(reps[0:len(reps)-1])
        try:
            ftp.cwd(select)
            self.ftpList.delete(0, END)
            self.ftpList.insert(0, 'BACK')
            for fileName in ftp.nlst():
                self.ftpList.insert(END, select+'/'+fileName)
    
            self.curFTPDir = select
        except:
            self.init_file =  "ftp://ftpbass2000.obspm.fr/" + select
            self.destroy()
            
        ftp.close()
        
    def get_result(self):
        """Return selection."""
        return self.init_file 
        
def askFTPfilename(parent=None, **kwargs):
    """
    Return '' or the absolute path of the chosen file
    """
    dialog = ftpBrowseWidget(parent, **kwargs)
    dialog.wait_window(dialog)
    return dialog.get_result()        

def launch_file_dialog_box():
        choosenFile = askFTPfilename()
        print(choosenFile)
    
if __name__ == "__main__":
    root = tk.Tk()
    tk.Button(root, text="Open files", command=launch_file_dialog_box).grid(row=1, column=1, padx=4, pady=4, sticky='ew')
    root.mainloop()
