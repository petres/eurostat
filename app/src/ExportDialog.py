# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# HELPERS AND SETTINGS
from helpers import Settings
import helpers as f

# EXPORT UI
import export

class ExportDialog(QtGui.QDialog):
    def __init__(self, mainWin):
        QtGui.QDialog.__init__(self, mainWin)
        self.main = mainWin
        self.ui = export.Ui_exportDialog()
        self.ui.setupUi(self)

        self.ui.emptyEntryEdit.setText(Settings.exportEmptyCellSign)

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._doExport)
        self.connect(self.ui.fileButton, QtCore.SIGNAL("clicked()"), self._fileSelect)
        self.connect(self.ui.presetButton, QtCore.SIGNAL("clicked()"), self._saveAsPreset)


    def init(self, metaData, selection):
        self.metaData   = metaData
        self.selection  = selection

        self.combos = { "tab": { "combo": self.ui.tabCombo, "values": ["None"] + metaData["_cols"]}, 
                        "row": { "combo": self.ui.rowCombo, "values": metaData["_cols"]}, 
                        "col": { "combo": self.ui.colCombo, "values": metaData["_cols"]}}

        for comboType in self.combos:
            combo = self.combos[comboType]["combo"]
            combo.addItems(self.combos[comboType]["values"])
            self.connect(combo, QtCore.SIGNAL("currentIndexChanged(QString)"), self._comboChanged)
            
        for comboType in self.combos:
            combo = self.combos[comboType]["combo"]
        
        self.ui.colCombo.setCurrentIndex(1)
        self.ui.colCombo.setCurrentIndex(0)

        self.ui.fileEdit.setText(Settings.exportFile.replace("##NAME##", self.metaData["_name"]))


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

    def _fileSelect(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", self.ui.fileEdit.text(), 
                                "Excel (*.xls)", options = QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName != "":
            self.ui.fileEdit.setText(fileName)

    def _saveAsPreset(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, "Choose File", Settings.presetFile.replace("##NAME##", self.metaData["_name"]), 
                                "Excel (*.xls)", options = QtGui.QFileDialog.DontConfirmOverwrite)

        if fileName == "":
            return

        f.savePreset(fileName, self._getOptions())

    def _getOptions(self):
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

        structure["row"].extend(allCols)

        options = { "name":         self.metaData["_name"],
                    "selection":    self.selection,
                    "structure":    structure,
                    "fileType":     "EXCEL",
                    "fileName":     str(self.ui.fileEdit.text()),
                    "sorting":      sorting,
                    "emptyCellSign": str(self.ui.emptyEntryEdit.text())}

        return options

    def _doExport(self): 
        f.export(self._getOptions())

        #self.close()