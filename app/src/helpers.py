# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "xlwt"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "simplejson"))

# CSV (reading csv/tsv files)
import csv
# GZIP (uncompress .gz files)
import gzip
# ITERTOOLS FOR PERMUTATIONS
import itertools
# SIMPLEJSON
import simplejson as sj


# QT
from PyQt4 import QtCore, QtGui

from ProgressDialog import ProgressDialog

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen


from datetime import datetime

import copy

#----------------------------------------------
#----- SETTINGS -------------------------------
#----------------------------------------------

class Settings():
    dataPath            = "data"

    #tocXmlURL           = "http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&file=table_of_contents.xml"
    tocXmlURL           = "http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?sort=1&file=table_of_contents.xml"

    tocXml              = os.path.join('data', 'table_of_contents.xml')
    tocDict             = os.path.join('data', 'toc.json')
    dictByName          = os.path.join('data', 'dictByName.json')

    treeInfoHtmlFileName= os.path.join('app', 'gui', 'treeInfo.html')

    dictPath            = os.path.join('data', 'dict')
    presetPath          = "presets"
    tmpPath             = "tmp"

    dataInfoFile        = os.path.join('data', 'info.json')

    applicationName     = "Data Exporter"
    iconFile            = "app/gui/icon.png"

    sources             = {
        "eurostat": {
            "browseable"          : True,
            "type"                : 'EUROSTAT-BULK',
            "dictURL"             : 'http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?sort=1&file=dic%2Fen%2F',
            "bulkURL"             : 'http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?sort=1&file=data%2F',
            "emptyCellSign"       : ':', 
            'URLchar'             : 'http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?dir=data&sort=1&sort=2&start='
        },
        "oecd": {
            "browseable"          : False,
            "type"                : 'SDMX-JSON',
            "url"                 : 'http://stats.oecd.org/SDMX-JSON/'
        }
    }


    presetFile          = os.path.join('presets', '##NAME##.preset')

    inGui               = False

    defaultOptions      = { #"name":            self.metaData["_name"],
                            #"selection":       self.options["selection"],
                            "structure":        { "sheet": [], "col": ["time"]},
                            "sheetName":        "##NAME##",
                            "fileType":         "EXCEL",
                            "fileName":         os.path.join('output', '##NAME##.##TYPE##'),
                            "sorting":          { "time": QtCore.Qt.DescendingOrder },
                            "locales":          "EN",
                            "shortLabels":      True,
                            "overwrite":        "Sheet",
                            "codeLabels":       True,
                            "longLabels":       False,
                            "exportFlags":      False,
                            "style":            "Basic",
                            "presetTime":       "Include Newer Periods",
                            "emptyCellSign":    "",
                            "graphs":           None,
                            "index":            None,}

    dateFormat          = '%d/%m/%Y %H:%M:%S'
#----------------------------------------------



#----------------------------------------------
#----- GENERIC ERROR BEHAVIOUR ----------------
#----------------------------------------------

class Error(Exception):
    ERROR           = 1
    WARNING         = 2

    text = {1: "Error", 2: "Warning"}

    def __init__(self, message, errorType = 1, addMessage = "", gui = Settings.inGui):
        super(Exception, self).__init__(message)
        self.errorType = errorType
        self.message = message
        self.addMessage = addMessage
        self.gui = gui
        #self.show()


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
#----- WORKERS --------------------------------
#----------------------------------------------

class Worker(QtCore.QThread):
    error = None
    stepTrigger = QtCore.pyqtSignal(int, str)
    finishedTrigger = QtCore.pyqtSignal()

    def __init__(self, name, parent = None):
        super(Worker, self).__init__(parent)
        self.name = name


    def setStep(self, i, info = ''):
        self.stepTrigger.emit(i, info)
        if i < len(self.steps):
            log('  ' + str(i+1) + '/' + str(len(self.steps)) + '  ' + self.steps[i])


    def run(self):
        try:
            self.work()
        except Error as e:
            self.error = e
            self.stepTrigger.emit(-1,"")
        #except Exception as e:
        #    self.error = Error(str(e))
        #    self.stepTrigger.emit(-1,"")

        self.setStep(len(self.steps))


    def startWork(self):
        if Settings.inGui:
            self.initGui()
            self.stepTrigger.connect(self.updateGui)
            self.start()
            self.dialog.exec_()
        else:
            self.work()


    def updateGui(self, code, info):
        if code == -1:
            self.dialog.close()
            self.error.show()
        elif code == len(self.steps):
            self.dialog.close()
            self.finishedTrigger.emit()
        else:
            self.dialog.setStep(code, info)

    def initGui(self):
        self.dialog = ProgressDialog()
        self.dialog.init(self.title, self.steps)




