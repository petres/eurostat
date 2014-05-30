import os

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

# CSV (reading csv/tsv files)
import csv
# GZIP (uncompress .gz files)
import gzip
#----------------------------------------------
#----- SETTINGS -------------------------------
#----------------------------------------------

class Settings():
    dataPath            = "data/"
    dictPath            = "data/dicx/"
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

    os.chdir(Settings.dataPath)  #change directory to Data (otherwise trouble with the "open" function
    gzFileName  = name + ".tsv.gz"
    tsvFileName = name + ".tsv"

    try:
        #---get gz file from eurostat page---
        fileURL = Settings.bulkURL + gzFileName
        response = urlopen(fileURL)

        with open(gzFileName, 'wb') as outfile:
            outfile.write(response.read())

        #---EXTRACT TSV.GZ.FILE---
        with open(tsvFileName, 'wb') as outfile, gzip.open(gzFileName) as infile:
            outfile.write(infile.read())

        #---delete gz file---
        os.remove(gzFileName)

        os.chdir("..")
        log("Download and Extraction successfull")
        return True

    except Exception as ee:   # delete the remains of partdownloads - if they exist
        log("ERROR in Download and/or Extraction of tsv file: "+str(ee))
        log("TIP: Check File availability at Eurostat, Database Name and the Download-URL in the Options")
        if gzFileName in os.listdir("./"):
            os.remove(gzFileName)
        if tsvFileName in os.listdir("./"):
            os.remove(tsvFileName)
        os.chdir("..")
        return False


def removeTsvFile(name):
    # removes selected tsv-file from data directory
    fileName = name + ".tsv"  #---get name of selected item---
    log("removing file " + Settings.dataPath + fileName)

    #---removing file---
    os.remove(Settings.dataPath + fileName)


def loadTsvFile(dbname):
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
    metaData["_cols"]   = []
    metaData["time"]    = []
    metaData["geo"]     = []


    #---open file and read line by line---
    tsvFileName = Settings.dataPath + dbname + '.tsv'
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
                    if tmp[i] not in metaData[colName]:           # if not then append to cat_list in the row of the respective title
                        metaData[colName].append(tmp[i].strip())

                if tmp[-1] not in metaData["geo"]:    # fill GEO List with the GEO Info (is always last)
                    metaData["geo"].append(tmp[-1].strip())

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

    lines = open(Settings.dataPath+"_INFO.txt").readlines()
    lines.remove(todelete)
    #newlines=lines
    open(Settings.dataPath + "_INFO.txt", 'w').writelines(lines)


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

    #---write in file
    with open(Settings.dataPath + "_INFO.txt", "a") as f:
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

        with open(dicFileName,"r") as dictFile:
            dictReader = csv.reader(dictFile,delimiter = "\t")
            for row in dictReader:                           #search every row of the dict for the short
                if row[0] == shorty:                              #if they match
                    longy = row[1]                           #append to long
                    return str(longy)
        return "n.a."
    except:
        print("ERROR- in Dic File opening:" + dictFileName)
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
        log("dictionary NOT found...start download attempt")
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
        os.chdir(Settings.dictPath)
        with open(dicFileName, 'wb') as outfile:
            outfile.write(response.read())

        os.chdir("..") # 2x because dic is 2steps down
        os.chdir("..")
    except:
        log("ERROR in saving Dictionary " + dictFileName)
        return False

#----------------------------------------------



#----------------------------------------------
#----- ELSE -----------------------------------
#----------------------------------------------

def log(message):
    print(message)

#----------------------------------------------