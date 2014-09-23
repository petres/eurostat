from __future__ import absolute_import
# Copyright (c) 2010-2014 openpyxl

"""Read in global settings to be maintained by the workbook object."""

# package imports
from openpyxl.xml.functions import fromstring, safe_iterator
from openpyxl.xml.constants import (
    DCORE_NS,
    COREPROPS_NS,
    DCTERMS_NS,
    SHEET_MAIN_NS,
    CONTYPES_NS,
    PKG_REL_NS,
    REL_NS,
    ARC_CONTENT_TYPES,
    ARC_WORKBOOK,
    ARC_WORKBOOK_RELS,
    WORKSHEET,
    EXTERNAL_LINK,
)
from openpyxl.workbook import DocumentProperties
from openpyxl.date_time import (
    W3CDTF_to_datetime,
    CALENDAR_WINDOWS_1900,
    CALENDAR_MAC_1904
    )
from openpyxl.workbook.names.named_range import (
    NamedRange,
    NamedValue,
    split_named_range,
    refers_to_range,
    external_range,
    )

import datetime
import re

# constants
BUGGY_NAMED_RANGES = re.compile("|".join(['NA()', '#REF!']))
DISCARDED_RANGES = re.compile("|".join(['Excel_BuiltIn', 'Print_Area']))
VALID_WORKSHEET = WORKSHEET


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
        yield type.get('ContentType'), type.get('PartName')


def read_rels(archive):
    """Read relationships for a workbook"""
    xml_source = archive.read(ARC_WORKBOOK_RELS)
    tree = fromstring(xml_source)
    for element in safe_iterator(tree, '{%s}Relationship' % PKG_REL_NS):
        rId = element.get('Id')
        pth = element.get("Target")
        typ = element.get('Type')
        # normalise path
        if pth.startswith("/xl"):
            pth = pth.replace("/xl", "xl")
        elif not pth.startswith("xl") and not pth.startswith(".."):
            pth = "xl/" + pth
        yield rId, {'path':pth, 'type':typ}


def read_sheets(archive):
    """Read worksheet titles and ids for a workbook"""
    xml_source = archive.read(ARC_WORKBOOK)
    tree = fromstring(xml_source)
    for element in safe_iterator(tree, '{%s}sheet' % SHEET_MAIN_NS):
        rId = element.get("{%s}id" % REL_NS)
        yield rId, element.get('name'), element.get('state')


def detect_worksheets(archive):
    """Return a list of worksheets"""
    # content types has a list of paths but no titles
    # workbook has a list of titles and relIds but no paths
    # workbook_rels has a list of relIds and paths but no titles
    # rels = {'id':{'title':'', 'path':''} }
    content_types = read_content_types(archive)
    valid_sheets = dict((path, ct) for ct, path in content_types if ct == VALID_WORKSHEET)
    rels = dict(read_rels(archive))
    for rId, title, state in read_sheets(archive):
        rel = rels[rId]
        rel['title'] = title
        if state is not None:
            rel['state'] = state
        if ("/" + rel['path'] in valid_sheets
            or "worksheets" in rel['path']): # fallback in case content type is missing
            yield rel


def read_named_ranges(xml_source, workbook):
    """Read named ranges, excluding poorly defined ranges."""
    sheetnames = set(sheet.title for sheet in workbook.worksheets)
    root = fromstring(xml_source)
    for name_node in safe_iterator(root, '{%s}definedName' %SHEET_MAIN_NS):

        range_name = name_node.get('name')
        if DISCARDED_RANGES.search(range_name) or BUGGY_NAMED_RANGES.search(range_name):
            continue

        node_text = name_node.text

        if external_range(node_text):
            # treat names referring to external workbooks as values
            named_range = NamedValue(range_name, node_text)

        elif refers_to_range(node_text):
            destinations = split_named_range(node_text)
            # it can happen that a valid named range references
            # a missing worksheet, when Excel didn't properly maintain
            # the named range list
            destinations = [(workbook[sheet], cells) for sheet, cells in destinations
                            if sheet in sheetnames]
            if not destinations:
                continue
            named_range = NamedRange(range_name, destinations)
        else:
            named_range = NamedValue(range_name, node_text)


        location_id = name_node.get("localSheetId")
        if location_id is not None:
            named_range.scope = workbook.worksheets[int(location_id)]

        yield named_range


def detect_external_links(archive):
    rels = read_rels(archive)
    for rId, d in rels:
        if d['type'] == EXTERNAL_LINK:
            pth = d['path']
