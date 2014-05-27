# -*- coding: utf-8 -*-

################## LIBRARY IMPORTs################################
import os, sys, time

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

# CSV (reading csv/tsv files)
import csv
# GZIP (uncompress .gz files)
import gzip

from PyQt4 import QtCore, QtGui

sys.path.append("./app/lib/")  # Excel read/write
import xlrd
import xlwt


sys.path.append("./app/gui/")  # Graphical Dialog Source
import base

#######################################################################
################## MAIN DIALOG CLASS################################
class BaseWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.ui = base.Ui_Dialog()
        self.ui.setupUi(self)

    #--------- CLASS VARIABLES --------------
        self.arr_chkbx=[]       #check box elements
        self.arr_chkbxall=[]  # checkbox for "Select all"
        self.arr_tab=[]      # Tabs of the TabWidget
        self.arr_table=[]    #tableWidget of each Tab

        self.cl_geo_list=[]         #array for GEO
        self.cl_time_list=[]       #array for GEO
        self.cl_cat_list=[]         #2D-array for categories
        self.cl_title_list=[]       #array for titles (without geo/time)   "unit,nace_r1,indic_na"

        self.cats_sel_mut=[]                    # List of mutation of cats_selected
        self.cats_selected=[]                   # List of Checkbox marked elements [AT, BE..]

        self.multisel_start=0                   # variables for multiselection of checkboxes
        self.multisel_end=0                     # variables for multiselection of checkboxes

        #---in Export Dialog manipulated variables---
        self.ex_tab=""  # chosen category to be in Excel Tabs (incl None)
        self.ex_row=""  # chosen category to be in Excel Rows
        self.ex_col=""  # chosen category to be in Excel Columns

    #---Option Parameters---
        self.ListFontSize=8

    #---- File Directories ----
        self.dataPath="data/"
        self.dicPath="data/dicx/"
        self.outPath="output/"
        self.dicURL='http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&downfile=dic%2Fen%2F'
        self.bulkURL = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&file=data%2F'
        self.eurostatURL ='http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&dir=data'
        self.eurostatURLchar= 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?dir=data&sort=1&sort=2&start=' #+'n' is the list of files start with "n"
    #---- call INITIALIZING FUNCTIONS --------


        self.updateDBList()  # fills List with tsv-filenames from directory /Data


    #---- LINKING BUTTONS --------
        # OK and Abort #+++++++++++++++++++++++++++
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"),self.doOK)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"),self.doAB)

        self.connect(self.ui.pushButton,QtCore.SIGNAL("clicked()"),self._loadDB)
        self.connect(self.ui.pushButton_2,QtCore.SIGNAL("clicked()"),self._addDB)
        self.connect(self.ui.pushButton_3,QtCore.SIGNAL("clicked()"),self._updateDBfile)
        self.connect(self.ui.pushButton_9,QtCore.SIGNAL("clicked()"),self._removeDBfile)

        #self.connect(self.ui.pushButton_4,QtCore.SIGNAL("clicked()"),self._loadPreset)
        self.connect(self.ui.pushButton_5,QtCore.SIGNAL("clicked()"),self._initExport)
        #self.connect(self.ui.pushButton_10,QtCore.SIGNAL("clicked()"),self._optionDialog)

        #TEST BUTTONS
        self.connect(self.ui.pushButton_6,QtCore.SIGNAL("clicked()"),self.printDuke)
##        self.connect(self.ui.pushButton_7,QtCore.SIGNAL("clicked()"),self.addFileInfo)

        #LINKING OTHER ACTIONS
        self.connect(self.ui.tabWidget,QtCore.SIGNAL("currentChanged()"),self._tabChanged) # to reset multi-select variables



######################### CLASS FUNCTIONS ############################




    def printDuke(self):
        #print self.duke
        print str(self.ui.lcdNumber.value())

    # OK & Abort +++++++++++++++++++++++++++
    def doOK(self):
        print("ok")
        self.accept()

    def doAB(self):
        print("abort")
        self.reject()

