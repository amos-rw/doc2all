"""Builds docs/design/doc2all-report.html from the report text (docs/02-doc2all-report.md)
and the static cat drawing (docs/design/doc2all-cat.html).
The same HTML is the artifact preview and, printed with headless Chrome, the PDF."""
import re
import pathlib
import markdown

root = pathlib.Path(__file__).resolve().parents[2]
md_text = (root / "docs" / "02-doc2all-report.md").read_text(encoding="utf-8")
cat_html = (root / "docs" / "design" / "doc2all-cat.html").read_text(encoding="utf-8")

# static cat: take the svg, drop the animation hooks
svg = re.search(r"<svg id=\"cat\".*?</svg>", cat_html, re.S).group(0)
svg = svg.replace('id="cat"', 'class="cover-cat"').replace('data-mood="hello"', "")
svg = re.sub(r'aria-label="[^"]*"', 'aria-hidden="true"', svg, count=1)
svg = svg.replace("role=\"img\"", "")

# split the markdown into parts
abstract = re.search(r"## Abstract\n\n(.*?)\n\n## 1\.", md_text, re.S).group(1)
intro = re.search(r"## 1\. Introduction\n(.*?)\n## 2\.", md_text, re.S).group(1)
objs = re.search(r"## 2\. Objectives\n(.*?)\n## 3\.", md_text, re.S).group(1)
reqs = re.search(r"## 3\. Requirements\n(.*?)\n## 4\. Design", md_text, re.S).group(1)
design = re.search(r"## 4\. Design\n(.*?)\n## References", md_text, re.S).group(1)
refs = re.search(r"## References\n(.*)$", md_text, re.S).group(1)

# the still data-flow diagram (made by build_threat_model.py) gets its own landscape page
dfd_html = (root / "docs" / "design" / "_dfd_print.html").read_text(encoding="utf-8")
design_a, design_b = design.split("<!--DFD-->")
design_intro, design_41 = design_a.split("### 4.1", 1)
# 4.6 has its own pages: the map, then the key screens
design_b, design_46 = design_b.split("### 4.6", 1)
design_46, design_47 = design_46.split("### 4.7", 1)
screens_intro, screens_table = ("### 4.6" + design_46).split("<!--SCREENS-->")
# the still data model drawing (made by build_data_model.py) gets its own landscape page, its tables follow
data_html = (root / "docs" / "design" / "_data_print.html").read_text(encoding="utf-8")
design_47, design_48 = design_47.split("### 4.8", 1)
data_intro, data_tables = ("### 4.7" + design_47).split("<!--DATA-->")
# 4.8: the access drawing and the common checks on a landscape page, then every call (made by build_server_interfaces.py)
calls_figure = (root / "docs" / "design" / "_calls_figure.html").read_text(encoding="utf-8")
calls_tables = (root / "docs" / "design" / "_calls_print.html").read_text(encoding="utf-8")
calls_intro, calls_rest = ("### 4.8" + design_48).split("<!--CHECKS-->")
calls_checks, calls_after = calls_rest.split("<!--CALLS-->")
design_41 = "### 4.1" + design_41

