"""Builds docs/design/doc2all-server-interfaces.html: every call the browser can make, who may make it and what is checked.
The calls below are the single source. Run: python -I docs/design/build_server_interfaces.py"""
import html
import pathlib
import re

design = pathlib.Path(__file__).resolve().parent

# who may call: key -> (short name, meaning)
WHO = {
    "open": ("Anyone", "No sign-in needed"),
    "half": ("Password done", "The password was right, the second step is still waiting"),
    "full": ("Signed in", "Both steps done"),
    "owner": ("Owner only", "Signed in, and the item is yours. Otherwise the answer is Not found"),
    "fresh": ("Confirmed", "Signed in, and the second step was done again in the last 5 minutes"),
    "admin": ("Administrator", "Signed in with the administrator role"),
}

# group -> [(method, address, what it does, who, [checks], requirements and abuse cases, screen)]
CALLS = [
    ("Getting in", [
        ("GET", "/api/session", "Ask who I am and get the form token", "open", ["Returns only signed out, password done or signed in"], "SR-03 SR-07", "1"),
        ("POST", "/api/register", "Create an account", "open", ["Password has 12 characters or more", "Same answer when the email already has an account; its owner is told by email", "At most 3 emails an hour for one address"], "FR-09 SR-01 SR-25 SR-26 AC-13 AC-15", "2"),
        ("POST", "/api/register/confirm", "Enter the emailed code", "open", ["Code matches its hash, is under 10 minutes old and unused", "Dead after 5 wrong tries"], "FR-09 SR-25 AC-13", "2"),
        ("POST", "/api/sign-in", "Give email and password", "open", ["Refused after 5 failures in 10 minutes, for 15 minutes", "Same message for a wrong email and a wrong password", "Starts a new session key. No access yet"], "FR-01 SR-01 SR-02 SR-27 AC-07 AC-14", "1"),
        ("POST", "/api/sign-in/passkey/options", "Get a passkey challenge", "half", ["A new random challenge that works once", "Also used to confirm a change"], "SR-28", "3"),
        ("POST", "/api/sign-in/passkey", "Prove it with a passkey", "half", ["Signature, challenge and our domain are right", "New session key", "A new device creates a notice and an email"], "FR-11 SR-28 SR-29 AC-14 AC-16", "3"),
        ("POST", "/api/sign-in/code/send", "Ask for an emailed code", "half", ["Only if the account allows email codes", "At most 3 codes an hour", "Also used to confirm a change"], "FR-11 SR-25 AC-13", "3"),
        ("POST", "/api/sign-in/code", "Prove it with the code", "half", ["Same code rules", "New session key", "A new device creates a notice and an email"], "FR-11 SR-25 SR-27 SR-29 AC-14", "3"),
        ("POST", "/api/sign-out", "Sign out", "half", ["The session is destroyed on the server", "Also works when fully signed in"], "FR-01 SR-03 AC-08", "8"),
    ]),
    ("Forgot password", [
        ("POST", "/api/password/forgot", "Ask for a reset code", "open", ["Same answer for any email", "At most 3 codes an hour"], "FR-10 SR-25 SR-26 AC-15", "4"),
        ("POST", "/api/password/reset/code", "Enter the reset code", "open", ["Same code rules", "Opens only the reset, never the account", "Gives a passkey challenge when the account has a passkey"], "FR-10 SR-25 SR-26 AC-15", "4"),
        ("POST", "/api/password/reset/passkey", "Confirm with the passkey", "open", ["Only after the code", "Needed when the account has a passkey"], "SR-26 SR-28 AC-15", "4"),
        ("POST", "/api/password/reset", "Save the new password", "open", ["Code done, and passkey done when needed", "12 characters or more", "Ends every session and emails the user"], "FR-10 SR-01 SR-26 AC-15", "4"),
    ]),
    ("My account", [
        ("GET", "/api/me", "Read my settings, passkeys and devices", "full", ["Only my own data. No hashes or keys are sent"], "FR-11 SR-07", "10"),
        ("PATCH", "/api/me/settings", "Change file notices and sound", "full", ["Only these two can change here. Security notices stay on"], "NFR-11 SR-29", "10"),
        ("DELETE", "/api/me/sessions/{id}", "Sign out another device", "owner", ["The session is mine"], "SR-03 SR-04 AC-08", "10"),
        ("POST", "/api/me/confirm", "Do the second step again", "full", ["Passkey, or emailed code if the account allows it", "Same rules as sign-in", "Counts for 5 minutes"], "SR-27 AC-18", "10"),
        ("PUT", "/api/me/password", "Change my password", "fresh", ["12 characters or more", "Ends my other sessions, notice and email"], "SR-01 SR-27 SR-29 AC-18", "10"),
        ("POST", "/api/me/email", "Start changing my email", "fresh", ["Sends a code to the new address", "Same answer when that address is already in use"], "SR-25 SR-27", "10"),
        ("POST", "/api/me/email/confirm", "Finish changing my email", "fresh", ["The code is right", "Tells the old address"], "SR-27 SR-29 AC-18", "10"),
        ("POST", "/api/me/passkeys/options", "Get a challenge for a new passkey", "fresh", ["A new random challenge that works once"], "SR-27 SR-28", "10"),
        ("POST", "/api/me/passkeys", "Add a passkey", "fresh", ["The challenge is the one just given, our domain", "Saves the public key only, notice and email"], "FR-11 SR-27 SR-28 SR-29 AC-18", "10"),
        ("DELETE", "/api/me/passkeys/{id}", "Remove a passkey", "fresh", ["It is mine", "With email codes stopped, two passkeys must stay", "Notice and email"], "SR-04 SR-27 SR-28 SR-29 AC-18", "10"),
        ("PUT", "/api/me/email-code", "Allow or stop email codes", "fresh", ["Stop only when the account has at least two passkeys", "Notice and email"], "SR-27 SR-28 SR-29", "10"),
        ("DELETE", "/api/me", "Delete my account", "fresh", ["Removes files, passkeys and sessions at once", "The log keeps no name or email", "Confirms by email"], "FR-12 SR-18 SR-27 SR-29 AC-18", "10"),
    ]),
    ("Files and work", [
        ("POST", "/api/files", "Upload a file", "full", ["Type from the name and first bytes", "20 MB, 100 pages, 20 uploads an hour", "Bomb check before opening", "Random name in the private folder"], "FR-02 SR-05 SR-08 SR-09 SR-10 SR-14 AC-03 AC-04 AC-05 AC-09", "5"),
        ("GET", "/api/files/{id}/check", "See what is hidden in the file", "owner", ["Opened in the sandbox with limits", "Values are shown to the owner and never saved"], "FR-05 SR-04 SR-12 SR-13 SR-19 AC-06", "5"),
        ("GET", "/api/files/{id}/matches", "See personal data to black out", "owner", ["Opened in the sandbox", "Matches are never saved"], "FR-06 SR-04 SR-12 SR-19", "5"),
        ("POST", "/api/jobs", "Start convert, clean, scan or black out", "owner", ["The file is mine and still there", "What runs by itself is removed whatever the request says", "Outside OCR only with consent for this file", "60 seconds, memory limit, own folder"], "FR-03 FR-04 FR-05 FR-06 SR-04 SR-12 SR-13 SR-15 SR-16 SR-17 AC-05 AC-06 AC-12 AC-17", "5 6"),
        ("GET", "/api/jobs/{id}", "Ask if the work is finished", "owner", ["The job is mine", "An error is a short code, never file content"], "NFR-05 SR-04 SR-19 SR-23 AC-02", "5"),
        ("GET", "/api/jobs/{id}/report", "Read the safety report", "owner", ["The job is mine", "Counts and actions only"], "FR-07 SR-04 SR-15 AC-02 AC-12", "7"),
        ("GET", "/api/files/{id}/download", "Download a file", "owner", ["The file is mine and not deleted", "Safe download headers", "Written to the log"], "SR-04 SR-11 SR-20 SR-21 AC-01 AC-02", "7 8"),
        ("DELETE", "/api/files/{id}", "Delete a file now", "owner", ["The content is removed", "Written to the log"], "FR-08 SR-04 SR-18 AC-11", "9"),
        ("GET", "/api/history", "List my files", "full", ["Only my own entries"], "FR-08 SR-04 AC-02", "8"),
        ("DELETE", "/api/history/{id}", "Remove an entry from History", "owner", ["The entry is mine", "Any content still there is deleted too"], "FR-08 SR-04 SR-18 AC-11", "8"),
    ]),
    ("Notices", [
        ("GET", "/api/notices", "Read my notices", "full", ["Only my own"], "SR-04 SR-29", "8"),
        ("POST", "/api/notices/read", "Mark notices as read", "full", ["Only my own. A pinned notice stays pinned"], "SR-29", "8"),
        ("POST", "/api/notices/{id}/mine", "Answer: yes, it was me", "fresh", ["The notice is mine", "Removes the pin"], "SR-27 SR-29 AC-18", "8"),
        ("POST", "/api/notices/{id}/not-mine", "Answer: no, secure my account", "owner", ["Ends every other session", "Opens the password change"], "SR-03 SR-29 AC-18", "8"),
    ]),
    ("Administrator", [
        ("GET", "/api/admin/audit", "Read the audit log", "admin", ["Administrator role", "Read only. No call can change a line"], "SR-06 SR-20 AC-10", "11"),
        ("GET", "/api/admin/records", "See records of users and jobs", "admin", ["Ids, times and results only", "No file names and no content"], "SR-06 SR-19 AC-10", "11"),
    ]),
]

