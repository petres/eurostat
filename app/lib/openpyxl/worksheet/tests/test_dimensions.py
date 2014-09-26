from __future__ import absolute_import
# Copyright (c) 2010-2014 openpyxl

import pytest

from openpyxl.collections import IndexedList

def test_invalid_dimension_ctor():
    from .. dimensions import Dimension
    with pytest.raises(TypeError):
        Dimension()

class DummyWorkbook:

    def __init__(self):
        self.shared_styles = IndexedList()

    def get_sheet_names(self):
        return []


class DummyWorksheet:

    def __init__(self):
        self.parent = DummyWorkbook()


def test_dimension():
    from .. dimensions import Dimension
    with pytest.raises(TypeError):
        Dimension()


def test_dimension_interface():
    from .. dimensions import Dimension
    d = Dimension(1, True, 1, False, None)
    assert d.worksheet is None
    assert dict(d) == {'hidden': '1', 'outlineLevel': '1'}


@pytest.mark.parametrize("key, value, expected",
                         [
                             ('ht', 1, {'ht':'1', 'customHeight':'1'}),
                             ('_style', 10, {'s':'10', 'customFormat':'1'}),
                         ]
                         )
def test_row_dimension(key, value, expected):
    from .. dimensions import RowDimension
    rd = RowDimension(worksheet=DummyWorksheet())
    setattr(rd, key, value)
    assert dict(rd) == expected


@pytest.mark.parametrize("key, value, expected",
                         [
                             ('width', 1, {'width':'1', 'customWidth':'1'}),
                             ('bestFit', True, {'bestFit':'1'}),
                         ]
                         )
def test_col_dimensions(key, value, expected):
    from .. dimensions import ColumnDimension
    cd = ColumnDimension()
    setattr(cd, key, value)
    assert dict(cd) == expected

def test_group_columns_simple():
    from ..worksheet import Worksheet
    ws = Worksheet(parent_workbook=DummyWorkbook())
    dims = ws.column_dimensions
    dims.group('A', 'C', 1)
    assert len(dims) == 1
    group = list(dims.values())[0]
    assert group.outline_level == 1
    assert group.min == 1
    assert group.max == 3


def test_group_columns_collapse():
    from ..worksheet import Worksheet
    ws = Worksheet(parent_workbook=DummyWorkbook())
    dims = ws.column_dimensions
    dims.group('A', 'C', 1, hidden=True)
    group = list(dims.values())[0]
    assert group.hidden
