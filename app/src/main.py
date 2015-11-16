#!/usr/bin/env python2
import sys
import os
from BaseWindow import BaseWindow
from PyQt4 import QtGui

# HELPERS AND SETTINGS
from helpers import Settings
from exportFunctions import runPresetsFromCL

import argparse

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)
os.chdir(os.path.join(dirname, "..", ".."))


def is_dir(dirname):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dirname):
        msg = "{0} is not a directory".format(dirname)
        raise argparse.ArgumentTypeError(msg)
    else:
        return dirname

parser = argparse.ArgumentParser(description='Eurostat Bulk Downloader: This program allows the download of \
                                  eurostat bulk datasets and the export it afterward filtered and sorted in other file formats \
                                  (for example excel). Without any arguments a GUI will be opened where the source and the export can be configured. \
                                  To allow better handling of recurrent tasks, presets can be created by the GUI. These presets can be \
                                  executed in the GUI or directly by adding them to the arguments.')

parser.add_argument('--presets', '-p', metavar='preset', type=argparse.FileType('r'), nargs='+',
                    help='Add presets which will be executed. No GUI will be opened!')

parser.add_argument('--folders', '-f', metavar='folder', type=is_dir, nargs='+',
                    help='Add preset folders which will be executed. No GUI will be opened!')


def main():
    #return sdmxGetData(("oecd", "MSTI_PUB"))

    args = parser.parse_args()

    if args.folders is not None:
        if args.presets is None:
            args.presets = []
        for folder in args.folders:
            for f in os.listdir(folder):
                if f[-7:] == ".preset":
                    args.presets.append(open(os.path.join(folder, f), "r"))

    if args.presets is not None:
        runPresetsFromCL(args.presets)
        exit()

    #sys.argv["name"] = "Eurostat Exporter"
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(Settings.applicationName)

    window = BaseWindow()
    window.show()

    print(sys.exit(app.exec_()))

if __name__ == "__main__":
    main()
