# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'export.ui'
#
# Created: Mon May 26 22:29:45 2014
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(385, 269)
        self.lineEdit = QtGui.QLineEdit(Dialog)
        self.lineEdit.setGeometry(QtCore.QRect(100, 20, 113, 20))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(30, 20, 61, 21))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(30, 50, 61, 21))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.lineEdit_2 = QtGui.QLineEdit(Dialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(100, 50, 113, 21))
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))
        self.groupBox = QtGui.QGroupBox(Dialog)
        self.groupBox.setGeometry(QtCore.QRect(20, 90, 221, 161))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.comboBox.setGeometry(QtCore.QRect(90, 20, 111, 22))
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.label_3 = QtGui.QLabel(self.groupBox)
        self.label_3.setGeometry(QtCore.QRect(20, 20, 61, 21))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setGeometry(QtCore.QRect(20, 60, 61, 21))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.label_5 = QtGui.QLabel(self.groupBox)
        self.label_5.setGeometry(QtCore.QRect(20, 100, 61, 21))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.comboBox_2 = QtGui.QComboBox(self.groupBox)
        self.comboBox_2.setGeometry(QtCore.QRect(90, 60, 111, 22))
        self.comboBox_2.setObjectName(_fromUtf8("comboBox_2"))
        self.comboBox_3 = QtGui.QComboBox(self.groupBox)
        self.comboBox_3.setGeometry(QtCore.QRect(90, 100, 111, 22))
        self.comboBox_3.setObjectName(_fromUtf8("comboBox_3"))
        self.pushButton = QtGui.QPushButton(Dialog)
        self.pushButton.setGeometry(QtCore.QRect(280, 190, 75, 23))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.pushButton_2 = QtGui.QPushButton(Dialog)
        self.pushButton_2.setGeometry(QtCore.QRect(280, 220, 75, 23))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.lineEdit.setText(_translate("Dialog", "Output/", None))
        self.label.setText(_translate("Dialog", "Outputpath", None))
        self.label_2.setText(_translate("Dialog", "Filename", None))
        self.lineEdit_2.setText(_translate("Dialog", "output.xls", None))
        self.groupBox.setTitle(_translate("Dialog", "Excel Options", None))
        self.label_3.setText(_translate("Dialog", "in Tabs", None))
        self.label_4.setText(_translate("Dialog", "in Rows", None))
        self.label_5.setText(_translate("Dialog", "in Columns", None))
        self.pushButton.setText(_translate("Dialog", "Export1", None))
        self.pushButton_2.setText(_translate("Dialog", "Abort2", None))

