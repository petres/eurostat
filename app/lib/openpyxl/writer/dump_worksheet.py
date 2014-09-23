from __future__ import absolute_import
# Copyright (c) 2010-2014 openpyxl


"""Write worksheets to xml representations in an optimized way"""

from fileinput import FileInput
from inspect import isgenerator
import os
from tempfile import NamedTemporaryFile

from openpyxl.compat import OrderedDict
from openpyxl.cell import get_column_letter, Cell
from openpyxl.worksheet import Worksheet

from openpyxl.xml.functions import (
    XMLGenerator,
    start_tag,
    end_tag,
    tag,
    tostring
)
from openpyxl.xml.constants import MAX_COLUMN, MAX_ROW, PACKAGE_XL
from openpyxl.exceptions import WorkbookAlreadySaved
from openpyxl.writer.excel import ExcelWriter
from openpyxl.writer.comments import CommentWriter
from .relations import write_rels
from .worksheet import (
    write_cell,
    write_cols,
    write_format
)
from openpyxl.xml.constants import PACKAGE_WORKSHEETS


DESCRIPTORS_CACHE_SIZE = 50
BOUNDING_BOX_PLACEHOLDER = 'A1:%s%d' % (get_column_letter(MAX_COLUMN), MAX_ROW)


class CommentParentCell(object):
    __slots__ = ('coordinate', 'row', 'column')

    def __init__(self, cell):
        self.coordinate = cell.coordinate
        self.row = cell.row
        self.column = cell.column


def create_temporary_file(suffix=''):
    fobj = NamedTemporaryFile(mode='w+', suffix=suffix,
                              prefix='openpyxl.', delete=False)
    filename = fobj.name
    return filename


def WriteOnlyCell(ws=None, value=None):
    return Cell(worksheet=ws, column='A', row=1, value=value)


class DumpWorksheet(Worksheet):
    """
    .. warning::

        You shouldn't initialize this yourself, use :class:`openpyxl.workbook.Workbook` constructor instead,
        with `optimized_write = True`.
    """
    def __init__(self, parent_workbook, title):
        Worksheet.__init__(self, parent_workbook, title)

        self.__saved = False

        self._max_col = 0
        self._max_row = 0
        self._parent = parent_workbook

        self._fileobj_header_name = create_temporary_file(suffix='.header')
        self._fileobj_content_name = create_temporary_file(suffix='.content')
        self._fileobj_name = create_temporary_file()

        self._comments = []

    def get_temporary_file(self, filename):
        if self.__saved:
            raise WorkbookAlreadySaved('this workbook has already been saved '
                    'and cannot be modified or saved anymore.')

        if filename in self._descriptors_cache:
            fobj = self._descriptors_cache[filename]
            # re-insert the value so it does not get evicted
            # from cache soon
            del self._descriptors_cache[filename]
            self._descriptors_cache[filename] = fobj
        else:
            fobj = open(filename, 'rb+')
            self._descriptors_cache[filename] = fobj
            if len(self._descriptors_cache) > DESCRIPTORS_CACHE_SIZE:
                filename, fileobj = self._descriptors_cache.popitem(last=False)
                fileobj.close()
        return fobj

    @property
    def _descriptors_cache(self):
        try:
            return self._parent._local_data.cache
        except AttributeError:
            self._parent._local_data.cache = OrderedDict()
            return self._parent._local_data.cache

    @property
    def filename(self):
        return self._fileobj_name

    def _cleanup(self):
        """
        Mark sheet as having been saved so no further changes are possible.
        Remove file handlers from cache
        """
        for attr in ('_fileobj_content_name', '_fileobj_header_name', '_fileobj_name'):
            obj = getattr(self, attr)
            del self._descriptors_cache[obj]
            os.remove(obj)
            setattr(self, attr, None)
        self.__saved = True

    def write_header(self):

        fobj = self.get_temporary_file(filename=self._fileobj_header_name)
        doc = XMLGenerator(fobj)

        start_tag(doc, 'worksheet',
                {
                'xmlns': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
                'xmlns:r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'})
        start_tag(doc, 'sheetPr')
        tag(doc, 'outlinePr',
                {'summaryBelow': '1',
                'summaryRight': '1'})
        end_tag(doc, 'sheetPr')
        tag(doc, 'dimension', {'ref': 'A1:%s' % (self.get_dimensions())})
        start_tag(doc, 'sheetViews')
        start_tag(doc, 'sheetView', {'workbookViewId': '0'})
        tag(doc, 'selection', {'activeCell': 'A1',
                'sqref': 'A1'})
        end_tag(doc, 'sheetView')
        end_tag(doc, 'sheetViews')
        fmt = write_format(self)
        fobj.write(tostring(fmt))
        cols = write_cols(self)
        if cols is not None:
            fobj.write(tostring(cols))

        return doc

    def close(self):
        self._close_content()
        files = [self._fileobj_header_name, self._fileobj_content_name]
        for f in files:
            self.get_temporary_file(f).close()
        output = self.get_temporary_file(self.filename)
        for line in FileInput(files, mode="rb"):
            output.write(line)
        output.close()

    def _close_content(self):
        doc = self._get_content_generator()
        end_tag(doc, 'sheetData')
        if self._comments:
            tag(doc, 'legacyDrawing', {'r:id': 'commentsvml'})
        end_tag(doc, 'worksheet')

    def get_dimensions(self):
        if not self._max_col or not self._max_row:
            return 'A1'
        else:
            return '%s%d' % (get_column_letter(self._max_col), (self._max_row))

    def _get_content_generator(self):
        """ XXX: this is ugly, but it allows to resume writing the file
        even after the handle is closed"""

        # restart XMLGenerator at the end of the file to prevent it being overwritten
        handle = self.get_temporary_file(filename=self._fileobj_content_name)
        handle.seek(0, 2)

        return XMLGenerator(out=handle)

    def append(self, row):
        """
        :param row: iterable containing values to append
        :type row: iterable
        """
        if (not isinstance(row, (list, tuple, range))
            and not isgenerator(row)):
            self._invalid_row(row)

        doc = self._get_content_generator()
        cell = WriteOnlyCell(self) # singleton

        self._max_row += 1
        span = len(row)
        self._max_col = max(self._max_col, span)
        row_idx = self._max_row
        attrs = {'r': '%d' % row_idx,
                 'spans': '1:%d' % span}
        start_tag(doc, 'row', attrs)

        for col_idx, value in enumerate(row, 1):
            if value is None:
                continue
            dirty_cell = False
            column = get_column_letter(col_idx)

            if isinstance(value, Cell):
                cell = value
                dirty_cell = True # cell may have other properties than a value
            else:
                cell.value = value

            cell.coordinate = '%s%d' % (column, row_idx)
            if cell.comment is not None:
                comment = cell.comment
                comment._parent = CommentParentCell(cell)
                self._comments.append(comment)

            write_cell(doc, self, cell)
            if dirty_cell:
                cell = WriteOnlyCell(self)
        end_tag(doc, 'row')


    def _invalid_row(self, iterable):
        raise TypeError('Value must be a list, tuple, range or a generator Supplied value is {0}'.format(
            type(iterable))
                        )