extra_css = """
/* landscape page for the data-flow diagram */
.paper.land{max-width:1123px;padding:36px 40px 30px}
.dfdfig{margin:0}
.paper.land h3{margin-top:0}
.kicker{break-after:avoid}
.dfdfig figcaption{font-size:12.5px;color:var(--muted);margin-top:10px;text-align:center}
@page land{size:A4 landscape;margin:12mm 14mm 16mm;@bottom-center{content:counter(page);font-family:"DM Sans",sans-serif;font-size:9pt;color:#7A879E}}
@media print{.paper.land{page:land;max-width:none;padding:0}.dfdfig figcaption{font-size:9pt}.dfdfig .key{font-size:8.5pt}}

/* section 4.8: the common checks in two columns, then compact tables of calls */
.checks ol{grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-flow:column;grid-template-rows:repeat(4,auto);gap:10px 24px;font-size:13px;line-height:1.5}
.calls table{table-layout:fixed}
.calls th:nth-child(1){width:31%}.calls th:nth-child(2){width:14%}.calls th:nth-child(3){width:38%}.calls th:nth-child(4){width:17%}
.calls td{padding:7px 10px 7px 0;font-size:12px;line-height:1.45;overflow-wrap:anywhere}
.calls code{font-size:10px;padding:0;background:none;color:var(--muted);display:block;margin-top:2px}
.calls td div+div{margin-top:2px}
@media (max-width:640px){.checks ol{grid-template-columns:minmax(0,1fr);grid-auto-flow:row;grid-template-rows:none}.calls table{min-width:560px}}
@media print{.checks ol{font-size:9.5pt;gap:2.5mm 8mm;margin-top:4mm}.calls td{font-size:8.4pt;padding:1.6mm 2.5mm 1.6mm 0}.calls code{font-size:7.4pt}.calls .tag{font-size:6.8pt;padding:0 1.4mm}.calls thead{display:table-header-group}}

/* section 4.6: screen map and full-size screens */
.smap{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px 16px;margin-top:16px}
.sgrp-t{font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--blue);margin-bottom:6px}
.srow{display:grid;gap:16px}
.smap figure{margin:0}
.smap img{display:block;width:100%;aspect-ratio:980/620;object-fit:cover;object-position:top;border:1px solid var(--rule);border-radius:8px}
.smap figcaption{font-size:11.5px;color:var(--head);font-weight:700;margin-top:5px}.smap figcaption b{color:var(--blue);margin-right:4px}
.mapcap{font-size:12.5px;color:var(--muted);text-align:center;margin:14px 0 0}
.shot{margin:0 0 30px;text-align:center;break-inside:avoid}
.shot-t{font-size:15px;font-weight:700;color:var(--head);text-align:left;margin-bottom:8px;display:flex;gap:10px;align-items:baseline}
.shot-t .n{font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--blue)}
.shot img{display:block;width:100%;height:auto;margin:0 auto}
.shot figcaption{font-size:12.5px;line-height:1.55;color:var(--muted);text-align:left;margin-top:8px}.shot figcaption b{color:var(--head);margin-right:4px}
.shot figcaption div{margin-top:3px}
.shots-end{margin-top:0}
@media (max-width:640px){.smap{grid-template-columns:repeat(2,minmax(0,1fr))}.sgrp{grid-column:1/-1!important}.srow{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media print{.smap{grid-template-columns:repeat(4,56mm);justify-content:center;gap:4mm 6mm;margin-top:4mm}.srow{gap:6mm}.smap img{border-radius:2mm}.smap figcaption{font-size:8.5pt;margin-top:1.2mm}.mapcap{font-size:9pt;margin-top:3mm}.shotpage{break-after:page}.shotpage:last-child{break-after:auto}.shot{margin:0 0 7mm}.shot img{width:var(--pw)}.shot figcaption{font-size:9pt}}
"""

# the whole plan, shown in the contents (no status, just what the report covers)
PLAN = [
    ("1", "Introduction", "The problem, why security matters, and security in every step of the life cycle"),
    ("2", "Objectives", "The general objective and the specific objectives, in the order the system is built"),
    ("3", "Requirements", "Functional, non-functional and security requirements, abuse cases and traceability"),
    ("4", "Design", "The threat model (data-flow diagram, trust boundaries, threats and protections), the screens, the data model and the server interfaces"),
    ("5", "Implementation", "Secure coding rules and the features, built one after another"),
    ("6", "Testing", "One test per abuse case, code, dependency and dynamic scans, fixes and retests"),
    ("7", "Deployment", "The hardening checklist for going live"),
    ("8", "Maintenance", "The audit log, the update routine and the incident-response note"),
    ("9", "Conclusion", "What was built, what was found and fixed, and what comes next"),
    ("R", "References", "The sources used"),
]
contents_html = "".join(
    f'<li><span class="c">{n}</span><div>{t}<small>{d}</small></div></li>' for n, t, d in PLAN
)

