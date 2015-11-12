# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# DIALOGS
from ExcelExportDialog import ExcelExportDialog
from StataExportDialog import StataExportDialog

from ProgressDialog import ProgressDialog
from TreeDialog import TreeDialog

# HELPERS AND SETTINGS
from helpers import Settings
import helpers as f

# BASE UI
import base

from datetime import datetime, timedelta


class BaseWindow(QtGui.QDialog):

    def __init__(self, parent=None):
        super(QtGui.QDialog, self).__init__(parent, QtCore.Qt.Window)
        self.ui = base.Ui_base()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(Settings.iconFile))
        self.setWindowTitle(Settings.applicationName)

        # init variables
        self.ignoreItemChanges = False
        self.metaData = None
        self.tables = None

        # update db list
        self.updateDBList()

        # connect buttons
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("close()"), self.close)
        self.connect(self.ui.loadButton, QtCore.SIGNAL("clicked()"), self._loadDB)
        self.connect(self.ui.addButton, QtCore.SIGNAL("clicked()"), self._addDB)
        self.connect(self.ui.updateButton, QtCore.SIGNAL("clicked()"), self._updateDBfile)
        self.connect(self.ui.removeButton, QtCore.SIGNAL("clicked()"), self._removeDBfile)
        self.connect(self.ui.browseButton, QtCore.SIGNAL("clicked()"), self._browse)

        self.connect(self.ui.databaseTable, QtCore.SIGNAL('cellDoubleClicked(int, int)'), self._loadDB)

        self.connect(self.ui.presetButton, QtCore.SIGNAL("clicked()"), self._loadPreset)

        self.connect(self.ui.addLineEdit, QtCore.SIGNAL("textChanged(const QString &)"), self._addLineEditChanged)

        self.connect(self.ui.excelExportButton, QtCore.SIGNAL("clicked()"), self._initExcelExport)
        self.connect(self.ui.stataExportButton, QtCore.SIGNAL("clicked()"), self._initStataExport)

        self.connect(self.ui.sourceComboBox, QtCore.SIGNAL("currentIndexChanged(const QString &)"), self._sourceChanged)
        #self.connect(self.ui.optionsButton, QtCore.SIGNAL("clicked()"), self._optionDialog)

        self.ui.sourceComboBox.addItems(f.Settings.sources.keys())

        #Settings.inGui = True

    def updateDBList(self):
        #---read filenames in data-directory ---
        #tsvNames = f.getFileList()
        dsList = f.getFileInfoJson()

        comb = []

        for source in dsList:
            for name in dsList[source]:
                comb.append((source, name))

        #---addjust List ----
        self.ui.databaseTable.setRowCount(len(comb))

        for i, (source, name) in enumerate(comb):
            self.ui.databaseTable.setItem(i, 0, QtGui.QTableWidgetItem(name))
            self.ui.databaseTable.setItem(i, 1, QtGui.QTableWidgetItem(source))
            info = f.getFileInfo(source = source, name = name)
            #f.log(info)
            self.ui.databaseTable.setItem(i, 2, QtGui.QTableWidgetItem(str(info["updatedDate"])))
            self.ui.databaseTable.setItem(i, 3, QtGui.QTableWidgetItem(info["size"]))

            newerVersionAvailable = False
            if "newerVersionAvailable" in info and info["newerVersionAvailable"]:
                newerVersionAvailable = True
            else:
                if source == "eurostat":
                    if info["lastCheckedDate"] < (datetime.now() - timedelta(minutes=60)):
                        newInfo = f.getFileInfoFromEurostat(name)
                        if newInfo["updatedDate"] > info["updatedDate"]:
                            newerVersionAvailable = True

            if newerVersionAvailable:
                for j in range(3):
                    self.ui.databaseTable.item(i, j).setForeground(QtGui.QColor.fromRgb(255, 0, 0))
            # myItem->setForeground(QColor::fromRgb(255,0,0));

        # adjust size
        #font= QtGui.QFont()
        # font.setPointSize(self.ListFontSize)
        # self.ui.databaseTable.setFont(font)
        # self.ui.databaseTable.resizeRowsToContents()

    def updateTab(self, metaData):
        # Read class arrays (self.cl_...) and create filling array.
        # The filling array is equal to the displayed array in the big Table
        #---create TAB titles--- incl TIME (pos 0) and GEO (last pos) PLUS check DICt
        tabnames = []                 # tabnames are all Titles (geo,time,unit,curr,...)
        for entry in metaData["_cols"]:
            tabnames.append(entry)

        tabnames.insert(0, "dummy")  # !! one additional Tab that will be deleted at the end

        self.ui.tabWidget.clear()
        self.metaData = metaData
        self.tables = {}

        #---generate Tables and link Tabs to Tables (incl dummy)

        for i, tn in enumerate(tabnames):                                    # LOOP for each TAB
            if i == 0:
                tWidget = QtGui.QWidget()  # do nothing for the dummy-TAB at pos 0 (will be deleted)
                self.ui.tabWidget.addTab(tWidget, tn)
                continue
            else:
                entries = metaData[tn]
                #---TABLE Properties----
                tableWidget = QtGui.QTableWidget(tWidget)           # set Table and Link to Tab
                self.ui.tabWidget.addTab(tableWidget, tn)
                #tableWidget.setGeometry(QtCore.QRect(10, 10, 491, 271))
                tableWidget.setColumnCount(3)
                tableWidget.setRowCount(len(entries) + 1)  # +1 for the "select all" button
                tableWidget.setColumnWidth(0,  40)
                tableWidget.setColumnWidth(1, 100)
                tableWidget.setColumnWidth(2, 300)
                tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
                tableWidget.verticalHeader().setVisible(False)
                tableWidget.setAlternatingRowColors(True)
                # tableWidget.setSortingEnabled(True)
                tableWidget.horizontalHeader().setStretchLastSection(True)

                tableWidget.setHorizontalHeaderLabels(["Select", "Short", "Long"])

                boxall = QtGui.QTableWidgetItem() 
                boxall.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                boxall.setCheckState(QtCore.Qt.Checked)

                tableWidget.setItem(0, 1, QtGui.QTableWidgetItem("Select All"))
                tableWidget.setItem(0, 0, boxall)

                for j, text in enumerate(entries):
                    box = QtGui.QTableWidgetItem()
                    box.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                    # box.setCheckState(QtCore.Qt.Unchecked)
                    box.setCheckState(QtCore.Qt.Checked)

                    tableWidget.setItem(j + 1, 0, box)
                    tableWidget.setItem(j + 1, 1, QtGui.QTableWidgetItem(text))
                    tableWidget.setItem(j + 1, 2, QtGui.QTableWidgetItem(entries[text]))

                tableWidget.resizeRowsToContents()

                self.connect(tableWidget, QtCore.SIGNAL("itemChanged(QTableWidgetItem*)"), self._tableItemChanged)
                self.tables[tn] = tableWidget

        #---delete Dummy Tab ----    due to an unknown reason , the first tab cannot be filled with a tab.
        #                           there fore the empty "dummy" tab is deleted in all arrays.
        self.ui.tabWidget.removeTab(0)
        self.ui.tabWidget.setCurrentIndex(0)

        self._updateLcdNumber()

        self.ui.database.setText("Actual Database: " + metaData["_name"] + " from " + metaData["_source"])

        self.options = Settings.defaultOptions

    def _sourceChanged(self, source):
        self.ui.browseButton.setEnabled(f.Settings.sources[str(source)]["browseable"])

    def _tableItemChanged(self, tableItem):
        table = tableItem.tableWidget()
        if not self.ignoreItemChanges:
            self.ignoreItemChanges = True
            col = tableItem.column()
            row = tableItem.row()

            if row == 0 and col == 0:
                # All Select
                for i in range(1, table.rowCount()):
                    table.item(i, 0).setCheckState(tableItem.checkState())
            else:
                # Area Select
                selectedRows = set()
                for s in table.selectedItems():
                    selectedRows.add(s.row())

                if row in selectedRows:
                    for i in selectedRows:
                        table.item(i, 0).setCheckState(tableItem.checkState())
            self.ignoreItemChanges = False
        self._updateLcdNumber()

    def _updateLcdNumber(self):
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

        self.ui.excelExportButton.setEnabled(ec > 0)
        self.ui.stataExportButton.setEnabled(ec > 0)
        self.ui.lcdNumber.display(ec)

    def _removeDBfile(self):
        # removes selected tsv-file from data directory
        row = self.ui.databaseTable.currentRow()  # ---get name of selected db---

        if row == -1:
            f.warn("WARNING - No Database seleced...no file removed.")  # ---check for no selection
            return False

        #f.removeTsvFile(name)
        f.delFileInfo(self._getDatasetIdFromTable(row))
        self.updateDBList()

    def _getDatasetIdFromTable(self, row):
        return (str(self.ui.databaseTable.item(row, 1).text()), str(self.ui.databaseTable.item(row, 0).text()))


    def _updateDBfile(self):
        # FUNCTION: IF a row(database) is selected try redownload file and update List in any case.

        #---get name of selected db---
        row = self.ui.databaseTable.currentRow()

        if row == -1:  # ---check for no selection
            f.warn("WARNING - No Database selected")
        else:
            self._downloadDB(self._getDatasetIdFromTable(row))

    def _addDB(self):
        # download new database and update lst
        # returns FALSE if download of tsv-File fails or file is already in the List

        name = str(self.ui.addLineEdit.displayText())  # ---GET FILENAME from LineEdit
        name = name.replace(" ", "")               # deleting unintentionally space-characers

        source = str(self.ui.sourceComboBox.currentText())
        #---CHECK - is file already in Database?
        #if fileName in f.getFileList():
        #    e = f.Error("tsv File already exists - Press Update button to redownload file", errorType=f.Error.WARNING)
        #    e.show()
        #    self.ui.addLineEdit.clear()
        #    return

        self._downloadDB((source, name))

    def _downloadDB(self, datasetId):
        self.worker = f.DownloadAndExtractDbWorker(datasetId, parent=self)
        self.worker.startWork()

        # self.worker.finishedTrigger.connect(self.updateDBList)
        self.updateDBList()

    def _loadDB(self):
        row = self.ui.databaseTable.currentRow()

        if row == -1:
            f.warn("WARNING - No Database seleced...")
            return False

        datasetId = self._getDatasetIdFromTable(row)
        f.log("Attempt to load selected database: " + datasetId[0] + " (" + datasetId[1] + ")")

        self.worker = f.LoadDbWorker(datasetId, baseDialog=self, parent=self)
        self.worker.startWork()

        #self.worker.finishedTrigger.connect(lambda: self.updateTab(self.worker.metaData))
        self.updateTab(self.worker.metaData)

    def _addLineEditChanged(self, text):
        self.ui.addButton.setEnabled(len(text) > 0)

    def _initExcelExport(self):
        #--check if in each Tab at least one is selected---
        checkLCD = self.ui.lcdNumber.value()
        if checkLCD == 0:
            f.warn("WARNING: For an Export procedure at least one item in each Tab need to be selected!!")
            return

        #---write box selection in CLass Array ---
        self.options["selection"] = self.getSelectedCats()

        #---show export option dialog---
        dialog = ExcelExportDialog(self)
        dialog.init(self.metaData, dict(self.options))
        dialog.exec_()

    def _initStataExport(self):
        #--check if in each Tab at least one is selected---
        checkLCD = self.ui.lcdNumber.value()
        if checkLCD == 0:
            f.warn("WARNING: For an Export procedure at least one item in each Tab need to be selected!!")
            return

        #---write box selection in CLass Array ---
        self.options["selection"] = self.getSelectedCats()

        #---show export option dialog---
        dialog = StataExportDialog(self)
        dialog.init(self.metaData, dict(self.options))
        dialog.exec_()

    def _browse(self):
        dialog = TreeDialog(self)
        dialog.exec_()

    def _loadPreset(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Run Preset", Settings.presetPath, "Presets (*.preset)")

        if fileName == "":
            f.warn("No file selected.")
            return

        options = f.getPresetFromFile(fileName)

        self.worker = f.LoadDbWorker(options["name"], baseDialog=self, parent=self)
        self.worker.startWork()

        #self.worker.finishedTrigger.connect(lambda: self.updateTab(self.worker.metaData))
        #self.worker.finishedTrigger.connect(lambda: self.setSelectedCats(options))
        self.updateTab(self.worker.metaData)
        self.setSelectedCats(options)

        if options['fileType'] == 'EXCEL':
            self._initExcelExport()
        elif options['fileType'] == 'STATA':
            self._initStataExport()
        # f.runPreset(fileName)

    def getSelectedCats(self):
        selection = {}
        for code, tableWidget in self.tables.items():
            selection[code] = []
            for i in range(1, tableWidget.rowCount()):
                if tableWidget.item(i, 0).checkState() == QtCore.Qt.Checked:
                    selection[code].append(str(tableWidget.item(i, 1).text()))
        return selection

    def setSelectedCats(self, options):
        selection = options["selection"]
        for code, tableWidget in self.tables.items():
            if code in selection:
                for i in range(1, tableWidget.rowCount()):
                    if tableWidget.item(i, 1).text() in selection[code]:
                        tableWidget.item(i, 0).setCheckState(QtCore.Qt.Checked)
        self.options = options
