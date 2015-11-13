# -*- coding: utf-8 -*-
import os
import sys
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

from helpers import Settings, Worker, log, findInDict, getFileInfo, loadTsvFile, LoadDbWorker

import copy

import pandas as pd


class ExportWorker(Worker):
    def __init__(self, options, parent=None):
        self.title = "Export ... "
        self.options = options
        self.exportFunction = None

        if self.options["fileType"] == "STATA":
            self.steps = ["Prepare Data", "Writing", "Saving"]
            self.exportFunction = exportStata
        elif self.options["fileType"] == "EXCEL":
            self.steps = ["Prepare Data", "Sorting", "Writing", "Saving"]
            self.exportFunction = exportExcel

        Worker.__init__(self, parent)

    def work(self):
        self.exportFunction(self.options, progressControl=self)


#----------------------------------------------
#----- EXPORT ---------------------------------
#----------------------------------------------

#def export(options, progressControl=None):
#    if options["fileType"] == "EXCEL":
#        exportExcel(options, progressControl=progressControl)
#    elif options["fileType"] == "STATA":
#        exportStata(options, progressControl=progressControl)


def exportStata(options, progressControl=None):
    structure = options["structure"]
    selection = options["selection"]

    if progressControl is not None:
        progressControl.setStep(0)

    data = _prepareData((options["source"], options["name"]), selection)

    if progressControl is not None:
        progressControl.setStep(1)

    rDim = []
    cols = []
    cDim = []
    rows = []
    for name in structure:
        format = structure[name]["format"]
        if format == "wide":
            cDim.append(name)
        elif format == "long":
            rDim.append(name)

            code = structure[name]["code"]
            if code == "short":
                cols.append(name)
            elif code == "long":
                cols.append(name)
            elif code == "both":
                cols.append(name)
                cols.append(name + "Label")

    rIterList = []
    cIterList = []

    for i in rDim:
        rIterList.append(selection[i])

    for i in cDim:
        cIterList.append(selection[i])

    # print "cols", len(cols)

    colValueNames = []
    if len(cDim) == 0:
        colValueNames += ["value"]
        if options["exportFlags"]:
            colValueNames += ["flag"]
    else:
        for c in itertools.product(*cIterList):
            colValueNames += ["value_" + "_".join(c)]
            if options["exportFlags"]:
                colValueNames += ["flag_" + "_".join(c)]

    lines = []
    for r in itertools.product(*rIterList):
        values = []
        for i, c in enumerate(rDim):
            code = structure[c]["code"]
            if code == "short":
                values.append(r[i])
            elif code == "long":
                # TODO findInDict
                values.append(r[i])
            elif code == "both":
                values.append(r[i])
                # TODO findInDict
                values.append(r[i])

        entry = False
        for c in itertools.product(*cIterList):
            keyList = []
            for bc in data["cols"]:
                if bc in rDim:
                    keyEntry = r[rDim.index(bc)]
                elif bc in cDim:
                    keyEntry = c[cDim.index(bc)]
                else:
                    raise Error('Wow Wow Wow, thats not good, keylist and dict differ, what have you done?')
                keyList.append(keyEntry)

            key = tuple(keyList)
            if key in data["data"]:
                values.append(data["data"][key]["value"])
                if options["exportFlags"]:
                    values.append(data["data"][key]["flag"])
                entry = True
            else:
                values.append(None)
                if options["exportFlags"]:
                    values.append(None)

        if entry:
            lines.append(values)


    df = pd.DataFrame(lines, columns=cols + colValueNames)

    convert_dates = None
    for colName in cols:
        if colName in structure and "encode" in structure[colName] and structure[colName]["encode"]:
            if colName == "time":
                convert_dates = {"time": 'ty'}
                if "Q" in df.loc[0, colName]:
                    convert_dates = {"time": 'tq'}
                df[colName] = pd.DatetimeIndex(df[colName])
                #df['timeTest2'] = pd.DatetimeIndex(df[colName])
                #df[colName] = pd.to_datetime(df[colName])
                #df[colName] = df[colName].to_period()
            else:
                df[colName] = df[colName].astype("category")

    for colName in colValueNames:
        if colName.startswith('value'):
            #log("convert col to float " + colName)
            df[colName] = df[colName].astype("float64")

    if progressControl is not None:
        progressControl.setStep(2)

    #info = getFileInfo(options["name"])
    #dataset_label=options["name"] + " LU: " + str(info["updatedDate"])
    df.to_stata(options["fileName"], write_index=False, convert_dates=convert_dates)
    #df.to_stata(options["fileName"], write_index=False)


