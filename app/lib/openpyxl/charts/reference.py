from __future__ import absolute_import
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

from openpyxl.cell import get_column_letter
from openpyxl.styles import NumberFormat, is_date_format, is_builtin
from openpyxl.descriptors import Tuple, Set, Strict


class Reference(Strict):
    """ a simple wrapper around a serie of reference data """

    data_type = Set(values=['n', 's', None])
    pos1 = Tuple()
    pos2 = Tuple(allow_none=True)

    def __init__(self, sheet, pos1, pos2=None, data_type=None, number_format=None):
        """Create a reference to a cell or range of cells

        :param sheet: the worksheet referred to
        :type sheet: string

        :type pos1: cell coordinate
        :type pos1: tuple

        :param pos2: optional second coordinate for a range
        :type row: tuple

        :param data_type: optionally specify the data type
        :type data_type: string

        :param number_format: optional formatting style
        :type number_format: string

        """

        self.sheet = sheet
        self.pos1 = pos1
        self.pos2 = pos2
        self.data_type = data_type
        self.number_format = number_format

    @property
    def number_format(self):
        return self._number_format

    @number_format.setter
    def number_format(self, value):
        if value is not None:
            if not is_builtin(value):
                raise ValueError("Invalid number format")
        self._number_format = value

    @property
    def values(self):
        """ read data in sheet - to be used at writing time """
        if hasattr(self, "_values"):
            return self._values
        if self.pos2 is None:
            cell = self.sheet.cell(row=self.pos1[0], column=self.pos1[1])
            self.data_type = cell.data_type
            self._values = [cell.internal_value]
        else:
            self._values = []

            for row in range(int(self.pos1[0]), int(self.pos2[0] + 1)):
                for col in range(int(self.pos1[1]), int(self.pos2[1] + 1)):
                    cell = self.sheet.cell(row=row, column=col)
                    self._values.append(cell.internal_value)
                    if cell.internal_value == '':
                        continue
                    if self.data_type is None and cell.data_type:
                        self.data_type = cell.data_type
        return self._values

    def __str__(self):
        """ format excel reference notation """

        if self.pos2 is not None:
            return "'%s'!$%s$%s:$%s$%s" % (self.sheet.title,
                get_column_letter(self.pos1[1]), self.pos1[0],
                get_column_letter(self.pos2[1]), self.pos2[0])
        else:
            return "'%s'!$%s$%s" % (self.sheet.title,
                get_column_letter(self.pos1[1]), self.pos1[0])