COMMON = [
    ("HTTPS", "Nothing travels unprotected. Security headers on every answer"),
    ("Is this call listed?", "A call that is not marked open needs a sign-in"),
    ("Form token", "A change is accepted only with the token our own page holds"),
    ("Session", "Real, not older than 30 minutes of rest, and in the right step"),
    ("Role and owner", "One place decides. Someone else's item is Not found"),
    ("Input", "Type, size and allowed values. Extra fields are ignored"),
    ("Limits", "Too many tries are refused"),
    ("Log and answer", "Important actions are logged. Errors are plain, with no inside details"),
]
ANSWERS = [("400", "Something in the request is wrong"), ("401", "Sign in first"), ("403", "Do the second step again"),
           ("404", "Not found. Also the answer for another person's item and for admin pages without the role"), ("429", "Too many tries, come back later")]
SERVER_ONLY = [("Delete after 24 hours", "A server timer. No call starts or stops it"),
               ("Make an administrator", "A command on the server. No call can give the role"),
               ("Check the audit log fingerprints", "A command on the server"),
               ("The sandbox runner", "Receives a job and a copy of the file. It has no address the browser can reach")]
CHOICES = [
    ("Reset with a passkey", "If the account has a passkey, a password reset asks for it too.", "Someone who gets into the mailbox still cannot take the account. With email codes only, the emailed code is the second step, so a passkey protects better."),
    ("Lost passkey", "Email codes can be stopped only while the account has at least two passkeys.", "If one device is lost, the other still opens the account. Losing every passkey and forgetting the password locks the account for good."),
    ("Yes, it was me", "This answer asks for the second step again.", "A person at your open computer cannot hide a security notice."),
    ("Confirmed time", "A second step done again counts for 5 minutes.", "Long enough to make a change, short enough to be safe."),
    ("Create account", "A known email gets the same answer, and its owner is told by email.", "Nobody can use this form to find which emails have accounts."),
]


