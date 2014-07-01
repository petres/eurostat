#!/usr/bin/env python
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib", "simplejson"))

# HELPERS AND SETTINGS
from helpers import Settings


import xml.etree.ElementTree as ET


def main(): 
    print outputJson(getTree())


def getTree():
    tree = ET.parse(Settings.tocXml)
    root = tree.getroot()
    return outputTree(root)


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
            if child.attrib["format"] == "sdmx":
                info["metadata"] = child.text
            continue
    return  info


def getClearTag(child):
    return child.tag.rsplit('}', 1)[1]


if __name__ == "__main__":
    main()