def exportExcel(options, progressControl=None):
    structure = options["structure"]
    selection = options["selection"]

    if options["presetTime"] == "Include Newer Periods":
        worker = LoadDbWorker((options["source"], options["name"]), baseDialog = None)
        worker.startWork()
        metaData = worker.metaData

        

        #log("      last used time is: " + lastTime)
        if "time" in metaData:
            lastTime = max(selection["time"])
            for t in metaData["time"]:
                if t > lastTime:
                    #log("       -> adding " + t)
                    selection["time"].append(t)

    #_sortingBeforeExport(selection, options["sorting"])

    existingSheets = []

    writer = Writer(options)

    if progressControl is not None:
        progressControl.setStep(0)

    data = _prepareData((options["source"], options["name"]), selection)

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

            table = _prepareTable(data, options, fixed=fixed)

            writer.changeActiveSheet(sheetName)
            writer.writeHeader(options)
            writer.writeTable(table, options)

    if progressControl is not None:
        progressControl.setStep(3)

    writer.save()


def _sortingBeforeExport(selection, sorting={}):
    for entry in sorting:
        if sorting[entry] == QtCore.Qt.DescendingOrder:
            selection[entry] = sorted(selection[entry], reverse=True)
        elif sorting[entry] == QtCore.Qt.AscendingOrder:
            selection[entry] = sorted(selection[entry])


def _manipulateData(data, options):
    if "index" in options and options["index"] != None:
        baseCols = data["cols"]
        selection = options["selection"]

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
                        data["data"][key]["value"] = value / compareValue * 100
                else:
                    data["data"][key]["value"] = None