def esc(text):
    return html.escape(text, quote=True)


ALL = [c for _group, calls in CALLS for c in calls]
used = set(re.findall(r"AC-\d\d", " ".join(c[5] for c in ALL)))
missing = sorted({f"AC-{i:02d}" for i in range(1, 19)} - used)
if missing:
    raise SystemExit(f"abuse cases with no call: {missing}")


def state_box(key, x, y, w, h, title, line):
    count = sum(1 for c in ALL if c[3] == key or (key == "full" and c[3] == "owner"))
    return (f'<g class="st {key}" data-who="{key}" tabindex="0" role="button" aria-pressed="false" aria-label="{esc(title)}: show its {count} calls">'
            f'<rect class="lip" x="{x}" y="{y + 5}" width="{w}" height="{h}" rx="16"/><rect class="face" x="{x}" y="{y}" width="{w}" height="{h}" rx="16"/>'
            f'<text class="tt" x="{x + w / 2}" y="{y + 28}">{esc(title)}</text><text class="sub" x="{x + w / 2}" y="{y + 49}">{esc(line)}</text>'
            + (f'<text class="num" x="{x + w / 2}" y="{y + 70}">{count} calls</text>' if h > 70 else "") + "</g>")


def drawing(still=False):
    s = ['<svg viewBox="0 0 1120 320" role="img" aria-label="Signed out becomes password done after the password, then signed in after the second step. '
         'Doing the second step again gives five minutes of confirmed access. Signing out or thirty idle minutes returns to signed out.">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="mk" d="M0 1L9.5 5L0 9z"/></marker></defs>']
    for path in ("M200 175 H316", "M500 175 H616", "M800 175 H916", "M960 220 V250 H760 V224", "M660 220 V285 H110 V224", "M710 130 V84"):
        s.append(f'<path class="ln" d="{path}" marker-end="url(#a)"/>')
    s.append('<path class="ln" d="M410 220 V285"/>')
    for x, y, text, anchor in ((260, 165, "password", "middle"), (560, 148, "second", "middle"), (560, 165, "step", "middle"),
                               (860, 148, "second step", "middle"), (860, 165, "again", "middle"), (860, 270, "after 5 minutes", "middle"),
                               (385, 305, "sign out, or 30 minutes of rest", "middle"), (720, 112, "with the role", "start")):
        s.append(f'<text class="lb" x="{x}" y="{y}" text-anchor="{anchor}">{text}</text>')
    s.append(state_box("open", 20, 130, 180, 90, "Signed out", "anyone"))
    s.append(state_box("half", 320, 130, 180, 90, "Password done", "no access yet"))
    s.append(state_box("full", 620, 130, 180, 90, "Signed in", "your own things"))
    s.append(state_box("fresh", 920, 130, 180, 90, "Confirmed", "account changes"))
    s.append(state_box("admin", 620, 14, 180, 66, "Administrator", "records, no content"))
    s.append("</svg>")
    out = "".join(s)
    if still:
        out = re.sub(r' tabindex="0" role="button" aria-pressed="false" aria-label="[^"]*"', "", out)
        out = out.replace('id="a"', 'id="si-a"').replace("url(#a)", "url(#si-a)")
    return out