#++++++++++++++INITIALIZING #+++++++++++++++++++++++++++

    def updateDBList(self):

        #---read filenames in data-directory ---
        tsv_cntr=0
        tsv_names=[]
        for ba in os.listdir(self.dataPath):
            if ba[-4:]==".tsv":
                tsv_cntr+=1
                tsv_names.append(ba[:-4])

        #---addjust List ----
        self.ui.tableWidget_3.setColumnCount(3)
        self.ui.tableWidget_3.setRowCount(tsv_cntr)
        self.ui.tableWidget_3.setColumnWidth(0,100)
        self.ui.tableWidget_3.setColumnWidth(1,70)
        self.ui.tableWidget_3.setColumnWidth(2,70)
        #self.ui.tableWidget_3.resizeRowsToContents()

        self.ui.tableWidget_3.setHorizontalHeaderLabels(["filename","last update","size"])

        for i,fname in enumerate(tsv_names):
            self.ui.tableWidget_3.setItem(i,0,QtGui.QTableWidgetItem(fname))
            fileinfo= self.getFileInfo(fname).split(";")
            self.ui.tableWidget_3.setItem(i,1,QtGui.QTableWidgetItem(fileinfo[1]))
            self.ui.tableWidget_3.setItem(i,2,QtGui.QTableWidgetItem(fileinfo[2]))

        #adjust size
        font= QtGui.QFont()
        font.setPointSize(self.ListFontSize)
        self.ui.tableWidget_3.setFont(font)
        self.ui.tableWidget_3.resizeRowsToContents()
