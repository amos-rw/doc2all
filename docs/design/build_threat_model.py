"""Builds two things from one drawing, so the coordinates live in one place:
  1. docs/design/doc2all-threat-model.html  (interactive: tour, click to explore)  from threat-model.src.html
  2. docs/design/_dfd_print.html            (still figure for the report; steps 1 to 9 are numbered on the drawing)
Run: python -I docs/design/build_threat_model.py
"""
import re
from pathlib import Path

root = Path(__file__).resolve().parent
src = (root / "threat-model.src.html").read_text(encoding="utf-8")
cat_html = (root / "doc2all-cat.html").read_text(encoding="utf-8")

cat_svg = re.search(r'<svg id="cat".*?</svg>', cat_html, re.S).group(0)
cat_svg = cat_svg.replace('aria-label="A ginger cat holding a document"', 'aria-hidden="true"')
css_start = cat_html.index("/* cat colours */")
css_end = cat_html.index("@media (max-width:760px)")
cat_css = cat_html[css_start:css_end]
cat_css += "@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation:none!important;transition-duration:.01ms!important}}\n"

R = 26  # corner radius of tiles

# journey step numbers drawn on the still figure: (number, x, y)
STEP_BADGES = {
    "f1": [(1, 122, 222)], "f9": [(2, 700, 64)], "f2": [(3, 284, 360)], "f3": [(5, 812, 340)], "f4": [(5, 930, 490)],
    "f5": [(7, 812, 384)], "f6": [(7, 1000, 490)], "f7": [(8, 300, 470)], "f8": [(6, 1150, 360)],
}