def call_list():
    out = []
    for group, calls in CALLS:
        out.append(f'<div class="grp"><h3>{esc(group)}</h3>')
        for method, address, what, who, checks, refs, screen in calls:
            tags = "".join(f'<span class="ref{" ac" if r.startswith("AC") else ""}">{r}</span>' for r in refs.split())
            state = "full" if who == "owner" else who
            out.append(f'<article class="call" data-who="{state}"><div class="a"><b>{esc(what)}</b><code><i class="{method.lower()}">{method}</i> {esc(address)}</code>'
                       f'<small>Screen {screen.replace(" ", " and ")}</small></div>'
                       f'<ul>{"".join(f"<li>{esc(c)}</li>" for c in checks)}</ul>'
                       f'<div class="c"><span class="who {who}">{WHO[who][0]}</span><div class="refs">{tags}</div></div></article>')
        out.append("</div>")
    return "".join(out)


def rows(pairs):
    return "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in pairs)


CSS = """
/* Layout: the sign-in states drawn first (press one to filter), the checks every call passes, then each call as one row. */
:root{--bg:#F3F7FD;--surface:#FFFFFF;--ink:#14305C;--muted:#586C90;--line:#D6E0F0;--edge:#BFCCE4;--primary:#2F6BFF;--primary-edge:#1B4BC4;--on-primary:#FFFFFF;--primary-text:#2257D8;
--grey:#EEF1F7;--grey-e:#7A879E;--amber:#FFF0DE;--amber-e:#C96F1D;--blue:#EAF1FF;--blue-e:#2F6BFF;--green:#DAF5E8;--green-e:#168A55;--violet:#E9E7FB;--violet-e:#6B5FD3;--coral:#C73935;
--font:"Nunito",ui-rounded,"Segoe UI",system-ui,sans-serif;--mono:"DM Mono",ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1730;--surface:#16264A;--ink:#EAF0FB;--muted:#A3B3D1;--line:#263A63;--edge:#0A1226;--primary:#5B8CFF;--primary-edge:#3566E0;--on-primary:#0D1730;--primary-text:#9DBCFF;
--grey:#233457;--grey-e:#8FA0C0;--amber:#46301D;--amber-e:#F5A862;--blue:#1B2F5B;--blue-e:#5B8CFF;--green:#123B33;--green-e:#3DD592;--violet:#2B2856;--violet-e:#A59BF5;--coral:#FF8E8B;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0D1730;--surface:#16264A;--ink:#EAF0FB;--muted:#A3B3D1;--line:#263A63;--edge:#0A1226;--primary:#5B8CFF;--primary-edge:#3566E0;--on-primary:#0D1730;--primary-text:#9DBCFF;
--grey:#233457;--grey-e:#8FA0C0;--amber:#46301D;--amber-e:#F5A862;--blue:#1B2F5B;--blue-e:#5B8CFF;--green:#123B33;--green-e:#3DD592;--violet:#2B2856;--violet-e:#A59BF5;--coral:#FF8E8B;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font:600 16px/1.5 var(--font);padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.wrap{max-width:1180px;margin:0 auto;padding-block:30px 64px;display:flex;flex-direction:column;gap:36px}
h1,h2,h3{font-weight:900;line-height:1.15;margin:0;text-wrap:balance}h1{font-size:clamp(28px,4.6vw,42px)}h2{font-size:clamp(22px,3vw,28px)}h3{font-size:18px}
p{margin:0}header,section{display:flex;flex-direction:column;gap:14px;min-width:0}header{gap:8px}header p,.note{color:var(--muted);max-width:66ch}
.brand{font-weight:900;font-size:20px}.brand b{color:var(--primary)}
.eyebrow{font-size:12.5px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.scroll{overflow-x:auto;background:var(--surface);border:2px solid var(--line);border-radius:26px;padding:16px 12px 8px}
svg{display:block;width:100%;min-width:900px;height:auto;font-family:var(--font)}
.st{cursor:pointer}.st:focus{outline:none}.st .face{stroke-width:2.5}.st:focus-visible .face,.st:hover .face{stroke-width:4}
.st.open .face{fill:var(--grey);stroke:var(--grey-e)}.st.open .lip{fill:var(--grey-e)}
.st.half .face{fill:var(--amber);stroke:var(--amber-e)}.st.half .lip{fill:var(--amber-e)}
.st.full .face{fill:var(--blue);stroke:var(--blue-e)}.st.full .lip{fill:var(--blue-e)}
.st.fresh .face{fill:var(--green);stroke:var(--green-e)}.st.fresh .lip{fill:var(--green-e)}
.st.admin .face{fill:var(--violet);stroke:var(--violet-e)}.st.admin .lip{fill:var(--violet-e)}
.st[aria-pressed="true"] .face{stroke:var(--ink);stroke-width:4.5}
.tt{font-size:17px;font-weight:900;fill:var(--ink);text-anchor:middle}.sub{font-size:13px;font-weight:700;fill:var(--muted);text-anchor:middle}.num{font-size:12.5px;font-weight:900;fill:var(--ink);text-anchor:middle}
.ln{fill:none;stroke:var(--ink);stroke-width:2.2}.mk{fill:var(--ink)}.lb{font-size:12.5px;font-weight:800;fill:var(--muted)}
.btn{font:inherit;font-weight:900;font-size:14px;letter-spacing:.03em;text-transform:uppercase;cursor:pointer;background:var(--surface);color:var(--primary-text);border:2px solid var(--edge);border-radius:14px;box-shadow:0 4px 0 var(--edge);padding:8px 18px;align-self:flex-start}
.btn:focus-visible{outline:3px solid var(--primary);outline-offset:3px}
.steps{list-style:none;margin:0;padding:0;counter-reset:s;display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:14px}
.steps li{counter-increment:s;background:var(--surface);border:2px solid var(--line);border-bottom-width:5px;border-radius:16px;padding:12px 14px;display:flex;flex-direction:column;gap:3px}
.steps b::before{content:counter(s) ". ";color:var(--primary-text)}.steps span{color:var(--muted);font-size:14px}
.grp{display:flex;flex-direction:column;gap:10px}.grp h3{margin-top:12px}.grp[hidden],.call[hidden]{display:none}
.call{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1.4fr) minmax(0,.9fr);gap:8px 22px;background:var(--surface);border:2px solid var(--line);border-radius:16px;padding:14px 18px}
.call>div,.call ul{min-width:0}.a{display:flex;flex-direction:column;gap:4px;align-items:flex-start}.a small{color:var(--muted);font-size:12.5px}
code{font-family:var(--mono);font-size:12.5px;font-weight:500;overflow-wrap:anywhere}
code i{font-style:normal;font-size:11px;border-radius:6px;padding:1px 6px;background:var(--blue);margin-right:2px}
code i.get{background:var(--grey)}code i.delete{background:var(--amber)}
.call ul{margin:0;padding-left:18px;font-size:14px;color:var(--muted)}
.c{display:flex;flex-direction:column;gap:8px;align-items:flex-start}
.who{font-size:12px;font-weight:900;border-radius:99px;padding:2px 11px;border:2px solid;white-space:nowrap}
.who.open{background:var(--grey);border-color:var(--grey-e)}.who.half{background:var(--amber);border-color:var(--amber-e)}.who.full,.who.owner{background:var(--blue);border-color:var(--blue-e)}.who.fresh{background:var(--green);border-color:var(--green-e)}.who.admin{background:var(--violet);border-color:var(--violet-e)}
.refs{display:flex;flex-wrap:wrap;gap:4px}.ref{font-family:var(--mono);font-size:11px;padding:0 7px;border-radius:99px;border:1px solid var(--edge)}.ref.ac{border-color:var(--coral);color:var(--coral)}
.tw{overflow-x:auto;background:var(--surface);border:2px solid var(--line);border-radius:18px;padding:4px 18px}
table{border-collapse:collapse;width:100%}td{padding:11px 16px 11px 0;border-bottom:1px solid var(--line);vertical-align:top;font-size:15px}tr:last-child td{border-bottom:0}td+td{color:var(--muted)}td:first-child{width:30%}
.ch{margin:0;padding:0;list-style:none;counter-reset:q;display:grid;gap:12px}
.ch li{counter-increment:q;display:grid;grid-template-columns:34px minmax(0,1fr);gap:14px;background:var(--surface);border:2px solid var(--line);border-bottom-width:5px;border-radius:18px;padding:14px 18px}
.ch li::before{content:counter(q);width:34px;height:34px;border-radius:11px;background:var(--primary);color:var(--on-primary);display:grid;place-items:center;font-weight:900}
.ch b{display:block}.ch span{color:var(--muted);font-size:14.5px}
@media (max-width:760px){.call{grid-template-columns:minmax(0,1fr)}td:first-child{width:auto}}
"""

