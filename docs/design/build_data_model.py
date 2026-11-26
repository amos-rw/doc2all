"""Builds docs/design/doc2all-data-model.html: what Doc2All saves, how the pieces connect and what protects them.
The tables below are the single source of the data model. Run: python -I docs/design/build_data_model.py"""
import html
import pathlib

design = pathlib.Path(__file__).resolve().parent

# key: (title, group, what it is, requirements, [(column, what it holds, protection mark or "")])
TABLES = {
    "users": ("Users", "account", "One row per person.", "SR-01 SR-06 SR-27", [
        ("id", "random, 128 bits", "random"), ("email", "one account per address", ""),
        ("email_confirmed_at", "empty until the emailed code is entered", ""),
        ("password_hash", "slow, salted hash (Argon2id). Never the password", "hash"),
        ("role", "user or administrator", ""), ("email_code_step", "can be off only with two passkeys or more", ""),
        ("file_notices, finish_sound", "on or off", ""), ("created_at", "", "")]),
    "passkeys": ("Passkeys", "account", "A user can have several.", "SR-28", [
        ("id", "random", "random"), ("user_id", "whose it is", "owner"),
        ("credential_id", "which key the device used", ""), ("public_key", "public half only. The private half stays on the device", ""),
        ("sign_count", "helps notice a copied key", ""), ("name", "for example Laptop", ""), ("added_at, last_used_at", "", "")]),
    "codes": ("One-time codes", "account", "Codes sent by email.", "SR-25 SR-26", [
        ("id", "", ""), ("user_id", "whose it is", "owner"), ("purpose", "confirm email, sign in, reset or change", ""),
        ("code_hash", "hash made with a server secret. Never the code", "hash"), ("expires_at", "10 minutes", ""),
        ("wrong_tries", "dead at 5", ""), ("used_at", "works once", "")]),
    "sessions": ("Sessions", "account", "Who is signed in now.", "SR-03 SR-27", [
        ("key", "random, kept in an HTTP-only cookie", "random"), ("user_id", "whose it is", "owner"),
        ("second_step_at", "empty means not signed in yet", ""), ("confirmed_at", "second step done again, counts for 5 minutes", ""), ("passkey_challenge", "new each time, works once", ""),
        ("device_name", "shown in Settings", ""), ("last_seen_at", "ends after 30 minutes idle", "")]),
    "devices": ("Known devices", "account", "Needed to notice a sign-in on a new device.", "SR-29", [
        ("id", "", ""), ("user_id", "whose it is", "owner"), ("device_hash", "hash of a random value in a cookie", "hash"),
        ("device_name", "for example Phone", ""), ("first_seen_at, last_seen_at", "", "")]),
    "attempts": ("Attempt counters", "limit", "Counts tries, so limits survive a restart.", "SR-02 SR-09 SR-25", [
        ("id", "", ""), ("kind", "sign-in, code sent or upload", ""),
        ("who_hash", "hash of the email, network address or user id", "hash"), ("at, success", "removed after 24 hours", "")]),
    "files": ("Files", "work", "The record. The content sits in the private folder.", "SR-05 SR-08 SR-10 SR-18", [
        ("id", "random, 128 bits", "random"), ("owner_id", "checked on every request", "owner"),
        ("job_id", "empty for an upload, set for a result", ""), ("shown_name", "for display only, never a path", ""),
        ("stored_name", "random name in the private folder", "random"), ("type", "decided from the first bytes", ""),
        ("size, pages", "within the limits", ""), ("delete_after", "upload time plus 24 hours", ""),
        ("deleted_at", "set when the content is gone", "")]),
    "jobs": ("Jobs", "work", "One piece of work on one file.", "SR-12 SR-15 SR-17", [
        ("id", "random, 128 bits", "random"), ("owner_id", "checked on every request", "owner"), ("file_id", "the upload", ""),
        ("action", "convert, clean, scan or black out", ""), ("choices", "what the user chose to keep", ""),
        ("outside_ocr_agreed_at", "empty means the text stays here", ""), ("status", "waiting, running, done or failed", ""),
        ("started_at, finished_at", "stopped after 60 seconds", ""), ("error_code", "a code, never file content", "")]),
    "reports": ("Safety reports", "work", "The proof shown to the user.", "SR-15 SR-18", [
        ("id", "random", "random"), ("job_id", "owner is the job's owner", "owner"),
        ("result", "all clear, something kept or problem", ""), ("created_at", "", "")]),
    "findings": ("Findings", "work", "One line of a report.", "SR-15 SR-19", [
        ("id", "", ""), ("report_id", "which report", ""), ("kind", "macro, author, phone number and so on", ""),
        ("how_many", "a number. Never the value that was found", ""), ("action", "removed, kept or still there", "")]),
    "notices": ("Notices", "account", "What the bell shows.", "SR-29", [
        ("id", "", ""), ("user_id", "whose it is", "owner"), ("kind", "the text is built from this", ""),
        ("file_id", "only for file notices", ""), ("pinned", "security notices wait for an answer", ""),
        ("created_at, read_at, answered_at", "", "")]),
    "audit": ("Audit log", "log", "Who did what, and when. Lines are only added.", "SR-19 SR-20", [
        ("id, at", "order and time", ""), ("actor_id", "the random user id only. No name, no email", ""),
        ("action, result", "for example Clean file, OK", ""), ("target_id", "file or job id. No file name", ""),
        ("previous_hash", "fingerprint of the line before, made with a server secret", "hash")]),
}