#++++++++++++++FUNCTIONS +++++++++++++++++++++++++++


    def _tabChanged(self):  # SIGNAL for the Checkbox-multiselection
        #set class-vars to 0 if tab is changed - to avoid errors of multiselection via several tabs
        print("Tab changed - multiselvariables reset")
        self.multisel_end=0
        self.multisel_start=0


    def updateTab(self):
        #FUNCITON:
        #Read class arrays (self.cl_...) and create filling array.
        #The filling array is equal to the displayed array in the big Table

        col_cnt = 3                #intput: number of Columns = 3  (Checkbox, Short, Long)
        filling=[]                 # fillin is the array of all what is displayed in the big TAble
        tabnames=[]                 # tabnames are all Titles (geo,time,unit,curr,...)
        cat_info=""                 # tmp var for infotext eg. "Austria" for "AT"

        #---check if input values exist---
        if self.cl_title_list.__len__()==0:     #if class variables are not filled use dummies
            print("Msg: Loading unsuccessful. Class variables empty")
            return False


        #---create TAB titles--- incl TIME (pos 0) and GEO (last pos) PLUS check DICt
        tabnames.append("TIME")
        for tt in self.cl_title_list:
            tabnames.append(tt)
            ##self.checkDICfile(tt) #redundant
        tabnames.append("GEO")
        tabnames.insert(0,"dummy") #!! one additional Tab that will be deleted at the end

        #---get the category arrays---incl TIME (pos 0) and GEO (last pos)

        filling=self.cl_cat_list[:] # !!! [:] is necessary otherwise the filling == cat_list  and change in filling -> change in catlist
        filling.insert(0,self.cl_time_list)
        filling.append(self.cl_geo_list)


        #---clear TAB array ---
        self.arr_tab=[]     #clear tab array
        self.arr_chkbx=[]   #clear checkbox array
        self.arr_chkbxall=[] #clear "select all" checkbox array

        #---remove all TABS---
        for i in range(self.ui.tabWidget.count()):
            self.ui.tabWidget.removeTab(0)

        #---create new TABS---
        for i,name in enumerate(tabnames):
            self.arr_tab.append(QtGui.QWidget())                # make (Tab)Widget
            self.ui.tabWidget.addTab(self.arr_tab[i],name)      # add new TAB with name-array


        #---generate Tables and link Tabs to Tables (incl dummy)
        self.arr_table=[]
        for i,tn in enumerate(tabnames):                                    # LOOP for each TAB
            if i==0:                                                        #do nothing for the dummy-TAB at pos 0 (will be deleted)
                continue
            else:
                #---TABLE Properties----
                tableWidget = QtGui.QTableWidget(self.arr_tab[i])           # set Table and Link to Tab
                tableWidget.setGeometry(QtCore.QRect(10, 10, 491, 271))
                tableWidget.setColumnCount(col_cnt)
                tableWidget.setRowCount(filling[i-1].__len__()+1)           #+1 for the "select all" button
                tableWidget.setColumnWidth(0,40)
                tableWidget.setColumnWidth(1,100)
                tableWidget.setColumnWidth(2,300)

                #---checkbox items ----
                self.arr_chkbx.append([])                                   #for each Tab a new CheckboxArray

                #---checkbox select all---
                boxall=QtGui.QTableWidgetItem()                             #make item for select-all-checkbox
                boxall.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                boxall.setCheckState(QtCore.Qt.Unchecked)
                self.arr_chkbxall.append(boxall)

                #---insert "select all" items---
                tableWidget.setItem(0,1,QtGui.QTableWidgetItem("Select All"))
                tableWidget.setItem(0,0,boxall)

                ##---data point counter (optional)
                ##self.connect(tableWidget,QtCore.SIGNAL("itemChanged(QTableWidgetItem*)"),self.selectAllSignal)   #activates data-point counter

                #---link CheckBoxClicking to Selection-Functions---
                self.connect(tableWidget,QtCore.SIGNAL("cellChanged(int,int)"),self._TableCellChanged)           #is called in case a checkBox was clicked - Use for counter
                self.connect(tableWidget,QtCore.SIGNAL("cellDoubleClicked(int,int)"),self._TableCellDoubleClicked) #is called in case a checkBox was double clicked - use for multi-selection


                for j,text in enumerate(filling[i-1]):                             # fill in categories in i-th Title/Tab
                    #---create  Checkboxes---
                    box=QtGui.QTableWidgetItem()
                    box.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    box.setCheckState(QtCore.Qt.Unchecked)
                    #---link checkboxitem to array and TAble
                    self.arr_chkbx[i-1].append(box)
                    tableWidget.setItem(j+1,0,box)  #j+1 due to empty first line (select all)

                    #---insert Info (short, long)---
                    tableWidget.setItem(j+1,1,QtGui.QTableWidgetItem(text))         #+1 for the "select all" button
                    cat_info=self.findInDict(tn,text)                              #get "Austria" from input Title ("GEO") and Abbreviationo "AT"
                    tableWidget.setItem(j+1,2,QtGui.QTableWidgetItem(cat_info))     #+1 for the "select all" button

                tableWidget.resizeRowsToContents()

                #---LINK TABLE TO class variable
                self.arr_table.append(tableWidget)


        #---delete Dummy Tab ----    due to an unknown reason , the first tab cannot be filled with a tab.
        #                           there fore the empty "dummy" tab is deleted in all arrays.
        self.ui.tabWidget.removeTab(0)
        #del self.arr_table[0]
        del self.arr_tab[0]

        self.ui.tabWidget.setCurrentIndex(0)


    def _removeDBfile(self):
        # removes selected tsv-file from data directory

        row_sel=self.ui.tableWidget_3.currentRow()  #---get name of selected db---

        if row_sel==-1:
            print("WARNING - No Database seleced...no file removed.")  #---check for no selection
            return False

        tsvfile=str(self.ui.tableWidget_3.item(row_sel,0).text())+".tsv"  #---get name of selected item---
        print("removing file "+self.dataPath+tsvfile)

        #---removing file---
        os.remove(self.dataPath+tsvfile)
        self.delFileInfo(tsvfile)  # -4 to delete the ".tsv" string
        self.updateDBList()





    def _updateDBfile(self):
        #FUNCTION: IF a row(database) is selected try redownload file and update List in any case.

        #---get name of selected db---
        row_sel=self.ui.tableWidget_3.currentRow()

        if row_sel==-1:                                                     #---check for no selection
            print("WARNING - No Database seleced...only an update of List is executed")
        else:
            file_selected=str(self.ui.tableWidget_3.item(row_sel,0).text())  #---get name of selected item---

            if(self.downloadTSV(file_selected)):                               #---re-download
                print("Update of "+file_selected+" successful")
                self.addFileInfo(file_selected)                   # --- get current file info
            else:
                print("ERROR in downloading the file: "+file_selected+".tsv")

        self.updateDBList()




    def _loadDB(self):   # loading the selected  database
    # return False if no Database was selected

        #---get selected database---
        row_sel=self.ui.tableWidget_3.currentRow()                              #---get selected row

        if row_sel==-1:                                                          #---check for invalid selection
            print("WARNING - No Database seleced...")
            return False

        file_selected=str(self.ui.tableWidget_3.item(row_sel,0).text())         #---read selected name---
        print ("Attempt to load selected database: "+file_selected)

        self.ui.label_2.setText("Actual Database: "+file_selected)               #---update info-label above TAble

        #---load TSV Information to class arrays---
        self.loadTSVinfo(file_selected)

        #---update Tabs = Filling tabs with info from class arrays ---
        self.updateTab()



    def _addDB(self):    # download new database and update lst
        # returns FALSE if download of tsv-File fails or file is already in the List

        fileName=str(self.ui.lineEdit.displayText())    #---GET FILENAME from LineEdit

        #---check empty
        if fileName=="":
            print("WARNING - No filename inserted - Nothing execuded!")
            return False

        fileName=fileName.replace(" ","")               # deleting unintentionally space-characers

        #---CHECK - is file already in Database?
        if fileName+".tsv" in os.listdir("data/"):
            print("Warning - tsv File already exists - Press Update button to redownload file")
            self.ui.lineEdit.clear()
            return False

        #---try to download and add file in db-directory ----
        if self.downloadTSV(fileName):
            self.ui.lineEdit.clear()    # clear line edit
            self.addFileInfo(fileName) # html-read the update-date and file size of the downloaded file
            self.updateDBList()         # update list to show new db

            print("Download successful")





    def loadTSVinfo(self,dbname):
        #FUNCtION: reads existing tsv-file
        #1) checks dictionary
        #2) fills class variables (cat_list,time_list) with the info
        #   (titles,categories,dictionary...)

        #TSV - FIle Structure after open as tsv:
        # 1st row: [unit,nace_r1,indic_na,geo\time] [2012]  [2011] ... [1980]
        # 2nd row  [CPI00_EUR,A_B,B1G,AT] [value] [value]...

        #OUTPUT: 2D-Array: for titles:[unit,nace_r1,indic_na,geo\time]
        # cat_list (2DArray) =[ [cpi00_eur,cpi00_nac...],[A_B,C-E,D,F...],[B1G] ]
        # time_list          = [2012,2011,2010...]
        # geo_list          = [AT,BE,BG...SI]

        tmp=[]
        title_list=[]    #array for titles (without geo/time)   "unit,nace_r1,indic_na"
        cat_list=[]     # array for all categories               "DI_pps,
        time_list=[]  #array for time                       "2012,2011,2010..."
        geo_list=[]   # array for GEO


        #---open file and read line by line---
        tsvFileName = self.dataPath+dbname+'.tsv'
        with open(tsvFileName, 'r') as tsvFile:
            tsvReader = csv.reader(tsvFile, delimiter='\t')

            for i, row in enumerate(tsvReader):
                if i==0:
                    #---get dic-TITLES---
                    title_list=(row[0].split(","))[:-1]        # [:-1] -> title_list without the last "geo/time"

                    #---check DICTIONARY and append 2D-array for Category-list
                    for tt in title_list:
                        self.checkDICfile(tt)           #check dictionary of each title
                        cat_list.append([])             # make category-Arrayfor each title

                    #---get TIME array from row---
                    for j in range(1,row.__len__()):  # starts at 1 because at [0] are categories
                        time_list.append(row[j])

                else:
                    #---get Categories and GEO
                    tmp=row[0].split(",")                     # row eg. CPI00_EUR,A_B,B1G,BG
                    for i,tt in enumerate(title_list):        # for each title check if the category of this row is in the cat_list
                        if tmp[i] not in cat_list[i]:           # if not then append to cat_list in the row of the respective title
                            cat_list[i].append(tmp[i])

                    if tmp[tmp.__len__()-1] not in geo_list:    # fill GEO List with the GEO Info (is always last)
                        geo_list.append(tmp[tmp.__len__()-1])

        #fill info in class-variables
        self.cl_time_list=time_list
        self.cl_cat_list=cat_list
        self.cl_geo_list=geo_list
        self.cl_title_list=title_list


    def findInDict(self,title,shorty):
        #INPUT: title is equal to .dic -filename    (Geo)
        #INPUT: shorts is the abbreviations (AT)
        #RETURN: Long-Text of shorts     (Austria...)

        if title.upper()=="TIME":    #TIME is the only title without long-text
            return ""

        longy=""

        try:
            dicFileName = self.dicPath+title+".dic"             #open dict that is equal to the TAbtitle

            with open(dicFileName,"r") as dicFile:
                dicReader = csv.reader(dicFile,delimiter="\t")
                for row in dicReader:                           #search every row of the dict for the short
                    if row[0]==shorty:                              #if they match
                        longy = row[1]                           #append to long
                        return str(longy)
            return "n.a."

        except:
            print("ERROR- in Dic File opening:"+dicFileName)
            return False



    def checkDICfile(self,fileName):
        #return True if dictionar exists or download was successful; or if fileName=TIME (where no Dic exists)
        #return False otherwise;

        if fileName.upper=="TIME":
            return True

        dicFileName=fileName+".dic"

        print("check for dictionary "+dicFileName)
        if dicFileName in os.listdir(self.dicPath):
            print("dictionary found...OK")
        else:
            print("dictionary NOT found...start download attempt")
            if self.downloadDIC(dicFileName):
                return True
            else:
                return False


    def downloadDIC(self,dicFileName):   # download of eurostat dictionary file
    #return True if download OK
    #return False otherwise

        try:#---get URL and response---
            fileURL =self.dicURL+dicFileName
            response = urlopen(fileURL)
            print("Dictionary download OK")
        except:
            print("ERROR in downloading Dictionary "+dicFileName)
            return False

        try:#---saving download---
            os.chdir(self.dicPath)
            with open(dicFileName, 'wb') as outfile:
                outfile.write(response.read())

            os.chdir("..") # 2x because dic is 2steps down
            os.chdir("..")
        except:
            print("ERROR in saving Dictionary "+dicFileName)
            return False



    def downloadTSV(self,fileName):
        #returns True if successful downloaded and extracted
        #returns False at any error


        print("START attempt to download file "+fileName+".tsv from the Eurostat Webpage...please wait")

        os.chdir(self.dataPath)  #change directory to Data (otherwise trouble with the "open" function
        gzFileName=fileName+".tsv.gz"
        tsvFileName =fileName+'.tsv'

        try:
            #---get gz file from eurostat page---
            fileURL = self.bulkURL + gzFileName
            response = urlopen(fileURL)

            with open(gzFileName, 'wb') as outfile:
                outfile.write(response.read())

            #---EXTRACT TSV.GZ.FILE---
            with open(tsvFileName, 'wb') as outfile, gzip.open(gzFileName) as infile:
                outfile.write(infile.read())

            #---delete gz file---
            os.remove(gzFileName)

            os.chdir("..")
            print("Download and Extraction successfull")
            return True

        except Exception as ee:   # delete the remains of partdownloads - if they exist
            print("ERROR in Download and/or Extraction of tsv file: "+str(ee))
            print("TIP: Check File availability at Eurostat, Database Name and the Download-URL in the Options")
            if gzFileName in os.listdir("./"):
                os.remove(gzFileName)
            if tsvFileName in os.listdir("./"):
                os.remove(tsvFileName)
            os.chdir("..")
            return False




    def addFileInfo(self,fname):
    #FUNCTION : reads fileinformation (last update, filesize) from the eurostat webpage
    #           and stores info in _INFO.txt

        #---read html data and search filename---
        fileURL = self.eurostatURLchar+fname[0]  # the url is sorted e.g. it ends with "a" for a List of files that start with "a"
        response = urlopen(fileURL)

        for line in response:
            if fname in line:
                info= line
                break

        # ---extract size and date from html text
        fsize= info.split("</td>")[1].split(">")[1]
        fdate= info.split("</td>")[3].split("&nbsp;")[1][:10]
        finfo=fname+";"+fdate+";"+fsize  # = "aact_ali02;6.5 KB;07/04/2014"

        #---write in file
        with open(self.dataPath+"_INFO.txt","a") as f:
            f.write(finfo+"\n")



    def getFileInfo(self,fname):
        # for filename "aact_ali02 this function returns: "6.5 KB;07/04/2014"
        # by looking in the _INFO-file.

        if fname[-4:]==".tsv":   #file.tsv -> file  (if necessary)
            fname=fname[:-4]

        lines = open(self.dataPath+"_INFO.txt").readlines()
        for ln in lines:
            if fname in ln:
                return ln
        return "n.a.;n.a.;n.a."


    def delFileInfo(self,fname):
    #FUNCTION : removes fileinfo (update-date,size) to _info.txt
        if fname[-4:]==".tsv":   #file.tsv -> file  (if necessary)
            fname=fname[:-4]

        todelete=self.getFileInfo(fname) #as "aact_ali02;6.5 KB;07/04/2014"

        lines = open(self.dataPath+"_INFO.txt").readlines()
        lines.remove(todelete)
        #newlines=lines
        open(self.dataPath+"_INFO.txt", 'w').writelines(lines)

    def _TableCellChanged(self,r,c):
        #FUNCTION: Signal is thrown if a Cell was changed
        # Here only applied for Checkbox-change

        #INPUT: r=row c=column of the changed Table-Cell
        #This function checks if it was the "Select All" box
        #and consequently de- or selects the respective boxes in the actual TAb

        #---if "Select all"-Checkbox was changed - deselect or select all
        if r==0 and c==0:
            print("select all was clicked...")

            #---get actual tab
            actTab=self.ui.tabWidget.currentIndex()

            #---if "Select All"-Box has changed to ==2  (has now a haekchen)  then select all boxes
            if self.arr_chkbxall[actTab].checkState()==2:
                self.selectAllInTab("select",actTab)
            #---if "Select All"-Box has changed to ==0  (has now no haekchen)  then DEselect all boxes
            if self.arr_chkbxall[actTab].checkState()==0:
                self.selectAllInTab("deselect",actTab)

        else:
            pass # another checkbox was changed - do nothing

        #---Count the checked boxes and calculate the Amount of its permutations---
        self.ui.lcdNumber.display(self.count_checked_boxes())



    def selectAllInTab(self,cmd,TabNr):
        # Function selects or de selects all boxes of a tab.
        #input : cmd = eiter "select" or "deselect" and The Tab index

        ##print("cmd is "+cmd)
        if cmd=="select":
            for box in self.arr_chkbx[TabNr]:           #for each box in this column
                box.setCheckState(QtCore.Qt.Checked)
            return True
        if cmd=="deselect":
            for box in self.arr_chkbx[TabNr]:
                box.setCheckState(QtCore.Qt.Unchecked)
            return True

        if cmd!="select" and cmd!="deselect":           #if wrong command is given
            print("WARNING - Select-All-Command unfeasable: "+str(cmd))
            return False


    def _TableCellDoubleClicked(self,r,c):
        #FUNCTION -Get Signal of DoubleClick in Table (row, column)
        # Select all Checkboxes between two Doubleclicks in Column 0


        print("Doubleclick at row: "+str(r)+" col: "+str(c))

        #---check row---
        if r==0:        # row 0 ="select all"-cell -> unvalid - therefore abort
            print("WARNING - Double click in unvalid Cell row - No start row set for multi-selection")
            return False

        #---set start/end variables ---
        if self.multisel_start==0:  # if start=0 (is not set yet) then set start-row
            self.multisel_start=r
        else:                       # if start!=0 (is already set) then set end row
            self.multisel_end=r
            self.selectRowsInTab(self.multisel_start,self.multisel_end)    #check the boxes


    def selectRowsInTab(self,r_start,r_end):
        #select the rows given
        #and reset the class variables to 0
        #!! Remember Row 1 = checkbox 0 ; Row 2 = checkbox 1 ...
        #therefore doubleclick row 0 (Select all) is alwys unvalid

        #---check if start=end - if so reset and abort
        if (r_end==r_start) and (r_end!=0 and r_start!=0) :
            self.multisel_start=0
            self.multisel_end=0
            print("WARNING - Start row is End row - MultiSelection variables reset to 0")
            return False


        #---get actual tab
        actTab=self.ui.tabWidget.currentIndex()

        #---check Checkboxes ----
        for j,box in enumerate(self.arr_chkbx[actTab]):           #for each box in this column (row =j)
            if self.isBetweenValues(j,r_start-1,r_end-1):         #if j is between r_start and r_end  ; -1 because checkbox 0 is at Row 1
                box.setCheckState(QtCore.Qt.Checked)

        #---reset varibales---
        self.multisel_start=0
        self.multisel_end=0


    def isBetweenValues(self,v,v1,v2):
           # return True if value is between val1 and val2 -inclusive v1 and v2
           #otherwise return False

        if v2>v1:
            if v<=v2 and v>=v1:
                print("value "+str(v)+" is between "+str(v1)+" and "+str(v2))
                return True

        if v1<v2:
            if v<=v1 and v>=v2:
                print("value "+str(v)+" is between "+str(v1)+" and "+str(v2))
                return True

        print("value "+str(v)+" is NOT between "+str(v1)+" and "+str(v2))
        return False





    def count_checked_boxes(self):
        #returns number of total selected data points (via checkboxes)

        chk_cnt=0   # count checks
        chksum=[]   #array of actual checks

        for boxcol in self.arr_chkbx:   # for each column of checkboxes...
            chk_cnt=0
            for box in boxcol:           #for each box in this column
                if box.checkState()==2:   #checkState 0(unchecked) 2(checked)
                    chk_cnt+=1

            chksum.append(chk_cnt)

        total=1
        for n in chksum:    #Mulitplication of selected rows equal the total selected data points
            total*=n

        return total



    def _initExport(self):

        #--check if in each Tab at least one is selected---
        checkLCD=self.ui.lcdNumber.value()
        if checkLCD<1:
            print("WARNING: For an Export procedure at least one item in each Tab need to be selected!!")
            return

        #---write box selection in CLass Array ---
        self.cats_selected=self.getSelectedCats()


       #---deselect all boxes (optional)---
        for i,boxcol in enumerate(self.arr_chkbx):           #for each column of checkboxes, i is equal to Tab index
            self.selectAllInTab("deselect",i)

        #---write Mutations in Class Array cats_sel_mut---
        self.cats_sel_mut=[] # leeren
        self.genrMutation(0,"",self.cats_selected.__len__()) #füllen

