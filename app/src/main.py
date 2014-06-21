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


parser = argparse.ArgumentParser(description = 'Eurostat Bulk Downloader: This program allows the download of \
                                  eurostat bulk datasets and the export it afterward filtered and sorted in other file formats \
                                  (for example excel). Without any arguments a GUI will be opened where the source and the export can be configured. \
                                  To allow better handling of recurrent tasks, presets can be created by the GUI. These presets can be \
                                  executed in the GUI or directly by adding them to the arguments.')

parser.add_argument('--presets', '-p', metavar = 'preset', type = argparse.FileType('r'), nargs = '+',
                   help = 'Add presets which will be executed. No GUI will be opened!')


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
    # options = Settings.defaultOptions
    # options["selection"] = {
    #                   "time":     ["2012", "2011", "2008"],
    #                   "unit":     ["CPI00_EUR", "CPI05_NAC"],
    #                   "nace_r1":    ["D", "F", "TOTAL"],
    #                   "indic_na":   ["B1G"],
    #                   "geo":      ["AT", "DE", "ES"]
    #                   }
    # window.setSelectedCats(options)
    # window._initExport()
    
    print(sys.exit(app.exec_()))

if __name__ == "__main__":
    main()