# box position and the lines shown on the drawing
BOXES = {
    "passkeys": (20, 20, 200, ["public key only"]), "codes": (20, 130, 200, ["saved as a hash", "10 minutes, one use"]),
    "sessions": (20, 260, 200, ["30 minutes idle"]), "devices": (20, 370, 200, ["saved as a hash"]),
    "users": (350, 160, 200, ["password as a hash", "role", "settings"]), "attempts": (350, 20, 200, ["limits on tries"]),
    "notices": (350, 370, 200, ["pinned if security"]),
    "files": (660, 40, 200, ["random id, owner", "24 hours"]), "jobs": (660, 190, 200, ["sandbox work", "choices, consent"]),
    "reports": (660, 340, 200, ["result"]), "findings": (930, 340, 170, ["counts, no values"]),
    "audit": (20, 510, 1080, ["only added, never edited  ·  user id only  ·  no name, no email, no file name"]),
}

# path, label, label x, label y, label anchor
LINKS = [
    ("M350 185 H325 V55 H222", "has", 265, 47, "middle"),
    ("M350 205 H310 V175 H222", "asks for", 265, 167, "middle"),
    ("M350 235 H310 V295 H222", "signs in", 265, 287, "middle"),
    ("M350 260 H325 V405 H222", "uses", 265, 397, "middle"),
    ("M450 258 V368", "receives", 458, 320, "start"),
    ("M550 190 H605 V75 H658", "owns", 612, 100, "start"),
    ("M730 130 V188", "is worked on", 722, 164, "end"),
    ("M800 190 V132", "makes results", 808, 164, "start"),
    ("M760 280 V338", "ends with", 768, 314, "start"),
    ("M860 375 H928", "lists", 894, 367, "middle"),
]

# what happens to each table: (after 24 hours, after "delete my account")
FATE = {
    "users": ("stays", "removed"), "passkeys": ("stays", "removed"), "codes": ("removed", "removed"),
    "sessions": ("removed", "removed"), "devices": ("stays", "removed"), "attempts": ("removed", "stays 24 h"),
    "files": ("content removed", "removed"), "jobs": ("stays", "removed"), "reports": ("stays", "removed"),
    "findings": ("stays", "removed"), "notices": ("stays", "removed"), "audit": ("stays", "stays"),
}

