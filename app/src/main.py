#!/usr/bin/env python
import sys, os
from BaseWindow import BaseWindow
from PyQt4 import QtGui

# HELPERS AND SETTINGS
from helpers import Settings
import helpers as f

import argparse

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)
os.chdir(os.path.join(dirname, "..", ".."))


parser = argparse.ArgumentParser(description='Open a GUI or process preset files directly.')
parser.add_argument('--presets', '-p', metavar='presets', type = argparse.FileType('r'), nargs='+',
                   help='presets to execute')


def main():
    args = parser.parse_args()
    if args.presets is not None:
        f.runPresetsFromCL(args.presets)
        exit()
    app = QtGui.QApplication(sys.argv)
    window = BaseWindow()
    window.show()

    # metaData = f.loadTsvFile('nama_nace06_p')
    # window.updateTab(metaData)
    # window.setSelectedCats( {
    # 	"time": 		["2012", "2011", "2008"],
    # 	"unit":			["CPI00_EUR", "CPI05_NAC"],
    # 	"nace_r1":		["D", "F", "TOTAL"],
    # 	"indic_na":		["B1G"],
    # 	"geo":			["AT", "DE", "ES"]
    # 	})
    # window._initExport()
    
    print(sys.exit(app.exec_()))

if __name__ == "__main__":
    main()
