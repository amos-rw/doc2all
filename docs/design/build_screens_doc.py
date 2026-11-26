"""Writes docs/design/screens.md from screens.src.html, so the developer notes match the designed screens.
Run after build_screen_shots.py: python -I docs/design/build_screens_doc.py"""
import pathlib
import re

design = pathlib.Path(__file__).resolve().parent
source = (design / "screens.src.html").read_text(encoding="utf-8")
screens = []
for block in re.split(r"\n\s*(?=\{n:\d+,)", source)[1:]:
    head = re.match(r"\{n:(\d+),name:'([^']+)',g:'([^']+)'", block)
    states = re.search(r"states:\[(.*?)\],\s*mood:", block, re.S).group(1)
    reqs = re.search(r"reqs:\[(.*?)\]", block, re.S).group(1)
    note = re.search(r"note:'((?:[^'\\]|\\.)*)'", block).group(1)
    screens.append((int(head.group(1)), head.group(2), head.group(3),
                    re.findall(r"\['[a-z]+','([^']+)'\]", states), re.findall(r"'([A-Z]+-\d\d)'", reqs), note))

out = ["# Screens", "",
       "<!-- Built by build_screens_doc.py from screens.src.html. Edit the source, not this file. -->", "",
       "Open `doc2all-screens.html` in a browser to see every view, light and dark, computer and phone.",
       "The pictures below are light mode, computer view.", "",
       "## Rules for every screen", "",
       "- Light and dark mode must both work. The app must fit a phone about 400 px wide (NFR-06).",
       "- Keyboard only must work, with text contrast of at least 4.5:1 (NFR-07).",
       "- Font Nunito. Navy `#14305C`, blue `#2F6BFF`, scan cyan `#19B5D6`, mint `#22B573`, coral `#EF5350`, ginger `#F2994A`.",
       "- The cat is live and animated, with four moods: hello, checking, all clear, alert.",
       "- Top bar: logo, Tools, History, a bell with a count, and a profile menu (Settings, Sign out).",
       "- Phone: only the logo on top, and a bottom bar with Tools, History, Alerts and Profile.",
       "- Before sign-in there is no menu (logo, plus Privacy, Cookies and About links). An administrator gets Audit log and Records.",
       "- The menu is dimmed while a question is open. The phone bottom bar is hidden before sign-in and during questions.",
       "- A security notice stays pinned at the top until the user answers it.",
       "- Buttons are centred on result screens, the main action first.",
       "- Use words that fit any device (\"Confirm on your device\"). Password strength is Weak, Medium or Strong, with no bars.",
       "- After a password reset, say an email was sent and ask the user to sign in.", "",
       "## All screens", "", "| # | Screen | Group | Views |", "| --- | --- | --- | --- |"]
for number, name, group, views, _reqs, _note in screens:
    out.append(f"| {number} | {name} | {group} | {', '.join(views)} |")
for number, name, _group, views, reqs, note in screens:
    picture = f"screen-{number}.png" if (design / "shots" / f"screen-{number}.png").exists() else f"map-{number}.png"
    out += ["", f"## {number}. {name}", "", note, "", f"- Views: {', '.join(views)}",
            f"- Requirements: {', '.join(reqs)}", "", f"![Screen {number}, {name}](shots/{picture})"]
(design / "screens.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("screens.md:", len(screens), "screens")
