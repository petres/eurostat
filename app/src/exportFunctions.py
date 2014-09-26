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

# SIMPLEJSON
import simplejson as sj

from helpers import Settings, Worker, log, findInDict

import copy

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
    _manipulateData(data, options)

    # sorting
    if progressControl is not None:
        progressControl.setStep(1)
    _sortingBeforeExport(selection, options["sorting"])


    if progressControl is not None:
        progressControl.setStep(2)

    if len(structure["sheet"]) == 0:
        writer.changeActiveSheet(options["sheetName"])
        writer.writeHeader(options)
        table = _prepareTable(data, options)
        writer.writeTable(table, options)
    else:
        sheet = []
        for i in structure["sheet"]:
            sheet.append(selection[i])

        sheetP = list(itertools.product(*sheet))

        for t in sheetP:
            sheetName = ""
            for i in t:
                sheetName += str(i)

            fixed = {}
            for i, j in enumerate(structure["sheet"]):
                fixed[j] = t[i]

            table = _prepareTable(data, options, fixed = fixed)

            writer.changeActiveSheet(sheetName)
            writer.writeHeader(options)
            writer.writeTable(table, options)

    if progressControl is not None:
        progressControl.setStep(3)

    writer.save()


def _sortingBeforeExport(selection, sorting = {}):
    for entry in sorting:
        if sorting[entry] == QtCore.Qt.DescendingOrder:
            selection[entry] = sorted(selection[entry], reverse = True)
        elif sorting[entry] == QtCore.Qt.AscendingOrder:
            selection[entry] = sorted(selection[entry])

def _manipulateData(data, options):
    if "index" in options and options["index"] != None:
        baseCols    = data["cols"]
        selection   = options["selection"]

        s = []
        for i, bc in enumerate(baseCols):
            if bc == "time":
                continue
            s.append(selection[bc])


        p = list(itertools.product(*s))
        for d in p:
            compareValue = data["data"][tuple(list(d) + [options["index"]])]["value"]

            for time in options["selection"]["time"]:
                key = tuple(list(d) + [time])
                if compareValue is not None and compareValue != 0:
                    value = data["data"][key]["value"]
                    if value != None:
                        data["data"][key]["value"] = value/compareValue*100
                else:
                    data["data"][key]["value"] = None



def _prepareTable(data, options, fixed = {}):
    structure = options["structure"]
    selection = options["selection"]
    emptyCellSign = options["emptyCellSign"]

    s = {}
    p = {}
    for dim in ["col", "row"]:
        s[dim] = []
        for i in structure[dim]:
            s[dim].append(selection[i])
        p[dim] = list(itertools.product(*s[dim]))

    baseCols = data["cols"]

    table = {   "structure": {
                        "row": [],
                        "col": [],
                        "fixed" : fixed
                    },
                "labels":   {
                        "row": [],
                        "col": []
                    },
                "data": []}

    for dim in ["col", "row"]:
        for i, item in enumerate(structure[dim]):
            toAppend = {"count": len(selection[item]), "name": item}
            if len(selection[item]) == 1:
                toAppend["value"] = selection[item][0]
            table["structure"][dim].append(toAppend)




    for dim in ["col", "row"]:
##        if options["codeLabels"]:
##            table["labels"][dim] = p[dim]
##        else:
##            for e in p[dim]:
##                label = []
##                for i, j in enumerate(e):
##                    label.append(findInDict(structure[dim][i],j))
##                table["labels"][dim].append(label)
        for e in p[dim]:
            label = []
            for i, j in enumerate(e):
                label.append({"code": j, "label": findInDict(structure[dim][i],j)})
            table["labels"][dim].append(label)

    for r in p["row"]:
        values = []
        for c in p["col"]:
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
            else:
                value = {"value": None, "flag": None}

            values.append(value)
        table["data"].append(values)

    return table


def _prepareData(name, selection = None):
    time    = []
    data    = { "data": {}, "cols": [], "flags": []}

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

                    flag = None
                    if " " in entry:
                        value = entry.split(' ')[0]
                        flag = entry.split(' ')[1]
                        if flag not in data["flags"]:
                            data["flags"].append(flag)
                    else:
                        value = entry

                    if value == Settings.eurostatEmptyCellSign:
                        value = None

                    if value is not None:
                        value = float(value)

                    data["data"][key] = {"value": value, "flag": flag}
    return data

#----------------------------------------------



def runPresetsFromCL(fileList):
    for i, file in enumerate(fileList):
        log(str(i+1) + "/" + str(len(fileList)) + " Executing preset of file " + file.name + " ... ")
        export(sj.loads(file.read()))
        #log("DONE")


def runPreset(fileName):
    export(getPresetFromFile(fileName))