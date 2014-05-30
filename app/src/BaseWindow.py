# -*- coding: utf-8 -*-

################## LIBRARY IMPORTs################################
import os, sys, time

from PyQt4 import QtCore, QtGui

import os, sys

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

import xlrd, xlwt

from ExportDialog import ExportDialog

from helpers import Settings
import helpers as f

import base

#######################################################################
################## MAIN DIALOG CLASS################################
class BaseWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(QtGui.QDialog, self).__init__(parent)
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

    #---Option Parameters---
        self.ListFontSize=8

    #---- call INITIALIZING FUNCTIONS --------


        self.updateDBList()  # fills List with tsv-filenames from directory /Data


    #---- LINKING BUTTONS --------
        # OK and Abort #+++++++++++++++++++++++++++
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("close()"),self.close)

        self.connect(self.ui.pushButton,QtCore.SIGNAL("clicked()"),self._loadDB)
        self.connect(self.ui.pushButton_2,QtCore.SIGNAL("clicked()"),self._addDB)
        self.connect(self.ui.pushButton_3,QtCore.SIGNAL("clicked()"),self._updateDBfile)
        self.connect(self.ui.pushButton_9,QtCore.SIGNAL("clicked()"),self._removeDBfile)

        #self.connect(self.ui.pushButton_4,QtCore.SIGNAL("clicked()"),self._loadPreset)
        self.connect(self.ui.pushButton_5,QtCore.SIGNAL("clicked()"),self._initExport)
        #self.connect(self.ui.pushButton_10,QtCore.SIGNAL("clicked()"),self._optionDialog)

        #TEST BUTTONS
##        self.connect(self.ui.pushButton_7,QtCore.SIGNAL("clicked()"),self.addFileInfo)

        #LINKING OTHER ACTIONS
        self.connect(self.ui.tabWidget,QtCore.SIGNAL("currentChanged()"),self._tabChanged) # to reset multi-select variables



######################### CLASS FUNCTIONS ############################


#++++++++++++++INITIALIZING #+++++++++++++++++++++++++++

    def updateDBList(self):
        #---read filenames in data-directory ---
        tsv_names = f.getFileList()

        #---addjust List ----
        self.ui.tableWidget_3.setColumnCount(3)
        self.ui.tableWidget_3.setRowCount(len(tsv_names))
        self.ui.tableWidget_3.setColumnWidth(0,100)
        self.ui.tableWidget_3.setColumnWidth(1,70)
        self.ui.tableWidget_3.setColumnWidth(2,70)
        #self.ui.tableWidget_3.resizeRowsToContents()

        self.ui.tableWidget_3.setHorizontalHeaderLabels(["filename","last update","size"])

        for i, fname in enumerate(tsv_names):
            self.ui.tableWidget_3.setItem(i,0,QtGui.QTableWidgetItem(fname))
            fileinfo = f.getFileInfo(fname).split(";")
            self.ui.tableWidget_3.setItem(i,1,QtGui.QTableWidgetItem(fileinfo[1].strip(' \t\n\r')))
            self.ui.tableWidget_3.setItem(i,2,QtGui.QTableWidgetItem(fileinfo[2].strip(' \t\n\r')))

        #adjust size
        #font= QtGui.QFont()
        #font.setPointSize(self.ListFontSize)
        #self.ui.tableWidget_3.setFont(font)
        #self.ui.tableWidget_3.resizeRowsToContents()
#++++++++++++++FUNCTIONS +++++++++++++++++++++++++++


    def _tabChanged(self):  # SIGNAL for the Checkbox-multiselection
        #set class-vars to 0 if tab is changed - to avoid errors of multiselection via several tabs
        print("Tab changed - multiselvariables reset")
        self.multisel_end=0
        self.multisel_start=0


    def updateTab(self, metaData):
        print(metaData)
        exit()
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
        row_sel = self.ui.tableWidget_3.currentRow()  #---get name of selected db---

        if row_sel == -1:
            print("WARNING - No Database seleced...no file removed.")  #---check for no selection
            return False

        name = str(self.ui.tableWidget_3.item(row_sel,0).text())   #---get name of selected item---
        f.removeTsvFile(name);
        f.delFileInfo(name)  # -4 to delete the ".tsv" string
        self.updateDBList()


    def _updateDBfile(self):
        #FUNCTION: IF a row(database) is selected try redownload file and update List in any case.

        #---get name of selected db---
        row_sel=self.ui.tableWidget_3.currentRow()

        if row_sel==-1:                                                     #---check for no selection
            print("WARNING - No Database seleced...only an update of List is executed")
        else:
            file_selected=str(self.ui.tableWidget_3.item(row_sel,0).text())  #---get name of selected item---

            if(f.downloadTsvFile(file_selected)):                               #---re-download
                print("Update of "+file_selected+" successful")
                f.addFileInfo(file_selected)                   # --- get current file info
            else:
                print("ERROR in downloading the file: "+file_selected+".tsv")

        self.updateDBList()


    def _loadDB(self):   
        # loading the selected  database
        # return False if no Database was selected

        #---get selected database---
        row_sel = self.ui.tableWidget_3.currentRow()                              #---get selected row

        if row_sel == -1:                                                          #---check for invalid selection
            f.log("WARNING - No Database seleced...")
            return False

        name = str(self.ui.tableWidget_3.item(row_sel, 0).text())         #---read selected name---
        f.log("Attempt to load selected database: " + name)

        self.ui.label_2.setText("Actual Database: " + name)               #---update info-label above TAble

        #---load TSV Information to class arrays---
        metaData = f.loadTsvFile(name)

        #---update Tabs = Filling tabs with info from class arrays ---
        self.updateTab(metaData)


    def _addDB(self):    
        # download new database and update lst
        # returns FALSE if download of tsv-File fails or file is already in the List

        fileName = str(self.ui.lineEdit.displayText())    #---GET FILENAME from LineEdit

        #---check empty
        if fileName=="":
            print("WARNING - No filename inserted - Nothing execuded!")
            return False

        fileName = fileName.replace(" ","")               # deleting unintentionally space-characers

        #---CHECK - is file already in Database?
        if fileName in f.getFileList():
            print("Warning - tsv File already exists - Press Update button to redownload file")
            self.ui.lineEdit.clear()
            return False

        #---try to download and add file in db-directory ----
        if f.downloadTsvFile(fileName):
            self.ui.lineEdit.clear()    # clear line edit
            f.addFileInfo(fileName) # html-read the update-date and file size of the downloaded file
            self.updateDBList()         # update list to show new db

            f.log("Download successful")
    

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