def sdlc_figure():
    import math
    cx, cy, rx, ry, bw, bh = 300, 190, 215, 140, 148, 44
    phases = ["Requirements", "Design", "Implementation", "Testing", "Deployment", "Maintenance"]
    out = ['<figure class="fig"><svg viewBox="0 0 600 380" role="img" aria-label="The software development life cycle: requirements, design, implementation, testing, deployment and maintenance, in a circle around SDLC">']
    out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="#C9D6EA" stroke-width="3" stroke-dasharray="2 9" stroke-linecap="round"/>')
    for k in range(6):  # arrows halfway between boxes, clockwise
        t = math.radians(-60 + 60 * k)
        px, py = cx + rx * math.cos(t), cy + ry * math.sin(t)
        ux, uy = -rx * math.sin(t), ry * math.cos(t)
        n = math.hypot(ux, uy)
        ux, uy = ux / n, uy / n
        nx, ny = -uy, ux
        tip = (px + ux * 8, py + uy * 8)
        a = (px - ux * 6 + nx * 7, py - uy * 6 + ny * 7)
        b = (px - ux * 6 - nx * 7, py - uy * 6 - ny * 7)
        out.append(f'<polygon points="{tip[0]:.1f},{tip[1]:.1f} {a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f}" fill="#2F6BFF"/>')
    for k, name in enumerate(phases):
        t = math.radians(-90 + 60 * k)
        x, y = cx + rx * math.cos(t) - bw / 2, cy + ry * math.sin(t) - bh / 2
        out.append(f'<rect x="{x:.1f}" y="{y + 4:.1f}" width="{bw}" height="{bh}" rx="11" fill="#C9D6EA"/>')
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{bh}" rx="11" fill="#fff" stroke="#C9D6EA" stroke-width="2"/>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{y + bh / 2:.1f}" text-anchor="middle" dominant-baseline="central" class="fig-t">{name}</text>')
    out.append(f'<circle cx="{cx}" cy="{cy + 5}" r="58" fill="#1B4BC4"/><circle cx="{cx}" cy="{cy}" r="58" fill="#2F6BFF"/>')
    out.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central" class="fig-c">SDLC</text>')
    out.append('</svg><figcaption>Security belongs in every step of the life cycle.</figcaption></figure>')
    return "".join(out)


FIGURE = sdlc_figure()

ID = re.compile(r"\b(?:NFR|FR|SR|AC)-\d\d\b")


def render(text):
    h = markdown.markdown(text, extensions=["tables"])
    h = re.sub(r"<h3>(\d\.\d) (.*?)</h3>", r'<h3><span class="n">\1</span>\2</h3>', h)
    h = re.sub(r"<p><strong>(.*?)</strong></p>", r'<p class="group">\1</p>', h)

    def cell(m):
        inner = m.group(1)
        if re.fullmatch(r"(?:NFR|FR|SR|AC)-\d\d", inner):
            return f'<td class="idc"><span class="pill">{inner}</span></td>'
        inner = ID.sub(lambda k: f'<span class="tag">{k.group(0)}</span>', inner)
        inner = inner.replace('</span>, <span', '</span> <span')
        inner = re.sub(r'\s*\((<span class="tag">[^<]*</span>(?: <span class="tag">[^<]*</span>)*)\)', lambda g: ' ' + g.group(1), inner)
        return f"<td>{inner}</td>"

    h = re.sub(r"<td>(.*?)</td>", cell, h, flags=re.S)
    h = re.sub(r"<li>(.*?)</li>", lambda m: "<li><div>" + m.group(1) + "</div></li>", h, flags=re.S)
    h = h.replace("<table>", '<div class="tw"><table>').replace("</table>", "</table></div>")
    h = h.replace("<!--SDLC-DIAGRAM-->", FIGURE)
    return h


def refs_html(text):
    items = [l[2:].strip() for l in text.strip().splitlines() if l.startswith("- ")]
    out = []
    for i in items:
        i = re.sub(r"\*(.*?)\*", r"<em>\1</em>", i)
        i = re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', i)
        out.append(f"<li>{i}</li>")
    return "<ul class=\"refs\">" + "".join(out) + "</ul>"


def png_size(path):
    head = path.read_bytes()[:24]
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def screen_map():
    """All screens as small pictures, in their groups."""
    source = (root / "docs" / "design" / "screens.src.html").read_text(encoding="utf-8")
    screens = re.findall(r"\{n:(\d+),name:'([^']+)',g:'([^']+)'", source)
    groups = {}
    for number, name, group in screens:
        groups.setdefault(group, []).append((number, name))
    order = ["Getting in", "Doing the work", "Admin", "Looking after files"]  # fills three rows of four
    out = ['<div class="smap">']
    for group in order:
        items = groups.pop(group)
        out.append(f'<div class="sgrp" style="grid-column:span {len(items)}"><div class="sgrp-t">{group}</div><div class="srow" style="grid-template-columns:repeat({len(items)},minmax(0,1fr))">')
        for number, name in items:
            out.append(f'<figure><img src="shots/map-{number}.png" alt="Screen {number}, {name}"><figcaption><b>{number}</b> {name}</figcaption></figure>')
        out.append("</div></div>")
    if groups:
        raise SystemExit(f"screen groups missing from the map: {list(groups)}")
    out.append('</div><p class="mapcap">Figure 4.2 · The eleven screens</p>')
    return "".join(out)


