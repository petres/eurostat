# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "xlwt"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "simplejson"))

# SIMPLEJSON
import simplejson as sj

# QT
from PyQt4 import QtCore, QtGui

from ProgressDialog import ProgressDialog

from datetime import datetime

import copy


from settings import Settings, log, error, warn


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
        downloadData(self.datasetId)
        self.setStep(1)
        extractData(self.datasetId)
        self.setStep(2)
        dsInfo = {}
        dsInfo["source"] = self.datasetId[0]
        dsInfo["name"] = self.datasetId[1]
        dsInfo["size"] = "TODO"
        dsInfo["extractedDate"] = currentTime
        dsInfo["updatedDate"] = currentTime
        dsInfo["lastCheckedDate"] = currentTime 


        # if self.datasetId[0] == "eurostat":
        #     eurostatBulkDownloadData(self.datasetId[1])
            
        #     eurostatBulkExtractData(self.datasetId[1])
        #     dsInfo = eurostatBulkCheckStatus(self.datasetId[1])
        #     dsInfo["extractedDate"] = currentTime
        #     dsInfo["name"] = self.datasetId[1]
        #     dsInfo["source"] = self.datasetId[0]
            
        # elif self.datasetId[0] == "oecd":
        #     sdmxDownloadData(self.datasetId)
        #     self.setStep(1)

        # else:
        #     raise Error("Source not implemented.", addMessage = "Source: '" + self.datasetId[0] + "'")

        addFileInfo(dsInfo)


class LoadDbWorker(Worker):
    title = "Loading Database ... "
    steps = ["Loading Categories"]

    def __init__(self, datasetId, baseDialog, parent = None):
        Worker.__init__(self, parent)
        self.datasetId = datasetId
        self.baseDialog = baseDialog


    def work(self):
        # CHECK EXISTENCE
        # if not os.path.isfile(metaFileName):
        #     worker = DownloadAndExtractDbWorker(datasetId)
        #     worker.startWork()
        #     worker.wait()

        self.setStep(0)
        self.metaData = loadMeta(self.datasetId)
        self.metaData["_source"] = self.datasetId[0]
        self.metaData["_name"] = self.datasetId[1]

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


from source import * 