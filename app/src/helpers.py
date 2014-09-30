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

    tocXmlURL           = "http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&file=table_of_contents.xml"
    tocXml              = os.path.join('data', 'table_of_contents.xml')
    tocDict             = os.path.join('data', 'toc.json')
    dictByName          = os.path.join('data', 'dictByName.json')

    treeInfoHtmlFileName= os.path.join('app', 'gui', 'treeInfo.html')

    dictPath            = os.path.join('data', 'dict')
    presetPath          = "presets"
    tmpPath             = "tmp"

    dataInfoFile        = os.path.join('data', 'info.json')

    applicationName     = "Eurostat Exporter"

    dictURL             = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&downfile=dic%2Fen%2F'
    bulkURL             = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&file=data%2F'
    eurostatURL         = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&dir=data'
    eurostatURLchar     = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?dir=data&sort=1&sort=2&start=' #+'n' is the list of files start with "n"

    eurostatEmptyCellSign = ":"

    presetFile          = os.path.join('presets', '##NAME##.preset')

    inGui               = False

    defaultOptions      = { #"name":            self.metaData["_name"],
                            #"selection":       self.options["selection"],
                            "structure":        { "sheet": [], "col": ["time"]},
                            "sheetName":        "##NAME##",
                            "fileType":         "EXCEL",
                            "fileName":         os.path.join('output', '##NAME##.xlsx'),
                            "sorting":          { "time": QtCore.Qt.DescendingOrder },
                            "locales":          "EN",
                            "shortLabels":      True,
                            "overwrite":        "Sheet",
                            "codeLabels":       True,
                            "longLabels":       False,
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

    def __init__(self, name, parent = None):
        Worker.__init__(self, parent)
        self.name = name


    def work(self):
        self.setStep(0)
        currentTime = datetime.now()
        downloadTsvGzFile(self.name)
        self.setStep(1)
        extractTsvGzFile(self.name)
        self.setStep(2)
        addFileInfo(self.name, currentTime)


class LoadDbWorker(Worker):
    title = "Loading Database ... "
    steps = ["Loading Categories"]

    def __init__(self, name, baseDialog, parent = None):
        Worker.__init__(self, parent)
        self.name = name
        self.baseDialog = baseDialog


    def work(self):
        self.setStep(0)
        self.metaData = loadTsvFile(self.name)

#----------------------------------------------



#----------------------------------------------
#----- TSV FUNCTIONS --------------------------
#----------------------------------------------

def downloadTsvGzFile(name):
    log("start to download the db " + name + " from the eurostat webpage")

    gzFileName   = name + ".tsv.gz"
    fGzFileName  = os.path.join(Settings.dataPath, gzFileName)

    try:
        #---get gz file from eurostat page---
        fileURL = Settings.bulkURL + gzFileName
        response = urlopen(fileURL)

        with open(fGzFileName, 'wb') as outfile:
            outfile.write(response.read())

        # CHECK IF IT IS A GZIP FILE
        with open(fGzFileName, 'rb') as binaryFile:
            magicNumber = binaryFile.read(2)

        if str(magicNumber.encode('hex')) != "1f8b":
            raise Exception("Wrong file format")

    except Exception as e:   # delete the remains of partdownloads - if they exist
        if os.path.isfile(fGzFileName):
            os.remove(fGzFileName)

        raise Error(message = "Dataset not available, check file availability at Eurostat.", addMessage = str(e))

    log("Download successfull")


def extractTsvGzFile(name):
    log("start to extract the db " + name)

    gzFileName   = name + ".tsv.gz"
    fGzFileName  = os.path.join(Settings.dataPath, gzFileName)

    tsvFileName  = name + ".tsv"
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
    # removes selected tsv-file from data directory
    fileName = name + ".tsv"  #---get name of selected item---
    log("removing file " + Settings.dataPath + fileName)

    #---removing file---
    os.remove(os.path.join(Settings.dataPath, fileName))


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
        worker = DownloadAndExtractDbWorker(name)
        worker.startWork()
        worker.wait()

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

fileInfo = {}
fileInfoLoaded = False

def getFileInfoJson():
    global fileInfo

    if fileInfoLoaded:
        return fileInfo

    if not os.path.isfile(Settings.dataInfoFile):
        saveFileInfoJson()

    with open(Settings.dataInfoFile, 'r') as infoFile:
        info = sj.loads(infoFile.read())

    for entry in info:
        if "updatedDate" in info[entry]:
            info[entry]["updatedDate"] = datetime.strptime(info[entry]["updatedDate"], Settings.dateFormat)
        if "extractedDate" in info[entry]:
            info[entry]["extractedDate"] = datetime.strptime(info[entry]["extractedDate"], Settings.dateFormat)
        if "lastCheckedDate" in info[entry]:
            info[entry]["lastCheckedDate"] = datetime.strptime(info[entry]["lastCheckedDate"], Settings.dateFormat)

    fileInfo = info

    return fileInfo


def saveFileInfoJson():
    wInfo = copy.deepcopy(fileInfo)
    for entry in wInfo:
        if "updatedDate" in wInfo[entry]:
            wInfo[entry]["updatedDate"] = wInfo[entry]["updatedDate"].strftime(Settings.dateFormat)
        if "extractedDate" in wInfo[entry]:
            wInfo[entry]["extractedDate"] = wInfo[entry]["extractedDate"].strftime(Settings.dateFormat)
        if "lastCheckedDate" in wInfo[entry]:
            wInfo[entry]["lastCheckedDate"] = wInfo[entry]["lastCheckedDate"].strftime(Settings.dateFormat)

    with open(Settings.dataInfoFile, 'w') as infoFile:
        infoFile.write(sj.dumps(wInfo))
        infoFile.close()


def getFileInfo(name):
    info = getFileInfoJson()
    if name in info:
        return info[name]


def delFileInfo(name):
    info = getFileInfoJson()

    if name in info:
        del info[name]

    saveFileInfoJson()


def getFileInfoFromEurostat(name):
    log("getFileInfoFromEurostat(" + name + ")")
    eInfo = {}
    eInfo["lastCheckedDate"] = datetime.now()

    fileURL = Settings.eurostatURLchar + name[0]  # the url is sorted e.g. it ends with "a" for a List of files that start with "a"
    response = urlopen(fileURL)

    for line in response:
        if name in line:
            break

    eInfo["size"] = line.split("</td>")[1].split(">")[1]

    dateString = line.split("</td>")[3].split("&nbsp;")[1]
    eInfo["updatedDate"] = datetime.strptime(dateString, Settings.dateFormat)

    info = getFileInfoJson()
    if name in info:
        info[name]["lastCheckedDate"] = eInfo["lastCheckedDate"]
        if eInfo["updatedDate"] > info[name]["updatedDate"]:
            info[name]["newerVersionAvailable"] = True
        saveFileInfoJson()

    return eInfo


def addFileInfo(name, extractedDate):
    eurostatInfo = getFileInfoFromEurostat(name)

    info = getFileInfoJson()
    info[name] = {"size": eurostatInfo["size"], "updatedDate": eurostatInfo["updatedDate"],
                "extractedDate": extractedDate, "lastCheckedDate": eurostatInfo["lastCheckedDate"] }


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