WHEN = [
    ("File contents (uploads and results)", "After 24 hours, or at once when the user presses Delete"),
    ("File records, jobs, reports, findings (the history)", "When the user removes them from History, or deletes the account"),
    ("One-time codes", "After use or after 10 minutes"),
    ("Sessions", "At sign-out, or after 30 minutes idle"),
    ("Attempt counters", "After 24 hours"),
    ("Users, passkeys, known devices, notices", "When the account is deleted"),
    ("Audit log", "Stays. It never holds a name, an email, a file name or file content"),
]

DECISIONS = [
    ("Database", "Use PostgreSQL.", "It can let the app add and read audit lines but never change them. SQLite cannot limit one table like that."),
    ("New device notice", "Add one more needed cookie that holds a random value.", "Without it the app cannot know a device is new. The Privacy screen would list three cookies."),
    ("History", "Keep the file name in History after the content is deleted, until the user removes it.", "The user sees what happened. The name can itself be personal, so it can be removed."),
    ("Administrator", "Show ids on the Records screen, never file names.", "A file name can reveal what a document is about."),
    ("Audit log", "Give each line the fingerprint of the line before.", "Someone with database access who changes a line can then be noticed."),
]


def esc(text):
    return html.escape(text, quote=True)


def height(key):
    return 70 if key == "audit" else 52 + 19 * len(BOXES[key][3])


def drawing(still=False):
    out = ['<svg viewBox="0 0 1120 600" role="img" aria-label="Users sit in the middle. Account tables hang on the left. '
           'A user owns files, a job works on a file and ends with a report and its findings. The audit log keeps only the user id.">',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           '<path class="mk" d="M0 1L9.5 5L0 9z"/></marker></defs>']
    for path, label, x, y, anchor in LINKS:
        out.append(f'<path class="ln" d="{path}" marker-end="url(#a)"/><text class="lb" x="{x}" y="{y}" text-anchor="{anchor}">{label}</text>')
    out.append('<path class="ln loose" d="M590 258 V508" marker-end="url(#a)"/><text class="lb" x="598" y="475">writes lines, id only</text>')
    out.append('<path class="ln" d="M550 258 H590"/>')
    for key, (x, y, w, lines) in BOXES.items():
        title, group = TABLES[key][0], TABLES[key][1]
        h = height(key)
        if not still:
            out.append(f'<a href="#t-{key}" aria-label="{esc(title)}: details">')
        out.append(f'<g class="bx {group}" data-a="{FATE[key][0]}" data-b="{FATE[key][1]}">'
                   f'<rect class="lip" x="{x}" y="{y + 5}" width="{w}" height="{h}" rx="16"/><rect class="face" x="{x}" y="{y}" width="{w}" height="{h}" rx="16"/>'
                   f'<text class="tt" x="{x + 16}" y="{y + 28}">{esc(title)}</text>')
        for i, line in enumerate(lines):
            out.append(f'<text class="sub" x="{x + 16}" y="{y + 50 + 19 * i}">{esc(line)}</text>')
        for view, text in () if still else (("a", FATE[key][0]), ("b", FATE[key][1])):
            bw = 14 + 7.4 * len(text)
            kind = "keep" if text == "stays" else "gone" if text == "removed" else "part"
            out.append(f'<g class="fate {view} {kind}"><rect x="{x + w - bw - 8}" y="{y - 11}" width="{bw}" height="22" rx="11"/>'
                       f'<text x="{x + w - bw / 2 - 8}" y="{y + 4}" text-anchor="middle">{text}</text></g>')
        out.append("</g>" if still else "</g></a>")
    out.append("</svg>")
    return "".join(out)


MARKS = {"hash": "saved as hash", "random": "random", "owner": "owner check"}