def screen_pages(table):
    """The key screens at full size, grouped into printed pages."""
    rows = {}
    for line in table.strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0].isdigit():
            rows[cells[0]] = cells[1:]
    pages = [["1", "3"], ["5"], ["7", "8"], ["11"]]
    if sorted(sum(pages, []), key=int) != sorted(rows, key=int):
        raise SystemExit("the 4.6 table and the page plan name different screens")
    figure = 3
    out = []
    for page in pages:
        # height of each picture if it filled the 176 mm text width
        full = [176 * h / w for w, h in (png_size(root / "docs" / "design" / "shots" / f"screen-{n}.png") for n in page)]
        room = 252 - 27 * len(page)  # printed page height left for pictures after titles and captions
        width = min(100, 100 * room / sum(full))
        out.append('<div class="shotpage">')
        for number in page:
            _view, title, caption, reqs = rows[number]
            tags = " ".join(f'<span class="tag">{r.strip()}</span>' for r in reqs.split(","))
            out.append(
                f'<figure class="shot"><div class="shot-t"><span class="n">Screen {number}</span>{title}</div>'
                f'<img src="shots/screen-{number}.png" alt="Screen {number}, {title}" style="--pw:{width:.1f}%">'
                f'<figcaption><b>Figure 4.{figure}</b> {caption}<div>{tags}</div></figcaption></figure>')
            figure += 1
        out.append("</div>")
    return "".join(out)


