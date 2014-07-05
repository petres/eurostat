# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# HELPERS AND SETTINGS
from helpers import Settings
import exportFunctions as e

import helpers as f

# EXPORT UI
import export

class ExportDialog(QtGui.QDialog):
    def __init__(self, mainWin):
        QtGui.QDialog.__init__(self, mainWin)
        self.main = mainWin
        self.ui = export.Ui_exportDialog()
        self.ui.setupUi(self)

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._doExport)
        self.connect(self.ui.fileButton, QtCore.SIGNAL("clicked()"), self._fileSelect)
        self.connect(self.ui.presetButton, QtCore.SIGNAL("clicked()"), self._saveAsPreset)


    def init(self, metaData, options):
        self.metaData   = metaData
        self.options  = options

        ### UPDATE GUI

        # EMPTY CELL SIGN
        self.ui.emptyEntryEdit.setText(options["emptyCellSign"])

        # TIME SORTING
        if options["sorting"]["time"] == QtCore.Qt.DescendingOrder:
            self.ui.timeSortingCombo.setCurrentIndex(self.ui.timeSortingCombo.findText("descending"))
        elif options["sorting"]["time"] == QtCore.Qt.AscendingOrder:
            self.ui.timeSortingCombo.setCurrentIndex(self.ui.timeSortingCombo.findText("ascending"))

        # OVERWRITE
        self.ui.overwriteComboBox.setCurrentIndex(self.ui.overwriteComboBox.findText(options["overwrite"]))
        # STYLE
        self.ui.styleComboBox.setCurrentIndex(self.ui.styleComboBox.findText(options["style"]))
        # PRESET TIME
        self.ui.timeComboBox.setCurrentIndex(self.ui.timeComboBox.findText(options["presetTime"]))
        # LOCALES
        self.ui.localeComboBox.setCurrentIndex(self.ui.localeComboBox.findText(options["locales"]))

        # STRUCTURE
        self.combos = { "sheet": { "combo": self.ui.sheetCombo, "values": ["None"] + metaData["_cols"]}, 
                        "row": { "combo": self.ui.rowCombo, "values": metaData["_cols"]}, 
                        "col": { "combo": self.ui.colCombo, "values": metaData["_cols"]}}

        for comboType in self.combos:
            combo = self.combos[comboType]["combo"]
            combo.addItems(self.combos[comboType]["values"])
            self.connect(combo, QtCore.SIGNAL("currentIndexChanged(QString)"), self._comboChanged)
        
        self.ui.colCombo.setCurrentIndex(1)
        self.ui.colCombo.setCurrentIndex(0)

        for comboType in options["structure"]:
            combo = self.combos[comboType]["combo"]
            if len(options["structure"][comboType]) == 0:
                combo.setCurrentIndex(combo.findText("None"))
            elif len(options["structure"][comboType]) > 0:
                combo.setCurrentIndex(combo.findText(options["structure"][comboType][0]))


        # FILE NAME
        self.ui.fileEdit.setText(options["fileName"].replace("##NAME##", self.metaData["_name"]))
        # TAB NAME
        if "sheetName" in options:
            self.ui.sheetName.setText(options["sheetName"].replace("##NAME##", self.metaData["_name"]))

        if options["codeLabels"]:
            self.ui.codeRadioButton.setChecked(True)
            self.ui.labelRadioButton.setChecked(False)
        else:
            self.ui.codeRadioButton.setChecked(False)
            self.ui.labelRadioButton.setChecked(True)


    def _comboChanged(self, text):
        sender = self.sender()
        selectedEntries = [sender.currentText()]
        for comboType in self.combos:
            combo = self.combos[comboType]["combo"]
            if combo == sender:
                continue
            while combo.currentText() in selectedEntries: 
                combo.setCurrentIndex((combo.currentIndex() + 1)%len(self.combos[comboType]["values"]))
            selectedEntries.append(combo.currentText())

        if self.combos["sheet"]["combo"].currentText() == "None":
            self.ui.sheetName.setEnabled(True)
        else:
            self.ui.sheetName.setEnabled(False)


    def _fileSelect(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", self.ui.fileEdit.text(), 
                                "Excel (*.xls)", options = QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName != "":
            self.ui.fileEdit.setText(fileName)


    def _saveAsPreset(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", Settings.presetFile.replace("##NAME##", self.metaData["_name"]), 
                                "Presets (*.preset)", options = QtGui.QFileDialog.DontConfirmOverwrite)

        if fileName == "":
            return

        f.savePreset(fileName, self._updateAndReturnOptions())


    def _updateAndReturnOptions(self):
        structure = {}
        sorting = {}

        ## Empty text setting
        Settings.exportEmptyCellSign = str(self.ui.emptyEntryEdit.text())

        ## Sorting setting
        timeSorting = str(self.ui.timeSortingCombo.currentText())
        if timeSorting == "ascending":
            sorting["time"] = QtCore.Qt.AscendingOrder
        elif timeSorting == "descending":
            sorting["time"] = QtCore.Qt.DescendingOrder

        ## Structure setting
        # copy list, we should not modify the meta data
        allCols = list(self.metaData["_cols"])
        for comboType in self.combos:
            text = self.combos[comboType]["combo"].currentText()
            if text == "None":
                structure[comboType] = []
            else:
                structure[comboType] = [str(text)]
                allCols.remove(text)          

        # all not used columns add to row structure
        structure["row"].extend(allCols)

        self.options = {"name":         self.metaData["_name"],
                        "selection":    self.options["selection"],
                        "structure":    structure,
                        "fileType":     "EXCEL",
                        "fileName":     str(self.ui.fileEdit.text()),
                        "sorting":      sorting,
                        "codeLabels":   True if self.ui.codeRadioButton.isChecked() else False,
                        "locales":      str(self.ui.localeComboBox.currentText()),
                        "overwrite":    str(self.ui.overwriteComboBox.currentText()),
                        "style":        str(self.ui.styleComboBox.currentText()),
                        "presetTime":   str(self.ui.timeComboBox.currentText()),
                        "emptyCellSign": str(self.ui.emptyEntryEdit.text())}


        if len(structure["sheet"]) == 0:
            sheetName = str(self.ui.sheetName.text());
            if len(sheetName) == 0:
                sheetName = self.metaData["_name"]
            self.options["sheetName"] = sheetName

        return self.options


    def _doExport(self):
        self.main.options = self._updateAndReturnOptions()
        self.worker = e.ExportWorker(self.main.options, parent = self)

        self.worker.startWork()
        #self.worker.finishedTrigger.connect(self.close)
        self.close()

        