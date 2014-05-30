#!/usr/bin/env python
import sys, os
from BaseWindow import BaseWindow
from PyQt4 import QtGui

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)
os.chdir(os.path.join(dirname, "..", ".."))


def main():
    app = QtGui.QApplication(sys.argv)
    window = BaseWindow()
    window.show()

    print sys.exit(app.exec_())

if __name__ == "__main__":
    main()
