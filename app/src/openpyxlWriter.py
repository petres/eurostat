from openpyxl import Workbook, load_workbook
from openpyxl.cell import get_column_letter

# ADD FOR ADDING TUPLES
from operator import add

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


    def write(self, coords, value, style = None):
        self.ws.cell('%s%s'%(get_column_letter(coords[0] + 1), coords[1] + 1)).value = str(value)


    def writeTable(self, table, sheetName = None, initialOffset = (0, 5)):
        if sheetName is not None:
            changeActiveSheet(sheetName)

        # Row Labels Labels
        for i, label in enumerate(table["rowLabelsStructure"]):
            self.write((initialOffset[0], initialOffset[1] + i), label)

        labelOffset = (len(table["colLabelsStructure"]), len(table["rowLabelsStructure"]))

        # Labels
        for i, labels in enumerate(table["rowLabels"]):
            for j, label in enumerate(labels):
                self.write((initialOffset[0] + i + labelOffset[0], initialOffset[1] + j), label)

        for i, label in enumerate(table["colLabels"]):
            self.write((initialOffset[0], initialOffset[1] + i + labelOffset[1]), label)

        offset = map(add, initialOffset, labelOffset)

        # Data
        for i, line in enumerate(table["data"]):
            for j, entry in enumerate(line):
                self.write((offset[0] + i, offset[1] + j), entry)


    def save(self):
        self.wb.save(filename = self.fileName)