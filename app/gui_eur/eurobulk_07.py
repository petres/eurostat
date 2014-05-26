# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'eurobulk_07.ui'
#
# Created: Sat May 17 13:18:36 2014
#      by: PyQt4 UI code generator 4.10.1
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
        Dialog.resize(963, 497)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(760, 460, 161, 32))
        self.buttonBox.setStyleSheet(_fromUtf8(""))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(310, 0, 181, 31))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.tabWidget = QtGui.QTabWidget(Dialog)
        self.tabWidget.setGeometry(QtCore.QRect(320, 30, 521, 421))
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.pushButton_5 = QtGui.QPushButton(Dialog)
        self.pushButton_5.setGeometry(QtCore.QRect(860, 150, 81, 31))
        self.pushButton_5.setObjectName(_fromUtf8("pushButton_5"))
        self.groupBox_2 = QtGui.QGroupBox(Dialog)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 20, 291, 431))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.pushButton_2 = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_2.setGeometry(QtCore.QRect(200, 380, 75, 23))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.pushButton_3 = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_3.setGeometry(QtCore.QRect(100, 290, 75, 23))
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.pushButton = QtGui.QPushButton(self.groupBox_2)
        self.pushButton.setGeometry(QtCore.QRect(10, 290, 75, 23))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.lineEdit = QtGui.QLineEdit(self.groupBox_2)
        self.lineEdit.setGeometry(QtCore.QRect(10, 380, 171, 20))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.pushButton_9 = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_9.setGeometry(QtCore.QRect(190, 290, 75, 23))
        self.pushButton_9.setObjectName(_fromUtf8("pushButton_9"))
        self.tableWidget_3 = QtGui.QTableWidget(self.groupBox_2)
        self.tableWidget_3.setGeometry(QtCore.QRect(10, 20, 261, 261))
        self.tableWidget_3.setObjectName(_fromUtf8("tableWidget_3"))
        self.tableWidget_3.setColumnCount(0)
        self.tableWidget_3.setRowCount(0)
        self.label_7 = QtGui.QLabel(Dialog)
        self.label_7.setGeometry(QtCore.QRect(850, 20, 91, 31))
        self.label_7.setObjectName(_fromUtf8("label_7"))
        self.lcdNumber = QtGui.QLCDNumber(Dialog)
        self.lcdNumber.setGeometry(QtCore.QRect(860, 52, 81, 31))
        self.lcdNumber.setObjectName(_fromUtf8("lcdNumber"))
        self.pushButton_6 = QtGui.QPushButton(Dialog)
        self.pushButton_6.setGeometry(QtCore.QRect(20, 470, 75, 23))
        self.pushButton_6.setObjectName(_fromUtf8("pushButton_6"))
        self.pushButton_7 = QtGui.QPushButton(Dialog)
        self.pushButton_7.setGeometry(QtCore.QRect(100, 470, 75, 23))
        self.pushButton_7.setObjectName(_fromUtf8("pushButton_7"))
        self.pushButton_8 = QtGui.QPushButton(Dialog)
        self.pushButton_8.setGeometry(QtCore.QRect(190, 470, 75, 23))
        self.pushButton_8.setObjectName(_fromUtf8("pushButton_8"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(330, 470, 151, 21))
        self.label.setObjectName(_fromUtf8("label"))
        self.pushButton_4 = QtGui.QPushButton(Dialog)
        self.pushButton_4.setGeometry(QtCore.QRect(860, 100, 81, 31))
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))

        self.retranslateUi(Dialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.pushButton_2, self.pushButton)
        Dialog.setTabOrder(self.pushButton, self.pushButton_3)
        Dialog.setTabOrder(self.pushButton_3, self.lineEdit)
        Dialog.setTabOrder(self.lineEdit, self.buttonBox)
        Dialog.setTabOrder(self.buttonBox, self.tabWidget)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.label_2.setText(_translate("Dialog", "\"Databasename\" - Data Selection", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Dialog", "Tab 1", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Dialog", "Tab 2", None))
        self.pushButton_5.setText(_translate("Dialog", "Export Data", None))
        self.groupBox_2.setTitle(_translate("Dialog", "Eurostat Databases available:", None))
        self.pushButton_2.setText(_translate("Dialog", "Add new", None))
        self.pushButton_3.setText(_translate("Dialog", "Update", None))
        self.pushButton.setText(_translate("Dialog", "Load", None))
        self.pushButton_9.setText(_translate("Dialog", "Remove", None))
        self.label_7.setText(_translate("Dialog", "Datasets selected", None))
        self.pushButton_6.setText(_translate("Dialog", "6Test", None))
        self.pushButton_7.setText(_translate("Dialog", "7Test", None))
        self.pushButton_8.setText(_translate("Dialog", "8Test", None))
        self.label.setText(_translate("Dialog", "..OK", None))
        self.pushButton_4.setText(_translate("Dialog", "Load Preset", None))

