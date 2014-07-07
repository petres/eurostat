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

"""Write worksheets to xml representations."""

# Python stdlib imports
import decimal
from io import BytesIO

# compatibility imports

from openpyxl.compat import long

# package imports
from openpyxl.cell import (
    coordinate_from_string,
    column_index_from_string,
    COORD_RE
)
from openpyxl.xml.functions import (
    Element,
    SubElement,
    XMLGenerator,
    get_document_content,
    start_tag,
    end_tag,
    tag,
    fromstring,
)
from openpyxl.xml.constants import (
    SHEET_MAIN_NS,
    PKG_REL_NS,
    REL_NS,
    COMMENTS_NS,
    VML_NS
)
from openpyxl.compat.itertools import iteritems, iterkeys
from openpyxl.formatting import ConditionalFormatting


def row_sort(cell):
    """Translate column names for sorting."""
    return column_index_from_string(cell.column)


def write_etree(doc, element):
    start_tag(doc, element.tag, element)
    for e in element.getchildren():
        write_etree(doc, e)
    end_tag(doc, element.tag)


def write_worksheet(worksheet, shared_strings, style_table):
    """Write a worksheet to an xml file."""
    if worksheet.xml_source:
        vba_root = fromstring(worksheet.xml_source)
    else:
        vba_root = None
    xml_file = BytesIO()
    doc = XMLGenerator(out=xml_file)
    start_tag(doc, 'worksheet',
              {'xmlns': SHEET_MAIN_NS,
               'xmlns:r': REL_NS})
    if vba_root is not None:
        el = vba_root.find('{%s}sheetPr' % SHEET_MAIN_NS)
        if el is not None:
            codename = el.get('codeName', worksheet.title)
            start_tag(doc, 'sheetPr', {"codeName": codename})
        else:
            start_tag(doc, 'sheetPr')
    else:
        start_tag(doc, 'sheetPr')
    tag(doc, 'outlinePr',
        {'summaryBelow': '%d' % (worksheet.show_summary_below),
         'summaryRight': '%d' % (worksheet.show_summary_right)})
    if worksheet.page_setup.fitToPage:
        tag(doc, 'pageSetUpPr', {'fitToPage': '1'})
    end_tag(doc, 'sheetPr')
    tag(doc, 'dimension', {'ref': '%s' % worksheet.calculate_dimension()})
    write_worksheet_sheetviews(doc, worksheet)
    tag(doc, 'sheetFormatPr', {'defaultRowHeight': '15', 'baseColWidth':'10'})
    write_worksheet_cols(doc, worksheet, style_table)
    write_worksheet_data(doc, worksheet, shared_strings, style_table)
    if worksheet.protection.enabled:
        tag(doc, 'sheetProtection',
            {'objects': '1', 'scenarios': '1', 'sheet': '1'})
    write_worksheet_autofilter(doc, worksheet)
    write_worksheet_mergecells(doc, worksheet)
    write_worksheet_conditional_formatting(doc, worksheet)
    write_worksheet_datavalidations(doc, worksheet)
    write_worksheet_hyperlinks(doc, worksheet)

    options = worksheet.page_setup.options
    if options:
        tag(doc, 'printOptions', options)

    tag(doc, 'pageMargins', dict(worksheet.page_margins))

    setup = worksheet.page_setup.setup
    if setup:
        tag(doc, 'pageSetup', setup)

    if worksheet.header_footer.hasHeader() or worksheet.header_footer.hasFooter():
        start_tag(doc, 'headerFooter')
        if worksheet.header_footer.hasHeader():
            tag(doc, 'oddHeader', None, worksheet.header_footer.getHeader())
        if worksheet.header_footer.hasFooter():
            tag(doc, 'oddFooter', None, worksheet.header_footer.getFooter())
        end_tag(doc, 'headerFooter')

    if worksheet._charts or worksheet._images:
        tag(doc, 'drawing', {'r:id': 'rId1'})

    # If vba is being preserved then add a legacyDrawing element so
    # that any controls can be drawn.
    if vba_root is not None:
        el = vba_root.find('{%s}legacyDrawing' % SHEET_MAIN_NS)
        if el is not None:
            rId = el.get('{%s}id' % REL_NS)
            tag(doc, 'legacyDrawing', {'r:id': rId})

    breaks = worksheet.page_breaks
    if breaks:
        start_tag(doc, 'rowBreaks', {'count': str(len(breaks)), 'manualBreakCount': str(len(breaks))})
        for b in breaks:
            tag(doc, 'brk', {'id': str(b), 'man': 'true', 'max': '16383', 'min': '0'})
        end_tag(doc, 'rowBreaks')

    # add a legacyDrawing so that excel can draw comments
    if worksheet._comment_count > 0:
        tag(doc, 'legacyDrawing', {'r:id': 'commentsvml'})

    end_tag(doc, 'worksheet')
    doc.endDocument()
    xml_string = xml_file.getvalue()
    xml_file.close()
    return xml_string