def make_svg(static):
    def img(name, cx, y, size=64):
        return f'<image href="icons/{name}-t.png" x="{cx - size / 2}" y="{y}" width="{size}" height="{size}" preserveAspectRatio="xMidYMid meet"/>'

    def sym(name, cx, y, size=64):
        return f'<use href="#ic-{name}" x="{cx - size / 2}" y="{y}" width="{size}" height="{size}"/>'

    def logb(x, y):
        return f'<use class="lb" href="#logb" x="{x}" y="{y}"/>'

    def wrap(i, aria, inner, extra_cls=""):
        if static:
            return f'<g>{inner}</g>'
        return f'<g class="node{extra_cls}" data-id="{i}" tabindex="0" role="button" aria-label="{aria}">{inner}</g>'

    def ring(x, y, w, h):
        return "" if static else f'<rect class="ring" x="{x - 7}" y="{y - 7}" width="{w + 14}" height="{h + 20}" rx="{R + 6}"/>'

    def badge(n, x, y):
        return f'<circle class="badge" cx="{x}" cy="{y}" r="12"/><text class="badge-t" x="{x}" y="{y + 4.6}">{n}</text>'

    def tile(i, kind, x, y, w, h, icon, label, aria, log=True, sub=None):
        cx = x + w / 2
        if sub:
            lab = (f'<text class="t-title" x="{cx}" y="{y + h - 33}" text-anchor="middle">{label}</text>'
                   f'<text class="t-sub" x="{cx}" y="{y + h - 13}" text-anchor="middle">{sub}</text>')
        else:
            lab = f'<text class="t-title" x="{cx}" y="{y + h - 15}" text-anchor="middle">{label}</text>'
        inner = f'''
  <rect class="lip {kind}" x="{x}" y="{y + 6}" width="{w}" height="{h}" rx="{R}"/>
  <rect class="face {kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{R}"/>
  {ring(x, y, w, h)}
  {icon(cx, y + 12)}
  {lab}
  {logb(x + w - 15, y + 15) if log else ""}'''
        return wrap(i, aria, inner)

    def pill(i, kind, x, y, w, h, icon, label, aria, log=True, extra=""):
        ih = min(64, h - 16)
        inner = f'''
  <rect class="lip {kind}" x="{x}" y="{y + 6}" width="{w}" height="{h}" rx="{R}"/>
  <rect class="face {kind}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{R}"/>
  {ring(x, y, w, h)}
  {icon(x + 16 + ih / 2, y + (h - ih) / 2, ih)}
  <text class="t-title" x="{x + 92}" y="{y + h / 2 + 5}">{label}</text>
  {logb(x + w - 17, y + 17) if log else ""}
  {extra}'''
        return wrap(i, aria, inner)

    def flow(i, d, bx, by, num, aria, opt=False):
        cls = "flow opt" if opt else "flow"
        mk = "ah-o" if opt else "ah"
        if static:
            bs = "".join(badge(n, x, y) for n, x, y in STEP_BADGES[i])
            return f'<g><path class="{cls}" d="{d}" marker-end="url(#{mk})"/>{bs}</g>'
        return wrap(i, aria, f'''
  <path class="hit" d="{d}"/>
  <path class="{cls}" d="{d}" marker-end="url(#{mk})"/>
  {badge(num, bx, by)}''', " flownode")

    def link(between, d, both=True):
        ms = ' marker-start="url(#ah)"' if both else ""
        return f'<path class="flow link" data-between="{between}" d="{d}"{ms} marker-end="url(#ah)"/>'

    nodes = [
        tile("e1", "ext", 20, 302, 130, 116, lambda cx, y: sym("browser", cx - 6, y - 2, 54) + sym("key", cx + 26, y - 6, 36), "Browser", "The person's browser, with a passkey", log=False, sub="+ passkey"),
        tile("x2", "ext", 1180, 84, 130, 116, lambda cx, y: sym("mail", cx, y), "Email service", "Email service for one-time codes", log=False),
        tile("x1", "ext optx", 1180, 302, 130, 116, lambda cx, y: img("cloud", cx, y + 6, 70), "Outside OCR", "Outside OCR service, optional", log=False),
        tile("p1", "proc", 230, 84, 140, 116, lambda cx, y: sym("key", cx, y), "Sign-in", "Sign-in and sessions"),
        tile("p2", "proc", 420, 302, 140, 116, lambda cx, y: img("shield", cx, y), "Upload gate", "Upload gate"),
        tile("p3", "proc", 640, 302, 140, 116, lambda cx, y: sym("gear", cx, y), "Job manager", "Job manager and report"),
        tile("p4", "proc", 895, 302, 140, 116, lambda cx, y: img("sealed-box", cx, y + 4, 70), "Runner", "Job runner in the sandbox"),
        pill("d1", "store", 420, 92, 320, 100, lambda cx, y, s=56: img("database", cx, y, s), "Database", "Database"),
    ]
    chip_badge = badge(9, 858, 562) if static else ""
    chip = f'''<g {'' if static else 'class="node" data-id="t" tabindex="0" role="button" aria-label="Deletion timer, files are deleted after 24 hours"'}>
    <rect class="chip" x="868" y="541" width="196" height="42" rx="21"/>
    <circle class="clk" cx="893" cy="562" r="10"/><path class="clk-h" d="M893 556 V562 L898 565"/>
    <text class="t-lab" x="912" y="567">gone in 24 h</text>{chip_badge}</g>'''
    nodes.append(pill("d2", "store", 420, 520, 670, 84, lambda cx, y, s=56: img("locked-folder", cx, y, s), "Private files", "Private file store", extra=chip))
    nodes.append(pill("d3", "store", 230, 632, 860, 68, lambda cx, y, s=56: img("log-page", cx, y, s), "Audit log", "Audit log", log=False,
                      extra=badge(10, 1062, 666) if static else ""))

    links = [
        link("p1 d1", "M370 142 H418"),
        link("d1 p2", "M490 192 V300"),
        link("d1 p3", "M710 192 V300"),
        link("p2 d2", "M490 424 V518", both=False),
        '<path class="flow link" data-between="d2 p3" d="M740 518 V428" marker-end="url(#ah)"/>',
        link("p2 p3", "M560 360 H638", both=False),
    ]
    if static:
        links.append(badge(4, 490, 497))

    flows = [
        flow("f1", "M122 302 V142 H228", 122, 222, 1, "Flow 1, sign-in details"),
        flow("f2", "M150 360 H418", 284, 360, 2, "Flow 2, the file and choices"),
        flow("f3", "M780 340 H893", 812, 340, 3, "Flow 3, job id to the runner"),
        flow("f4", "M930 520 V426", 930, 490, 4, "Flow 4, file copy into the sandbox"),
        flow("f5", "M893 384 H782", 812, 384, 5, "Flow 5, findings back"),
        flow("f6", "M1000 426 V518", 1000, 490, 6, "Flow 6, result out of the sandbox"),
        flow("f7", "M680 424 V470 H503 a13 13 0 0 0 -26 0 H85 V428", 300, 470, 7, "Flow 7, report and download"),
        flow("f8", "M1035 360 H1178", 1150, 360, 8, "Flow 8, text to an outside service, only with consent", opt=True),
        flow("f9", "M300 84 V64 H1150 V142 H1178", 700, 64, 9, "Flow 9, one-time code sent by email"),
    ]

    vb = "0 36 1340 706" if static else "0 0 1340 760"
    role = 'role="img" aria-label="Data-flow diagram of a file journey through Doc2All, from the browser through the upload gate, private storage and the sandbox, to the report and deletion."' if static \
        else 'role="group" aria-label="Data-flow diagram. Use the tour above, or press any part."'
    return f'''<svg class="dfd" id="dfd" viewBox="{vb}" {role}>
  <defs>
    <marker id="ah" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="5.2" markerHeight="5.2" orient="auto-start-reverse"><path class="mk" d="M0 1 L9.4 5 L0 9z"/></marker>
    <marker id="ah-o" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="5.2" markerHeight="5.2" orient="auto-start-reverse"><path class="mk-o" d="M0 1 L9.4 5 L0 9z"/></marker>
    <g id="logb"><circle class="logc" r="10"/><line class="logl" x1="-4.5" y1="-3.4" x2="4.5" y2="-3.4"/><line class="logl" x1="-4.5" y1="0" x2="4.5" y2="0"/><line class="logl" x1="-4.5" y1="3.4" x2="1.5" y2="3.4"/></g>
    <symbol id="ic-browser" viewBox="0 0 64 64">
      <rect x="5" y="10" width="54" height="44" rx="9" fill="#fff"/>
      <path d="M5 19 a9 9 0 0 1 9 -9 h36 a9 9 0 0 1 9 9 v4 h-54z" fill="#2F6BFF"/>
      <circle cx="15" cy="17" r="2.4" fill="#fff"/><circle cx="23" cy="17" r="2.4" fill="#fff"/><circle cx="31" cy="17" r="2.4" fill="#fff"/>
      <rect x="14" y="31" width="36" height="5" rx="2.5" fill="#C9D6EA"/><rect x="14" y="41" width="24" height="5" rx="2.5" fill="#C9D6EA"/>
      <rect x="5" y="10" width="54" height="44" rx="9" fill="none" stroke="#14305C" stroke-width="3"/>
    </symbol>
    <symbol id="ic-key" viewBox="0 0 64 64">
      <rect x="30" y="27" width="31" height="10" rx="4" fill="#FFC83D" stroke="#DB7C2B" stroke-width="3"/>
      <path d="M47 37 v9 M55 37 v7" stroke="#DB7C2B" stroke-width="4.5" stroke-linecap="round"/>
      <circle cx="20" cy="32" r="14" fill="#FFC83D" stroke="#DB7C2B" stroke-width="3"/>
      <circle cx="20" cy="32" r="5.5" fill="var(--f-proc)" stroke="#DB7C2B" stroke-width="2.4"/>
    </symbol>
    <symbol id="ic-gear" viewBox="0 0 64 64">
      <g fill="#2F6BFF"><rect x="27" y="4" width="10" height="56" rx="3"/><rect x="27" y="4" width="10" height="56" rx="3" transform="rotate(45 32 32)"/><rect x="27" y="4" width="10" height="56" rx="3" transform="rotate(90 32 32)"/><rect x="27" y="4" width="10" height="56" rx="3" transform="rotate(135 32 32)"/></g>
      <circle cx="32" cy="32" r="19" fill="#2F6BFF" stroke="#1B4BC4" stroke-width="3"/>
      <circle cx="32" cy="32" r="8" fill="var(--f-proc)" stroke="#1B4BC4" stroke-width="2.4"/>
    </symbol>
    <symbol id="ic-mail" viewBox="0 0 64 64">
      <rect x="6" y="14" width="52" height="38" rx="8" fill="#fff" stroke="#14305C" stroke-width="3"/>
      <path d="M9 21 L32 39 L55 21" fill="none" stroke="#2F6BFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    </symbol>
  </defs>

  <rect class="zone" x="190" y="50" width="930" height="680" rx="26"/>
  <rect class="sbx" x="840" y="245" width="250" height="210" rx="22"/>
  <text class="t-zone" x="232" y="44">OUR SERVER</text>
  <text class="t-zone" x="1180" y="72">NOT TRUSTED</text>
  <text class="t-zone" x="20" y="290">NOT TRUSTED</text>
  <text class="t-zone" x="1180" y="290">NOT TRUSTED</text>
  <text class="t-coral" x="860" y="273">SANDBOX</text>
  <g class="tbp"><rect x="168" y="228" width="44" height="24" rx="12"/><text x="190" y="244.5">TB1</text></g>
  <g class="tbp"><rect x="818" y="233" width="44" height="24" rx="12"/><text x="840" y="249.5">TB2</text></g>
  <g class="tbp"><rect x="1098" y="228" width="44" height="24" rx="12"/><text x="1120" y="244.5">TB3</text></g>

  {chr(10).join(links)}
  {chr(10).join(flows)}
  {chr(10).join(nodes)}
</svg>'''


