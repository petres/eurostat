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
        self.ui = export.Ui_Dialog()
        self.ui.setupUi(self)

        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._doExport)


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
            combo.setCurrentIndex(1)
            combo.setCurrentIndex(0)


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


    def _doExport(self): 
        #---read from combobox---
        structure = {}

        allCols = self.metaData["_cols"]
        print allCols
        for comboType in self.combos:
            text = self.combos[comboType]["combo"].currentText()
            if text == "None":
                structure[comboType] = []
            else:
                structure[comboType] = [str(text)]
                allCols.remove(text)
            

        structure["row"].extend(allCols)

        f.export(self.metaData["_name"], selection = self.selection, structure = structure, fileType = "EXCEL")