def _prepareTable(data, options, fixed={}):
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

    table = {"structure": {
        "row": [],
        "col": [],
        "fixed": fixed
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
        # if options["codeLabels"]:
        ##            table["labels"][dim] = p[dim]
        # else:
        # for e in p[dim]:
        ##                label = []
        # for i, j in enumerate(e):
        # label.append(findInDict(structure[dim][i],j))
        # table["labels"][dim].append(label)
        for e in p[dim]:
            label = []
            for i, j in enumerate(e):
                label.append({"code": j, "long": findInDict(structure[dim][i], j)})
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


def _prepareData(datasetId, selection=None):
    if datasetId[0] == "eurostat":
        return eurostatBulkGetData(datasetId[1], selection)
    elif datasetId[0] == "oecd":
        return sdmxGetData(datasetId, selection)
    else:
        raise Error("Unknown Source")


def sdmxGetData(datasetId, selection=None):
    colDimValues = []
    data = {"data": {}, "cols": [], "flags": []}

    keys = {}
    dataFileName = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + '-data.json')
    with open(dataFileName, 'r') as dataFile:
        dataJson = sj.loads(dataFile.read())
        cols = []

        dims = dataJson['structure']['dimensions']['series']
        log("dimensions - series")
        for dim in dims:
            log(" - " + dim["id"])
            keys[dim["id"]] = dim["values"]
            cols.append(dim["id"])
            data["cols"].append(dim["id"])

        log("attributes - series")
        dims = dataJson['structure']['attributes']['series']
        for dim in dims:
            log(" - " + dim["id"])
            keys[dim["id"]] = dim["values"]
            cols.append(dim["id"])

        log("dimensions - observation")
        dims = dataJson['structure']['dimensions']['observation']
        for dim in dims:
            log(" - " + dim["id"])
            keys[dim["id"]] = dim["values"]
            cols.append(dim["id"])
            data["cols"].append(dim["id"])

        log("attributes - observation")
        dims = dataJson['structure']['attributes']['observation']
        for dim in dims:
            log(" - " + dim["id"])
            keys[dim["id"]] = dim["values"]
            cols.append(dim["id"])

        series = dataJson['dataSets'][0]['series']
        for dk in series:
            kIdA = []
            cont = False
            for i, dkp in enumerate(dk.split(':')):
                v = int(dkp)
                if selection and keys[cols[i]][v]['id'] not in selection[cols[i]]:
                    cont = True
                kIdA.append(v)
            if cont:
                continue

            kIdA += series[dk]['attributes']
            for obsK in series[dk]['observations']:
                if selection and keys[cols[len(kIdA)]][int(obsK)]['id'] not in selection[cols[len(kIdA)]]:
                    continue

                okIdA = kIdA + [int(obsK)]
                obs = series[dk]['observations'][obsK]
                value = obs[0]
                okIdA += obs[1:]
                #print str(okIdA) + " - " + str(value)

                okVA = []
                for i, k in enumerate(okIdA):
                    if k is None:
                        okVA.append(None)
                    else:
                        okVA.append(keys[cols[i]][k]['id'])

                dKey = []
                for col in data["cols"]:
                    dKey.append(okVA[cols.index(col)])

                data["data"][tuple(dKey)] = {"value": value, "flag": okVA[-1]}

                #print str(okVA) + " - " + str(value)
            


    return data

#----------------------------------------------




#----------------------------------------------

def eurostatBulkGetData(name, selection=None):
    colDimValues = []
    data = {"data": {}, "cols": [], "flags": []}

    tsvFileName = os.path.join(Settings.dataPath, "eurostat-" + name + '.tsv')
    with open(tsvFileName, 'r') as tsvFile:
        tsvReader = csv.reader(tsvFile, delimiter='\t')
        for i, row in enumerate(tsvReader):
            if i == 0:
                tmp = row[0].split("\\")
                colDim = tmp[1]
                data["cols"] = tmp[0].split(",") + [colDim]
                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    colDimValues.append(row[j].strip())
            else:
                inSelection = True
                keyList = []
                tmp = row[0].split(",")                     # row eg. CPI00_EUR,A_B,B1G,BG

                for k, rowDimValue in enumerate(tmp):
                    # FILTERING
                    if (selection is not None) and (rowDimValue.strip() not in selection[data["cols"][k]]):
                        inSelection = False
                        break
                    keyList.append(rowDimValue.strip())

                if not inSelection:
                    continue

                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    # FILTERING
                    if (selection is not None) and (colDimValues[j - 1] not in selection[colDim]):
                        continue

                    key = tuple(keyList + [colDimValues[j - 1]])
                    entry = row[j].strip()

                    flag = None
                    if " " in entry:
                        value = entry.split(' ')[0]
                        flag = entry.split(' ')[1]
                        if flag not in data["flags"]:
                            data["flags"].append(flag)
                    else:
                        value = entry

                    if value == Settings.sources["eurostat"]["emptyCellSign"]:
                        value = None

                    if value is not None:
                        value = float(value)

                    data["data"][key] = {"value": value, "flag": flag}
    return data

#----------------------------------------------





def runPresetsFromCL(fileList):
    for i, file in enumerate(fileList):
        log(str(i + 1) + "/" + str(len(fileList)) + " Executing preset of file " + file.name + " ... ")
        export(sj.loads(file.read()))
        # log("DONE")


def runPreset(fileName):
    export(getPresetFromFile(fileName))
