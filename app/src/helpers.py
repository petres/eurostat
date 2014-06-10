# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))

# CSV (reading csv/tsv files)
import csv
# GZIP (uncompress .gz files)
import gzip
# EXCEL READ
import xlrd
# EXCEL WRITE
import xlwt
# ITERTOOLS FOR PERMUTATIONS
import itertools
# SIMPLEJSON
import simplejson as sj


import copy
# QT
from PyQt4 import QtCore, QtGui

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from operator import add


#----------------------------------------------
#----- SETTINGS -------------------------------
#----------------------------------------------

class Settings():
    dataPath            = "data/"
    dictPath            = "data/dict/"
    presetPath          = "presets/"

    dictURL             = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&downfile=dic%2Fen%2F'
    bulkURL             = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&file=data%2F'
    eurostatURL         = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&dir=data'
    eurostatURLchar     = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?dir=data&sort=1&sort=2&start=' #+'n' is the list of files start with "n"

    exportEmptyCellSign = ""
    eurostatEmptyCellSign = ":"

    exportFile          = os.path.join('output', '##NAME##.xls')
    presetFile          = os.path.join('presets', '##NAME##.preset')

    inGui               = False

#----------------------------------------------



#----------------------------------------------
#----- GENERIC ERROR BEHAVIOUR ----------------
#----------------------------------------------

class Error(Exception):
    ERROR           = 1
    WARNING         = 2

    text = {1: "Error", 2: "Warning"}

    def __init__(self, message, errorType = 1, addMessage = ""):
        super(Exception, self).__init__(message)
        self.errorType = errorType
        self.message = message
        self.addMessage = addMessage

        self.show()

    def show(self):
        self.log()
        if Settings.inGui:
            self.messageBox()

    def log(self):
        sys.stderr.write("--------------------\n") 
        sys.stderr.write("--- " + Error.text[self.errorType] + ": " + self.message + "\n") 
        if len(self.addMessage) > 0:
            sys.stderr.write(("--- {0:" + str(len(Error.text[self.errorType])) + "}  " + self.addMessage).format("") + "\n") 
        sys.stderr.write("--------------------\n") 

    def messageBox(self):
        messageDialog = QtGui.QMessageBox()
        messageDialog.setWindowTitle(Error.text[self.errorType])
        messageDialog.setText(self.message)
        messageDialog.exec_()

#----------------------------------------------



#----------------------------------------------
#----- TSV FUNCTIONS --------------------------
#----------------------------------------------

def downloadTsvFile(name):
    #returns True if successful downloaded and extracted
    #returns False at any error

    log("START attempt to download file " + name + ".tsv from the Eurostat Webpage ... please wait")

    gzFileName   = name + ".tsv.gz"
    fGzFileName  = os.path.join(Settings.dataPath, gzFileName)
    tsvFileName  = name + ".tsv"
    fTsvFileName = os.path.join(Settings.dataPath, tsvFileName)

    try:
        #---get gz file from eurostat page---
        fileURL = Settings.bulkURL + gzFileName
        response = urlopen(fileURL)

        with open(fGzFileName, 'wb') as outfile:
            outfile.write(response.read())

        #---EXTRACT TSV.GZ.FILE---
        with open(fTsvFileName, 'w') as outfile, gzip.open(fGzFileName) as infile:
            outfile.write(infile.read())

        #---delete gz file---
        os.remove(fGzFileName)

        log("Download and Extraction successfull")

    except Exception as e:   # delete the remains of partdownloads - if they exist
        if os.path.isfile(fGzFileName):
            os.remove(fGzFileName)
        if os.path.isfile(fTsvFileName):
            os.remove(fTsvFileName)

        raise Error(message = "Dataset not available, check file availability at Eurostat.", addMessage = str(e))


def removeTsvFile(name):
    # removes selected tsv-file from data directory
    fileName = name + ".tsv"  #---get name of selected item---
    log("removing file " + Settings.dataPath + fileName)

    #---removing file---
    os.remove(Settings.dataPath + fileName)


