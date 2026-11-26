"""The processing programs: where they are, and how they are started. Only this file starts them.

Adapted from Cohortly's `converter/tools.py`: LibreOffice and Tesseract are found the same way, each run
has a time limit, and LibreOffice does one job at a time. Still to add when the work is protected: memory
limits, a non-administrator account and checks for bombs before a file is opened.
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from django.conf import settings

# name -> (setting that overrides, command name, usual Windows places)
PROGRAMS = {
    "libreoffice": ("SOFFICE_PATH", "soffice", (r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe")),
    "tesseract": ("TESSERACT_PATH", "tesseract", (r"C:\Program Files\Tesseract-OCR\tesseract.exe",)),
}

_one_at_a_time = threading.Lock()  # two LibreOffice runs cannot share one settings folder


class ToolError(Exception):
    """A job a program could not do. The message is safe to show: it holds no file content and no paths."""


def find(name):
    """The full path of a program, or None when it is not installed."""
    setting, command, usual = PROGRAMS[name]
    for candidate in (getattr(settings, setting), shutil.which(command), *usual):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def run(command, timeout=None, env=None):
    """Runs a program and returns (exit code, output). When time runs out, it and what it started are stopped."""
    windows = sys.platform == "win32"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, errors="replace", start_new_session=not windows)
    try:
        output, _ = process.communicate(timeout=timeout or settings.CONVERTER_TIMEOUT)
    except subprocess.TimeoutExpired:
        if windows:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise ToolError("The work took too long and was stopped.") from None
    return process.returncode, output


def office_convert(source, kind, folder):
    """LibreOffice turns the file `source` into `kind` ("pdf", "png", ...) inside `folder`. Returns the new file."""
    soffice = find("libreoffice")
    if not soffice:
        raise ToolError("LibreOffice is not installed on this server.")
    # Our own settings folder, so we never collide with another project or an open LibreOffice window.
    profile = Path(settings.CONVERTER_PROFILE_DIR or Path(tempfile.gettempdir()) / "doc2all-soffice-profile")
    command = [soffice, "--headless", "--norestore", "--nologo", "--nodefault", "--nofirststartwizard",
               f"-env:UserInstallation={profile.resolve().as_uri()}", "--convert-to", kind, "--outdir", str(folder), str(source)]
    with _one_at_a_time:
        run(command)
    result = Path(folder) / f"{Path(source).stem}.{kind}"
    if not result.is_file() or result.stat().st_size == 0:
        raise ToolError("This file could not be converted. It may be damaged or protected by a password.")
    return result


def tesseract(arguments):
    """Runs Tesseract with our language files. Returns (exit code, output)."""
    program = find("tesseract")
    if not program:
        raise ToolError("Tesseract is not installed on this server.")
    env = dict(os.environ, OMP_THREAD_LIMIT="1")  # its own threads slow down a busy server
    if settings.TESSDATA_DIR:
        env["TESSDATA_PREFIX"] = settings.TESSDATA_DIR
    return run([program, *arguments], env=env)
