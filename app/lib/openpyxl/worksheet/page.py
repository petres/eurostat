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


from openpyxl.compat import OrderedDict, safe_string
from openpyxl.descriptors import Strict, Float


class PageSetup(object):
    """Information about page layout for this sheet"""
    valid_setup = ("orientation", "paperSize", "scale", "fitToPage",
                   "fitToHeight", "fitToWidth", "firstPageNumber", "useFirstPageNumber")
    valid_options = ("horizontalCentered", "verticalCentered")
    orientation = None
    paperSize = None
    scale = None
    fitToPage = None
    fitToHeight = None
    fitToWidth = None
    firstPageNumber = None
    useFirstPageNumber = None
    horizontalCentered = None
    verticalCentered = None

    @property
    def setup(self):
        setupGroup = OrderedDict()
        for setup_name in self.valid_setup:
            setup_value = getattr(self, setup_name)
            if setup_value is not None:
                if setup_name == 'orientation':
                    setupGroup[setup_name] = '%s' % setup_value
                elif setup_name in ('paperSize', 'scale'):
                    setupGroup[setup_name] = '%d' % int(setup_value)
                elif setup_name in ('fitToHeight', 'fitToWidth') and int(setup_value) >= 0:
                    setupGroup[setup_name] = '%d' % int(setup_value)

        return setupGroup

    @property
    def options(self):
        optionsGroup = OrderedDict()
        for options_name in self.valid_options:
            options_value = getattr(self, options_name)
            if options_value is not None:
                optionsGroup[options_name] = '1'

        return optionsGroup


class PageMargins(Strict):
    """
    Information about page margins for view/print layouts.
    Standard values (in inches)
    left, right = 0.75
    top, bottom = 1
    header, footer = 0.5
    """

    left = Float()
    right = Float()
    top = Float()
    bottom = Float()
    header = Float()
    footer = Float()

    def __init__(self, left=0.75, right=0.75, top=1, bottom=1, header=0.5, footer=0.5):
        self.left = left
        self.right = right
        self.top = top
        self.bottom =  bottom
        self.header = header
        self.footer = footer

    def __iter__(self):
        for key in ("left", "right", "top", "bottom", "header", "footer"):
            value = getattr(self, key)
            yield key, safe_string(value)