##        print("All Mutations:") #show all mutatiaons
##        print self.cats_sel_mut
        print("Check - TARGET Permutations Count: "+str(checkLCD))
        print("ACTUAL Permutation Count         : "+str(self.cats_sel_mut.__len__()))


        #---show export option dialog---
        dialog = ExportDialog(self)
        dialog.show()




    def setExportCats(self,tab,row,col):
        #---this function is solely for the Export dialog to call

        self.ex_col=col
        self.ex_row=row
        self.ex_tab=tab

        print("slected Structure  for export:")
        print("tab: "+self.ex_tab)
        print("row: "+self.ex_row)
        print("column: "+self.ex_col)


    def startExport(self):
        print("Start exporting...")

        #---structure selection ok---
        #---mutations generated

        # if self.ex_tab!="":  # split mutations.





    def getSelectedCats(self):
        #FUNCTION: read all selected boxes and make an array of the Shorts
        #e.g. [AT,BG,UK][EUR,NAC][A_B,D,E,F][2011,2010,2009,2008]
        # return array of selections

        selection=[]   #array of selections (subset of whole_list)

        #---create array of all category items - check box reference ----
        whole_list=self.cl_cat_list[:]
        whole_list.insert(0,self.cl_time_list[:])
        whole_list.append(self.cl_geo_list[:])

        for i,boxcol in enumerate(self.arr_chkbx):           #for each column of checkboxes, i is equal to Tab index
            selection.append([])
            for j,box in enumerate(boxcol):                  #for each box, j is equal to Row index
                if box.checkState()==2:
                    selection[i].append(whole_list[i][j])
        return selection


    def genrMutation(self,lvl,txt,maxlvl):
        #Function receives an Array of Selected categories
        #Goal: Make all possible Mutations of this selection and return it
        # cannot remember how I did it, but it worx
        # starting call is: self.genrMutation(0,"",self.cats_selected.__len__())

        if lvl<maxlvl:
            for j in range(self.cats_selected[lvl].__len__()):
                self.genrMutation(lvl+1,txt+self.cats_selected[lvl][j]+",",maxlvl)
        else:
            self.cats_sel_mut.append(txt[:-1])
            return

        return True

####################################################################
############################# END ##################################
####################################################################

def main():
    app = QtGui.QApplication(sys.argv)
    window = BaseWindow()
    window.show()

    print sys.exit(app.exec_())


if __name__ == "__main__":
    main()