def write_worksheet_sheetviews(doc, worksheet):
    start_tag(doc, 'sheetViews')
    start_tag(doc, 'sheetView', {'workbookViewId': '0'})
    selectionAttrs = {}
    topLeftCell = worksheet.freeze_panes
    if topLeftCell:
        colName, row = coordinate_from_string(topLeftCell)
        column = column_index_from_string(colName)
        pane = 'topRight'
        paneAttrs = {}
        if column > 1:
            paneAttrs['xSplit'] = str(column - 1)
        if row > 1:
            paneAttrs['ySplit'] = str(row - 1)
            pane = 'bottomLeft'
            if column > 1:
                pane = 'bottomRight'
        paneAttrs.update(dict(topLeftCell=topLeftCell,
                              activePane=pane,
                              state='frozen'))
        tag(doc, 'pane', paneAttrs)
        selectionAttrs['pane'] = pane
        if row > 1 and column > 1:
            tag(doc, 'selection', {'pane': 'topRight'})
            tag(doc, 'selection', {'pane': 'bottomLeft'})

    selectionAttrs.update({'activeCell': worksheet.active_cell,
                           'sqref': worksheet.selected_cell})

    tag(doc, 'selection', selectionAttrs)
    end_tag(doc, 'sheetView')
    end_tag(doc, 'sheetViews')


def write_worksheet_cols(doc, worksheet, style_table=None):
    """Write worksheet columns to xml.

    style_table is ignored but required
    for compatibility with the dumped worksheet <cols> may never be empty -
    spec says must contain at least one child
    """
    cols = []
    for label, dimension in iteritems(worksheet.column_dimensions):
        col_def = dict(dimension)
        style = worksheet._styles.get(label)
        if col_def == {} and style is None:
            continue
        elif style is not None:
            col_def['style'] = '%d' % style
        idx = column_index_from_string(label)
        cols.append((idx, col_def))
    if cols == []:
        return
    start_tag(doc, 'cols')
    for idx, col_def in sorted(cols):
        v = "%d" % idx
        col_def.update({'min':v, 'max':v})
        tag(doc, 'col', col_def)
    end_tag(doc, 'cols')


def write_worksheet_conditional_formatting(doc, worksheet):
    """Write conditional formatting to xml."""
    for range_string, rules in iteritems(worksheet.conditional_formatting.cf_rules):
        if not len(rules):
            # Skip if there are no rules.  This is possible if a dataBar rule was read in and ignored.
            continue
        start_tag(doc, 'conditionalFormatting', {'sqref': range_string})
        for rule in rules:
            if rule['type'] == 'dataBar':
                # Ignore - uses extLst tag which is currently unsupported.
                continue
            attr = {'type': rule['type']}
            for rule_attr in ConditionalFormatting.rule_attributes:
                if rule_attr in rule:
                    attr[rule_attr] = str(rule[rule_attr])
            start_tag(doc, 'cfRule', attr)
            if 'formula' in rule:
                for f in rule['formula']:
                    tag(doc, 'formula', None, f)
            if 'colorScale' in rule:
                start_tag(doc, 'colorScale')
                for cfvo in rule['colorScale']['cfvo']:
                    tag(doc, 'cfvo', cfvo)
                for color in rule['colorScale']['color']:
                    tag(doc, 'color', dict(color))
                end_tag(doc, 'colorScale')
            if 'iconSet' in rule:
                iconAttr = {}
                for icon_attr in ConditionalFormatting.icon_attributes:
                    if icon_attr in rule['iconSet']:
                        iconAttr[icon_attr] = rule['iconSet'][icon_attr]
                start_tag(doc, 'iconSet', iconAttr)
                for cfvo in rule['iconSet']['cfvo']:
                    tag(doc, 'cfvo', cfvo)
                end_tag(doc, 'iconSet')
            end_tag(doc, 'cfRule')
        end_tag(doc, 'conditionalFormatting')


