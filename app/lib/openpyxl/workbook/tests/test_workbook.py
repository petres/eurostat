# coding: utf-8
# Copyright (c) 2010-2014 openpyxl
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# @license: http://www.opensource.org/licenses/mit-license.php
# @author: see AUTHORS file

# stdlib
import datetime

# package imports
from openpyxl.workbook import Workbook
from openpyxl.reader.excel import load_workbook
from openpyxl.workbook.names.named_range import NamedRange
from openpyxl.exceptions import ReadOnlyWorkbookException

# test imports
import pytest
from openpyxl.tests.schema import validate_archive


def test_get_active_sheet():
    wb = Workbook()
    active_sheet = wb.get_active_sheet()
    assert active_sheet == wb.worksheets[0]


def test_create_sheet():
    wb = Workbook()
    new_sheet = wb.create_sheet(0)
    assert new_sheet == wb.worksheets[0]

def test_create_sheet_with_name():
    wb = Workbook()
    new_sheet = wb.create_sheet(0, title='LikeThisName')
    assert new_sheet == wb.worksheets[0]

def test_add_correct_sheet():
    wb = Workbook()
    new_sheet = wb.create_sheet(0)
    wb._add_sheet(new_sheet)
    assert new_sheet == wb.worksheets[2]

def test_add_sheetname():
    wb = Workbook()
    with pytest.raises(TypeError):
        wb._add_sheet("Test")


def test_add_sheet_from_other_workbook():
    wb1 = Workbook()
    wb2 = Workbook()
    ws = wb1.active
    with pytest.raises(ValueError):
        wb2._add_sheet(ws)


def test_create_sheet_readonly():
    wb = Workbook(read_only=True)
    #wb._set_optimized_read()
    with pytest.raises(ReadOnlyWorkbookException):
        wb.create_sheet()


def test_remove_sheet():
    wb = Workbook()
    new_sheet = wb.create_sheet(0)
    wb.remove_sheet(new_sheet)
    assert new_sheet not in wb.worksheets


def test_get_sheet_by_name():
    wb = Workbook()
    new_sheet = wb.create_sheet()
    title = 'my sheet'
    new_sheet.title = title
    found_sheet = wb.get_sheet_by_name(title)
    assert new_sheet == found_sheet


def test_getitem(Workbook, Worksheet):
    wb = Workbook()
    ws = wb['Sheet']
    assert isinstance(ws, Worksheet)
    with pytest.raises(KeyError):
        wb['NotThere']


def test_delitem(Workbook):
    wb = Workbook()
    del wb['Sheet']
    assert wb.worksheets == []


def test_contains(Workbook):
    wb = Workbook()
    assert "Sheet" in wb
    assert "NotThere" not in wb

def test_iter(Workbook):
    wb = Workbook()
    for i, ws in enumerate(wb):
        pass
    assert i == 0
    assert ws.title == "Sheet"

def test_get_index():
    wb = Workbook()
    new_sheet = wb.create_sheet(0)
    sheet_index = wb.get_index(new_sheet)
    assert sheet_index == 0


def test_get_sheet_names():
    wb = Workbook()
    names = ['Sheet', 'Sheet1', 'Sheet2', 'Sheet3', 'Sheet4', 'Sheet5']
    for count in range(5):
        wb.create_sheet(0)
    actual_names = wb.get_sheet_names()
    assert sorted(actual_names) == sorted(names)


def test_get_named_ranges():
    wb = Workbook()
    assert wb.get_named_ranges() == wb._named_ranges


def test_add_named_range():
    wb = Workbook()
    new_sheet = wb.create_sheet()
    named_range = NamedRange('test_nr', [(new_sheet, 'A1')])
    wb.add_named_range(named_range)
    named_ranges_list = wb.get_named_ranges()
    assert named_range in named_ranges_list


def test_get_named_range():
    wb = Workbook()
    new_sheet = wb.create_sheet()
    named_range = NamedRange('test_nr', [(new_sheet, 'A1')])
    wb.add_named_range(named_range)
    found_named_range = wb.get_named_range('test_nr')
    assert named_range == found_named_range


def test_remove_named_range():
    wb = Workbook()
    new_sheet = wb.create_sheet()
    named_range = NamedRange('test_nr', [(new_sheet, 'A1')])
    wb.add_named_range(named_range)
    wb.remove_named_range(named_range)
    named_ranges_list = wb.get_named_ranges()
    assert named_range not in named_ranges_list

def test_add_local_named_range(tmpdir):
    tmpdir.chdir()
    wb = Workbook()
    new_sheet = wb.create_sheet()
    named_range = NamedRange('test_nr', [(new_sheet, 'A1')])
    named_range.scope = new_sheet
    wb.add_named_range(named_range)
    dest_filename = 'local_named_range_book.xlsx'
    wb.save(dest_filename)


def test_write_regular_date(tmpdir):
    tmpdir.chdir()
    today = datetime.datetime(2010, 1, 18, 14, 15, 20, 1600)
    book = Workbook()
    sheet = book.get_active_sheet()
    sheet.cell("A1").value = today
    dest_filename = 'date_read_write_issue.xlsx'
    book.save(dest_filename)

    validate_archive(dest_filename)
    test_book = load_workbook(dest_filename)
    test_sheet = test_book.get_active_sheet()

    assert test_sheet.cell("A1").value == today

def test_write_regular_float(tmpdir):
    float_value = 1.0 / 3.0
    book = Workbook()
    sheet = book.get_active_sheet()
    sheet.cell("A1").value = float_value
    dest_filename = 'float_read_write_issue.xlsx'
    book.save(dest_filename)

    validate_archive(dest_filename)
    test_book = load_workbook(dest_filename)
    test_sheet = test_book.get_active_sheet()

    assert test_sheet.cell("A1").value == float_value


class AlternativeWorksheet(object):
    def __init__(self, parent_workbook, title=None):
        self.parent_workbook = parent_workbook
        if not title:
            title = 'AlternativeSheet'
        self.title = title


def test_worksheet_class():
    wb = Workbook(worksheet_class=AlternativeWorksheet)
    assert isinstance(wb.worksheets[0], AlternativeWorksheet)


def test_add_invalid_worksheet_class_instance():
    wb = Workbook()
    ws = AlternativeWorksheet(parent_workbook=wb)
    with pytest.raises(TypeError):
        wb._add_sheet(worksheet=ws)
