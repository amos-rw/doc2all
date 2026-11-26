"""Where the processing programs are on this computer."""
import os
import shutil
from pathlib import Path

# name -> (environment variable that overrides, command name, usual Windows place)
PROGRAMS = {
    "libreoffice": ("SOFFICE_PATH", "soffice", r"C:\Program Files\LibreOffice\program\soffice.exe"),
    "tesseract": ("TESSERACT_PATH", "tesseract", r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
}


def find(name):
    """The full path of a program, or None when it is not installed."""
    variable, command, usual = PROGRAMS[name]
    for candidate in (os.environ.get(variable), shutil.which(command), usual):
        if candidate and Path(candidate).is_file():
            return candidate
    return None