def write_worksheet_data(doc, worksheet, string_table, style_table):
    """Write worksheet data to xml."""
    start_tag(doc, 'sheetData')
    max_column = worksheet.get_highest_column()
    shared_styles = worksheet.parent.shared_styles
    cells_by_row = {}
    for styleCoord in iterkeys(worksheet._styles):
        # Ensure a blank cell exists if it has a style
        if isinstance(styleCoord, str) and COORD_RE.search(styleCoord):
            worksheet.cell(styleCoord)
    for cell in worksheet.get_cell_collection():
        cells_by_row.setdefault(cell.row, []).append(cell)
    for row_idx in sorted(cells_by_row):
        row_dimension = worksheet.row_dimensions[row_idx]
        attrs = {'r': '%d' % row_idx,
                 'spans': '1:%d' % max_column}
        if not row_dimension.visible:
            attrs['hidden'] = '1'
        if row_dimension.height is not None:
            attrs['ht'] = str(row_dimension.ht)
            attrs['customHeight'] = '1'
        if row_idx in worksheet._styles:
            attrs['s'] = '%d' % worksheet._styles[row_idx]
            attrs['customFormat'] = '1'
        start_tag(doc, 'row', attrs)
        row_cells = cells_by_row[row_idx]
        sorted_cells = sorted(row_cells, key=row_sort)
        for cell in sorted_cells:
            value = cell.internal_value
            coordinate = cell.coordinate
            attributes = {'r': coordinate}
            if cell.data_type != cell.TYPE_FORMULA:
                attributes['t'] = cell.data_type
            if coordinate in worksheet._styles:
                attributes['s'] = '%d' % worksheet._styles[coordinate]

            if value in ('', None):
                tag(doc, 'c', attributes)
            else:
                start_tag(doc, 'c', attributes)
                if cell.data_type == cell.TYPE_STRING:
                    tag(doc, 'v', body='%s' % string_table.index(value))
                elif cell.data_type == cell.TYPE_FORMULA:
                    if coordinate in worksheet.formula_attributes:
                        attr = worksheet.formula_attributes[coordinate]
                        if 't' in attr and attr['t'] == 'shared' and 'ref' not in attr:
                            # Don't write body for shared formula
                            tag(doc, 'f', attr=attr)
                        else:
                            tag(doc, 'f', attr=attr, body='%s' % value[1:])
                    else:
                        tag(doc, 'f', body='%s' % value[1:])
                    tag(doc, 'v')
                elif cell.data_type == cell.TYPE_NUMERIC:
                    if isinstance(value, (long, decimal.Decimal)):
                        func = str
                    else:
                        func = repr
                    tag(doc, 'v', body=func(value))
                elif cell.data_type == cell.TYPE_BOOL:
                    tag(doc, 'v', body='%d' % value)
                else:
                    tag(doc, 'v', body='%s' % value)
                end_tag(doc, 'c')
        end_tag(doc, 'row')
    end_tag(doc, 'sheetData')

