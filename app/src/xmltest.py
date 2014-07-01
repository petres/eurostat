#!/usr/bin/env python
import sys, os

# HELPERS AND SETTINGS
from helpers import Settings

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)
os.chdir(os.path.join(dirname, "..", ".."))

import xml.etree.ElementTree as ET

def main(): 
    tree = ET.parse(Settings.tocXml)
    root = tree.getroot()
    info = outputTree(root)
    print info

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
    #print " " * i, getClearTag(tree)
    
    # if tag == "leaf":
    #     code = getInfoForDataset(tree)
    #     print " " * i, code
    #     return
    info = []
    for child in tree:
        tag = getClearTag(child)
        if tag == "branch":
            childInfo = getInfoForBranch(child)
        elif tag == "leaf":
            childInfo = getInfoForDataset(child)
        info.append(childInfo)
    return info;

    # for child in tree:
    #     outputTree(child, i + 1)


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
