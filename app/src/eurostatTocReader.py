#!/usr/bin/env python
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "simplejson"))

# HELPERS AND SETTINGS
from helpers import Settings, Worker, log

import simplejson as sj

import xml.etree.ElementTree as ET

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

dictByName = {}
class TocWorker(Worker):
    title = "Browse ... "
    steps = ["Download", "Prepare", "Save"]

    def __init__(self, parent = None): 
        Worker.__init__(self, parent)

    def isWorkAndIfStart(self):
        if not os.path.isfile(Settings.tocDict):
            self.startWork()
            return True
        else:
            with open(Settings.tocDict, 'r') as infile:
                self.toc = sj.loads(infile.read())
        return False


    def work(self):
        self.setStep(0)
        response = urlopen(Settings.sources['eurostat']['tocXmlURL'])
        with open(Settings.tocXml, 'wb') as outfile:
            outfile.write(response.read())
        
        self.setStep(1)

        tree = ET.parse(Settings.tocXml)
        root = tree.getroot()
        output = outputTree(root)

        self.setStep(2)

        with open(Settings.tocDict, 'w') as outfile:
            outfile.write(sj.dumps(output))

        with open(Settings.dictByName, 'w') as outfile:
            outfile.write(sj.dumps(dictByName))

        self.toc = output

        self.setStep(3)


def outputJson(info, i = 0):
    if type(info) is list:
        i += 1
        for part in info:
            outputJson(part, i)
    else:
        if info["type"] == "leaf":
            print " " * i, info["code"] + " - "  + info["title"]
        else:
            print " " * i, info["title"]
        if "children" in info:
            outputJson(info["children"], i)




def outputTree(tree):
    info = []
    for child in tree:
        tag = getClearTag(child)
        if tag == "branch":
            childInfo = getInfoForBranch(child)
        elif tag == "leaf":
            childInfo = getInfoForDataset(child)
        info.append(childInfo)
    return info;


def getInfoForBranch(branch):
    info = {}
    info["type"] = "branch"
    for child in branch:
        tag = getClearTag(child)
        if tag == "title":
            if child.attrib["language"] == "en":
                info["title"] = child.text
            continue
        if tag == "code":
            info["code"] = child.text
            continue
        if tag == "children":
            info["children"] = outputTree(child)

    return  info



def getInfoForDataset(dataset):
    global dictByName
    info = {}
    info["type"] = "leaf"
    for child in dataset:
        tag = getClearTag(child)
        if tag == "title":
            if child.attrib["language"] == "en":
                info["title"] = child.text
            continue
        if tag == "code":
            info["code"] = child.text
            continue
        if tag == "metadata":
            if "metadata" not in info:
                info["metadata"] = {}
            if child.attrib["format"] == "sdmx":
                info["metadata"]["sdmx"] = child.text
            if child.attrib["format"] == "html":
                info["metadata"]["html"] = child.text
            continue
    dictByName[info["code"]] = info
    return  info


def getClearTag(child):
    return child.tag.rsplit('}', 1)[1]


if __name__ == "__main__":
    main()
