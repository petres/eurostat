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
import excelExport

class ExcelExportDialog(QtGui.QDialog):
    def __init__(self, mainWin):
        QtGui.QDialog.__init__(self, mainWin, QtCore.Qt.Tool)
        self.main = mainWin
        self.ui = excelExport.Ui_excelExportDialog()
        self.ui.setupUi(self)

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._doExport)
        self.connect(self.ui.fileButton, QtCore.SIGNAL("clicked()"), self._fileSelect)
        self.connect(self.ui.presetButton, QtCore.SIGNAL("clicked()"), self._saveAsPreset)
        self.connect(self.ui.indexCheckBox, QtCore.SIGNAL("clicked()"), self._indexHelper)


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

        #print metaData

        if "time" in metaData["_cols"]:
            self.ui.indexCheckBox.setEnabled(True)
            self.ui.indexCombo.addItems(metaData["time"][::-1])

        if "index" in options and options["index"] is not None:
            self.ui.indexCheckBox.setChecked(True)
            self.ui.indexCombo.setCurrentIndex(self.ui.indexCombo.findText(options["index"]))

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
        self.ui.fileEdit.setText(options["fileName"].replace("##NAME##", self.metaData["_name"]).replace("##TYPE##", "xlsx"))
        # TAB NAME
        if "sheetName" in options:
            self.ui.sheetName.setText(options["sheetName"].replace("##NAME##", self.metaData["_name"]))

        self.ui.graphDisabledButton.setChecked(True)
        if "graphs" in options:
            if options["graphs"] == "excel":
                self.ui.graphExcelButton.setChecked(True)
            elif options["graphs"] == "image":
                self.ui.graphImageButton.setChecked(True)

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

    def _indexHelper(self):
        if self.ui.indexCheckBox.isChecked():
            self.ui.indexCombo.setEnabled(True)
        else:
            self.ui.indexCombo.setEnabled(False)


    def _fileSelect(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", self.ui.fileEdit.text(),
                                "Excel (*.xlsx)", options = QtGui.QFileDialog.DontConfirmOverwrite)
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
                        "codeLabels":   True if self.ui.codeRadioButton.isChecked() or self.ui.bothRadioButton.isChecked() else False,
                        "longLabels":   True if self.ui.labelRadioButton.isChecked() or self.ui.bothRadioButton.isChecked() else False,
                        "locales":      str(self.ui.localeComboBox.currentText()),
                        "overwrite":    str(self.ui.overwriteComboBox.currentText()),
                        "style":        str(self.ui.styleComboBox.currentText()),
                        "presetTime":   str(self.ui.timeComboBox.currentText()),
                        "emptyCellSign": str(self.ui.emptyEntryEdit.text())}

        if self.ui.indexCheckBox.isChecked():
            self.options["index"] = str(self.ui.indexCombo.currentText())
        else:
            self.options["index"] = None

        if self.ui.graphDisabledButton.isChecked():
            self.options["graphs"] = None
        if self.ui.graphExcelButton.isChecked():
            self.options["graphs"] = "excel"
        if self.ui.graphImageButton.isChecked():
            self.options["graphs"] = "image"

        if len(structure["sheet"]) == 0:
            sheetName = str(self.ui.sheetName.text());
            if len(sheetName) == 0:
                sheetName = self.metaData["_name"]
            self.options["sheetName"] = sheetName

        return self.options


    def _doExport(self):
        #self.main.options = self._updateAndReturnOptions()
        self.worker = e.ExportWorker(self._updateAndReturnOptions(), parent = self)

        self.worker.startWork()
        #self.worker.finishedTrigger.connect(self.close)
        self.close()