def loadTsvFile(name):
    #FUNCtION: reads existing tsv-file
    #1) checks dictionary
    #2) fills class variables (cat_list,time_list) with the info
    #   (titles,categories,dictionary...)

    #TSV - FIle Structure after open as tsv:
    # 1st row: [unit,nace_r1,indic_na,geo\time] [2012]  [2011] ... [1980]
    # 2nd row  [CPI00_EUR,A_B,B1G,AT] [value] [value]...

    #OUTPUT: 2D-Array: for titles:[unit,nace_r1,indic_na,geo\time]
    # cat_list (2DArray) =[ [cpi00_eur,cpi00_nac...],[A_B,C-E,D,F...],[B1G] ]
    # time_list          = [2012,2011,2010...]
    # geo_list          = [AT,BE,BG...SI]

    metaData = {}
    metaData["_name"]   = name
    metaData["_cols"]   = []
    metaData["time"]    = []
    metaData["geo"]     = []
    checkDictFile("geo")

    #---open file and read line by line---
    tsvFileName = os.path.join(Settings.dataPath, name + '.tsv')

    if not os.path.isfile(tsvFileName):
        downloadTsvFile(name)

    with open(tsvFileName, 'r') as tsvFile:
        tsvReader = csv.reader(tsvFile, delimiter='\t')

        for i, row in enumerate(tsvReader):
            if i == 0:
                #---get dic-TITLES---
                metaData["_cols"] = (row[0].split(","))[:-1]        # [:-1] -> title_list without the last "geo/time"

                #---check DICTIONARY and append 2D-array for Category-list
                for tt in metaData["_cols"]:
                    checkDictFile(tt)           #check dictionary of each title
                    metaData[tt] = []

                #---get TIME array from row---
                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    metaData["time"].append(row[j].strip())

            else:
                #---get Categories and GEO
                tmp = row[0].split(",")                     # row eg. CPI00_EUR,A_B,B1G,BG
                for i, tt in enumerate(metaData["_cols"]):  # for each title check if the category of this row is in the cat_list
                    colName = metaData["_cols"][i]
                    if tmp[i].strip() not in metaData[colName]:           # if not then append to cat_list in the row of the respective title
                        metaData[colName].append(tmp[i].strip())

                if tmp[-1].strip() not in metaData["geo"]:    # fill GEO List with the GEO Info (is always last)
                    metaData["geo"].append(tmp[-1].strip())

    metaData["_cols"].insert(0, "time")
    metaData["_cols"].append("geo")

    return metaData

#----------------------------------------------



#----------------------------------------------
#----- FILE INFO FUNCTIONS --------------------
#----------------------------------------------

def getFileInfo(fname):
    # for filename "aact_ali02 this function returns: "6.5 KB;07/04/2014"
    # by looking in the _INFO-file.

    if fname[-4:] == ".tsv":   #file.tsv -> file  (if necessary)
        fname = fname[:-4]

    infoFile = os.path.join(Settings.dataPath, "_INFO.txt")

    if not os.path.isfile(infoFile):
        open(infoFile, 'a').close()

    lines = open(Settings.dataPath + "_INFO.txt").readlines()
    for ln in lines:
        if fname in ln:
            return ln

    return "n.a.;n.a.;n.a."


def delFileInfo(fname):
    #FUNCTION : removes fileinfo (update-date,size) to _info.txt
    if fname[-4:] == ".tsv":   #file.tsv -> file  (if necessary)
        fname = fname[:-4]

    todelete = Settings.getFileInfo(fname) #as "aact_ali02;6.5 KB;07/04/2014"

    infoFile = os.path.join(Settings.dataPath, "_INFO.txt")

    lines = open(infoFile).readlines()
    lines.remove(todelete)
    open(infoFile, 'w').writelines(lines)


def addFileInfo(fname):
    #FUNCTION : reads fileinformation (last update, filesize) from the eurostat webpage
    #           and stores info in _INFO.txt

    #---read html data and search filename---
    fileURL = Settings.eurostatURLchar + fname[0]  # the url is sorted e.g. it ends with "a" for a List of files that start with "a"
    response = urlopen(fileURL)

    for line in response:
        if fname in line:
            info = line
            break

    # ---extract size and date from html text
    fsize = info.split("</td>")[1].split(">")[1]
    fdate = info.split("</td>")[3].split("&nbsp;")[1][:10]
    finfo = fname + ";" + fdate + ";" + fsize  # = "aact_ali02;6.5 KB;07/04/2014"

    infoFile = os.path.join(Settings.dataPath, "_INFO.txt")
    #---write in file
    with open(infoFile, "a") as f:
        f.write(finfo + "\n")


def getFileList():
    names = []
    for ba in os.listdir(Settings.dataPath):
        if ba[-4:] == ".tsv":
            names.append(ba[:-4])
    return names

#----------------------------------------------



#----------------------------------------------
#----- DICT FILE FUNCTIONS --------------------
#----------------------------------------------

def findInDict(title, shorty):
    #INPUT: title is equal to .dic -filename    (Geo)
    #INPUT: shorts is the abbreviations (AT)
    #RETURN: Long-Text of shorts     (Austria...)

    if title.upper() == "TIME":    #TIME is the only title without long-text
        return ""

    longy = ""

    try:
        dictFileName = Settings.dictPath + title + ".dic"             #open dict that is equal to the TAbtitle

        with open(dictFileName, "r") as dictFile:
            dictReader = csv.reader(dictFile, delimiter = "\t")
            for row in dictReader:                           #search every row of the dict for the short
                if row[0] == shorty:                              #if they match
                    longy = row[1]                           #append to long
                    return str(longy)
        return "n.a."
    except:
        error("in Dic File opening: " + dictFileName)
        return False


def checkDictFile(fileName):
    #return True if dictionar exists or download was successful; or if fileName=TIME (where no Dic exists)
    #return False otherwise;

    if fileName.upper == "TIME":
        return True

    dictFileName = fileName + ".dic"

    log("check for dictionary " + dictFileName)
    if dictFileName in os.listdir(Settings.dictPath):
        log("dictionary found...OK")
        return True
    else:
        log("dictionary NOT found ... start download attempt")
        return downloadDictFile(dictFileName) 


