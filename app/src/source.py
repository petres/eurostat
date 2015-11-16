# -*- coding: utf-8 -*-

import os, sys

from settings import Settings

import eurostatBulk as e
import sdmx as s

#----------------------------------------------
#----- EUROSTAT BULK FUNCTIONS ----------------
#----------------------------------------------

def downloadData(datasetId):
    return _getBase(datasetId).downloadData(datasetId)

def extractData(datasetId):
    return _getBase(datasetId).extractData(datasetId)

def loadMeta(datasetId):
    return _getBase(datasetId).loadMeta(datasetId)

def getData(datasetId, selection=None):
    return _getBase(datasetId).getData(datasetId, selection)

def checkStatus(datasetId):
    return _getBase(datasetId).checkStatus(datasetId)



def _getBase(datasetId):
    sourceType = Settings.sources[datasetId[0]]['type']
    if sourceType == "sdmx":
        return s
    elif sourceType == "eurostatBulk":
        return e
    else:
        raise Exception("SOURCE NOT IMPLEMENTED")
    