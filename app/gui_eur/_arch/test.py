import os,sys
from PyQt4 import QtGui

app = QtGui.QApplication(sys.argv)
window = QtGui.QMainWindow()
window.setGeometry(0, 0, 400, 200)

pic = QtGui.QLabel(window)
pic.setGeometry(10, 10, 400, 100)
#use full ABSOLUTE path to the image, not relative
pic.setPixmap(QtGui.QPixmap(os.getcwd() + "/eu.gif"))

window.show()
sys.exit(app.exec_())