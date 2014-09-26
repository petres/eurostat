from __future__ import absolute_import
# Copyright (c) 2010-2014 openpyxl

import pytest

from openpyxl.xml.constants import CHART_DRAWING_NS, SHEET_DRAWING_NS
from openpyxl.xml.functions import Element, fromstring, tostring

from openpyxl.tests.helper import compare_xml
from openpyxl.tests.schema import drawing_schema, chart_schema

def test_bounding_box():
    from openpyxl.drawing import bounding_box
    w, h = bounding_box(80, 80, 90, 100)
    assert w == 72
    assert h == 80


class TestDrawing(object):

    def setup(self):
        from openpyxl.drawing import Drawing
        self.drawing = Drawing()

    def test_ctor(self):
        d = self.drawing
        assert d.coordinates == ((1, 2), (16, 8))
        assert d.width == 21
        assert d.height == 192
        assert d.left == 0
        assert d.top == 0
        assert d.count == 0
        assert d.rotation == 0
        assert d.resize_proportional is False
        assert d.description == ""
        assert d.name == ""

    def test_width(self):
        d = self.drawing
        d.width = 100
        d.height = 50
        assert d.width == 100

    def test_proportional_width(self):
        d = self.drawing
        d.resize_proportional = True
        d.width = 100
        d.height = 50
        assert (d.width, d.height) == (5, 50)

    def test_height(self):
        d = self.drawing
        d.height = 50
        d.width = 100
        assert d.height == 50

    def test_proportional_height(self):
        d = self.drawing
        d.resize_proportional = True
        d.height = 50
        d.width = 100
        assert (d.width, d.height) == (100, 1000)

    def test_set_dimension(self):
        d = self.drawing
        d.resize_proportional = True
        d.set_dimension(100, 50)
        assert d.width == 6
        assert d.height == 50

        d.set_dimension(50, 500)
        assert d.width == 50
        assert d.height == 417

    def test_get_emu(self):
        d = self.drawing
        dims = d.get_emu_dimensions()
        assert dims == (0, 0, 200025, 1828800)


class DummyDrawing(object):

    """Shapes need charts which need drawings"""

    width = 10
    height = 20


class DummyChart(object):

    """Shapes need a chart to calculate their coordinates"""

    width = 100
    height = 100

    def __init__(self):
        self.drawing = DummyDrawing()

    def _get_margin_left(self):
        return 10

    def _get_margin_top(self):
        return 5

    def get_x_units(self):
        return 25

    def get_y_units(self):
        return 15


class TestShape(object):

    def setup(self):
        from openpyxl.drawing import Shape
        self.shape = Shape(chart=DummyChart())

    def test_ctor(self):
        s = self.shape
        assert s.axis_coordinates == ((0, 0), (1, 1))
        assert s.text is None
        assert s.scheme == "accent1"
        assert s.style == "rect"
        assert s.border_color == "000000"
        assert s.color == "FFFFFF"
        assert s.text_color == "000000"
        assert s.border_width == 0

    def test_border_color(self):
        s = self.shape
        s.border_color = "BBBBBB"
        assert s.border_color == "BBBBBB"

    def test_color(self):
        s = self.shape
        s.color = "000000"
        assert s.color == "000000"

    def test_text_color(self):
        s = self.shape
        s.text_color = "FF0000"
        assert s.text_color == "FF0000"

    def test_border_width(self):
        s = self.shape
        s.border_width = 50
        assert s.border_width == 50

    def test_coordinates(self):
        s = self.shape
        s.coordinates = ((0, 0), (60, 80))
        assert s.axis_coordinates == ((0, 0), (60, 80))
        assert s.coordinates == (1, 1, 1, 1)

    def test_pct(self):
        s = self.shape
        assert s._norm_pct(10) == 1
        assert s._norm_pct(0.5) == 0.5
        assert s._norm_pct(-10) == 0


class TestShadow(object):

    def setup(self):
        from openpyxl.drawing import Shadow
        self.shadow = Shadow()

    def test_ctor(self):
        s = self.shadow
        assert s.visible == False
        assert s.blurRadius == 6
        assert s.distance == 2
        assert s.direction == 0
        assert s.alignment == "br"
        assert s.color.index == "00000000"
        assert s.alpha == 50


class DummySheet(object):
    """Required for images"""

    def point_pos(self, vertical, horizontal):
        return vertical, horizontal


class DummyCell(object):
    """Required for images"""

    column = "A"
    row = 1
    anchor = (0, 0)

    def __init__(self):
        self.parent = DummySheet()


@pytest.fixture
def Image():
    from openpyxl.drawing import Image
    return Image

@pytest.fixture()
def ImageFile(datadir, Image):
    datadir.chdir()
    return Image("plain.png")


