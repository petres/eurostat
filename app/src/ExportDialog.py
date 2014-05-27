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

import os, sys

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

import xlrd
import xlwt

import export





#######################################################################
################## ADDITIONAL DIALOGS CLASS################################

class ExportDialog(QtGui.QDialog):
    def __init__(self, mainWin):
        QtGui.QDialog.__init__(self,mainWin)
        self.main=mainWin
        self.ui = export.Ui_Dialog()
        self.ui.setupUi(self)

        self._initExportDialog()

##        self.connect(self.ui.buttonBox, QtCore.SIGNAL("accepted()"),self.doOK)
##        self.connect(self.ui.buttonBox, QtCore.SIGNAL("rejected()"),self.doAB)
        self.connect(self.ui.pushButton, QtCore.SIGNAL("clicked()"),self._doExport)
        self.connect(self.ui.pushButton_2, QtCore.SIGNAL("clicked()"),self._doAbort)

    def _initExportDialog(self):
        #---get selected categories---
        cat_sel=self.main.cl_title_list[:]
        cat_sel.insert(0,"GEO")
        cat_sel.append("TIME")

        self.ui.comboBox.addItem("None") # NONE-Option for Excel-Tabs

        for sel in cat_sel:
            self.ui.comboBox.addItem(sel)
            self.ui.comboBox_2.addItem(sel)
            self.ui.comboBox_3.addItem(sel)


        self.ui.comboBox.setCurrentIndex(0)
        self.ui.comboBox_2.setCurrentIndex(self.ui.comboBox_2.count()-1)
        self.ui.comboBox_3.setCurrentIndex(0)


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
##
##    def _test(self):
##        print("you clicked me...!")
##        pass