#!/usr/bin/env python

# IMPORTING THE LIB FOLDER
import os, sys
sys.path.insert(1,os.path.join(os.path.dirname(__file__), "..", "lib"))


# **********************************
# ** LIBS
# ***********************************

# NUMPY (scientific computing package)
import numpy as np

# OPENPYXL (reads and writes excel files)
from openpyxl import load_workbook
from openpyxl.cell import get_column_letter, column_index_from_string
from openpyxl.workbook import Workbook
from openpyxl.drawing import Image

# MATPLOTLIB (draws graphs)
import matplotlib
#print matplotlib.__version__
from matplotlib.ticker import FuncFormatter
matplotlib.use('Qt4Agg')
matplotlib.rcParams.update({'font.size': 14})
from matplotlib import pylab as p

# ORDEREDDICT
from collections import OrderedDict

from operator import add
# ***********************************


fileName    = "../../output/lfsq_egan2.xlsx"
outFileName    = "../../output/lfsq_egan2_img.xlsx"

offset      = 12

# DIMENSIONS: Sheet, Row

lines = []
lines.append({
    'color'     : '#000000',
    'row'       : 'TOTAL'});

lines.append({
    'color'     : '#0070c0',
    'row'       : 'A'});

# DIMENSIONS: Sheets, Rows
graphs = {
    'type'      : 'sheets',
    'selection' : ['AT', 'DE']}


wb = load_workbook(filename = fileName)
ws = {}
rowNameToRowNumber = {}
timeLabels = None
startRow = 1
endRow = None

def findRowNumberByRowName(sheet, row):
    t = startRow
    while t < 1000:
        t += 1
        if row == sheet.cell('A%s'%(t)).value:
            break

    return t

def getData(sheet, row):
    print sheet, row
    global timeLabels, startRow, endRow
    if sheet not in ws:
        ws[sheet] = wb.get_sheet_by_name(name = sheet)
    cSheet = ws[sheet]
    if row not in rowNameToRowNumber:
        rowNameToRowNumber[row] = findRowNumberByRowName(cSheet, row)

    if timeLabels is None:
        timeLabels = []
        startRow = findRowNumberByRowName(cSheet, "Data:") + 1
        endRow = findRowNumberByRowName(cSheet, None)
        t = 2
        while t < 1000:
            label = cSheet.cell('%s%s'%( get_column_letter(t), startRow)).value
            if label is None:
                break
            timeLabels.append(label)
            t += 1


    rowNumber = rowNameToRowNumber[row]

    data = []

    for t in range(len(timeLabels)):
        d = cSheet.cell('%s%s'%( get_column_letter(t+2), rowNumber)).value
        data.append(d)

    return data

def main():


    for s1 in graphs['selection']:
        dataParam = {}
        if graphs['type'] == "sheets":
            dataParam['sheet'] = s1
        elif raphs['type'] == "row":
            dataParam['row'] = s1


        p.figure(figsize=(10.0, 5.0))

        maxValue = -float("inf")
        minValue =  float("inf")

        for line in lines:
            if 'row' in line:
                s2 = line['row']
                dataParam['row'] = s2
            elif 'sheet' in line:
                s2 = line['sheet']
                dataParam['sheet'] = s2

            print dataParam
            data = getData(**dataParam)

            p.plot(range(0, len(data)), data, color=line["color"], label = s2)

        #p.xlabel(timeLabels, rotation='vertical', size = 'x-small')
        ax = p.gca()
        ax.yaxis.label.set_size('x-small')
        p.xticks(range(len(data)), timeLabels, rotation='vertical', size = 'x-small', multialignment = 'center')
        #p.xticks(map(add, range(len(data)), [-0.5] * len(data)), timeLabels, rotation='vertical', size = 'x-small', ha = 'right')

        p.legend(loc='best', prop={"size": 'small'}).draw_frame(False)
        p.grid(True)
        p.tight_layout()

        p.savefig("tttt.png")

        img = Image('tttt.png')
        img.anchor(ws[dataParam['sheet']]['B%s'%(endRow + 1)], anchortype='oneCell')
        ws[dataParam['sheet']].add_image(img)

        wb.save(outFileName)




if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt):
        print "KeyboardInterrupt"