class TestImage(object):

    @pytest.mark.pil_not_installed
    def test_import(self, Image, datadir):
        datadir.chdir()
        with pytest.raises(ImportError):
            Image._import_image("plain.png")

    @pytest.mark.pil_required
    def test_ctor(self, Image, datadir):
        datadir.chdir()
        i = Image(img="plain.png")
        assert i.nochangearrowheads == True
        assert i.nochangeaspect == True
        d = i.drawing
        assert d.coordinates == ((0, 0), (1, 1))
        assert d.width == 118
        assert d.height == 118

    @pytest.mark.pil_required
    def test_anchor(self, Image, datadir):
        datadir.chdir()
        i = Image("plain.png")
        c = DummyCell()
        vals = i.anchor(c)
        assert vals == (('A', 1), (118, 118))

    @pytest.mark.pil_required
    def test_anchor_onecell(self, Image, datadir):
        datadir.chdir()
        i = Image("plain.png")
        c = DummyCell()
        vals = i.anchor(c, anchortype="oneCell")
        assert vals == ((0, 0), None)


class TestDrawingWriter(object):

    def setup(self):
        from openpyxl.writer.drawings import DrawingWriter
        sheet = DummySheet()
        sheet._charts = []
        sheet._images = []
        self.dw = DrawingWriter(sheet=sheet)

    def test_write(self):
        xml = self.dw.write()
        expected = """<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing">
</xdr:wsDr>"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff

    @pytest.mark.lxml_required
    def test_write_chart(self):
        from openpyxl.drawing import Drawing
        root = Element("{%s}wsDr" % SHEET_DRAWING_NS)
        chart = DummyChart()
        drawing = Drawing()
        chart.drawing = drawing
        self.dw._write_chart(root, chart, 1)
        drawing_schema.assertValid(root)
        xml = tostring(root)
        expected = """<xdr:wsDr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
  <xdr:absoluteAnchor>
    <xdr:pos x="0" y="0"/>
    <xdr:ext cx="200025" cy="1828800"/>
    <xdr:graphicFrame macro="">
      <xdr:nvGraphicFramePr>
        <xdr:cNvPr id="2" name="Chart 1"/>
        <xdr:cNvGraphicFramePr/>
      </xdr:nvGraphicFramePr>
      <xdr:xfrm>
        <a:off x="0" y="0"/>
        <a:ext cx="0" cy="0"/>
      </xdr:xfrm>
      <a:graphic>
        <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/chart">
          <c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:id="rId1"/>
        </a:graphicData>
      </a:graphic>
    </xdr:graphicFrame>
    <xdr:clientData/>
  </xdr:absoluteAnchor>
</xdr:wsDr>"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff

    @pytest.mark.lxml_required
    @pytest.mark.pil_required
    def test_write_images(self, ImageFile):

        root = Element("{%s}wsDr" % SHEET_DRAWING_NS)
        self.dw._write_image(root, ImageFile, 1)
        drawing_schema.assertValid(root)
        xml = tostring(root)
        expected = """<xdr:wsDr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing">
  <xdr:absoluteAnchor>
    <xdr:pos x="0" y="0"/>
    <xdr:ext cx="1123950" cy="1123950"/>
    <xdr:pic>
      <xdr:nvPicPr>
        <xdr:cNvPr id="2" name="Picture 1"/>
        <xdr:cNvPicPr>
          <a:picLocks noChangeArrowheads="1" noChangeAspect="1"/>
        </xdr:cNvPicPr>
      </xdr:nvPicPr>
      <xdr:blipFill>
        <a:blip xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" cstate="print" r:embed="rId1"/>
        <a:srcRect/>
        <a:stretch>
          <a:fillRect/>
        </a:stretch>
      </xdr:blipFill>
      <xdr:spPr bwMode="auto">
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="0" cy="0"/>
        </a:xfrm>
        <a:prstGeom prst="rect">
          <a:avLst/>
        </a:prstGeom>
        <a:noFill/>
        <a:ln w="1">
          <a:noFill/>
          <a:miter lim="800000"/>
          <a:headEnd/>
          <a:tailEnd len="med" type="none" w="med"/>
        </a:ln>
        <a:effectLst/>
      </xdr:spPr>
    </xdr:pic>
    <xdr:clientData/>
  </xdr:absoluteAnchor>
</xdr:wsDr>
"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff


    @pytest.mark.pil_required
    def test_write_anchor(self, ImageFile):
        drawing = ImageFile.drawing
        root = Element("test")
        self.dw._write_anchor(root, drawing)
        xml = tostring(root)
        expected = """<test><xdr:absoluteAnchor xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"><xdr:pos x="0" y="0"/><xdr:ext cx="1123950" cy="1123950"/></xdr:absoluteAnchor></test>"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff


    @pytest.mark.pil_required
    def test_write_anchor_onecell(self, ImageFile):
        drawing =ImageFile.drawing
        drawing.anchortype =  "oneCell"
        drawing.anchorcol = 0
        drawing.anchorrow = 0
        root = Element("test")
        self.dw._write_anchor(root, drawing)
        xml = tostring(root)
        expected = """<test><xdr:oneCellAnchor xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"><xdr:from><xdr:col>0</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>0</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:ext cx="1123950" cy="1123950"/></xdr:oneCellAnchor></test>"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff

    def test_write_rels(self):
        self.dw._sheet._charts.append(None)
        self.dw._sheet._images.append(None)
        xml = self.dw.write_rels(1, 1)
        expected = """<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Target="../charts/chart1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart"/>
  <Relationship Id="rId1" Target="../media/image1.png" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"/>
