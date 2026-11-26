"""Builds harmless trick files for the security tests. They only reach a listener and files that the tests make."""
import io
import struct
import threading
import zipfile
import zlib
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "public"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def red_square(side=64):
    """A small PNG picture."""
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    rows = b"".join(b"\x00" + b"\xff\x00\x00" * side for _ in range(side))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", side, side, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


@contextmanager
def listener():
    """A tiny web server on this computer. Yields (address, list of requests it received)."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            body = red_square()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_HEAD(self):
            seen.append(self.path)
            self.send_response(200)
            self.end_headers()

        do_OPTIONS = do_PROPFIND = do_HEAD

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}", seen
    finally:
        server.shutdown()
        server.server_close()


def rebuild(sample, change=None, add=None):
    """A copy of a sample file with some parts changed (name -> function of its text) or added."""
    out = io.BytesIO()
    with zipfile.ZipFile(SAMPLES / sample) as source, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        names = set(source.namelist())
        for name in source.namelist():
            data = source.read(name)
            if change and name in change:
                data = change[name](data.decode("utf-8")).encode("utf-8")
            target.writestr(name, data)
        for name, data in (add or {}).items():
            if name not in names:
                target.writestr(name, data)
    return out.getvalue()


def _relationship(rel_id, kind, target):
    return f'<Relationship Id="{rel_id}" Type="{R}/{kind}" Target="{target}" TargetMode="External"/>'


def _add_relationship(line):
    return lambda xml: xml.replace("</Relationships>", line + "</Relationships>")


def _in_body(paragraph):
    return lambda xml: xml.replace("<w:body>", "<w:body>" + paragraph)


def docx_with_outside_picture(target):
    paragraph = (
        f'<w:p><w:r><w:drawing><wp:inline xmlns:wp="{WP}" distT="0" distB="0" distL="0" distR="0"><wp:extent cx="1905000" cy="1905000"/>'
        f'<wp:docPr id="7" name="p"/><a:graphic xmlns:a="{A}"><a:graphicData uri="{PIC}"><pic:pic xmlns:pic="{PIC}">'
        f'<pic:nvPicPr><pic:cNvPr id="7" name="p"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip xmlns:r="{R}" r:link="rIdOut"/>'
        '<a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1905000" cy="1905000"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )
    return rebuild("sample-letter.docx", {"word/document.xml": _in_body(paragraph), "word/_rels/document.xml.rels": _add_relationship(_relationship("rIdOut", "image", target))})


def pptx_with_outside_picture(target):
    picture = (
        '<p:pic><p:nvPicPr><p:cNvPr id="99" name="x"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:link="rIdOut"/>'
        '<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1905000" cy="1905000"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
    )
    return rebuild("sample-slides.pptx", {
        "ppt/slides/slide1.xml": lambda xml: xml.replace("</p:spTree>", picture + "</p:spTree>"),
        "ppt/slides/_rels/slide1.xml.rels": _add_relationship(_relationship("rIdOut", "image", target)),
    })


def docx_with_outside_template(target):
    relations = (
        '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + _relationship("rIdT", "attachedTemplate", target) + "</Relationships>"
    )
    return rebuild("sample-letter.docx",
                   {"word/settings.xml": lambda xml: xml.replace("</w:settings>", f'<w:attachedTemplate xmlns:r="{R}" r:id="rIdT"/></w:settings>')},
                   {"word/_rels/settings.xml.rels": relations})


def docx_with_field(instruction, split=False):
    """A field such as INCLUDETEXT that tells the program to fetch something."""
    def escape(text):
        return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")

    if not split:
        paragraph = f'<w:p><w:fldSimple w:instr=" {escape(instruction)} "><w:r><w:t>saved text</w:t></w:r></w:fldSimple></w:p>'
    else:  # the instruction cut into small pieces, to slip past a simple search
        pieces = "".join(f'<w:r><w:instrText xml:space="preserve">{escape(instruction[i:i + 3])}</w:instrText></w:r>'
                         for i in range(0, len(instruction), 3))
        paragraph = ('<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>' + pieces
                     + '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>saved text</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
    return rebuild("sample-letter.docx", {"word/document.xml": _in_body(paragraph)})


def odt_renamed():
    """A different kind of document (OpenDocument, which can carry macros) given a Word name."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as target:
        target.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        target.writestr("content.xml", '<?xml version="1.0"?><office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
                        'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"><office:body><office:text><text:p>not a Word file</text:p>'
                        "</office:text></office:body></office:document-content>")
        target.writestr("META-INF/manifest.xml", '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
                        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>'
                        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/></manifest:manifest>')
    return out.getvalue()


def docx_bomb(expanded_mb=600):
    """A small Word file that grows to a huge size when opened."""
    out = io.BytesIO()
    with zipfile.ZipFile(SAMPLES / "sample-letter.docx") as source, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for name in source.namelist():
            target.writestr(name, source.read(name))
        with target.open("word/media/filler.bin", "w", force_zip64=True) as entry:
            block = bytes(1024 * 1024)
            for _ in range(expanded_mb):
                entry.write(block)
    return out.getvalue()


def docx_with_pages(count):
    breaks = '<w:p><w:r><w:t>page</w:t></w:r><w:r><w:br w:type="page"/></w:r></w:p>' * (count - 1)
    return rebuild("sample-letter.docx", {"word/document.xml": _in_body(breaks)})
