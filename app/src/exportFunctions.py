# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
#sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "xlwt"))

from openpyxlWriter import Writer

# CSV (reading csv/tsv files)
import csv

# QT
from PyQt4 import QtCore, QtGui

# ITERTOOLS FOR PERMUTATIONS
import itertools


from helpers import Settings, Worker
import helpers as f

class ExportWorker(Worker):
    title = "Export ... "
    steps = ["Prepare Data", "Sorting", "Writing", "Saving"]

    def __init__(self, options, parent = None): 
        Worker.__init__(self, parent)
        self.options = options


    def work(self):
        export(self.options, progressControl = self)


#----------------------------------------------
#----- EXPORT ---------------------------------
#----------------------------------------------

def export(options, progressControl = None):
    structure = options["structure"]
    selection = options["selection"]

    existingSheets = []


    writer = Writer(options)

    if progressControl is not None:
        progressControl.setStep(0)

    data = _prepareData(options["name"], selection)

    # sorting
    if progressControl is not None:
        progressControl.setStep(1)
    _sortingBeforeExport(selection, options["sorting"])

    
    if progressControl is not None:
        progressControl.setStep(2)

    if len(structure["tab"]) == 0:
        writer.changeActiveSheet(options["tabName"])
        writer.write((1, 0), "Name:")
        writer.write((1, 1), options["name"])

        writer.write((1, 0), "Preset:")
        writer.write((1, 1), f.getStringOfPreset(options))

        table = _prepareTable(data, options)
        writer.writeTable(table)
    else:
        tab = []
        for i in structure["tab"]:
            tab.append(selection[i])

        tabP = list(itertools.product(*tab))

        for t in tabP:
            tabName = ""
            for i in t:
                tabName += str(i)

            fixed = {}
            for i, j in enumerate(structure["tab"]):
                fixed[j] = t[i]

            table = _prepareTable(data, options, fixed = fixed)
            
            writer.changeActiveSheet(tabName)
            writer.writeTable(table)


    if progressControl is not None:
        progressControl.setStep(3)

    writer.save()


def _sortingBeforeExport(selection, sorting = {}):
    for entry in sorting:
        if sorting[entry] == QtCore.Qt.DescendingOrder:
            selection[entry] = sorted(selection[entry], reverse = True)
        elif sorting[entry] == QtCore.Qt.AscendingOrder:
            selection[entry] = sorted(selection[entry])



def _prepareTable(data, options, fixed = {}):
    structure = options["structure"]
    selection = options["selection"]
    emptyCellSign = options["emptyCellSign"]

    cols = []
    for i in structure["col"]:
        cols.append(selection[i])

    rows = []
    for i in structure["row"]:
        rows.append(selection[i])

    baseCols = data["cols"]

    colP = list(itertools.product(*cols))
    rowP = list(itertools.product(*rows))

    table = { "rowLabelsStructure": structure["row"],
              "colLabelsStructure": structure["col"],
              "rowLabels": rowP,
              "colLabels": colP,
              "data":      []}

    for r in rowP:
        values = []
        for c in colP:
            keyList = []
            for bc in baseCols:
                if bc in structure["col"]:
                    keyEntry = c[structure["col"].index(bc)]
                elif bc in structure["row"]:
                    keyEntry = r[structure["row"].index(bc)]
                elif bc in fixed:
                    keyEntry = fixed[bc]
                else:
                    raise Error('Wow Wow Wow, thats not good, keylist and dict differ, what have you done?')

                keyList.append(keyEntry)

            key = tuple(keyList)
            value = None
            if key in data["data"]:
                value = data["data"][key]

            if value is None:
                value = Settings.exportEmptyCellSign

            values.append(value)
        table["data"].append(values)

    return table


def _prepareData(name, selection = None):
    time    = []
    data    = { "data": {}, "cols": []}

    tsvFileName = os.path.join(Settings.dataPath, name + '.tsv')
    with open(tsvFileName, 'r') as tsvFile:
        tsvReader = csv.reader(tsvFile, delimiter = '\t')
        for i, row in enumerate(tsvReader):
            if i == 0:
                data["cols"] = (row[0].split(","))[:-1] + ["geo", "time"]
                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    time.append(row[j].strip())
            else:
                inSelection = True
                keyList = []
                tmp = row[0].split(",")                     # row eg. CPI00_EUR,A_B,B1G,BG

                for k, tt in enumerate(tmp):
                    # FILTERING
                    if (selection is not None) and (tt.strip() not in selection[data["cols"][k]]):
                        inSelection = False
                        break
                    keyList.append(tt.strip())

                if not inSelection:
                    continue

                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    # FILTERING
                    if (selection is not None) and (time[j - 1] not in selection["time"]):
                        continue

                    key = tuple(keyList + [time[j - 1]])
                    entry = row[j].strip()
                    if entry == Settings.eurostatEmptyCellSign:
                        entry = None

                    data["data"][key] = entry
    return data

#----------------------------------------------