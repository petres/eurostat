# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "gui"))

# QT
from PyQt4 import QtCore, QtGui

# PROGRESS UI
import progress

class ProgressDialog(QtGui.QDialog):

    def __init__(self, mainWin = None):
        QtGui.QDialog.__init__(self, mainWin, QtCore.Qt.Dialog)
        self.main = mainWin
        self.ui = progress.Ui_progressDialog()
        self.ui.setupUi(self)

        self.activeFont = QtGui.QFont()
        self.activeFont.setBold(True)
        self.activeFont.setWeight(75)

        self.inactiveFont = QtGui.QFont()
        self.inactiveFont.setBold(False)
        self.inactiveFont.setWeight(50)

        self.steps = []


    def init(self, title, steps = []):
        self.setWindowTitle(title)
        for i, step in enumerate(steps):
            number = QtGui.QLabel(self)
            number.setText(str(i+1) + ".")
            number.setFont(self.inactiveFont)

            text = QtGui.QLabel(self)
            text.setText(step)
            text.setFont(self.inactiveFont)

            self.ui.formLayout.setWidget(i + 3, QtGui.QFormLayout.LabelRole, number)
            self.ui.formLayout.setWidget(i + 3, QtGui.QFormLayout.FieldRole, text)

            self.steps.append({"number": number, "text": text, "stepText": step})


    def setStep(self, stepNumber, info):
        #print("set step", step)
        for i, step in enumerate(self.steps):
            font = self.inactiveFont
            if i == stepNumber:
                font = self.activeFont
                if len(info) > 0:
                    step['text'].setText(step['text'] + " " + info)

            step["number"].setFont(font)
            step["text"].setFont(font)