class DownloadAndExtractDbWorker(Worker):
    title = "Get Database ... "
    steps = ["Download File", "Extracting", "Get File Info"]

    def __init__(self, datasetId, parent = None):
        Worker.__init__(self, parent)
        self.datasetId = datasetId

    def work(self):
        self.setStep(0)
        currentTime = datetime.now()
        if self.datasetId[0] == "eurostat":
            downloadTsvGzFile(self.datasetId[1])
            self.setStep(1)
            extractTsvGzFile(self.datasetId[1])
            dsInfo = getFileInfoFromEurostat(self.datasetId[1])
            dsInfo["extractedDate"] = currentTime
            dsInfo["name"] = self.datasetId[1]
            dsInfo["source"] = self.datasetId[0]
            self.setStep(2)
        elif self.datasetId[0] == "oecd":
            sdmxDownloadData(self.datasetId)
            self.setStep(1)
            dsInfo = {}
            dsInfo["source"] = self.datasetId[0]
            dsInfo["name"] = self.datasetId[1]
            dsInfo["size"] = "TODO"
            dsInfo["extractedDate"] = currentTime
            dsInfo["updatedDate"] = currentTime
            dsInfo["lastCheckedDate"] = currentTime  
            self.setStep(2)
        else:
            raise Error("Source not implemented.", addMessage = "Source: '" + self.datasetId[0] + "'")

        addFileInfo(dsInfo)


class LoadDbWorker(Worker):
    title = "Loading Database ... "
    steps = ["Loading Categories"]

    def __init__(self, datasetId, baseDialog, parent = None):
        Worker.__init__(self, parent)
        self.datasetId = datasetId
        self.baseDialog = baseDialog


    def work(self):
        self.setStep(0)
        if self.datasetId[0] == "eurostat":
            self.metaData = loadTsvFile(self.datasetId)
            
        elif self.datasetId[0] == "oecd":
            self.metaData = sdmxLoadMeta(self.datasetId)

        self.metaData["_source"] = self.datasetId[0]
        self.metaData["_name"] = self.datasetId[1]

        log(self.metaData)

#----------------------------------------------


#----------------------------------------------
#----- SDMX FUNCTIONS -------------------------
#----------------------------------------------


def sdmxDownloadData(datasetId):
    fileNameData   = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + "-data.json")
    fileNameMeta   = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + "-meta.json")

    try:
        fileURL = Settings.sources[datasetId[0]]["url"] + "data/" + datasetId[1]
        response = urlopen(fileURL)

        with open(fileNameData, 'w') as outfile:
            outfile.write(response.read())

        fileURL = Settings.sources[datasetId[0]]["url"] + "metadata/" + datasetId[1]
        response = urlopen(fileURL)

        with open(fileNameMeta, 'w') as outfile:
            outfile.write(response.read())

    except Exception as e:   
        # delete the remains of partdownloads - if they exist
        if os.path.isfile(fileName):
            os.remove(fileName)

        raise Error(message = "Dataset not available, check file availability.", addMessage = str(e))

    log("Download successfull")



def sdmxLoadMeta(datasetId):
    metaData = {}
    metaData["_cols"]   = []

    metaFileName = fileNameMeta   = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + "-meta.json")

    # TODO: PUT IT GENERIC OUTSIDE
    if not os.path.isfile(metaFileName):
        worker = DownloadAndExtractDbWorker(datasetId)
        worker.startWork()
        worker.wait()

    with open(metaFileName, 'r') as metaFile:
        mD = sj.loads(metaFile.read())
        dims = mD["structure"]["dimensions"]["observation"]

        for dim in dims:
            log(dim["id"]);
            metaData["_cols"].append(dim["id"])
            metaData[dim["id"]] = {}
            for val in dim["values"]:
                metaData[dim["id"]][val["id"]] = val["name"]
        #log(metaFile.read())

    return metaData



#----------------------------------------------
#----- EUROSTAT BULK FUNCTIONS ----------------
#----------------------------------------------

def downloadTsvGzFile(name):
    log("start to download the db " + name + " from the eurostat webpage")

    gzFileName   = name + ".tsv.gz"
    fGzFileName  = os.path.join(Settings.dataPath, "eurostat-" + gzFileName)

    try:
        #---get gz file from eurostat page---
        fileURL = Settings.sources["eurostat"]["bulkURL"] + gzFileName
        log(fileURL)
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

    log("Download successfull")


def extractTsvGzFile(name):
    log("start to extract the db " + name)

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

    log("Extraction successfull")


def removeTsvFile(name):
    fileName = "eurostat-" + name + ".tsv"
    log("removing file " + Settings.dataPath + fileName)
    os.remove(os.path.join(Settings.dataPath, fileName))