def removed_method(*args, **kw):
    raise NotImplementedError

setattr(DumpWorksheet, '__getitem__', removed_method)
setattr(DumpWorksheet, '__setitem__', removed_method)
setattr(DumpWorksheet, 'cell', removed_method)
setattr(DumpWorksheet, 'range', removed_method)
setattr(DumpWorksheet, 'merge_cells', removed_method)


def save_dump(workbook, filename):
    if workbook.worksheets == []:
        workbook.create_sheet()
    writer = ExcelDumpWriter(workbook)
    writer.save(filename)
    return True


class DumpCommentWriter(CommentWriter):
    def extract_comments(self):
        for comment in self.sheet._comments:
            if comment is not None:
                self.authors.add(comment.author)
                self.comments.append(comment)


class ExcelDumpWriter(ExcelWriter):

    def _write_worksheets(self, archive):
        drawing_id = 1
        comments_id = 1

        for i, sheet in enumerate(self.workbook.worksheets, 1):
            header_doc = sheet.write_header() # written after worksheet body to include dimensions

            start_tag(header_doc, 'sheetData')

            sheet.close()
            archive.write(sheet.filename, PACKAGE_WORKSHEETS + '/sheet%d.xml' % i)
            sheet._cleanup()

            # write comments
            if sheet._comments:
                rels = write_rels(sheet, drawing_id, comments_id)
                archive.writestr( PACKAGE_WORKSHEETS +
                                  '/_rels/sheet%d.xml.rels' % i, tostring(rels) )

                cw = DumpCommentWriter(sheet)
                archive.writestr(PACKAGE_XL + '/comments%d.xml' % comments_id,
                    cw.write_comments())
                archive.writestr(PACKAGE_XL + '/drawings/commentsDrawing%d.vml' % comments_id,
                    cw.write_comments_vml())
                comments_id += 1
