# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# PROGRESS UI
import tree

from eurostatTocReader import getTree

class TreeDialog(QtGui.QDialog):
    def __init__(self, mainWin = None):
        QtGui.QDialog.__init__(self, mainWin)
        self.main = mainWin
        self.ui = tree.Ui_TreeDialog()
        self.ui.setupUi(self)

        treeData = getTree()
        self._addItem(treeData, self.ui.treeWidget)




    def _addItem(self, tree, parentItem):
        if type(tree) is list:
            for part in tree:
                self._addItem(part, parentItem)
        else:
            item = QtGui.QTreeWidgetItem(parentItem);
            item.setText(0, tree["title"]);
            if tree["type"] == "leaf":
                item.setText(0, tree["code"] + " - " + tree["title"])
            elif tree["type"] == "branch":
                if "children" in tree:
                    self._addItem(tree["children"], item)
