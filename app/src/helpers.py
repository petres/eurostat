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

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen


#----------------------------------------------
#----- SETTINGS -------------------------------
#----------------------------------------------

class Settings():
    dataPath            = "data/"
    dictPath            = "data/dict/"
    outputPath          = "output/"
    dictURL             = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&downfile=dic%2Fen%2F'
    bulkURL             = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&file=data%2F'
    eurostatURL         = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?sort=1&dir=data'
    eurostatURLchar     = 'http://epp.eurostat.ec.europa.eu/NavTree_prod/everybody/BulkDownloadListing?dir=data&sort=1&sort=2&start=' #+'n' is the list of files start with "n"

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
        return True

    except Exception as ee:   # delete the remains of partdownloads - if they exist
        log("ERROR in Download and/or Extraction of tsv file: "+str(ee))
        log("TIP: Check File availability at Eurostat, Database Name and the Download-URL in the Options")

        if os.path.isfile(fGzFileName):
            os.remove(fGzFileName)
        if os.path.isfile(fTsvFileName):
            os.remove(fTsvFileName)

        return False


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
        log("ERROR - in Dic File opening: " + dictFileName)
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

    try:#---get URL and response---
        fileURL = Settings.dictURL + dictFileName
        response = urlopen(fileURL)
        log("Dictionary download OK")
    except:
        log("ERROR in downloading Dictionary " + dictFileName)
        return False

    try:#---saving download---
        with open(os.path.join(Settings.dictPath, dictFileName), 'wb') as outfile:
            outfile.write(response.read())
    except:
        log("ERROR in saving Dictionary " + dictFileName)
        return False

#----------------------------------------------



#----------------------------------------------
#----- EXPRT ----------------------------------
#----------------------------------------------
def export(name, selection = None, structure = None, fileType = "EXCEL", fileName = "output/output.xls"):
    wb = xlwt.Workbook()
    data = _prepareData(name, selection)

    #if len(structure["tab"]) == 0:
    offset = (5, 0)

    #for 
    table = _prepareTable(data, structure, selection)

    ws = wb.add_sheet("0", cell_overwrite_ok = True)

    for i, label in enumerate(table["rowLabels"]):
        ws.write(offset[0] + i, offset[1], label)

    for i, label in enumerate(table["colLabels"]):
        ws.write(offset[0], offset[1] + i, label)

    
    for i, line in enumerate(table["data"]):
        for j, entry in enumerate(line):
            ws.write(offset[0] + i + 1, offset[1] + j + 1, entry)

    wb.save(fileName)


def _prepareTable(data, structure, selection, fixed = {}):
    cols = []
    print selection
    for i in structure["col"]:
        cols.append(selection[i])

    rows = []
    for i in structure["row"]:
        rows.append(selection[i])

    baseCols = data["cols"]
    
    colP = list(itertools.product(*cols))
    rowP = list(itertools.product(*rows))

    table = { "rowLabels": rowP,
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
                    raise Exception('Wow Wow Wow')

                keyList.append(keyEntry)

            value = data["data"][tuple(keyList)]
            values.append(value)
        table["data"].append(values)

    return table


def _prepareData(name, selection = None):
    time    = []
    data    = { "data": {}, "cols": []}

    tsvFileName = os.path.join(Settings.dataPath, name + '.tsv')
    with open(tsvFileName, 'r') as tsvFile:
        tsvReader = csv.reader(tsvFile, delimiter='\t')
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
                    data["data"][key] = row[j].strip()
    return data


#----------------------------------------------
#----- ELSE -----------------------------------
#----------------------------------------------

def log(message):
    print(message)

#----------------------------------------------