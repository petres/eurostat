# Copyright (c) 2010-2014 openpyxl

import pytest

from lxml.etree import iterparse, fromstring

from openpyxl.xml.constants import SHEET_MAIN_NS
from openpyxl.cell import Cell
from openpyxl.collections import IndexedList
from openpyxl.styles import Style


@pytest.fixture
def Worksheet(Workbook):
    class DummyWorkbook:

        _guess_types = False
        data_only = False

        def __init__(self):
            self.shared_styles = IndexedList(range(28))
            self.shared_styles.add(Style())


    from openpyxl.styles import numbers

    class DummyStyle:
        number_format = numbers.FORMAT_GENERAL


    class DummyWorksheet:

        encoding = "utf-8"
        title = "Dummy"

        def __init__(self):
            self.parent = DummyWorkbook()
            self.column_dimensions = {}
            self.row_dimensions = {}
            self._styles = {}
            self.cell = None
            self._data_validations = []

        def __getitem__(self, value):
            if self.cell is None:
                self.cell = Cell(self, 'A', 1)
            return self.cell

        def get_style(self, coordinate):
            return DummyStyle()

    return DummyWorksheet()


@pytest.fixture
def WorkSheetParser(Worksheet):
    """Setup a parser instance with an empty source"""
    from .. worksheet import WorkSheetParser
    return WorkSheetParser(Worksheet, None, {0:'a'}, {})


def test_col_width(datadir, Worksheet, WorkSheetParser):
    datadir.chdir()
    ws = Worksheet
    parser = WorkSheetParser

    with open("complex-styles-worksheet.xml", "rb") as src:
        cols = iterparse(src, tag='{%s}col' % SHEET_MAIN_NS)
        for _, col in cols:
            parser.parse_column_dimensions(col)
    assert set(ws.column_dimensions.keys()) == set(['A', 'C', 'E', 'I', 'G'])
    assert dict(ws.column_dimensions['A']) == {'max': '1', 'min': '1',
                                               'customWidth': '1',
                                               'width': '31.1640625'}


def test_hidden_col(datadir, Worksheet, WorkSheetParser):
    datadir.chdir()
    ws = Worksheet
    parser = WorkSheetParser

    with open("hidden_rows_cols.xml", "rb") as src:
        cols = iterparse(src, tag='{%s}col' % SHEET_MAIN_NS)
        for _, col in cols:
            parser.parse_column_dimensions(col)
    assert 'D' in ws.column_dimensions
    assert dict(ws.column_dimensions['D']) == {'customWidth': '1', 'hidden': '1', 'max': '4', 'min': '4'}


def test_styled_col(datadir, Worksheet, WorkSheetParser):
    datadir.chdir()
    ws = Worksheet
    parser = WorkSheetParser
    with open("complex-styles-worksheet.xml", "rb") as src:
        cols = iterparse(src, tag='{%s}col' % SHEET_MAIN_NS)
        for _, col in cols:
            parser.parse_column_dimensions(col)
    assert 'I' in ws.column_dimensions
    cd = ws.column_dimensions['I']
    assert cd._style == 28
    assert cd.style == Style()
    assert dict(cd) ==  {'customWidth': '1', 'max': '9', 'min': '9', 'width': '25', 'style':'28'}


def test_hidden_row(datadir, Worksheet, WorkSheetParser):
    datadir.chdir()
    ws = Worksheet
    parser = WorkSheetParser

    with open("hidden_rows_cols.xml", "rb") as src:
        rows = iterparse(src, tag='{%s}row' % SHEET_MAIN_NS)
        for _, row in rows:
            parser.parse_row_dimensions(row)
    assert 2 in ws.row_dimensions
    assert dict(ws.row_dimensions[2]) == {'hidden': '1'}


def test_styled_row(datadir, Worksheet, WorkSheetParser):
    datadir.chdir()
    ws = Worksheet
    parser = WorkSheetParser
    parser.shared_strings = dict((i, i) for i in range(30))

    with open("complex-styles-worksheet.xml", "rb") as src:
        rows = iterparse(src, tag='{%s}row' % SHEET_MAIN_NS)
        for _, row in rows:
            parser.parse_row_dimensions(row)
    assert 23 in ws.row_dimensions
    rd = ws.row_dimensions[23]
    assert rd._style == 28
    assert rd.style == Style()
    assert dict(rd) == {'s':'28', 'customFormat':'1'}