page = f"""<title>Doc2All Server Interfaces</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800;900&family=DM+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header><div class="brand">Doc<b>2</b>All</div><span class="eyebrow">Design · Server interfaces</span><h1>What the browser can ask the server</h1>
<p>{len(ALL)} calls. Each one says who may make it and what the server checks first. A call that is not on this page is refused.</p></header>
<section aria-label="Sign-in states"><h2>How far in are you?</h2><p class="note">Press a box to see only its calls.</p><div class="scroll">{drawing()}</div>
<button class="btn" id="all" type="button" hidden>Show all calls</button></section>
<section><h2>Every call passes these checks</h2><ol class="steps">{"".join(f"<li><b>{esc(a)}</b><span>{esc(b)}</span></li>" for a, b in COMMON)}</ol></section>
<section id="list"><h2 id="listh">All calls</h2>{call_list()}</section>
<section><h2>When the server says no</h2><div class="tw"><table>{rows(ANSWERS)}</table></div></section>
<section><h2>What no browser can ask for</h2><div class="tw"><table>{rows(SERVER_ONLY)}</table></div></section>
<section><h2>Five decisions</h2><ol class="ch">{"".join(f"<li><div><b>{esc(t)}: {esc(p)}</b><span>{esc(w)}</span></div></li>" for t, p, w in CHOICES)}</ol></section>
</div>
<script>
(function(){{
  var names={{open:"Calls open to anyone",half:"Calls after the password",full:"Calls when signed in",fresh:"Calls that need a confirmation",admin:"Administrator calls"}};
  var boxes=[].slice.call(document.querySelectorAll('.st')),calls=[].slice.call(document.querySelectorAll('.call')),all=document.getElementById('all');
  function show(who){{
    calls.forEach(function(c){{c.hidden=!!who&&c.dataset.who!==who}});
    [].slice.call(document.querySelectorAll('.grp')).forEach(function(g){{g.hidden=!g.querySelector('.call:not([hidden])')}});
    boxes.forEach(function(b){{b.setAttribute('aria-pressed',b.dataset.who===who)}});
    all.hidden=!who;document.getElementById('listh').textContent=who?names[who]:'All calls';
  }}
  boxes.forEach(function(b){{
    function pick(){{show(b.getAttribute('aria-pressed')==='true'?null:b.dataset.who)}}
    b.addEventListener('click',pick);
    b.addEventListener('keydown',function(e){{if(e.key==='Enter'||e.key===' '){{e.preventDefault();pick()}}}});
  }});
  all.addEventListener('click',function(){{show(null)}});
}})();
</script>
"""
(design / "doc2all-server-interfaces.html").write_text(page, encoding="utf-8")
print("built", len(page), "bytes,", len(ALL), "calls")


