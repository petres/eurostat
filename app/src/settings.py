# -*- coding: utf-8 -*-

import os, sys

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
            "type"                : 'eurostatBulk',
            "dictURL"             : 'http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?sort=1&file=dic%2Fen%2F',
            "bulkURL"             : 'http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?sort=1&file=data%2F',
            "emptyCellSign"       : ':', 
            'URLchar'             : 'http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/BulkDownloadListing?dir=data&sort=1&sort=2&start=',
            'defaultTimeColumn'   : 'time'
        },
        "oecd": {
            "browseable"          : False,
            "type"                : 'sdmx',
            "url"                 : 'http://stats.oecd.org/SDMX-JSON/',
            'defaultTimeColumn'   : 'TIME_PERIOD'
        }
    }


    presetFile          = os.path.join('presets', '##NAME##.preset')

    inGui               = False

    defaultOptions      = { #"name":            self.metaData["_name"],
                            #"selection":       self.options["selection"],
                            #"structure":        { "sheet": [], "col": ["time"]},
                            "structure":        { "sheet": [], "col": ["time"]},
                            "sheetName":        "##NAME##",
                            "fileType":         "EXCEL",
                            "fileName":         os.path.join('output', '##NAME##.##TYPE##'),
                            #"sorting":          { "time": QtCore.Qt.DescendingOrder },
                            "sorting":          {},
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