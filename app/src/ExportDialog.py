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

        self.metaData = None
        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"), self.close)
        self.connect(self.ui.exportButton, QtCore.SIGNAL("clicked()"), self._doExport)


    def init(self, metaData, selection):
        self.metaData = metaData

        self.combos = { self.ui.tabCombo: ["None"] + metaData["_cols"], 
                        self.ui.rowCombo: metaData["_cols"], 
                        self.ui.colCombo: metaData["_cols"]}

        for combo in self.combos:
            combo.addItems(self.combos[combo])
            self.connect(combo, QtCore.SIGNAL("currentIndexChanged(QString)"), self._comboChanged)
            combo.setCurrentIndex(0)    


    def _comboChanged(self, text):
        sender = self.sender()
        selectedEntries = [sender.currentText()]
        for combo in self.combos:
            if combo == sender:
                continue
            while combo.currentText() in selectedEntries: 
                combo.setCurrentIndex((combo.currentIndex() + 1)%len(self.combos[combo]))
            selectedEntries.append(combo.currentText())

    def _doExport(self): # return selected categories

        #---read from combobox---
        ex_tab=str(self.ui.comboBox.currentText())
        ex_row=str(self.ui.comboBox_2.currentText())
        ex_col=str(self.ui.comboBox_3.currentText())

        #--check---
        if self.checkCombo(ex_tab,ex_row,ex_col):    #---if all chosen texts are different
            self.main.setExportCats(ex_tab,ex_row,ex_col)
            self.accept()
            self.main.startExport()
        else:
            print("WARNING - Selected categories need to be different!")


    def _doAbort(self): # return empty categories
        print ("export aborted")
        self.main.setExportCats("","","") #---to be safe...
        self.reject()

    def checkCombo(self,a,b,c): #checks if all texts are different, then return true
        if a!=b and a!=c and b!=c:
            return True
        return False
