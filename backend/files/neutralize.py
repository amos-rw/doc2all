"""Makes the copy that LibreOffice opens: without macros, and unable to ask for anything outside the file.

The user's own upload is not changed. This is part of "what runs by itself or reaches outside is always removed"
(SR-15, AC-06). The full cleaning of hidden data is a later piece.
"""
import re
import zipfile
from xml.dom import minidom
from xml.parsers.expat import ExpatError

from .inspect_office import is_xml

BLOCKED = "blocked:outside-link"
LEADS_OUTSIDE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9+.\-]*:|\\\\|//)")  # http:, file:, \\server, //server
MACRO_PART = re.compile(r"(^|/)(vbaProject\.bin|vbaProjectSignature[^/]*\.bin|vbaData\.xml)$|(^|/)activeX/", re.IGNORECASE)
WORD = ("http://schemas.openxmlformats.org/wordprocessingml/2006/main", "http://purl.oclc.org/ooxml/wordprocessingml/main")
FETCHING_FIELDS = {"INCLUDETEXT", "INCLUDEPICTURE", "INCLUDE", "IMPORT", "LINK", "DDE", "DDEAUTO", "DATABASE", "RD"}


class Unreadable(Exception):
    pass


def safe_copy(source, target, kind):
    """Writes the safe copy to `target`. Returns how many macros, outside links and fetching fields were blocked."""
    removed = {"macro": 0, "outside_link": 0, "outside_field": 0}
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as copy:
        for part in original.infolist():
            name = part.filename
            if MACRO_PART.search(name):
                removed["macro"] += 1
                continue
            data = original.read(part)
            if name.lower().endswith(".rels"):
                data = _edit(data, lambda document: _block_links(document, removed))
            elif kind == "docx" and is_xml(name) and name.lower().startswith("word/"):
                data = _edit(data, lambda document: _block_fields(document, removed))
            copy.writestr(name, data)
    return removed


def _edit(data, change):
    """Reads one XML part, lets `change` alter it, and writes it again only when something changed."""
    try:
        document = minidom.parseString(data)
    except (ExpatError, ValueError):
        raise Unreadable from None
    return document.toxml(encoding="UTF-8") if change(document) else data


def _elements(document):
    return document.getElementsByTagName("*")


def _block_links(document, removed):
    changed = False
    for element in _elements(document):
        if element.localName != "Relationship":
            continue
        target, kind = element.getAttribute("Target"), element.getAttribute("Type")
        outside = element.getAttribute("TargetMode").lower() == "external" or LEADS_OUTSIDE.match(target)
        if outside and not kind.endswith("/hyperlink"):  # a link the reader may click is not fetched by opening
            element.setAttribute("Target", BLOCKED)
            element.setAttribute("TargetMode", "External")
            removed["outside_link"] += 1
            changed = True
    return changed


def _fetches(instruction):
    words = instruction.split()
    return bool(words) and words[0].upper().strip('"\\') in FETCHING_FIELDS


def _block_fields(document, removed):
    changed = False
    open_fields = []  # for each field not yet closed: the pieces of its instruction

    def judge(pieces):
        nonlocal changed
        if _fetches("".join(node.data for piece in pieces for node in piece.childNodes if node.nodeType == node.TEXT_NODE)):
            for piece in pieces:
                while piece.firstChild:
                    piece.removeChild(piece.firstChild)
            removed["outside_field"] += 1
            changed = True
        pieces.clear()

    for element in list(_elements(document)):
        if element.namespaceURI not in WORD:
            continue
        if element.localName == "fldSimple":
            for attribute in list(element.attributes.values()):
                if attribute.localName == "instr" and _fetches(attribute.value):
                    attribute.value = ""
                    removed["outside_field"] += 1
                    changed = True
        elif element.localName == "fldChar":
            what = next((a.value for a in element.attributes.values() if a.localName == "fldCharType"), "")
            if what == "begin":
                open_fields.append([])
            elif what in ("separate", "end") and open_fields:
                judge(open_fields[-1])
                if what == "end":
                    open_fields.pop()
        elif element.localName in ("instrText", "delInstrText"):
            if open_fields:
                open_fields[-1].append(element)
            else:
                judge([element])
    for pieces in open_fields:  # fields that were never closed
        judge(pieces)
    return changed
