# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# PROGRESS UI
import tree

from eurostatTocReader import TocWorker

class TreeDialog(QtGui.QDialog):

    leafFont = QtGui.QFont()
    leafFont.setBold(True)
    leafFont.setWeight(75)

    branchFont = QtGui.QFont()
    branchFont.setBold(False)
    branchFont.setWeight(50)

    def __init__(self, mainWin = None):
        QtGui.QDialog.__init__(self, mainWin)
        self.main = mainWin
        self.ui = tree.Ui_TreeDialog()
        self.ui.setupUi(self)

        self._stringDict = {}
        self._allItems = []

        self._infoGroupBoxTitle = self.ui.infoGroupBox.title()
        self._emptyHTML = self.ui.textEdit.toHtml()

        self._searchWillFollow = False
        self._selectedDatabase = None

        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False);

        self.worker = TocWorker(parent = self)
        self.worker.isWorkAndIfStart()
        self.init()
        #if self.worker.isWorkAndIfStart():
        #    self.worker.finishedTrigger.connect(self.init)
        #else:
        #    self.init()

    def init(self):
        self._addItem(self.worker.toc, self.ui.treeWidget)
        
        self.connect(self.ui.treeWidget, QtCore.SIGNAL("currentItemChanged(QTreeWidgetItem *, QTreeWidgetItem * )"), self._currentItemChanged)
        self.connect(self.ui.searchEdit, QtCore.SIGNAL("textChanged(const QString &)"), self._searchEditTextChanged)
        self.connect(self, QtCore.SIGNAL("accepted()"), self._accepted)
        self.connect(self.ui.updateButton, QtCore.SIGNAL("clicked()"), self._update)


    def _addItem(self, tree, parentItem):
        if type(tree) is list:
            for part in tree:
                self._addItem(part, parentItem)
        else:
            item = QtGui.QTreeWidgetItem(parentItem)
            item._info = tree
            if tree["type"] == "leaf":
                title = tree["code"] + " - " + tree["title"]
                item.setFont(0, TreeDialog.leafFont)
            elif tree["type"] == "branch":
                item.setFont(0, TreeDialog.branchFont)
                title = tree["title"]
                if "children" in tree:
                    self._addItem(tree["children"], item)
            item.setText(0, title);
            if title in self._stringDict:
                self._stringDict[title].append(item)
            else:
                self._stringDict[title] = [item]
            self._allItems.append(item)


    def _currentItemChanged(self, current, previous):
        if current._info["type"] == "leaf":
            self.ui.infoGroupBox.setTitle(self._infoGroupBoxTitle + " " + current._info["code"])
            self.ui.textEdit.setHtml(current._info["code"] + "<br>" + current._info["title"])
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True);
            self._selectedDatabase = current._info["code"]
        else:
            self.ui.infoGroupBox.setTitle(self._infoGroupBoxTitle) 
            self.ui.textEdit.setHtml(self._emptyHTML)
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False);
            self._selectedDatabase = None


    def _searchEditTextChanged(self, searchString):
        if not self._searchWillFollow:
            self._searchWillFollow = True
            QtCore.QTimer.singleShot(500, self._search);


    def _search(self):
        searchString = str(self.ui.searchEdit.text()) 

        for item in self._allItems:
            item._matched = 0

        if len(searchString) > 0:
            for key in self._stringDict:
                if key.lower().find(searchString.lower()) > -1:
                    for item in self._stringDict[key]:
                        item._matched = 1
                        while item.parent() != None:
                            item = item.parent()
                            if item._matched != 1:
                                item._matched = 2

        for item in self._allItems:
            if item._matched == 1:
                item.setForeground(0, QtGui.QColor.fromRgb(150,0,0))
            elif item._matched == 0:
                item.setForeground(0, QtGui.QColor.fromRgb(0,0,0))
            elif item._matched == 2:
                item.setForeground(0, QtGui.QColor.fromRgb(0,150,0))

        self._searchWillFollow = False


    def _update(self):
        self.worker = TocWorker(parent = self)
        self.worker.startWork()
        #self.worker.finishedTrigger.connect(self.init)
        self.init()

    def _accepted(self):
        if self._selectedDatabase is not None:
            self.close()
            self.main._downloadDB(self._selectedDatabase)