def loadTsvFile(datasetId):
    name = datasetId[1]
    metaData = {}
    metaData["_cols"]   = []

    #---open file and read line by line---
    tsvFileName = os.path.join(Settings.dataPath, "eurostat-" + name + '.tsv')

    if not os.path.isfile(tsvFileName):
        worker = DownloadAndExtractDbWorker(datasetId)
        worker.startWork()
        worker.wait()

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
                    checkDictFile(tt)           #check dictionary of each title
                    metaData[tt] = {}

                #---get col entries ---
                for j in range(1, len(row)):  # starts at 1 because at [0] are categories
                    metaData[colDim][row[j].strip()] = findInDict(colDim, row[j].strip())

            else:
                #---get row entries
                tmp = row[0].split(",")                     # row eg. CPI00_EUR,A_B,B1G,BG
                for i, tt in enumerate(rowDims):  # for each title check if the category of this row is in the cat_list
                    colName = rowDims[i]
                    if tmp[i].strip() not in metaData[colName]:           # if not then append to cat_list in the row of the respective title
                        #metaData[colName].append(tmp[i].strip())
                        metaData[colName][tmp[i].strip()] = findInDict(colName, tmp[i].strip())



    return metaData

#----------------------------------------------



#----------------------------------------------
#----- FILE INFO FUNCTIONS --------------------
#----------------------------------------------

fileInfo = {}
fileInfoLoaded = False

def getFileInfoJson():
    global fileInfo

    if fileInfoLoaded:
        return fileInfo

    if not os.path.isfile(Settings.dataInfoFile):
        saveFileInfoJson()

    with open(Settings.dataInfoFile, 'r') as infoFile:
        wInfo = sj.loads(infoFile.read())

    for source in wInfo:
        info = wInfo[source]
        for entry in info:
            if "updatedDate" in info[entry]:
                info[entry]["updatedDate"] = datetime.strptime(info[entry]["updatedDate"], Settings.dateFormat)
            if "extractedDate" in info[entry]:
                info[entry]["extractedDate"] = datetime.strptime(info[entry]["extractedDate"], Settings.dateFormat)
            if "lastCheckedDate" in info[entry]:
                info[entry]["lastCheckedDate"] = datetime.strptime(info[entry]["lastCheckedDate"], Settings.dateFormat)

    fileInfo = wInfo

    return fileInfo


def saveFileInfoJson():
    info = copy.deepcopy(fileInfo)
    log(info)
    for source in info:
        wInfo = info[source]
        log(wInfo)
        for entry in wInfo:
            if "updatedDate" in wInfo[entry]:
                wInfo[entry]["updatedDate"] = wInfo[entry]["updatedDate"].strftime(Settings.dateFormat)
            if "extractedDate" in wInfo[entry]:
                wInfo[entry]["extractedDate"] = wInfo[entry]["extractedDate"].strftime(Settings.dateFormat)
            if "lastCheckedDate" in wInfo[entry]:
                wInfo[entry]["lastCheckedDate"] = wInfo[entry]["lastCheckedDate"].strftime(Settings.dateFormat)

    with open(Settings.dataInfoFile, 'w') as infoFile:
        infoFile.write(sj.dumps(info))
        infoFile.close()


def getFileInfo(source, name):
    info = getFileInfoJson()
    if source in info:
        if name in info[source]:
            return info[source][name]


def delFileInfo(datasetId):
    info = getFileInfoJson()

    if datasetId[0] in info:
        if datasetId[1] in info[datasetId[0]]:
            del info[datasetId[0]][datasetId[1]]

    saveFileInfoJson()


def getFileInfoFromEurostat(name):
    log("getFileInfoFromEurostat(" + name + ")")
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


def addFileInfo(dsInfo):
    base = getFileInfoJson()

    try:
        info = base[dsInfo["source"]]
    except KeyError:
        base[dsInfo["source"]] = {}
        info = base[dsInfo["source"]]

    info[dsInfo["name"]] = {
            "size"              : dsInfo["size"], 
            "updatedDate"       : dsInfo["updatedDate"],
            "extractedDate"     : dsInfo["extractedDate"], 
            "lastCheckedDate"   : dsInfo["lastCheckedDate"] 
        }

    saveFileInfoJson()


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


def checkDictFile(fileName):
    #return True if dictionar exists or download was successful; or if fileName=TIME (where no Dic exists)
    #return False otherwise;

    if fileName.upper == "TIME":
        return True

    dictFileName = fileName + ".dic"

    #log("check for dictionary " + dictFileName)
    if dictFileName in os.listdir(Settings.dictPath):
        #log("dictionary found...OK")
        return True
    else:
        #log("dictionary NOT found ... start download attempt")
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

#----------------------------------------------





#----------------------------------------------
#----- ELSE -----------------------------------
#----------------------------------------------

def log(message):
    print(message)


def warn(message):
    print("WARNING: " + message)


def error(message):
    print("ERROR: " + message)

#----------------------------------------------