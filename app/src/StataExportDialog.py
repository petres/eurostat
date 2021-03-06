# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# HELPERS AND SETTINGS
from helpers import Settings
import exportFunctions as e

import helpers as f

# EXPORT UI
import stataExport


class StataExportDialog(QtGui.QDialog):

    def __init__(self, mainWin):
        QtGui.QDialog.__init__(self, mainWin, QtCore.Qt.Dialog)
        self.main = mainWin
        self.ui = stataExport.Ui_stataExportDialog()
        self.ui.setupUi(self)

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._doExport)
        self.connect(self.ui.fileButton, QtCore.SIGNAL("clicked()"), self._fileSelect)
        self.connect(self.ui.presetButton, QtCore.SIGNAL("clicked()"), self._saveAsPreset)

    def init(self, metaData, options):
        self.metaData = metaData
        self.options = options

        # UPDATE GUI
        # PRESET TIME
        self.ui.timeComboBox.setCurrentIndex(self.ui.timeComboBox.findText(options["presetTime"]))

        self.ui.tableWidget.setRowCount(len(metaData["_cols"]))
        self.ui.tableWidget.setColumnCount(4)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Dimension", "Format", "Code",  "Encoding"])
        self.ui.tableWidget.verticalHeader().setVisible(False)
        self.ui.tableWidget.setAlternatingRowColors(True)
        self.ui.tableWidget.horizontalHeader().setStretchLastSection(True)

        strItems = ["long", "wide"]
        codeItems = ["short", "long", "both"]

        self.combos = {}

        for i, name in enumerate(metaData["_cols"]):
            self.ui.tableWidget.setItem(i, 0, QtGui.QTableWidgetItem(name))
            self.combos[name] = {}

            strCombo = QtGui.QComboBox()
            strCombo.addItems(strItems)
            self.ui.tableWidget.setCellWidget(i, 1, strCombo)
            self.combos[name]["str"] = strCombo
            

            codeCombo = QtGui.QComboBox()
            codeCombo.addItems(codeItems)
            self.ui.tableWidget.setCellWidget(i, 2, codeCombo)
            self.combos[name]["code"] = codeCombo


            encodingBox = QtGui.QCheckBox()
            encodingBox.setCheckState(QtCore.Qt.Unchecked)
            if name == 'time':
                encodingBox.setText("as stata time")
            else:
                encodingBox.setText("as factor")
            self.ui.tableWidget.setCellWidget(i, 3, encodingBox)
            self.combos[name]["encoding"] = encodingBox


            self.connect(strCombo, QtCore.SIGNAL("currentIndexChanged(QString)"), self._strChanged)
        
            try:
                strCombo.setCurrentIndex(strCombo.findText(options["structure"][name]["format"]))
            except:
                pass


            try:
                codeCombo.setCurrentIndex(codeCombo.findText(options["structure"][name]["code"]))
            except:
                pass


            try:
                if options["structure"][name]["encode"]:
                    encodingBox.setCheckState(QtCore.Qt.Checked)
                else:
                    encodingBox.setCheckState(QtCore.Qt.Unchecked)
            except:
                pass


        # FILE NAME
        self.ui.fileEdit.setText(options["fileName"].replace(
            "##NAME##", self.metaData["_name"]).replace("##TYPE##", "dta"))

        # FLAG EXPORT
        if options["exportFlags"]:
            self.ui.flagCheckBox.setCheckState(QtCore.Qt.Checked)
        else:
            self.ui.flagCheckBox.setCheckState(QtCore.Qt.Unchecked)

    def _strChanged(self):
        sender = self.sender()
        for name in self.combos:
            if sender == self.combos[name]["str"]:
                selected = sender.currentText()
                if selected == "wide":
                    self.combos[name]["code"].setEnabled(False)
                    self.combos[name]["encoding"].setEnabled(False)
                elif selected == "long":
                    self.combos[name]["code"].setEnabled(True)
                    self.combos[name]["encoding"].setEnabled(True)

    def _fileSelect(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", self.ui.fileEdit.text(),
                                                     "Excel (*.dta)", options=QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName != "":
            self.ui.fileEdit.setText(fileName)

    def _saveAsPreset(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", Settings.presetFile.replace("##NAME##", self.metaData["_name"]),
                                                     "Presets (*.preset)", options=QtGui.QFileDialog.DontConfirmOverwrite)

        if fileName == "":
            return

        f.savePreset(fileName, self._updateAndReturnOptions())

    def _updateAndReturnOptions(self):
        structure = {}

        for name in self.combos:
            structure[name] = {}
            structure[name]["format"] = str(self.combos[name]["str"].currentText())
            structure[name]["code"] = str(self.combos[name]["code"].currentText())
            structure[name]["encode"] = (self.combos[name]["encoding"].checkState() == QtCore.Qt.Checked)

        self.options = {"name":         self.metaData["_name"],
                        "source":       self.metaData["_source"],
                        "selection":    self.options["selection"],
                        "structure":    structure,
                        "fileType":     "STATA",
                        "fileName":     str(self.ui.fileEdit.text()),
                        "presetTime":   str(self.ui.timeComboBox.currentText())}

        if self.ui.flagCheckBox.checkState() == QtCore.Qt.Checked:
            self.options["exportFlags"] = True
        else:
            self.options["exportFlags"] = False

        return self.options

    def _doExport(self):
        #self.main.options = self._updateAndReturnOptions()
        self.worker = e.ExportWorker(self._updateAndReturnOptions(), parent=self)

        self.worker.startWork()
        # self.worker.finishedTrigger.connect(self.close)
        self.close()