def test_sheet_protection(datadir, Worksheet, WorkSheetParser):
    datadir.chdir()
    ws = Worksheet
    parser = WorkSheetParser

    with open("protected_sheet.xml", "rb") as src:
        tree = iterparse(src, tag='{%s}sheetProtection' % SHEET_MAIN_NS)
        for _, tag in tree:
            parser.parse_sheet_protection(tag)
    assert dict(ws.protection) == {
        'autoFilter': '0', 'deleteColumns': '0',
        'deleteRows': '0', 'formatCells': '0', 'formatColumns': '0', 'formatRows':
        '0', 'insertColumns': '0', 'insertHyperlinks': '0', 'insertRows': '0',
        'objects': '0', 'password': 'DAA7', 'pivotTables': '0', 'scenarios': '0',
        'selectLockedCells': '0', 'selectUnlockedCells': '0', 'sheet': '1', 'sort':
        '0'
    }


def test_formula_without_value(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser

    src = """
      <x:c r="A1" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:f>IF(TRUE, "y", "n")</x:f>
        <x:v />
      </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 'f'
    assert ws['A1'].value == '=IF(TRUE, "y", "n")'


def test_formula(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser

    src = """
    <x:c r="A1" t="str" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:f>IF(TRUE, "y", "n")</x:f>
        <x:v>y</x:v>
    </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 'f'
    assert ws['A1'].value == '=IF(TRUE, "y", "n")'


def test_formula_data_only(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser
    parser.data_only = True

    src = """
    <x:c r="A1" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:f>1+2</x:f>
        <x:v>3</x:v>
    </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 'n'
    assert ws['A1'].value == 3


def test_string_formula_data_only(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser
    parser.data_only = True

    src = """
    <x:c r="A1" t="str" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:f>IF(TRUE, "y", "n")</x:f>
        <x:v>y</x:v>
    </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 's'
    assert ws['A1'].value == 'y'


def test_number(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser

    src = """
    <x:c r="A1" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:v>1</x:v>
    </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 'n'
    assert ws['A1'].value == 1


def test_string(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser

    src = """
    <x:c r="A1" t="s" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:v>0</x:v>
    </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 's'
    assert ws['A1'].value == "a"


def test_boolean(Worksheet, WorkSheetParser):
    ws = Worksheet
    parser = WorkSheetParser

    src = """
    <x:c r="A1" t="b" xmlns:x="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
        <x:v>1</x:v>
    </x:c>
    """
    element = fromstring(src)

    parser.parse_cell(element)
    assert ws['A1'].data_type == 'b'
    assert ws['A1'].value is True


def test_inline_string(Worksheet, WorkSheetParser, datadir):
    ws = Worksheet
    parser = WorkSheetParser
    datadir.chdir()

    with open("Table1-XmlFromAccess.xml") as src:
        sheet = fromstring(src.read())

    element = sheet.find("{%s}sheetData/{%s}row/{%s}c" % (SHEET_MAIN_NS, SHEET_MAIN_NS, SHEET_MAIN_NS))
    parser.parse_cell(element)
    assert ws['A1'].data_type == 's'
    assert ws['A1'].value == "ID"


def test_inline_richtext(Worksheet, WorkSheetParser, datadir):
    ws = Worksheet
    parser = WorkSheetParser
    datadir.chdir()
    with open("jasper_sheet.xml", "rb") as src:
        sheet = fromstring(src.read())

    element = sheet.find("{%s}sheetData/{%s}row[2]/{%s}c[18]" % (SHEET_MAIN_NS, SHEET_MAIN_NS, SHEET_MAIN_NS))
    assert element.get("r") == 'R2'
    parser.parse_cell(element)
    cell = ws['B2'].style = ws.get_style(coordinate='')
    assert ws['B2'].data_type == 's'
    assert ws['B2'].value == "11 de September de 2014"


def test_data_validation(Worksheet, WorkSheetParser, datadir):
    ws = Worksheet
    parser = WorkSheetParser
    datadir.chdir()

    with open("worksheet_data_validation.xml") as src:
        sheet = fromstring(src.read())

    element = sheet.find("{%s}dataValidations" % SHEET_MAIN_NS)
    parser.parse_data_validation(element)
    dvs = ws._data_validations
    assert len(dvs) == 1