def downloadDictFile(dictFileName):   
    # download of eurostat dictionary file
    #return True if download OK
    #return False otherwise

    try:
        # get URL and response
        fileURL = Settings.dictURL + dictFileName
        response = urlopen(fileURL)
        log("Dictionary download OK")
    except:
        error("Downloading Dictionary " + dictFileName)
        return False

    try:
        with open(os.path.join(Settings.dictPath, dictFileName), 'wb') as outfile:
            # saving download
            outfile.write(response.read())
    except:
        error("Saving Dictionary " + dictFileName)
        return False

#----------------------------------------------



#----------------------------------------------
#----- PRESETS --------------------------------
#----------------------------------------------

def savePreset(fileName, options):
    with open(fileName, 'w') as outfile:
        outfile.write(getStringOfPreset(options))

def getStringOfPreset(options):
    return sj.dumps(options)

def getPresetFromFile(fileName):
    with open(fileName, 'r') as presetFile:
        return sj.loads(presetFile.read())

def runPreset(fileName):
    export(getPresetFromFile(fileName))

#----------------------------------------------



#----------------------------------------------
#----- EXPORT ---------------------------------
#----------------------------------------------

def export(options):
    wb = xlwt.Workbook()

    data = _prepareData(options["name"], options["selection"])

    #ws = wb.add_sheet("0", cell_overwrite_ok = True)
    ws = wb.add_sheet("Data")

    ws.write(1, 0, "Name:")
    ws.write(1, 1, options["name"], xlwt.easyxf("font: bold on; "))
    
    ws.write(2, 0, "Preset:")
    ws.write(2, 1, getStringOfPreset(options))

    table = _prepareTable(data, options["structure"], options["selection"], options["sorting"], options["emptyCellSign"])
    _writeWorksheet(table, ws)

    wb.save(options["fileName"])


def _writeWorksheet(table, ws):
    initialOffset = (5, 0)

    styleString = "font: bold on; pattern: pattern_fore_colour ice_blue, pattern solid; "
    style = xlwt.easyxf(styleString)

    # Row Labels Labels
    for i, label in enumerate(table["rowLabelsStructure"]):
        borders = xlwt.Borders()
        borders.top = xlwt.Borders.MEDIUM
        borders.bottom = xlwt.Borders.THIN
        borders.left = xlwt.Borders.NO_LINE
        if i == 0:
            borders.left = xlwt.Borders.MEDIUM
        if i == len(table["rowLabelsStructure"]) - 1:
            borders.right = xlwt.Borders.THIN
        style.borders = borders
        ws.write(initialOffset[0], initialOffset[1] + i, label, style)

    labelOffset = (len(table["colLabelsStructure"]), len(table["rowLabelsStructure"]))

    # Labels
    for i, labels in enumerate(table["rowLabels"]):
        borders = xlwt.Borders()
        if i == len(table["rowLabels"]) - 1:
            borders.bottom = xlwt.Borders.MEDIUM
        for j, label in enumerate(labels):
            borders.left = xlwt.Borders.NO_LINE
            if j == 0:
                borders.left = xlwt.Borders.MEDIUM
            elif j == len(labels) - 1:
                borders.right = xlwt.Borders.THIN
            style.borders = borders
            ws.write(initialOffset[0] + i + labelOffset[0], initialOffset[1] + j, label, copy.deepcopy(style))

    
    for i, label in enumerate(table["colLabels"]):
        borders = xlwt.Borders()
        borders.top = xlwt.Borders.MEDIUM
        borders.bottom = xlwt.Borders.THIN
        if i == len(table["colLabels"]) - 1:
            borders.right = xlwt.Borders.MEDIUM
        style.borders = borders
        ws.write(initialOffset[0], initialOffset[1] + i + labelOffset[1], label, style)

    offset = map(add, initialOffset, labelOffset)

    style = xlwt.easyxf()
    # Data
    for i, line in enumerate(table["data"]):
        borders = xlwt.Borders()
        if i == len(table["data"]) - 1:
            borders.bottom = xlwt.Borders.MEDIUM
        for j, entry in enumerate(line):
            if j == len(line) - 1:
                borders.right = xlwt.Borders.MEDIUM
            style.borders = borders
            #rint entry, style.borders.right
            ws.write(offset[0] + i, offset[1] + j, entry, copy.deepcopy(style))


def _prepareTable(data, structure, selection, sorting = {}, fixed = {}, emptyCellSign = Settings.exportEmptyCellSign):
    # SORTING
    for entry in sorting:
        if sorting[entry] == QtCore.Qt.DescendingOrder:
            selection[entry] = sorted(selection[entry], reverse=True)
        elif sorting[entry] == QtCore.Qt.AscendingOrder:
            selection[entry] = sorted(selection[entry])

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



#----------------------------------------------
#----- ELSE -----------------------------------
#----------------------------------------------

def log(message):
    print("LOG: " + message)


def warn(message):
    print("WARNING: " + message)


def error(message):
    print("ERROR: " + message)

#----------------------------------------------