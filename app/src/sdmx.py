# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "simplejson"))

# SIMPLEJSON
import simplejson as sj

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from settings import Settings
from helpers import Error

#----------------------------------------------
#----- SDMX FUNCTIONS -------------------------
#----------------------------------------------

def downloadData(datasetId):
    fileNameData   = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + "-data.json")
    fileNameMeta   = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + "-meta.json")

    try:
        fileURL = Settings.sources[datasetId[0]]["url"] + "data/" + datasetId[1] + "?detail=dataonly"
        response = urlopen(fileURL)

        with open(fileNameData, 'w') as outfile:
            outfile.write(response.read())

        fileURL = Settings.sources[datasetId[0]]["url"] + "metadata/" + datasetId[1]
        response = urlopen(fileURL)

        with open(fileNameMeta, 'w') as outfile:
            outfile.write(response.read())

    except Exception as e:
        from helpers import Error
        # if os.path.isfile(fileNameData):
        #     os.remove(fileName)

        # if os.path.isfile(fileNameMeta):
        #     os.remove(fileName)

        raise Error(message = "Dataset not available, check file availability.", addMessage = str(e))

    #log("Download successfull")


def extractData(datasetId):
    pass


def loadMeta(datasetId):
    metaData = {}
    metaData["_cols"]   = []

    metaFileName = fileNameMeta   = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + "-meta.json")

    with open(metaFileName, 'r') as metaFile:
        mD = sj.loads(metaFile.read())
        dims = mD["structure"]["dimensions"]["observation"]

        for dim in dims:
            #log(dim["id"]);
            metaData["_cols"].append(dim["id"])
            metaData[dim["id"]] = {}
            for val in dim["values"]:
                metaData[dim["id"]][val["id"]] = val["name"]
            #metaData[dim["id"]] = OrderedDict(sorted(metaData[dim["id"]].iteritems()))
        #log(metaFile.read())

    return metaData


def getData(datasetId, selection=None):
    colDimValues = []
    data = {"data": {}, "cols": [], "flags": [], "long": {}}

    keys = {}
    dataFileName = os.path.join(Settings.dataPath, datasetId[0] + "-" + datasetId[1] + '-data.json')
    with open(dataFileName, 'r') as dataFile:
        dataJson = sj.loads(dataFile.read())
        cols = []

        dims = dataJson['structure']['dimensions']['series']
        #log("dimensions - series")
        for dim in dims:
            #log(" - " + dim["id"])
            keys[dim["id"]] = dim["values"]
            cols.append(dim["id"])
            data["cols"].append(dim["id"])

        # log("attributes - series")
        # dims = dataJson['structure']['attributes']['series']
        # for dim in dims:
        #     log(" - " + dim["id"])
        #     keys[dim["id"]] = dim["values"]
        #     cols.append(dim["id"])

        #log("dimensions - observation")
        dims = dataJson['structure']['dimensions']['observation']
        for dim in dims:
            #log(" - " + dim["id"])
            keys[dim["id"]] = dim["values"]
            cols.append(dim["id"])
            data["cols"].append(dim["id"])

        # log("attributes - observation")
        # dims = dataJson['structure']['attributes']['observation']
        # for dim in dims:
        #     log(" - " + dim["id"])
        #     keys[dim["id"]] = dim["values"]
        #     cols.append(dim["id"])

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

            #kIdA += series[dk]['attributes']
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

                flag = None
                if len(obs) > 1:
                    flag = ", ".join(okVA[-(len(obs)-1):])

                data["data"][tuple(dKey)] = {"value": value, "flag": flag}

                #print str(okVA) + " - " + str(value)
    
    meta = loadMeta(datasetId)
    # GET LONG (LABELS)
    for col in data["cols"]:
        data["long"][col] = meta[col]

    return data