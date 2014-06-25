from openpyxl import Workbook, load_workbook
from openpyxl.cell import get_column_letter

# ADD FOR ADDING TUPLES
from operator import add

import helpers as f

class Writer():
    def __init__(self, options):
        self.overwrite = options["overwrite"]
        self.fileName = options["fileName"]

        print "Creating Writer", self.fileName, self.overwrite

        self.existingSheets = []
        self.opened = False


    def open(self):
        if self.overwrite == "File":
            print "Creating New File"
            wb = Workbook()
        else:
            try:
                wb = load_workbook(self.fileName)
                self.existingSheets = wb.get_sheet_names()
                print "Using old file, has sheets:", self.existingSheets
            except Exception as e:
                print "Creating New File, but have tried to use old one"
                print e
                wb = Workbook()

        self.wb = wb
        self.opened = True


    def changeActiveSheet(self, name):
        if not self.opened:
            self.open()

        if name in self.existingSheets:
            if self.overwrite == "Sheet":
                print "Replacing Sheet", name
                self.wb.remove_sheet(self.wb[name])
                ws = self.wb.create_sheet()
                ws.title = name
            else:
                print "Using existing Sheet", name
                ws = self.wb[name]
        else:
            print "Creating New Sheet", name
            ws = self.wb.create_sheet()
            ws.title = name

        self.ws = ws

    def writeHeader(self, options):
        self.write((0, 0), "Name:")
        self.write((0, 1), options["name"])

        self.write((1, 0), "Preset:")
        self.write((1, 1), f.getStringOfPreset(options))

    def write(self, coords, value, style = None):
        self.ws.cell('%s%s'%(get_column_letter(coords[1] + 1), coords[0] + 1)).value = str(value)


    def writeTable(self, table, sheetName = None, initialOffset = (5, 0)):
        if sheetName is not None:
            changeActiveSheet(sheetName)


        

        # Row Labels Labels
        rowLabels = []
        tableOffsetRow = 0
        for label in table["structure"]["row"]:
            if label["count"] > 1:
                rowLabels.append(label["name"])
            else:
                self.write((initialOffset[0] + tableOffsetRow, 0), label["name"])
                self.write((initialOffset[0] + tableOffsetRow, 1), label["value"])
                tableOffsetRow += 1

        tableOffset = (tableOffsetRow + 2, 0)
        offset = map(add, initialOffset, tableOffset)


        for i, label in enumerate(rowLabels):
            self.write((offset[0], offset[1] + i), label)
                


        labelOffset = (1, len(rowLabels))

        # Labels
        for i, labels in enumerate(table["labels"]["row"]):
            k = 0
            for j, label in enumerate(labels):
                if table["structure"]["row"][j]["count"] > 1:
                    self.write((offset[0] + i + labelOffset[0], offset[1] + k), label)
                    k += 1

        for i, labels in enumerate(table["labels"]["col"]):
            self.write((offset[0], offset[1] + i + labelOffset[1]), " - ".join(labels))

        dataOffset = map(add, offset, labelOffset)

        # Data
        for i, line in enumerate(table["data"]):
            for j, entry in enumerate(line):
                self.write((dataOffset[0] + i, dataOffset[1] + j), entry)


    def save(self):
        self.wb.save(filename = self.fileName)