</Relationships>
"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff


class TestShapeWriter(object):

    def setup(self):
        from openpyxl.writer.drawings import ShapeWriter
        from openpyxl.drawing import Shape
        chart = DummyChart()
        self.shape = Shape(chart=chart, text="My first chart")
        self.sw = ShapeWriter(shapes=[self.shape])

    @pytest.mark.lxml_required
    def test_write(self):
        xml = self.sw.write(0)
        tree = fromstring(xml)
        chart_schema.assertValid(tree)
        expected = """
           <c:userShapes xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">
             <cdr:relSizeAnchor xmlns:cdr="http://schemas.openxmlformats.org/drawingml/2006/chartDrawing">
               <cdr:from>
                 <cdr:x>1</cdr:x>
                 <cdr:y>1</cdr:y>
               </cdr:from>
               <cdr:to>
                 <cdr:x>1</cdr:x>
                 <cdr:y>1</cdr:y>
               </cdr:to>
               <cdr:sp macro="" textlink="">
                 <cdr:nvSpPr>
                   <cdr:cNvPr id="0" name="shape 0" />
                   <cdr:cNvSpPr />
                 </cdr:nvSpPr>
                 <cdr:spPr>
                   <a:xfrm xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:off x="0" y="0" />
                     <a:ext cx="0" cy="0" />
                   </a:xfrm>
                   <a:prstGeom prst="rect" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:avLst />
                   </a:prstGeom>
                   <a:solidFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:srgbClr val="FFFFFF" />
                   </a:solidFill>
                   <a:ln w="0" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:solidFill>
                       <a:srgbClr val="000000" />
                     </a:solidFill>
                   </a:ln>
                 </cdr:spPr>
                 <cdr:style>
                   <a:lnRef idx="2" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:schemeClr val="accent1">
                       <a:shade val="50000" />
                     </a:schemeClr>
                   </a:lnRef>
                   <a:fillRef idx="1" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:schemeClr val="accent1" />
                   </a:fillRef>
                   <a:effectRef idx="0" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:schemeClr val="accent1" />
                   </a:effectRef>
                   <a:fontRef idx="minor" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:schemeClr val="lt1" />
                   </a:fontRef>
                 </cdr:style>
                 <cdr:txBody>
                   <a:bodyPr vertOverflow="clip" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" />
                   <a:lstStyle xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" />
                   <a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                     <a:r>
                       <a:rPr lang="en-US">
                         <a:solidFill>
                           <a:srgbClr val="000000" />
                         </a:solidFill>
                       </a:rPr>
                       <a:t>My first chart</a:t>
                     </a:r>
                   </a:p>
                 </cdr:txBody>
               </cdr:sp>
             </cdr:relSizeAnchor>
           </c:userShapes>
"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff

    def test_write_text(self):
        root = Element("{%s}test" % CHART_DRAWING_NS)
        self.sw._write_text(root, self.shape)
        xml = tostring(root)
        expected = """<cdr:test xmlns:cdr="http://schemas.openxmlformats.org/drawingml/2006/chartDrawing"><cdr:txBody><a:bodyPr vertOverflow="clip" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" /><a:lstStyle xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" /><a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:r><a:rPr lang="en-US"><a:solidFill><a:srgbClr val="000000" /></a:solidFill></a:rPr><a:t>My first chart</a:t></a:r></a:p></cdr:txBody></cdr:test>"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff


    def test_write_style(self):
        root = Element("{%s}test" % CHART_DRAWING_NS)
        self.sw._write_style(root)
        xml = tostring(root)
        expected = """<cdr:test xmlns:cdr="http://schemas.openxmlformats.org/drawingml/2006/chartDrawing"><cdr:style><a:lnRef idx="2" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:schemeClr val="accent1"><a:shade val="50000" /></a:schemeClr></a:lnRef><a:fillRef idx="1" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:schemeClr val="accent1" /></a:fillRef><a:effectRef idx="0" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:schemeClr val="accent1" /></a:effectRef><a:fontRef idx="minor" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:schemeClr val="lt1" /></a:fontRef></cdr:style></cdr:test>"""
        diff = compare_xml(xml, expected)
        assert diff is None, diff