def cards():
    out = []
    for key, (title, group, what, refs, columns) in TABLES.items():
        rows = "".join(
            f'<li><code>{esc(c)}</code><span>{esc(d)}</span>' + (f'<em class="m {m}">{MARKS[m]}</em>' if m else "") + "</li>"
            for c, d, m in columns)
        tags = "".join(f'<span class="ref">{r}</span>' for r in refs.split())
        out.append(f'<article class="card {group}" id="t-{key}"><h3>{esc(title)}</h3><p>{esc(what)}</p><ul>{rows}</ul><div class="refs">{tags}</div></article>')
    return "".join(out)


CSS = """
/* Layout: one drawing with three views (all, after 24 hours, account deleted), then every table as a card, deletion rules and choices. */
:root{--bg:#F3F7FD;--surface:#FFFFFF;--ink:#14305C;--muted:#586C90;--line:#D6E0F0;--edge:#BFCCE4;--primary:#2F6BFF;--primary-edge:#1B4BC4;--on-primary:#FFFFFF;--primary-text:#2257D8;
--account:#EAF1FF;--account-e:#2F6BFF;--work:#DDF4F9;--work-e:#0E8DA6;--limit:#FFF0DE;--limit-e:#DB7C2B;--log:#E9E7FB;--log-e:#6B5FD3;
--gone:#C73935;--gone-bg:#FDE3E1;--keep:#13744A;--keep-bg:#DAF5E8;--part:#8A5200;--part-bg:#FFEBC2;
--font:"Nunito",ui-rounded,"Segoe UI",system-ui,sans-serif;--mono:"DM Mono",ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1730;--surface:#16264A;--ink:#EAF0FB;--muted:#A3B3D1;--line:#263A63;--edge:#0A1226;--primary:#5B8CFF;--primary-edge:#3566E0;--on-primary:#0D1730;--primary-text:#9DBCFF;
--account:#1B2F5B;--account-e:#5B8CFF;--work:#0F3646;--work-e:#3CC8E4;--limit:#46301D;--limit-e:#F5A862;--log:#2B2856;--log-e:#A59BF5;--gone:#FF8E8B;--gone-bg:#44232B;--keep:#3DD592;--keep-bg:#123B33;--part:#FFC862;--part-bg:#46371A;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0D1730;--surface:#16264A;--ink:#EAF0FB;--muted:#A3B3D1;--line:#263A63;--edge:#0A1226;--primary:#5B8CFF;--primary-edge:#3566E0;--on-primary:#0D1730;--primary-text:#9DBCFF;
--account:#1B2F5B;--account-e:#5B8CFF;--work:#0F3646;--work-e:#3CC8E4;--limit:#46301D;--limit-e:#F5A862;--log:#2B2856;--log-e:#A59BF5;--gone:#FF8E8B;--gone-bg:#44232B;--keep:#3DD592;--keep-bg:#123B33;--part:#FFC862;--part-bg:#46371A;color-scheme:dark}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font:600 16px/1.5 var(--font);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.wrap{max-width:1180px;margin:0 auto;padding-block:30px 64px;display:flex;flex-direction:column;gap:36px}
h1,h2,h3{font-weight:900;line-height:1.15;margin:0;text-wrap:balance}h1{font-size:clamp(28px,4.6vw,42px)}h2{font-size:clamp(22px,3vw,28px)}h3{font-size:18px}
p{margin:0}header,section{display:flex;flex-direction:column;gap:14px;min-width:0}header{gap:8px}header p{color:var(--muted);max-width:62ch}
.brand{font-weight:900;font-size:20px}.brand b{color:var(--primary)}
.eyebrow{font-size:12.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.views{display:flex;gap:12px;flex-wrap:wrap}
.btn{font:inherit;font-weight:900;font-size:14px;letter-spacing:.03em;text-transform:uppercase;cursor:pointer;background:var(--surface);color:var(--primary-text);border:2px solid var(--edge);border-radius:14px;box-shadow:0 4px 0 var(--edge);padding:8px 18px}
.btn[aria-pressed="true"]{background:var(--primary);border-color:var(--primary);color:var(--on-primary);box-shadow:0 4px 0 var(--primary-edge)}
.btn:focus-visible,svg a:focus-visible{outline:3px solid var(--primary);outline-offset:3px}
.scroll{overflow-x:auto;background:var(--surface);border:2px solid var(--line);border-radius:26px;padding:18px 12px 12px}
svg{display:block;width:100%;min-width:900px;height:auto;font-family:var(--font)}
.face{stroke-width:2.5}.lip{stroke:none}
.bx.account .face{fill:var(--account);stroke:var(--account-e)}.bx.account .lip{fill:var(--account-e)}
.bx.work .face{fill:var(--work);stroke:var(--work-e)}.bx.work .lip{fill:var(--work-e)}
.bx.limit .face{fill:var(--limit);stroke:var(--limit-e)}.bx.limit .lip{fill:var(--limit-e)}
.bx.log .face{fill:var(--log);stroke:var(--log-e)}.bx.log .lip{fill:var(--log-e)}
.tt{font-size:17px;font-weight:900;fill:var(--ink)}.sub{font-size:13px;font-weight:700;fill:var(--muted)}
.ln{fill:none;stroke:var(--ink);stroke-width:2.2}.ln.loose{stroke-dasharray:7 6;stroke:var(--log-e)}.mk{fill:var(--ink)}
.lb{font-size:12.5px;font-weight:800;fill:var(--muted)}
.fate{display:none}.fate text{font-size:12px;font-weight:900}
.fate.gone rect{fill:var(--gone-bg);stroke:var(--gone)}.fate.gone text{fill:var(--gone)}
.fate.keep rect{fill:var(--keep-bg);stroke:var(--keep)}.fate.keep text{fill:var(--keep)}
.fate.part rect{fill:var(--part-bg);stroke:var(--part)}.fate.part text{fill:var(--part)}
[data-view="a"] .fate.a,[data-view="b"] .fate.b{display:inline}
[data-view="a"] .bx[data-a="removed"] .face,[data-view="b"] .bx[data-b="removed"] .face{stroke-dasharray:7 6;fill:var(--surface)}
.legend{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--muted);font-size:14px}.legend span{display:inline-flex;gap:8px;align-items:center}
.legend i{width:22px;height:15px;border-radius:5px;border:2px solid}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,340px),1fr));gap:18px}
.card{background:var(--surface);border:2px solid var(--line);border-top:8px solid var(--account-e);border-radius:18px;padding:14px 18px 16px;display:flex;flex-direction:column;gap:8px;min-width:0;scroll-margin-top:16px}
.card.work{border-top-color:var(--work-e)}.card.limit{border-top-color:var(--limit-e)}.card.log{border-top-color:var(--log-e)}.card:target{outline:3px solid var(--primary)}
.card p{color:var(--muted);font-size:14.5px}.card ul{list-style:none;margin:0;padding:0}
.card li{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line);font-size:14px}
.card li span{color:var(--muted);flex:1 1 150px;min-width:0}
code{font-family:var(--mono);font-size:12.5px;font-weight:500;overflow-wrap:anywhere}
.m{font-style:normal;font-size:11px;font-weight:900;border-radius:99px;padding:1px 9px;white-space:nowrap}
.m.hash{background:var(--log);color:var(--ink)}.m.random{background:var(--account);color:var(--ink)}.m.owner{background:var(--keep-bg);color:var(--keep)}
.refs{display:flex;flex-wrap:wrap;gap:5px;margin-top:auto}.ref{font-family:var(--mono);font-size:11.5px;padding:1px 8px;border-radius:99px;border:1px solid var(--edge)}
.tw{overflow-x:auto;background:var(--surface);border:2px solid var(--line);border-radius:18px;padding:4px 18px}
table{border-collapse:collapse;width:100%}td{padding:12px 16px 12px 0;border-bottom:1px solid var(--line);vertical-align:top;font-size:15px;min-width:180px}
tr:last-child td{border-bottom:0}td+td{color:var(--muted)}
ol{margin:0;padding:0;list-style:none;counter-reset:q;display:grid;gap:12px}
ol li{counter-increment:q;display:grid;grid-template-columns:34px minmax(0,1fr);gap:14px;background:var(--surface);border:2px solid var(--line);border-bottom-width:5px;border-radius:18px;padding:14px 18px}
ol li::before{content:counter(q);width:34px;height:34px;border-radius:11px;background:var(--primary);color:var(--on-primary);display:grid;place-items:center;font-weight:900}
ol b{display:block}ol span{color:var(--muted);font-size:14.5px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

page = f"""<title>Doc2All Data Model</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&family=DM+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header><div class="brand">Doc<b>2</b>All</div><span class="eyebrow">Design · Data model</span><h1>What Doc2All saves</h1>
<p>Twelve tables, how they connect and what protects them. File contents are kept in a private folder, outside the database. Press a box to read its columns.</p></header>
<section aria-label="Drawing" id="draw" data-view="all">
<div class="views" role="group" aria-label="Show what is removed"><button class="btn" type="button" data-v="all" aria-pressed="true">Everything</button><button class="btn" type="button" data-v="a" aria-pressed="false">After 24 hours</button><button class="btn" type="button" data-v="b" aria-pressed="false">Account deleted</button></div>
<div class="scroll">{drawing()}</div>
<div class="legend"><span><i style="background:var(--account);border-color:var(--account-e)"></i>The account</span><span><i style="background:var(--work);border-color:var(--work-e)"></i>The work on files</span><span><i style="background:var(--limit);border-color:var(--limit-e)"></i>Limits</span><span><i style="background:var(--log);border-color:var(--log-e)"></i>The log</span></div>
</section>
<section><h2>When each thing is removed</h2><div class="tw"><table>{"".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in WHEN)}</table></div></section>
<section><h2>Who can touch the database</h2><div class="tw"><table>
<tr><td>The app</td><td>Reads and writes the tables. On the audit log it can only add and read</td></tr>
<tr><td>The setup account</td><td>Owns the tables. Used only to create or change them, never while the app runs</td></tr>
<tr><td>The sandbox runner</td><td>No access at all</td></tr></table></div></section>
<section><h2>Every table</h2><div class="grid">{cards()}</div></section>
<section><h2>Five decisions</h2><ol>{"".join(f"<li><div><b>{esc(t)}: {esc(p)}</b><span>{esc(w)}</span></div></li>" for t, p, w in DECISIONS)}</ol></section>
</div>
<script>
(function(){{
  var draw=document.getElementById('draw'),b=[].slice.call(draw.querySelectorAll('.btn'));
  b.forEach(function(x){{x.addEventListener('click',function(){{draw.setAttribute('data-view',x.dataset.v);b.forEach(function(y){{y.setAttribute('aria-pressed',y===x)}})}})}});
  [].slice.call(draw.querySelectorAll('svg a')).forEach(function(a){{a.addEventListener('click',function(e){{e.preventDefault();var t=document.querySelector(a.getAttribute('href'));t.scrollIntoView({{block:'start'}});}})}});
}})();
</script>
"""
(design / "doc2all-data-model.html").write_text(page, encoding="utf-8")
print("built", len(page), "bytes,", len(TABLES), "tables")


# ---------- the still figure for the report (light colours, scoped so the report's own styles cannot touch it) ----------
PRINT_CSS = """
.dm{margin:6px 0 0;text-align:center}.dm svg{display:block;width:100%;height:auto;margin:0 auto;font-family:"DM Sans",sans-serif}
.dm .face{stroke-width:2.2}.dm .lip{stroke:none}
.dm .account .face{fill:#EAF1FF;stroke:#2F6BFF}.dm .account .lip{fill:#2F6BFF}
.dm .work .face{fill:#DDF4F9;stroke:#0E8DA6}.dm .work .lip{fill:#0E8DA6}
.dm .limit .face{fill:#FFF0DE;stroke:#DB7C2B}.dm .limit .lip{fill:#DB7C2B}
.dm .log .face{fill:#E9E7FB;stroke:#6B5FD3}.dm .log .lip{fill:#6B5FD3}
.dm .tt{font-size:17px;font-weight:800;fill:#14305C}.dm text.sub{font-size:13px;font-weight:500;fill:#586C90;margin:0}
.dm .ln{fill:none;stroke:#14305C;stroke-width:2}.dm .ln.loose{stroke-dasharray:7 6;stroke:#6B5FD3}.dm .mk{fill:#14305C}
.dm .lb{font-size:12.5px;font-weight:700;fill:#586C90}
.dm figcaption{font-size:12.5px;color:#7A879E;margin-top:8px}
@media print{.dm svg{width:auto;height:136mm;max-width:100%}.dm figcaption{font-size:9pt;margin-top:2mm}}
"""
still = drawing(still=True).replace('id="a"', 'id="dm-a"').replace("url(#a)", "url(#dm-a)")
(design / "_data_print.html").write_text(
    f'<style>{PRINT_CSS}</style><figure class="dm">{still}<figcaption>Figure 4.9 · What Doc2All saves and how it connects</figcaption></figure>',
    encoding="utf-8")

# ---------- notes for development ----------
lines = ["# Data model", "", "<!-- Built by build_data_model.py. Edit the builder, not this file. -->", "",
         "The database is **PostgreSQL**. File contents live in a private folder, outside the database.",
         "Interactive drawing: open `doc2all-data-model.html` in a browser.", "", "```mermaid", "erDiagram"]
for a, verb, b in [("USERS", "has", "PASSKEYS"), ("USERS", "asks_for", "ONE_TIME_CODES"), ("USERS", "signs_in", "SESSIONS"),
                   ("USERS", "uses", "KNOWN_DEVICES"), ("USERS", "receives", "NOTICES"), ("USERS", "owns", "FILES"),
                   ("FILES", "is_worked_on", "JOBS"), ("JOBS", "makes_results", "FILES"), ("JOBS", "ends_with", "REPORTS"),
                   ("REPORTS", "lists", "FINDINGS")]:
    lines.append(f"  {a} ||--o{{ {b} : {verb}")
lines += ["  ATTEMPT_COUNTERS", "  AUDIT_LOG", "```", "",
          "The audit log has no foreign key to users: it keeps the random user id, so it survives account deletion.", "",
          "## Tables"]
for key, (title, _group, what, refs, columns) in TABLES.items():
    lines += ["", f"### {title}", "", f"{what} Requirements: {refs.replace(' ', ', ')}.", "",
              "| Column | What it holds | Protection |", "| --- | --- | --- |"]
    lines += [f"| `{c}` | {d} | {MARKS.get(m, '')} |" for c, d, m in columns]
lines += ["", "## When each thing is removed", "", "| Data | Removed |", "| --- | --- |"]
lines += [f"| {a} | {b} |" for a, b in WHEN]
lines += ["", "## Database accounts", "",
          "- The app account reads and writes the tables. On the audit log it can only add and read.",
          "- The setup account owns the tables and runs changes. The running app never uses it.",
          "- The sandbox runner has no database account.", "", "## Decisions", ""]
lines += [f"- **{t}:** {p} {w}" for t, p, w in DECISIONS]
lines += ["", "## Limit to remember", "",
          "The fingerprint chain shows a changed line, or a line removed from the middle. It cannot show that the newest",
          "lines were cut off. Keep a copy of the latest fingerprint outside the database if that matters."]
(design / "data-model.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("print figure and data-model.md written")