page = f"""<title>Doc2All Report</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,700;0,9..40,800;1,9..40,400&display=swap">
<style>
/* Layout: white A4 sheets on a soft ground. Cover with the cat, then one flowing content sheet. Same page prints to PDF. */
:root{{
  --bg:#EEF2F9; --chrome-ink:#14305C; --chrome-muted:#5F7093; --chrome-line:#D6E0F0;
  --paper:#FFFFFF; --head:#14305C; --text:#3A4663; --muted:#7A879E; --rule:#E6ECF5;
  --blue:#2F6BFF; --blue-edge:#1B4BC4; --blue-soft:#E8F0FF;
  --ginger:#F2994A; --ginger-dark:#DB7C2B; --cream:#FFE7C9; --pink:#F5859C;
  --catink:#14305C; --whisker:#AAB8D2; --mouth:#5B1F2E; --docline:#C9D6EA; --gold:#FFC83D;
  --safe:#22B573; --warn:#EF5350; --scan:#19B5D6;
  --font:"DM Sans", ui-rounded, "Segoe UI", system-ui, sans-serif;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{ --bg:#0D1730; --chrome-ink:#EAF0FB; --chrome-muted:#A3B3D1; --chrome-line:#263A63; color-scheme:dark; }}
}}
:root[data-theme="dark"]{{ --bg:#0D1730; --chrome-ink:#EAF0FB; --chrome-muted:#A3B3D1; --chrome-line:#263A63; color-scheme:dark; }}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--chrome-ink);font-family:var(--font);
  padding-block:24px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.bar{{max-width:794px;margin:0 auto 18px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;
  font-size:13px;font-weight:700;color:var(--chrome-muted)}}
.bar b{{color:var(--chrome-ink)}}
.paper{{background:var(--paper);color:var(--text);max-width:794px;margin:0 auto 26px;border-radius:10px;
  box-shadow:0 1px 2px rgba(20,48,92,.08),0 14px 44px rgba(20,48,92,.14);
  -webkit-print-color-adjust:exact;print-color-adjust:exact}}

/* cover */
.cover{{aspect-ratio:210/297;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:48px 40px;gap:0}}
.kicker{{font-size:10.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)}}
.cover .kicker{{margin-bottom:34px}}
.cover-cat{{width:min(300px,62%);height:auto;display:block;overflow:visible;margin-bottom:30px}}
.cover-cat .open-eyes{{display:inline}}
.cover-cat .happy-eyes,.cover-cat .brows,.cover-cat .beam,.cover-cat .sparks,.cover-cat .alerts,.cover-cat .m-safe,.cover-cat .m-alert,.cover-cat .badge-safe,.cover-cat .badge-alert,.cover-cat .heart{{display:none}}
.f-ginger{{fill:var(--ginger)}} .f-dark{{fill:var(--ginger-dark)}} .f-cream{{fill:var(--cream)}} .f-pink{{fill:var(--pink)}} .f-white{{fill:#fff}} .f-ink{{fill:var(--catink)}}
.s-ginger{{stroke:var(--ginger)}} .s-dark{{stroke:var(--ginger-dark)}} .s-ink{{stroke:var(--catink)}}
.line{{fill:none;stroke-linecap:round;stroke-linejoin:round}} .shadow{{fill:var(--catink);opacity:.12}}
.doc-head{{fill:var(--blue)}}
.cover h1{{font-size:clamp(40px,8vw,60px);line-height:1.05;font-weight:800;letter-spacing:-.02em;color:var(--head);margin:0}}
.sub{{font-size:clamp(15px,2.6vw,18px);color:var(--muted);margin:12px 0 0;font-weight:400}}
.bar-accent{{width:72px;height:6px;border-radius:6px;background:var(--blue);margin:30px 0 26px}}
.who{{font-weight:700;color:var(--head);font-size:15px;margin:0}}
.meta{{font-size:13px;color:var(--muted);margin:6px 0 0;line-height:1.7}}
.meta a{{color:var(--blue);text-decoration:none;font-weight:700}}

/* content */
.doc{{padding:60px 72px 64px;font-size:14px;line-height:1.7}}
.lead{{font-size:15.5px;line-height:1.75;color:var(--text);margin:12px 0 0}}
.contents{{list-style:none;margin:14px 0 0;padding:0;display:grid;gap:10px}}
.contents li{{display:flex;gap:14px;align-items:flex-start;font-weight:700;color:var(--head);font-size:15px;line-height:1.35;break-inside:avoid}}
.contents small{{display:block;font-weight:400;color:var(--muted);font-size:12.5px;line-height:1.5;margin-top:1px}}
ol{{list-style:none;counter-reset:o;padding:0;margin:14px 0;display:grid;gap:14px}}
ol>li{{counter-increment:o;display:grid;grid-template-columns:28px 1fr;gap:14px;align-items:start;break-inside:avoid}}
ol>li::before{{content:counter(o);width:28px;height:28px;border-radius:9px;background:var(--blue-soft);color:var(--blue);font-weight:800;font-size:13px;display:grid;place-items:center}}
.contents .c{{width:28px;height:28px;border-radius:9px;display:grid;place-items:center;font-size:13px;font-weight:800;color:var(--blue);background:var(--blue-soft)}}
.block{{margin-top:44px}}
.block:first-child{{margin-top:0}}
h2{{font-size:27px;line-height:1.2;font-weight:700;color:var(--head);margin:0 0 6px;display:flex;align-items:center;gap:14px;break-after:avoid}}
.num{{width:36px;height:36px;border-radius:11px;background:var(--blue);color:#fff;display:grid;place-items:center;font-size:19px;font-weight:800;flex:none;box-shadow:0 3px 0 var(--blue-edge)}}
h3{{font-size:16.5px;font-weight:700;color:var(--head);margin:30px 0 4px;display:flex;gap:10px;align-items:baseline;break-after:avoid}}
h3 .n{{color:var(--blue);font-weight:800;font-size:13px;letter-spacing:.04em}}
p{{margin:10px 0}}
.group{{font-size:10.5px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:var(--blue);margin:26px 0 2px;display:flex;align-items:center;gap:10px;break-after:avoid}}
.group::before{{content:"";width:8px;height:8px;border-radius:50%;background:var(--blue)}}
.fig{{margin:26px 0 12px;text-align:center;break-inside:avoid}}
.fig svg{{width:100%;max-width:560px;height:auto;display:block;margin:0 auto;overflow:visible}}
.fig-t{{font-family:var(--font);font-size:16px;font-weight:700;fill:var(--head)}}
.fig-c{{font-family:var(--font);font-size:28px;font-weight:800;fill:#fff;letter-spacing:.02em}}
.fig figcaption{{font-size:12.5px;color:var(--muted);margin-top:8px}}
.tw{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;margin:8px 0 6px}}
th{{text-align:left;font-size:9.5px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding:8px 12px 8px 0;border-bottom:1.5px solid var(--rule)}}
td{{padding:12px 12px 12px 0;border-bottom:1px solid var(--rule);vertical-align:top;font-size:13px;line-height:1.55}}
tr{{break-inside:avoid}}
td.idc{{white-space:nowrap;width:1%}}
.pill{{display:inline-block;background:var(--blue-soft);color:var(--blue);font-weight:800;font-size:10.5px;letter-spacing:.05em;border-radius:999px;padding:3px 10px}}
.tag{{display:inline-block;background:var(--blue-soft);color:var(--blue);font-weight:800;font-size:10px;letter-spacing:.04em;border-radius:999px;padding:1px 7px;margin:1px 2px 1px 0;white-space:nowrap}}
code{{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;font-size:.88em;background:#F1F4FA;color:var(--head);padding:1px 6px;border-radius:6px}}
strong{{color:var(--head)}}
.refs{{list-style:none;margin:12px 0 0;padding:0;display:grid;gap:14px;font-size:12.5px;color:var(--text)}}
.refs li{{padding-left:16px;position:relative;line-height:1.6;overflow-wrap:anywhere}}
.refs li::before{{content:"";position:absolute;left:0;top:.6em;width:6px;height:6px;border-radius:50%;background:var(--blue)}}
.refs a{{color:var(--blue);text-decoration:none}}

{extra_css}
@media (max-width:640px){{
  .doc{{padding:32px 22px 40px}}
  .cover{{padding:36px 22px}}
  td{{font-size:12.5px}}
}}

@page{{size:A4;margin:18mm 17mm 20mm}}
@page{{@bottom-center{{content:counter(page);font-family:"DM Sans",sans-serif;font-size:9pt;color:#7A879E}}}}
@page :first{{margin:0;@bottom-center{{content:none}}}}
@media print{{
  body{{background:#fff;padding:0}}
  .bar{{display:none}}
  .paper{{box-shadow:none;border-radius:0;max-width:none;margin:0}}
  .cover{{aspect-ratio:auto;height:290mm;break-after:page;padding:0 20mm}}
  .doc{{padding:0;font-size:10.5pt}}
  td{{font-size:9.6pt}}
  .cover-cat{{width:76mm}}
}}
</style>

<div class="bar"><span><b>Doc2All</b> · report preview</span><span>A4 · the PDF is made from this page</span></div>

<section class="paper cover">
  <div class="kicker">Application Security Technologies · Project report</div>
  {svg}
  <h1>Doc2All</h1>
  <p class="sub">Scan, convert and clean your documents safely</p>
  <div class="bar-accent"></div>
  <p class="who">Amos Ishimwe</p>
  <p class="meta">Student number 223019604<br>24 November 2026<br>Source code: <a href="https://github.com/amos-rw/doc2all">github.com/amos-rw/doc2all</a></p>
</section>

<article class="paper doc">
  <div class="block">
    <div class="kicker">Abstract</div>
    <p class="lead">{abstract.replace("**Keywords:**", "<br><br><strong>Keywords:</strong>")}</p>
  </div>

  <div class="block">
    <div class="kicker">Contents</div>
    <ul class="contents">{contents_html}</ul>
  </div>

  <div class="block">
    <h2><span class="num">1</span>Introduction</h2>
    {render(intro)}
  </div>

  <div class="block">
    <h2><span class="num">2</span>Objectives</h2>
    {render(objs)}
  </div>

  <div class="block">
    <h2><span class="num">3</span>Requirements</h2>
    {render(reqs)}
  </div>

  <div class="block">
    <h2><span class="num">4</span>Design</h2>
    {render(design_intro)}
  </div>
</article>

<section class="paper land">{render(design_41)}{dfd_html}</section>

<article class="paper doc">
  <div class="block">
    {render(design_b)}
  </div>
</article>

<section class="paper land">{render(screens_intro)}{screen_map()}</section>

<article class="paper doc">
  <div class="block">{screen_pages(screens_table)}</div>
</article>

<section class="paper land">{render(data_intro)}{data_html}</section>

<article class="paper doc">
  <div class="block">{render(data_tables)}</div>
</article>

<section class="paper land">{render(calls_intro)}{calls_figure}<div class="checks">{render(calls_checks)}</div></section>

<article class="paper doc">
  <div class="block">{calls_tables}{render(calls_after)}</div>

  <div class="block">
    <div class="kicker">References</div>
    {refs_html(refs)}
  </div>
</article>
"""

out = root / "docs" / "design" / "doc2all-report.html"
out.write_text(page, encoding="utf-8")
print("written", out, len(page))
