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

from openpyxl.descriptors import Set, Float, Bool, Integer

from .hashable import HashableObject

HORIZONTAL_GENERAL = 'general'
HORIZONTAL_LEFT = 'left'
HORIZONTAL_RIGHT = 'right'
HORIZONTAL_CENTER = 'center'
HORIZONTAL_CENTER_CONTINUOUS = 'centerContinuous'
HORIZONTAL_JUSTIFY = 'justify'
VERTICAL_BOTTOM = 'bottom'
VERTICAL_TOP = 'top'
VERTICAL_CENTER = 'center'
VERTICAL_JUSTIFY = 'justify'

alignments = (HORIZONTAL_GENERAL, HORIZONTAL_LEFT, HORIZONTAL_RIGHT,
              HORIZONTAL_CENTER, HORIZONTAL_CENTER_CONTINUOUS, HORIZONTAL_JUSTIFY,
              VERTICAL_BOTTOM, VERTICAL_TOP, VERTICAL_CENTER, VERTICAL_JUSTIFY)


class Alignment(HashableObject):
    """Alignment options for use in styles."""

    __fields__ = ('horizontal',
                  'vertical',
                  'text_rotation',
                  'wrap_text',
                  'shrink_to_fit',
                  'indent')
    horizontal = Set(values=alignments)
    vertical = Set(values=alignments)
    text_rotation = Integer()
    wrap_text = Bool()
    shrink_to_fit = Bool()
    indent = Integer()

    def __init__(self, horizontal=HORIZONTAL_GENERAL, vertical=VERTICAL_BOTTOM,
                 text_rotation=0, wrap_text=False, shrink_to_fit=False,
                 indent=0):
        self.horizontal = horizontal
        self.vertical = vertical
        self.text_rotation = text_rotation
        self.wrap_text = wrap_text
        self.shrink_to_fit = shrink_to_fit
        self.indent = indent
