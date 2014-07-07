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

import os.path

from openpyxl.comments import Comment
from openpyxl.xml.constants import (
    PACKAGE_XL,
    PACKAGE_WORKSHEET_RELS,
    PACKAGE_WORKSHEETS,
    SHEET_MAIN_NS,
    COMMENTS_NS
    )
from openpyxl.xml.functions import fromstring, safe_iterator

def _get_author_list(root):
    author_subtree = root.find('{%s}authors' % SHEET_MAIN_NS)
    return [author.text for author in author_subtree]

def read_comments(ws, xml_source):
    """Given a worksheet and the XML of its comments file, assigns comments to cells"""
    root = fromstring(xml_source)
    authors = _get_author_list(root)
    comment_nodes = safe_iterator(root, ('{%s}comment' % SHEET_MAIN_NS))
    for node in comment_nodes:
        author = authors[int(node.attrib['authorId'])]
        cell = node.attrib['ref']
        text_node = node.find('{%s}text' % SHEET_MAIN_NS)
        substrs = []
        for run in text_node.findall('{%s}r' % SHEET_MAIN_NS):
            runtext = ''.join([t.text for t in run.findall('{%s}t' % SHEET_MAIN_NS)])
            substrs.append(runtext)
        comment_text = ''.join(substrs)

        comment = Comment(comment_text, author)
        ws.cell(coordinate=cell).comment = comment

def get_comments_file(worksheet_path, archive, valid_files):
    """Returns the XML filename in the archive which contains the comments for
    the spreadsheet with codename sheet_codename. Returns None if there is no
    such file"""
    sheet_codename = os.path.split(worksheet_path)[-1]
    rels_file = PACKAGE_WORKSHEET_RELS + '/' + sheet_codename + '.rels'
    if rels_file not in valid_files:
        return None
    rels_source = archive.read(rels_file)
    root = fromstring(rels_source)
    for i in root:
        if i.attrib['Type'] == COMMENTS_NS:
            comments_file = os.path.split(i.attrib['Target'])[-1]
            comments_file = PACKAGE_XL + '/' + comments_file
            if comments_file in valid_files:
                return comments_file
    return None