# 1. interactive page
out = src.replace("%%SVG%%", make_svg(False)).replace("%%CATSVG%%", cat_svg).replace("%%CATCSS%%", cat_css)
(root / "doc2all-threat-model.html").write_text(out, encoding="utf-8")
print("built interactive", len(out), "bytes")

# 2. still figure for the report (light colours fixed, so it prints the same everywhere)
FRAG_CSS = """<style>
.dfdfig{--surface:#FFFFFF;--ink:#14305C;--muted:#586C90;--line:#D6E0F0;--primary:#2F6BFF;--on-primary:#FFFFFF;
  --scan:#19B5D6;--safe:#22B573;--warn:#EF5350;--warn-soft:#FDE3E1;--coral-text:#C73935;--ginger:#F2994A;--ginger-dark:#DB7C2B;
  --f-proc:#EAF1FF;--f-store:#DDF4F9;--f-ext:#FFF0DE;--e-proc:#2F6BFF;--e-store:#19B5D6;--e-ext:#F2994A;
  --lip-proc:#1B4BC4;--lip-store:#0E8DA6;--lip-ext:#DB7C2B;--on-cyan:#FFFFFF}
.dfdfig svg.dfd{display:block;width:100%;height:auto;max-width:94%;margin:0 auto;overflow:visible;font-family:"DM Sans",ui-rounded,"Segoe UI",system-ui,sans-serif}
.dfdfig .zone{fill:var(--surface);stroke:var(--warn);stroke-width:2.2;stroke-dasharray:9 7}
.dfdfig .sbx{fill:var(--warn-soft);stroke:var(--warn);stroke-width:2.2;stroke-dasharray:9 7}
.dfdfig .lip{stroke:none}.dfdfig .lip.proc{fill:var(--lip-proc)}.dfdfig .lip.store{fill:var(--lip-store)}.dfdfig .lip.ext{fill:var(--lip-ext)}
.dfdfig .face{stroke-width:2.5}.dfdfig .face.proc{fill:var(--f-proc);stroke:var(--e-proc)}.dfdfig .face.store{fill:var(--f-store);stroke:var(--e-store)}.dfdfig .face.ext{fill:var(--f-ext);stroke:var(--e-ext)}
.dfdfig .face.optx{stroke-dasharray:7 6}
.dfdfig .chip{fill:var(--surface);stroke:var(--ginger);stroke-width:2.2}
.dfdfig .clk,.dfdfig .clk-h{fill:none;stroke:var(--ginger-dark);stroke-width:2.2;stroke-linecap:round}
.dfdfig .flow{fill:none;stroke:var(--ink);stroke-width:2.4}.dfdfig .flow.opt{stroke:var(--safe);stroke-dasharray:7 6}
.dfdfig .mk{fill:var(--ink)}.dfdfig .mk-o{fill:var(--safe)}
.dfdfig .t-title{font-size:16px;font-weight:800;fill:var(--ink)}
.dfdfig .t-lab{font-size:14px;font-weight:800;fill:var(--ink)}
.dfdfig .t-sub{font-size:12.5px;font-weight:700;fill:var(--muted)}
.dfdfig .t-zone{font-size:12px;font-weight:800;letter-spacing:.14em;fill:var(--muted)}
.dfdfig .t-coral{font-size:12px;font-weight:800;letter-spacing:.14em;fill:var(--coral-text)}
.dfdfig .badge{fill:var(--primary)}.dfdfig .badge-t{font-size:13px;font-weight:800;fill:var(--on-primary);text-anchor:middle}
.dfdfig .tbp rect{fill:var(--warn)}.dfdfig .tbp text{font-size:11.5px;font-weight:800;fill:#fff;text-anchor:middle;letter-spacing:.06em}
.logc{fill:#19B5D6}.logl{stroke:#fff;stroke-width:1.7;stroke-linecap:round}
.dfdfig .key{display:flex;flex-wrap:wrap;gap:6px 20px;justify-content:center;color:#586C90;font-size:11px;margin-top:10px}
.dfdfig .key span{display:inline-flex;align-items:center;gap:7px}
.dfdfig .sw{width:20px;height:13px;border-radius:5px;border:1.8px solid;flex:none}
.dfdfig .sw.p{background:var(--f-proc);border-color:var(--e-proc)}.dfdfig .sw.s{background:var(--f-store);border-color:var(--e-store)}
.dfdfig .sw.e{background:var(--f-ext);border-color:var(--e-ext)}.dfdfig .sw.b{background:transparent;border:2px dashed var(--warn)}
.dfdfig .dot{width:17px;height:17px;border-radius:50%;display:inline-grid;place-items:center;font-size:9.5px;font-weight:800;background:var(--primary);color:#fff;flex:none}
.dfdfig .dot.l{background:var(--scan)}
</style>"""
KEY = ('<div class="key"><span><i class="sw p"></i>Our code</span><span><i class="sw s"></i>Where data rests</span>'
       '<span><i class="sw e"></i>Outside our control</span><span><i class="sw b"></i>Trust boundary</span>'
       '<span><i class="dot">1</i>Step of the journey</span><span><i class="dot l">&#8801;</i>Writes to the audit log</span></div>')
frag = f'{FRAG_CSS}\n<figure class="dfdfig">{make_svg(True)}{KEY}<figcaption>Figure 4.1. The journey of one file through Doc2All.</figcaption></figure>'
(root / "_dfd_print.html").write_text(frag, encoding="utf-8")
print("built print figure", len(frag), "bytes")
