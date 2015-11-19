# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "xlwt"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "simplejson"))

# CSV (reading csv/tsv files)
import csv
# GZIP (uncompress .gz files)
import gzip

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from datetime import datetime

from settings import Settings, log, error, warn


#----------------------------------------------
#----- EUROSTAT BULK FUNCTIONS ----------------
#----------------------------------------------

def downloadData(datasetId):
    name = datasetId[1]
    #log("start to download the db " + name + " from the eurostat webpage")

    gzFileName   = name + ".tsv.gz"
    fGzFileName  = os.path.join(Settings.dataPath, "eurostat-" + gzFileName)

    try:
        fileURL = Settings.sources["eurostat"]["bulkURL"] + gzFileName
        #log(fileURL)
        response = urlopen(fileURL)

        with open(fGzFileName, 'wb') as outfile:
            outfile.write(response.read())

        # CHECK IF IT IS A GZIP FILE
        with open(fGzFileName, 'rb') as binaryFile:
            magicNumber = binaryFile.read(2)

        if str(magicNumber.encode('hex')) != "1f8b":
            raise Exception("Wrong file format")

    except Exception as e:   
        # delete the remains of partdownloads - if they exist
        if os.path.isfile(fGzFileName):
            os.remove(fGzFileName)

        raise Error(message = "Dataset not available, check file availability at Eurostat.", addMessage = str(e))

    #log("Download successfull")


def extractData(datasetId):
    name = datasetId[1]
    #log("start to extract the db " + name)

    gzFileName   = "eurostat-" + name + ".tsv.gz"
    fGzFileName  = os.path.join(Settings.dataPath, gzFileName)

    tsvFileName  = "eurostat-" + name + ".tsv"
    fTsvFileName = os.path.join(Settings.dataPath, tsvFileName)

    try:
        #---EXTRACT TSV.GZ.FILE---
        with open(fTsvFileName, 'w') as outfile, gzip.open(fGzFileName) as infile:
            outfile.write(infile.read())

        #---delete gz file---
        os.remove(fGzFileName)

    except Exception as e:   # delete the remains of partdownloads - if they exist
        if os.path.isfile(fGzFileName):
            os.remove(fGzFileName)
        if os.path.isfile(fTsvFileName):
            os.remove(fTsvFileName)

        raise Error(message = "Extraction Error.", addMessage = str(e))

    #log("Extraction successfull")


# def removeTsvFile(name):
#     fileName = "eurostat-" + name + ".tsv"
#     log("removing file " + Settings.dataPath + fileName)
#     os.remove(os.path.join(Settings.dataPath, fileName))


def loadMeta(datasetId):
    name = datasetId[1]
    metaData = {}
    metaData["_cols"]   = []

    #---open file and read line by line---
    tsvFileName = os.path.join(Settings.dataPath, "eurostat-" + name + '.tsv')

    with open(tsvFileName, 'r') as tsvFile:
        tsvReader = csv.reader(tsvFile, delimiter='\t')

        for i, row in enumerate(tsvReader):
            if i == 0:
                tmp = row[0].split("\\")  # sepearating row and col dimensions

                rowDims = tmp[0].split(",")
                colDim = tmp[1]
        
                metaData["_cols"] = [colDim] + rowDims

                #---check DICTIONARY and append 2D-array for Category-list
                for tt in metaData["_cols"]:
                    _checkDictFile(tt)           #check dictionary of each title
                    metaData[tt] = {}

                #---get col entries ---
                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    metaData[colDim][row[j].strip()] = _findInDict(colDim, row[j].strip())

            else:
                #---get row entries
                tmp = row[0].split(",")                     # row eg. CPI00_EUR,A_B,B1G,BG
                for i, tt in enumerate(rowDims):  # for each title check if the category of this row is in the cat_list
                    colName = rowDims[i]
                    if tmp[i].strip() not in metaData[colName]:           # if not then append to cat_list in the row of the respective title
                        #metaData[colName].append(tmp[i].strip())
                        metaData[colName][tmp[i].strip()] = _findInDict(colName, tmp[i].strip())



    return metaData

#----------------------------------------------


def getData(datasetId, selection=None):
    name = datasetId[1]
    colDimValues = []
    data = {"data": {}, "cols": [], "flags": [], "long": {}}

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

    # GET LONG (LABELS)
    #for col in data["cols"]:
    #    if col.upper() != "TIME":
    #        data["long"][col] = _getDict(col)

    meta = loadMeta(datasetId)
    # GET LONG (LABELS)
    for col in data["cols"]:
        data["long"][col] = meta[col]

    return data


def checkStatus(datasetId):
    name = datasetId[1]
    #log("getFileInfoFromEurostat(" + name + ")")
    eInfo = {}
    eInfo["lastCheckedDate"] = datetime.now()

    fileURL = Settings.sources["eurostat"]["URLchar"] + name[0]  # the url is sorted e.g. it ends with "a" for a List of files that start with "a"
    response = urlopen(fileURL)

    for line in response:
        if name in line:
            break

    eInfo["size"] = line.split("</td>")[1].split(">")[1]

    dateString = line.split("</td>")[3].split("&nbsp;")[1]
    eInfo["updatedDate"] = datetime.strptime(dateString, Settings.dateFormat)

    wInfo = getFileInfoJson()
    if "eurostat" in wInfo:
        info = wInfo["eurostat"]
        if name in info:
            info[name]["lastCheckedDate"] = eInfo["lastCheckedDate"]
            if eInfo["updatedDate"] > info[name]["updatedDate"]:
                info[name]["newerVersionAvailable"] = True
            saveFileInfoJson()

    return eInfo


# def getFileList():
#     names = []
#     for ba in os.listdir(Settings.dataPath):
#         if ba[-4:] == ".tsv":
#             names.append(ba[:-4])
#     return names

#----------------------------------------------
#----- DICT FILE FUNCTIONS --------------------
#----------------------------------------------
def _getDict(title):
    d = {}

    try:
        dictFileName = os.path.join(Settings.dictPath, title + ".dic" )            #open dict that is equal to the TAbtitle

        with open(dictFileName, "r") as dictFile:
            dictReader = csv.reader(dictFile, delimiter = "\t")
            for row in dictReader:                           #search every row of the dict for the short
                d[row[0]] = row[1]
        return d
    except:
        error("in Dic File opening: " + dictFileName)
        return False


def _findInDict(title, shorty):
    if title.upper() == "TIME":    #TIME is the only title without long-text
        return shorty

    longy = ""

    try:
        dictFileName = os.path.join(Settings.dictPath, title + ".dic" )            #open dict that is equal to the TAbtitle

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


def _checkDictFile(fileName):
    if fileName.upper == "TIME":
        return True

    dictFileName = fileName + ".dic"

    if dictFileName in os.listdir(Settings.dictPath):
        return True
    else:
        return _downloadDictFile(dictFileName)


def _downloadDictFile(dictFileName):
    fileURL = Settings.sources["eurostat"]["dictURL"] + dictFileName
    try:
        response = urlopen(fileURL)
    except:
        error("Downloading Dictionary " + dictFileName + " (" + fileURL + ")")
        return False

    try:
        with open(os.path.join(Settings.dictPath, dictFileName), 'wb') as outfile:
            outfile.write(response.read())
    except:
        error("Saving Dictionary " + dictFileName)
        return False

#----------------------------------------------