def write_worksheet_autofilter(doc, worksheet):
    auto_filter = worksheet.auto_filter
    if auto_filter.filter_columns or auto_filter.sort_conditions:
        start_tag(doc, 'autoFilter', {'ref': auto_filter.ref})
        for col_id, filter_column in sorted(auto_filter.filter_columns.items()):
            start_tag(doc, 'filterColumn', {'colId': str(col_id)})
            if filter_column.blank:
                start_tag(doc, 'filters', {'blank': '1'})
            else:
                start_tag(doc, 'filters')
            for val in filter_column.vals:
                tag(doc, 'filter', {'val': val})
            end_tag(doc, 'filters')
            end_tag(doc, 'filterColumn')
        if auto_filter.sort_conditions:
            start_tag(doc, 'sortState', {'ref': auto_filter.ref})
            for sort_condition in auto_filter.sort_conditions:
                sort_attr = {'ref': sort_condition.ref}
                if sort_condition.descending:
                    sort_attr['descending'] = '1'
                tag(doc, 'sortCondtion', sort_attr)
            end_tag(doc, 'sortState')
        end_tag(doc, 'autoFilter')
    elif auto_filter.ref:
        tag(doc, 'autoFilter', {'ref': auto_filter.ref})

def write_worksheet_mergecells(doc, worksheet):
    """Write merged cells to xml."""
    if len(worksheet._merged_cells) > 0:
        start_tag(doc, 'mergeCells', {'count': str(len(worksheet._merged_cells))})
        for range_string in worksheet._merged_cells:
            attrs = {'ref': range_string}
            tag(doc, 'mergeCell', attrs)
        end_tag(doc, 'mergeCells')

def write_worksheet_datavalidations(doc, worksheet):
    """ Write data validation(s) to xml."""
    # Filter out "empty" data-validation objects (i.e. with 0 cells)
    required_dvs = [x for x in worksheet._data_validations
                    if len(x.cells) or len(x.ranges)]
    count = len(required_dvs)
    if count == 0:
        return

    start_tag(doc, 'dataValidations', {'count': str(count)})
    for data_validation in required_dvs:
        start_tag(doc, 'dataValidation', data_validation.generate_attributes_map())
        if data_validation.formula1:
            tag(doc, 'formula1', body=data_validation.formula1)
        if data_validation.formula2:
            tag(doc, 'formula2', body=data_validation.formula2)
        end_tag(doc, 'dataValidation')
    end_tag(doc, 'dataValidations')

def write_worksheet_hyperlinks(doc, worksheet):
    """Write worksheet hyperlinks to xml."""
    write_hyperlinks = False
    for cell in worksheet.get_cell_collection():
        if cell.hyperlink_rel_id is not None:
            write_hyperlinks = True
            break
    if write_hyperlinks:
        start_tag(doc, 'hyperlinks')
        for cell in worksheet.get_cell_collection():
            if cell.hyperlink_rel_id is not None:
                attrs = {'display': cell.hyperlink,
                         'ref': cell.coordinate,
                         'r:id': cell.hyperlink_rel_id}
                tag(doc, 'hyperlink', attrs)
        end_tag(doc, 'hyperlinks')


def write_worksheet_rels(worksheet, drawing_id, comments_id):
    """Write relationships for the worksheet to xml."""
    root = Element('{%s}Relationships' % PKG_REL_NS)
    for rel in worksheet.relationships:
        attrs = {'Id': rel.id, 'Type': rel.type, 'Target': rel.target}
        if rel.target_mode:
            attrs['TargetMode'] = rel.target_mode
        SubElement(root, '{%s}Relationship' % PKG_REL_NS, attrs)
    if worksheet._charts or worksheet._images:
        attrs = {'Id': 'rId1',
                 'Type': '%s/drawing' % REL_NS,
                 'Target': '../drawings/drawing%s.xml' % drawing_id}
        SubElement(root, '{%s}Relationship' % PKG_REL_NS, attrs)
    if worksheet._comment_count > 0:
        # there's only one comments sheet per worksheet,
        # so there's no reason to call the Id rIdx
        attrs = {'Id': 'comments',
                 'Type': COMMENTS_NS,
                 'Target': '../comments%s.xml' % comments_id}
        SubElement(root, '{%s}Relationship' % PKG_REL_NS, attrs)
        attrs = {'Id': 'commentsvml',
                 'Type': VML_NS,
                 'Target': '../drawings/commentsDrawing%s.vml' % comments_id}
        SubElement(root, '{%s}Relationship' % PKG_REL_NS, attrs)
    return get_document_content(root)
