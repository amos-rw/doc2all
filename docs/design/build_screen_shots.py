"""Takes still pictures of the designed screens for the report: light mode, computer view.
Which view of each screen goes in the report is read from the 4.6 table in the report text.
Run after build_screens.py and before build_report.py: python -I docs/design/build_screen_shots.py
Needs Google Chrome and pymupdf."""
import json
import pathlib
import re
import subprocess
import tempfile

import pymupdf

design = pathlib.Path(__file__).resolve().parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
WIDTH = 980  # width of the screen in the computer view

page_html = (design / "doc2all-screens.html").read_text(encoding="utf-8")
md = (design.parent / "02-doc2all-report.md").read_text(encoding="utf-8")
rows = re.findall(r"^\| (\d+) \| ([a-z]+) \|", md[md.index("<!--SCREENS-->"):], re.M)
if not rows:
    raise SystemExit("no screen rows found after <!--SCREENS--> in the report text")
blocks = re.split(r"\n\s*\{n:\d+,", page_html)[1:]  # one block of source per screen

shots = design / "shots"
shots.mkdir(exist_ok=True)
tmp = pathlib.Path(tempfile.mkdtemp())


def chrome(*args):
    base = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=8000"]
    return subprocess.run(base + list(args), capture_output=True, timeout=120).stdout.decode("utf-8", "replace")


def view_keys(number):
    """The view names of one screen, in the order of its buttons."""
    states = re.search(r"states:\[(.*?)\],\s*mood:", blocks[number - 1], re.S).group(1)
    return re.findall(r"\['([a-z]+)','", states)


def shoot(number, view, name, scale):
    press = ""
    if view:
        keys = view_keys(number)
        if view not in keys:
            raise SystemExit(f"screen {number} has no view called {view}; it has {keys}")
        press = f"document.querySelectorAll('#states .pillb')[{keys.index(view)}].click();"
    # light mode, press the wanted view, then keep only the screen itself and stop all movement
    script = ("<script>(function(){document.documentElement.setAttribute('data-theme','light');" + press +
              "var f=document.getElementById('stage');document.body.innerHTML='';document.body.appendChild(f);"
              "document.body.style.cssText='margin:0;padding:0;background:#fff';"
              f"f.style.cssText='width:{WIDTH}px;max-width:none;margin:0;box-shadow:none';"
              "var s=document.createElement('style');s.textContent='*{animation:none!important;transition:none!important}';"
              "document.head.appendChild(s);window.scrollTo(0,0);"
              "document.body.setAttribute('data-h',Math.ceil(f.getBoundingClientRect().height));})();</script>")
    page = tmp / f"{name}.html"
    page.write_text("<!doctype html><meta charset=utf8>" + page_html + script, encoding="utf-8")
    url = page.as_uri() + f"#screen-{number}"
    height = int(re.search(r'<body[^>]*data-h="(\d+)"', chrome("--window-size=1200,1800", "--dump-dom", url)).group(1))
    raw = tmp / f"{name}.png"
    chrome(f"--window-size={WIDTH},{height + 200}", f"--force-device-scale-factor={scale}", f"--screenshot={raw}", url)
    full = pymupdf.Pixmap(str(raw))
    box = pymupdf.IRect(0, 0, round(WIDTH * scale), round(height * scale))
    cut = pymupdf.Pixmap(full.colorspace, box, full.alpha)
    cut.copy(full, box)
    cut.save(shots / f"{name}.png")
    print(name, cut.width, "x", cut.height, (shots / f"{name}.png").stat().st_size, "bytes")


for n in range(1, len(blocks) + 1):
    shoot(n, None, f"map-{n}", 1)
for n, view in rows:
    shoot(int(n), view, f"screen-{n}", 1.6)
