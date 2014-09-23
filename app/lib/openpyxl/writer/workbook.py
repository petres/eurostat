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

"""Write the workbook global settings to the archive."""

from functools import partial

# package imports

from openpyxl import LXML
from openpyxl.xml.functions import Element, SubElement
from openpyxl.cell import absolute_coordinate
from openpyxl.xml.constants import (
    ARC_CORE,
    ARC_WORKBOOK,
    ARC_APP,
    ARC_THEME,
    ARC_STYLE,
    ARC_SHARED_STRINGS,
    COREPROPS_NS,
    VTYPES_NS,
    XPROPS_NS,
    DCORE_NS,
    DCTERMS_NS,
    DCTERMS_PREFIX,
    XSI_NS,
    SHEET_MAIN_NS,
    CONTYPES_NS,
    PKG_REL_NS,
    CUSTOMUI_NS,
    REL_NS,
    ARC_CUSTOM_UI,
    ARC_CONTENT_TYPES,
    ARC_ROOT_RELS,
    EXTERNAL_LINK,
)
from openpyxl.xml.functions import tostring, fromstring
from openpyxl.date_time import datetime_to_W3CDTF
from openpyxl.worksheet import Worksheet
from openpyxl.workbook.names.named_range import NamedRange, NamedValue


def write_properties_core(properties):
    """Write the core properties to xml."""
    root = Element('{%s}coreProperties' % COREPROPS_NS)
    SubElement(root, '{%s}creator' % DCORE_NS).text = properties.creator
    SubElement(root, '{%s}lastModifiedBy' % COREPROPS_NS).text = properties.last_modified_by
    SubElement(root, '{%s}created' % DCTERMS_NS,
               {'{%s}type' % XSI_NS: '%s:W3CDTF' % DCTERMS_PREFIX}).text = \
                   datetime_to_W3CDTF(properties.created)
    SubElement(root, '{%s}modified' % DCTERMS_NS,
               {'{%s}type' % XSI_NS: '%s:W3CDTF' % DCTERMS_PREFIX}).text = \
                   datetime_to_W3CDTF(properties.modified)
    SubElement(root, '{%s}title' % DCORE_NS).text = properties.title
    SubElement(root, '{%s}description' % DCORE_NS).text = properties.description
    SubElement(root, '{%s}subject' % DCORE_NS).text = properties.subject
    SubElement(root, '{%s}keywords' % COREPROPS_NS).text = properties.keywords
    SubElement(root, '{%s}category' % COREPROPS_NS).text = properties.category
    return tostring(root)