# ---------- the still figure and the tables for the report (light colours, scoped so the report's styles cannot touch it) ----------
PRINT_CSS = """
.si{margin:8px 0 0;text-align:center}.si svg{display:block;width:100%;height:auto;margin:0 auto;font-family:"DM Sans",sans-serif}
.si .face{stroke-width:2.2}
.si .open .face{fill:#EEF1F7;stroke:#7A879E}.si .open .lip{fill:#7A879E}
.si .half .face{fill:#FFF0DE;stroke:#C96F1D}.si .half .lip{fill:#C96F1D}
.si .full .face{fill:#EAF1FF;stroke:#2F6BFF}.si .full .lip{fill:#2F6BFF}
.si .fresh .face{fill:#DAF5E8;stroke:#168A55}.si .fresh .lip{fill:#168A55}
.si .admin .face{fill:#E9E7FB;stroke:#6B5FD3}.si .admin .lip{fill:#6B5FD3}
.si .tt{font-size:17px;font-weight:800;fill:#14305C;text-anchor:middle}.si text.sub{font-size:13px;font-weight:500;fill:#586C90;text-anchor:middle;margin:0}
.si .num{font-size:12.5px;font-weight:800;fill:#14305C;text-anchor:middle}
.si .ln{fill:none;stroke:#14305C;stroke-width:2}.si .mk{fill:#14305C}.si .lb{font-size:12.5px;font-weight:700;fill:#586C90}
.si figcaption{font-size:12.5px;color:#7A879E;margin-top:8px}
@media print{.si svg{width:246mm;max-width:100%}.si figcaption{font-size:9pt;margin-top:2mm}}
"""
(design / "_calls_figure.html").write_text(
    f'<style>{PRINT_CSS}</style><figure class="si">{drawing(still=True)}<figcaption>Figure 4.10 · Who may ask: the levels of access</figcaption></figure>',
    encoding="utf-8")


