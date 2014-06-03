# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# EXPORT DIALOT
from ExportDialog import ExportDialog

# HELPERS AND SETTINGS
from helpers import Settings
import helpers as f

# EXPORT UI
import base

class BaseWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(QtGui.QDialog, self).__init__(parent)
        self.ui = base.Ui_base()
        self.ui.setupUi(self)

        # init variables
        self.ignoreItemChanges = False
        self.metaData = None
        self.tables = None

        self.ListFontSize=8

        # update db list
        self.updateDBList() 

        # connect buttons
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("close()"), self.close)
        self.connect(self.ui.loadButton, QtCore.SIGNAL("clicked()"), self._loadDB)
        self.connect(self.ui.addButton, QtCore.SIGNAL("clicked()"), self._addDB)
        self.connect(self.ui.updateButton, QtCore.SIGNAL("clicked()"), self._updateDBfile)
        self.connect(self.ui.removeButton, QtCore.SIGNAL("clicked()"), self._removeDBfile)

        #self.connect(self.ui.loadPresetButton, QtCore.SIGNAL("clicked()"), self._loadPreset)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._initExport)
        #self.connect(self.ui.optionsButton, QtCore.SIGNAL("clicked()"), self._optionDialog)


    def updateDBList(self):
        #---read filenames in data-directory ---
        tsv_names = f.getFileList()

        #---addjust List ----
        self.ui.databaseTable.setRowCount(len(tsv_names))


        #self.ui.databaseTable.setHorizontalHeaderLabels(["filename","last update","size"])

        for i, fname in enumerate(tsv_names):
            self.ui.databaseTable.setItem(i, 0, QtGui.QTableWidgetItem(fname))
            fileinfo = f.getFileInfo(fname).split(";")
            self.ui.databaseTable.setItem(i, 1, QtGui.QTableWidgetItem(fileinfo[1].strip(' \t\n\r')))
            self.ui.databaseTable.setItem(i, 2, QtGui.QTableWidgetItem(fileinfo[2].strip(' \t\n\r')))

        #adjust size
        #font= QtGui.QFont()
        #font.setPointSize(self.ListFontSize)
        #self.ui.databaseTable.setFont(font)
        #self.ui.databaseTable.resizeRowsToContents()


    def updateTab(self, metaData):
        #Read class arrays (self.cl_...) and create filling array.
        #The filling array is equal to the displayed array in the big Table


        #---create TAB titles--- incl TIME (pos 0) and GEO (last pos) PLUS check DICt
        tabnames = []                 # tabnames are all Titles (geo,time,unit,curr,...)
        for entry in metaData["_cols"]:
            tabnames.append(entry)

        tabnames.insert(0, "dummy") #!! one additional Tab that will be deleted at the end

        self.ui.tabWidget.clear();
        self.metaData = metaData
        self.tables = {}

        #---generate Tables and link Tabs to Tables (incl dummy)
        
        for i, tn in enumerate(tabnames):                                    # LOOP for each TAB
            if i == 0:
                tWidget = QtGui.QWidget()                                                        #do nothing for the dummy-TAB at pos 0 (will be deleted)
                self.ui.tabWidget.addTab(tWidget, tn)
                continue
            else:
                entries = metaData[tn]
                #---TABLE Properties----
                tableWidget = QtGui.QTableWidget(tWidget)           # set Table and Link to Tab
                self.ui.tabWidget.addTab(tableWidget, tn)
                #tableWidget.setGeometry(QtCore.QRect(10, 10, 491, 271))
                tableWidget.setColumnCount(3)
                tableWidget.setRowCount(len(entries) + 1)           #+1 for the "select all" button
                tableWidget.setColumnWidth(0,  40)
                tableWidget.setColumnWidth(1, 100)
                tableWidget.setColumnWidth(2, 300)
                tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
                tableWidget.verticalHeader().setVisible(False)
                tableWidget.setAlternatingRowColors(True)
                #tableWidget.setSortingEnabled(True)
                tableWidget.horizontalHeader().setStretchLastSection(True)

                tableWidget.setHorizontalHeaderLabels(["Select", "Short", "Long"])

                #---checkbox select all---
                boxall = QtGui.QTableWidgetItem()                             #make item for select-all-checkbox
                boxall.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                boxall.setCheckState(QtCore.Qt.Unchecked)

                #---insert "select all" items---
                tableWidget.setItem(0, 1, QtGui.QTableWidgetItem("Select All"))
                tableWidget.setItem(0, 0, boxall)

                for j, text in enumerate(entries):                             # fill in categories in i-th Title/Tab
                    #---create  Checkboxes---
                    box = QtGui.QTableWidgetItem()
                    box.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    box.setCheckState(QtCore.Qt.Unchecked)
                    #---link checkboxitem to array and TAble
                    tableWidget.setItem(j + 1, 0, box)  #j+1 due to empty first line (select all)

                    #---insert Info (short, long)---
                    tableWidget.setItem(j + 1, 1, QtGui.QTableWidgetItem(text))         #+1 for the "select all" button
                    cat_info = f.findInDict(tn, text)                              #get "Austria" from input Title ("GEO") and Abbreviationo "AT"
                    tableWidget.setItem(j + 1, 2, QtGui.QTableWidgetItem(cat_info))     #+1 for the "select all" button

                tableWidget.resizeRowsToContents()

                self.connect(tableWidget, QtCore.SIGNAL("itemChanged(QTableWidgetItem*)"), self._tableItemChanged)
                self.tables[tn] = tableWidget


        #---delete Dummy Tab ----    due to an unknown reason , the first tab cannot be filled with a tab.
        #                           there fore the empty "dummy" tab is deleted in all arrays.
        self.ui.tabWidget.removeTab(0)
        self.ui.tabWidget.setCurrentIndex(0)

        self.ui.lcdNumber.display(0)
        self.ui.exportButton.setEnabled(False)



    def _tableItemChanged(self, tableItem):
        table   = tableItem.tableWidget()
        if not self.ignoreItemChanges:
            self.ignoreItemChanges = True
            col     = tableItem.column()
            row     = tableItem.row()

            if row == 0 and col == 0:
                # All Select
                for i in range(1, table.rowCount()):
                    table.item(i, 0).setCheckState(tableItem.checkState())
            else:
                # Area Select
                selectedRows = set();
                for s in table.selectedItems():
                    selectedRows.add(s.row());

                if row in selectedRows:
                    for i in selectedRows:
                        table.item(i, 0).setCheckState(tableItem.checkState())
            self.ignoreItemChanges = False

        # Set Counter
        ec = 1
        for tableWidget in self.tables.values():
            c = 0
            for i in range(1, tableWidget.rowCount()):
                if tableWidget.item(i, 0).checkState() == QtCore.Qt.Checked:
                    c += 1
            ec *= c
            if ec == 0:
                break

        self.ui.exportButton.setEnabled(ec > 0)
        self.ui.lcdNumber.display(ec)


    def _removeDBfile(self):
        # removes selected tsv-file from data directory
        row_sel = self.ui.databaseTable.currentRow()  #---get name of selected db---

        if row_sel == -1:
            print("WARNING - No Database seleced...no file removed.")  #---check for no selection
            return False

        name = str(self.ui.databaseTable.item(row_sel,0).text())   #---get name of selected item---
        f.removeTsvFile(name);
        f.delFileInfo(name)  # -4 to delete the ".tsv" string
        self.updateDBList()


    def _updateDBfile(self):
        #FUNCTION: IF a row(database) is selected try redownload file and update List in any case.

        #---get name of selected db---
        row_sel=self.ui.databaseTable.currentRow()

        if row_sel==-1:                                                     #---check for no selection
            print("WARNING - No Database seleced...only an update of List is executed")
        else:
            file_selected=str(self.ui.databaseTable.item(row_sel,0).text())  #---get name of selected item---

            if(f.downloadTsvFile(file_selected)):                               #---re-download
                print("Update of "+file_selected+" successful")
                f.addFileInfo(file_selected)                   # --- get current file info
            else:
                print("ERROR in downloading the file: " + file_selected + ".tsv")

        self.updateDBList()


    def _loadDB(self):   
        # loading the selected  database
        # return False if no Database was selected

        #---get selected database---
        row = self.ui.databaseTable.currentRow()                              #---get selected row

        if row == -1:                                                          #---check for invalid selection
            f.log("WARNING - No Database seleced...")
            return False

        name = str(self.ui.databaseTable.item(row, 0).text())         #---read selected name---
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


    def _initExport(self):
        #--check if in each Tab at least one is selected---
        checkLCD = self.ui.lcdNumber.value()
        if checkLCD == 0:
            f.log("WARNING: For an Export procedure at least one item in each Tab need to be selected!!")
            return

        #---write box selection in CLass Array ---
        selection = self.getSelectedCats()

        #---show export option dialog---
        dialog = ExportDialog(self)
        dialog.init(self.metaData, selection)
        dialog.show()


    def getSelectedCats(self):
        selection = {}
        for code, tableWidget in self.tables.items():
            selection[code] = []
            for i in range(1, tableWidget.rowCount()):
                if tableWidget.item(i, 0).checkState() == QtCore.Qt.Checked:
                    selection[code].append(str(tableWidget.item(i, 1).text()))
        return selection


    def setSelectedCats(self, selection):
        for code, tableWidget in self.tables.items():
            if code in selection:
                for i in range(1, tableWidget.rowCount()):
                    if tableWidget.item(i, 1).text() in selection[code]:
                        tableWidget.item(i, 0).setCheckState(QtCore.Qt.Checked)