static_content_types_config = [
    ('Override', ARC_THEME, 'application/vnd.openxmlformats-officedocument.theme+xml'),
    ('Override', ARC_STYLE, 'application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml'),

    ('Default', 'rels', 'application/vnd.openxmlformats-package.relationships+xml'),
    ('Default', 'xml', 'application/xml'),
    ('Default', 'png', 'image/png'),
    ('Default', 'vml', 'application/vnd.openxmlformats-officedocument.vmlDrawing'),

    ('Override', ARC_WORKBOOK,
     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml'),
    ('Override', ARC_APP,
     'application/vnd.openxmlformats-officedocument.extended-properties+xml'),
    ('Override', ARC_CORE,
     'application/vnd.openxmlformats-package.core-properties+xml'),
    ('Override', ARC_SHARED_STRINGS,
     'application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml'),
]


def write_content_types(workbook):
    """Write the content-types xml."""
    seen = set()
    if workbook.vba_archive:
        root = fromstring(workbook.vba_archive.read(ARC_CONTENT_TYPES))
        for elem in root.findall('{%s}Override' % CONTYPES_NS):
            seen.add(elem.attrib['PartName'])
        for elem in root.findall('{%s}Default' % CONTYPES_NS):
            seen.add(elem.attrib['Extension'])
    else:
        if LXML:
            NSMAP = {None : CONTYPES_NS}
            root = Element('{%s}Types' % CONTYPES_NS, nsmap=NSMAP)
        else:
            root = Element('{%s}Types' % CONTYPES_NS)
    for setting_type, name, content_type in static_content_types_config:
        attrib = {'ContentType': content_type}
        if setting_type == 'Override':
            if '/' + name not in seen:
                tag = '{%s}Override' % CONTYPES_NS
                attrib['PartName'] = '/' + name
                SubElement(root, tag, attrib)
        else:
            if name not in seen:
                tag = '{%s}Default' % CONTYPES_NS
                attrib['Extension'] =  name
                SubElement(root, tag, attrib)

    drawing_id = 1
    chart_id = 1
    comments_id = 1

    for sheet_id, sheet in enumerate(workbook.worksheets):
        name = '/xl/worksheets/sheet%d.xml' % (sheet_id + 1)
        if name not in seen:
            SubElement(root, '{%s}Override' % CONTYPES_NS, {'PartName': name,
                'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'})
        if sheet._charts or sheet._images:
            name = '/xl/drawings/drawing%d.xml' % drawing_id
            if name not in seen:
                SubElement(root, '{%s}Override' % CONTYPES_NS, {'PartName' : name,
                'ContentType' : 'application/vnd.openxmlformats-officedocument.drawing+xml'})
            drawing_id += 1

            for chart in sheet._charts:
                name = '/xl/charts/chart%d.xml' % chart_id
                if name not in seen:
                    SubElement(root, '{%s}Override' % CONTYPES_NS, {'PartName' : name,
                    'ContentType' : 'application/vnd.openxmlformats-officedocument.drawingml.chart+xml'})
                chart_id += 1
                if chart._shapes:
                    name = '/xl/drawings/drawing%d.xml' % drawing_id
                    if name not in seen:
                        SubElement(root, '{%s}Override' % CONTYPES_NS, {'PartName' : name,
                        'ContentType' : 'application/vnd.openxmlformats-officedocument.drawingml.chartshapes+xml'})
                    drawing_id += 1
        if sheet._comment_count > 0:
            SubElement(root, '{%s}Override' % CONTYPES_NS,
                {'PartName': '/xl/comments%d.xml' % comments_id,
                 'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml'})
            comments_id += 1

    for idx, _ in enumerate(workbook._external_links, 1):
        el = Element('{%s}Override' % CONTYPES_NS,
                     {'PartName':'/xl/externalLinks/externalLink{0}.xml'.format(idx),
                      'ContentType': EXTERNAL_LINK})
        root.append(el)

    return tostring(root)


def write_properties_app(workbook):
    """Write the properties xml."""
    worksheets_count = len(workbook.worksheets)
    root = Element('{%s}Properties' % XPROPS_NS)
    SubElement(root, '{%s}Application' % XPROPS_NS).text = 'Microsoft Excel'
    SubElement(root, '{%s}DocSecurity' % XPROPS_NS).text = '0'
    SubElement(root, '{%s}ScaleCrop' % XPROPS_NS).text = 'false'
    SubElement(root, '{%s}Company' % XPROPS_NS)
    SubElement(root, '{%s}LinksUpToDate' % XPROPS_NS).text = 'false'
    SubElement(root, '{%s}SharedDoc' % XPROPS_NS).text = 'false'
    SubElement(root, '{%s}HyperlinksChanged' % XPROPS_NS).text = 'false'
    SubElement(root, '{%s}AppVersion' % XPROPS_NS).text = '12.0000'

    # heading pairs part
    heading_pairs = SubElement(root, '{%s}HeadingPairs' % XPROPS_NS)
    vector = SubElement(heading_pairs, '{%s}vector' % VTYPES_NS,
            {'size': '2', 'baseType': 'variant'})
    variant = SubElement(vector, '{%s}variant' % VTYPES_NS)
    SubElement(variant, '{%s}lpstr' % VTYPES_NS).text = 'Worksheets'
    variant = SubElement(vector, '{%s}variant' % VTYPES_NS)
    SubElement(variant, '{%s}i4' % VTYPES_NS).text = '%d' % worksheets_count

    # title of parts
    title_of_parts = SubElement(root, '{%s}TitlesOfParts' % XPROPS_NS)
    vector = SubElement(title_of_parts, '{%s}vector' % VTYPES_NS,
            {'size': '%d' % worksheets_count, 'baseType': 'lpstr'})
    for ws in workbook.worksheets:
        SubElement(vector, '{%s}lpstr' % VTYPES_NS).text = '%s' % ws.title
    return tostring(root)


def write_root_rels(workbook):
    """Write the relationships xml."""
    root = Element('{%s}Relationships' % PKG_REL_NS)
    relation_tag = '{%s}Relationship' % PKG_REL_NS
    SubElement(root, relation_tag, {'Id': 'rId1', 'Target': ARC_WORKBOOK,
            'Type': '%s/officeDocument' % REL_NS})
    SubElement(root, relation_tag, {'Id': 'rId2', 'Target': ARC_CORE,
            'Type': '%s/metadata/core-properties' % PKG_REL_NS})
    SubElement(root, relation_tag, {'Id': 'rId3', 'Target': ARC_APP,
            'Type': '%s/extended-properties' % REL_NS})
    if workbook.vba_archive is not None:
        # See if there was a customUI relation and reuse its id
        arc = fromstring(workbook.vba_archive.read(ARC_ROOT_RELS))
        rels = arc.findall(relation_tag)
        rId = None
        for rel in rels:
                if rel.get('Target') == ARC_CUSTOM_UI:
                        rId = rel.get('Id')
                        break
        if rId is not None:
            SubElement(root, relation_tag, {'Id': rId, 'Target': ARC_CUSTOM_UI,
                'Type': '%s' % CUSTOMUI_NS})
    return tostring(root)


def write_workbook(workbook):
    """Write the core workbook xml."""
    root = Element('{%s}workbook' % SHEET_MAIN_NS)
    SubElement(root, '{%s}fileVersion' % SHEET_MAIN_NS,
               {'appName': 'xl', 'lastEdited': '4', 'lowestEdited': '4', 'rupBuild': '4505'})
    SubElement(root, '{%s}workbookPr' % SHEET_MAIN_NS,
               {'defaultThemeVersion': '124226', 'codeName': 'ThisWorkbook'})

    # book views
    book_views = SubElement(root, '{%s}bookViews' % SHEET_MAIN_NS)
    SubElement(book_views, '{%s}workbookView' % SHEET_MAIN_NS,
               {'activeTab': '%d' % workbook.get_index(workbook.get_active_sheet()),
                'autoFilterDateGrouping': '1', 'firstSheet': '0', 'minimized': '0',
                'showHorizontalScroll': '1', 'showSheetTabs': '1',
                'showVerticalScroll': '1', 'tabRatio': '600',
                'visibility': 'visible'})

    # worksheets
    sheets = SubElement(root, '{%s}sheets' % SHEET_MAIN_NS)
    for i, sheet in enumerate(workbook.worksheets, 1):
        sheet_node = SubElement(
            sheets, '{%s}sheet' % SHEET_MAIN_NS,
            {'name': sheet.title, 'sheetId': '%d' % i,
             '{%s}id' % REL_NS: 'rId%d' % i })
        if not sheet.sheet_state == Worksheet.SHEETSTATE_VISIBLE:
            if len(workbook.worksheets) == 1:
                raise ValueError("The only worksheet of a workbook cannot be hidden")
            sheet_node.set('state', sheet.sheet_state)

    # external references
    if getattr(workbook, '_external_links', []):
        external_references = SubElement(root, '{%s}externalReferences' % SHEET_MAIN_NS)
        # need to match a counter with a workbook's relations
        counter = len(workbook.worksheets) + 3 # strings, styles, theme
        if workbook.vba_archive:
            counter += 1
        for idx, _ in enumerate(workbook._external_links, counter+1):
            ext = Element("{%s}externalReference" % SHEET_MAIN_NS, {"{%s}id" % REL_NS:"rId%d" % idx})
            external_references.append(ext)

    # Defined names
    defined_names = SubElement(root, '{%s}definedNames' % SHEET_MAIN_NS)
    _write_defined_names(workbook, defined_names)

    # Defined names -> autoFilter
    for i, sheet in enumerate(workbook.worksheets):
        auto_filter = sheet.auto_filter.ref
        if not auto_filter:
            continue
        name = SubElement(
            defined_names, '{%s}definedName' % SHEET_MAIN_NS,
            dict(name='_xlnm._FilterDatabase', localSheetId=str(i), hidden='1'))
        name.text = "'%s'!%s" % (sheet.title.replace("'", "''"),
                                 absolute_coordinate(auto_filter))

    SubElement(root, '{%s}calcPr' % SHEET_MAIN_NS,
               {'calcId': '124519', 'calcMode': 'auto', 'fullCalcOnLoad': '1'})
    return tostring(root)


def _write_defined_names(workbook, names):
    """
    Append definedName elements to the definedNames node.
    """
    for named_range in workbook.get_named_ranges():
        attrs = dict(named_range)
        if named_range.scope is not None:
            attrs['localSheetId'] = '%d' % workbook.get_index(named_range.scope)

        name = Element('{%s}definedName' % SHEET_MAIN_NS, attrs)
        name.text = named_range.value
        names.append(name)


RelationElement = partial(Element, '{%s}Relationship' % PKG_REL_NS)


def write_workbook_rels(workbook):
    """Write the workbook relationships xml."""
    root = Element('{%s}Relationships' % PKG_REL_NS)

    for i, _ in enumerate(workbook.worksheets, 1):
        attrs = {'Id': 'rId%d' % i, 'Target': 'worksheets/sheet%s.xml' % i,
                 'Type': '%s/worksheet' % REL_NS}
        root.append(RelationElement(attrs))

    i += 1
    attrs = {'Id': 'rId%d' % i, 'Target': 'sharedStrings.xml',
             'Type': '%s/sharedStrings' % REL_NS}
    root.append(RelationElement(attrs))

    i += 1
    attrs = {'Id': 'rId%d' % i, 'Target': 'styles.xml',
             'Type': '%s/styles' % REL_NS}
    root.append(RelationElement(attrs))

    i += 1
    attrs = {'Id': 'rId%d' % i, 'Target': 'theme/theme1.xml',
             'Type': '%s/theme' % REL_NS}
    root.append(RelationElement(attrs))

    if workbook.vba_archive:
        i += 1
        attrs = {'Id': 'rId%d' % i, 'Target': 'vbaProject.bin',
                 'Type': 'http://schemas.microsoft.com/office/2006/relationships/vbaProject'}
        root.append(RelationElement(attrs))

    external_links = workbook._external_links
    if external_links:
        for idx, link in enumerate(external_links, 1):
            attrs = {'Id':'rId%d' % (i + idx), 'Target':'externalLinks/externalLink%d.xml' % idx,
                     'Type':'%s/externalLink' % REL_NS}
            root.append(RelationElement(attrs))

    return tostring(root)