def tags(refs):
    return " ".join(f'<span class="tag">{r}</span>' for r in refs.split())


tables = ['<div class="calls">']
for group, calls in CALLS:
    tables.append(f'<p class="group">{esc(group)}</p><div class="tw"><table><thead><tr><th>Call</th><th>Who</th><th>The server checks</th><th>From</th></tr></thead><tbody>')
    for method, address, what, who, checks, refs, _screen in calls:
        lines_ = "".join(f"<div>{esc(c)}</div>" for c in checks)
        tables.append(f"<tr><td><strong>{esc(what)}</strong><code>{method} {esc(address)}</code></td><td>{WHO[who][0]}</td><td>{lines_}</td><td>{tags(refs)}</td></tr>")
    tables.append("</tbody></table></div>")
tables.append("</div>")
(design / "_calls_print.html").write_text("".join(tables), encoding="utf-8")

# ---------- notes for development ----------
md = ["# Server interfaces", "", "<!-- Built by build_server_interfaces.py. Edit the builder, not this file. -->", "",
      f"The browser can make these {len(ALL)} calls. Any other address is refused.",
      "Interactive page: open `doc2all-server-interfaces.html` in a browser.", "",
      "## Who may ask", "", "| Level | Means |", "| --- | --- |"]
md += [f"| {name} | {meaning} |" for name, meaning in WHO.values()]
md += ["", "## Checks on every call", ""]
md += [f"{i}. **{name}** {text}." for i, (name, text) in enumerate(COMMON, 1)]
for group, calls in CALLS:
    md += ["", f"## {group}", "", "| Call | What it does | Who | The server checks | From | Screen |", "| --- | --- | --- | --- | --- | --- |"]
    for method, address, what, who, checks, refs, screen in calls:
        md.append(f"| `{method} {address}` | {what} | {WHO[who][0]} | {'; '.join(c.replace(';', ',') for c in checks)} | {refs.replace(' ', ', ')} | {screen.replace(' ', ', ')} |")
md += ["", "## When the server says no", "", "| Answer | Means |", "| --- | --- |"]
md += [f"| {a} | {b} |" for a, b in ANSWERS]
md += ["", "## No call for these", ""]
md += [f"- **{a}:** {b}." for a, b in SERVER_ONLY]
md += ["", "## Decisions", ""]
md += [f"- **{t}:** {p} {w}" for t, p, w in CHOICES]
(design / "server-interfaces.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("report figure, report tables and server-interfaces.md written")
