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

"""Read in global settings to be maintained by the workbook object."""

# package imports
from openpyxl.xml.functions import fromstring, safe_iterator
from openpyxl.xml.constants import (
    DCORE_NS,
    COREPROPS_NS,
    DCTERMS_NS,
    SHEET_MAIN_NS,
    CONTYPES_NS,
    PACKAGE_XL,
    PKG_REL_NS,
    REL_NS,
    ARC_CONTENT_TYPES,
    ARC_WORKBOOK,
    ARC_WORKBOOK_RELS,
)
from openpyxl.workbook import DocumentProperties
from openpyxl.date_time import (
    W3CDTF_to_datetime,
    CALENDAR_WINDOWS_1900,
    CALENDAR_MAC_1904
    )
from openpyxl.namedrange import (
    NamedRange,
    NamedRangeContainingValue,
    split_named_range,
    refers_to_range
    )

import os
import datetime
import re

# constants
BUGGY_NAMED_RANGES = re.compile("|".join(['NA()', '#REF!']))
DISCARDED_RANGES = re.compile("|".join(['Excel_BuiltIn', 'Print_Area']))
VALID_WORKSHEET = "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"


def read_properties_core(xml_source):
    """Read assorted file properties."""
    properties = DocumentProperties()
    root = fromstring(xml_source)
    properties.creator = root.findtext('{%s}creator' % DCORE_NS, '')
    properties.last_modified_by = root.findtext('{%s}lastModifiedBy' % COREPROPS_NS, '')

    created_node = root.find('{%s}created' % DCTERMS_NS)
    if created_node is not None:
        properties.created = W3CDTF_to_datetime(created_node.text)
    else:
        properties.created = datetime.datetime.now()

    modified_node = root.find('{%s}modified' % DCTERMS_NS)
    if modified_node is not None:
        properties.modified = W3CDTF_to_datetime(modified_node.text)
    else:
        properties.modified = properties.created

    return properties


def read_excel_base_date(xml_source):
    root = fromstring(text = xml_source)
    wbPr = root.find('{%s}workbookPr' % SHEET_MAIN_NS)
    if wbPr is not None and wbPr.get('date1904') in ('1', 'true'):
        return CALENDAR_MAC_1904
    return CALENDAR_WINDOWS_1900


def read_content_types(archive):
    """Read content types."""
    xml_source = archive.read(ARC_CONTENT_TYPES)
    root = fromstring(xml_source)
    contents_root = root.findall('{%s}Override' % CONTYPES_NS)
    for type in contents_root:
        yield type.get('PartName'), type.get('ContentType')


def read_rels(archive):
    """Read relationships for a workbook"""
    xml_source = archive.read(ARC_WORKBOOK_RELS)
    tree = fromstring(xml_source)
    for element in safe_iterator(tree, '{%s}Relationship' % PKG_REL_NS):
        rId = element.get('Id')
        pth = element.get("Target")
        # normalise path
        if pth.startswith("/xl"):
            pth = pth.replace("/xl", "xl")
        elif not pth.startswith("xl") and not pth.startswith(".."):
            pth = "xl/" + pth
        yield rId, {'path':pth}


def read_sheets(archive):
    """Read worksheet titles and ids for a workbook"""
    xml_source = archive.read(ARC_WORKBOOK)
    tree = fromstring(xml_source)
    for element in safe_iterator(tree, '{%s}sheet' % SHEET_MAIN_NS):
        rId = element.get("{%s}id" % REL_NS)
        yield rId, element.get('name')


def detect_worksheets(archive):
    """Return a list of worksheets"""
    # content types has a list of paths but no titles
    # workbook has a list of titles and relIds but no paths
    # workbook_rels has a list of relIds and paths but no titles
    # rels = {'id':{'title':'', 'path':''} }
    from openpyxl.reader.workbook import read_rels, read_sheets
    content_types = read_content_types(archive)
    valid_sheets = dict((path, ct) for path, ct in content_types if ct == VALID_WORKSHEET)
    rels = dict(read_rels(archive))
    for rId, title in read_sheets(archive):
        rel = rels[rId]
        rel['title'] = title
        if "/" + rel['path'] in valid_sheets:
            yield rel


def read_named_ranges(xml_source, workbook):
    """Read named ranges, excluding poorly defined ranges."""
    root = fromstring(xml_source)
    names_root = root.find('{%s}definedNames' %SHEET_MAIN_NS)
    existing_sheets = workbook.get_sheet_names()
    if names_root is not None:
        for name_node in names_root:
            range_name = name_node.get('name')
            node_text = name_node.text or ''
            if bool(name_node.get("hidden", False)):
                continue

            if DISCARDED_RANGES.search(range_name) or BUGGY_NAMED_RANGES.search(range_name):
                continue

            if refers_to_range(node_text):
                destinations = split_named_range(node_text)

                new_destinations = []
                for worksheet_name, cells_range in destinations:
                    # it can happen that a valid named range references
                    # a missing worksheet, when Excel didn't properly maintain
                    # the named range list
                    #
                    # we just ignore them here
                    if worksheet_name in existing_sheets:
                        worksheet = workbook[worksheet_name]
                        new_destinations.append((worksheet, cells_range))
                if not new_destinations:
                    continue
                named_range = NamedRange(range_name, new_destinations)
            else:
                named_range = NamedRangeContainingValue(range_name, node_text)

            location_id = name_node.get("localSheetId")
            if location_id:
                named_range.scope = workbook.worksheets[int(location_id)]
            yield named_range
