"""The processing programs: where they are, and how they are started. Only this file starts them.

Adapted from Cohortly's `converter/tools.py` (finding the programs, the time limit). Added here: a memory and
process limit, a clean environment without the server's secrets, a new LibreOffice settings folder for every
job with macros and outside links switched off, and a refusal to run as an administrator (SR-12, SR-13, AC-06).
"""
import ctypes
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
MAX_PROCESSES = 8
WINDOWS = sys.platform == "win32"


class ToolError(Exception):
    """A job a program could not do. The message is safe to show: it holds no file content and no paths."""


def find(name):
    """The full path of a program, or None when it is not installed."""
    setting, command, usual = PROGRAMS[name]
    for candidate in (getattr(settings, setting), shutil.which(command), *usual):
        if candidate and Path(candidate).is_file():
            return str(candidate)
    return None


def running_as_administrator():
    if WINDOWS:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    return os.geteuid() == 0


# What a program is given of our environment: only what it needs to start. Never keys, passwords or settings.
_NEEDED = ("SystemRoot", "SystemDrive", "windir", "PATH", "PATHEXT", "COMSPEC", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "LANG", "LC_ALL")
_NOWHERE = "http://127.0.0.1:9"  # a proxy that leads nowhere, for anything that tries to reach the network


def clean_environment(folder, extra=None):
    env = {name: os.environ[name] for name in _NEEDED if name in os.environ}
    for name in ("TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
        env[name] = str(folder)
    env.update(http_proxy=_NOWHERE, https_proxy=_NOWHERE, ftp_proxy=_NOWHERE, **(extra or {}))
    return env


def _limit_windows(process):
    """Puts a still sleeping process in a Windows "job" with a memory and process limit, then wakes it."""
    from ctypes import wintypes

    class Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class Extended(ctypes.Structure):
        _fields_ = [("Basic", Basic), ("IoInfo", ctypes.c_ulonglong * 6), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]

    job = kernel32.CreateJobObjectW(None, None)
    limits = Extended()
    # limit processes (0x8) and memory of them all together (0x200); end them all when the job is closed (0x2000)
    limits.Basic.LimitFlags = 0x8 | 0x200 | 0x400 | 0x2000
    limits.Basic.ActiveProcessLimit = MAX_PROCESSES
    limits.JobMemoryLimit = settings.CONVERTER_MEMORY_MB * 1024 * 1024
    handle = int(process._handle)
    ready = job and kernel32.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) and kernel32.AssignProcessToJobObject(job, handle)
    if not ready or ntdll.NtResumeProcess(handle) != 0:
        process.kill()
        if job:
            kernel32.CloseHandle(job)
        raise ToolError("The program could not be started safely.")
    return lambda: kernel32.CloseHandle(job)


def _limit_elsewhere():
    import resource  # not on Windows

    most = settings.CONVERTER_MEMORY_MB * 1024 * 1024 * 4  # address space is larger than the memory really used
    resource.setrlimit(resource.RLIMIT_AS, (most, most))


def run(command, timeout=None, folder=None, extra_env=None):
    """Runs a program under limits and returns (exit code, output). When time runs out, it and what it started are stopped."""
    if running_as_administrator():
        raise ToolError("Documents are not opened by an administrator account. Start the server as a normal user.")
    folder = folder or tempfile.gettempdir()
    options = dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=clean_environment(folder, extra_env),
                   cwd=str(folder), text=True, errors="replace")
    if WINDOWS:
        process = subprocess.Popen(command, creationflags=0x4 | subprocess.CREATE_NO_WINDOW, **options)  # 0x4: start asleep
        release = _limit_windows(process)
    else:
        process = subprocess.Popen(command, start_new_session=True, preexec_fn=_limit_elsewhere, **options)
        release = None
    try:
        output, _ = process.communicate(timeout=timeout or settings.CONVERTER_TIMEOUT)
    except subprocess.TimeoutExpired:
        if WINDOWS:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise ToolError("The work took too long and was stopped.") from None
    finally:
        if release:
            release()
    return process.returncode, output


# LibreOffice settings for opening files we do not trust.
_OFFICE_SETTINGS = (
    ("Office.Common/Security/Scripting", "MacroSecurityLevel", "3"),
    ("Office.Common/Security/Scripting", "DisableMacrosExecution", "true"),
    ("Office.Common/Security/Scripting", "BlockUntrustedRefererLinks", "true"),
    ("Office.Writer/Content/Update", "Link", "0"),
    ("Inet/Settings", "ooInetProxyType", "2"),
    ("Inet/Settings", "ooInetNoProxy", ""),
    ("Inet/Settings", "ooInetHTTPProxyName", "127.0.0.1"),
    ("Inet/Settings", "ooInetHTTPProxyPort", "9"),
    ("Inet/Settings", "ooInetHTTPSProxyName", "127.0.0.1"),
    ("Inet/Settings", "ooInetHTTPSProxyPort", "9"),
)


def _write_office_settings(profile):
    (profile / "user").mkdir(parents=True, exist_ok=True)
    items = "".join(f'<item oor:path="/org.openoffice.{path}"><prop oor:name="{name}" oor:op="fuse"><value>{value}</value></prop></item>'
                    for path, name, value in _OFFICE_SETTINGS)
    (profile / "user" / "registrymodifications.xcu").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry" '
        f'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">{items}</oor:items>', encoding="utf-8")
    return profile


_at_once = threading.BoundedSemaphore(2)  # LibreOffice is heavy: two jobs at a time
TEMPLATE_PREFIX = "doc2all-office-template-"
_template = None
_template_lock = threading.Lock()


def _soffice(profile, source, kind, folder, timeout=None):
    soffice = find("libreoffice")
    if not soffice:
        raise ToolError("LibreOffice is not installed on this server.")
    command = [soffice, "--headless", "--norestore", "--nologo", "--nodefault", "--nofirststartwizard", "--nolockcheck",
               f"-env:UserInstallation={profile.resolve().as_uri()}", "--convert-to", kind, "--outdir", str(folder), str(source)]
    run(command, timeout=timeout, folder=folder)


def is_current_template(folder):
    return _template is not None and _template.parent == folder


def office_template():
    """A LibreOffice settings folder that has been through its slow first start, made once for each server run
    from a line of our own text. No uploaded file ever touches it: every job works with its own copy."""
    global _template
    with _template_lock:
        if _template is None or not _template.is_dir():
            folder = Path(tempfile.mkdtemp(prefix=TEMPLATE_PREFIX, dir=settings.CONVERTER_WORKDIR or None))
            (folder / "first.txt").write_text("Doc2All", encoding="ascii")
            profile = _write_office_settings(folder / "office-profile")
            _soffice(profile, folder / "first.txt", "pdf", folder, timeout=max(180, settings.CONVERTER_TIMEOUT))
            if not (folder / "first.pdf").is_file():
                raise ToolError("LibreOffice did not start properly.")
            _template = profile
        return _template


def office_convert(source, kind, folder):
    """LibreOffice turns the file `source` into `kind` ("pdf", "png", ...) inside `folder`. Returns the new file."""
    template = office_template()
    profile = Path(folder) / "office-profile"
    shutil.rmtree(profile, ignore_errors=True)  # nothing is carried from one job to the next
    shutil.copytree(template, profile, ignore=shutil.ignore_patterns(".lock"))
    _write_office_settings(profile)
    with _at_once:
        _soffice(profile, source, kind, folder)
    result = Path(folder) / f"{Path(source).stem}.{kind}"
    if not result.is_file() or result.stat().st_size == 0:
        raise ToolError("This file could not be converted. It may be damaged or protected by a password.")
    return result


def tesseract(arguments, folder=None):
    """Runs Tesseract with our language files. Returns (exit code, output)."""
    program = find("tesseract")
    if not program:
        raise ToolError("Tesseract is not installed on this server.")
    env = {"OMP_THREAD_LIMIT": "1"}  # its own threads slow down a busy server
    if settings.TESSDATA_DIR:
        env["TESSDATA_PREFIX"] = settings.TESSDATA_DIR
    return run([program, *arguments], folder=folder, extra_env=env)
