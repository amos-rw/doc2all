# Doc2All 🐱

**Scan, convert and clean your documents safely.**

Doc2All is a web app that works on documents. It turns a Word, PowerPoint or PDF file into another format, reads the text
from a scanned page, and **checks and cleans every file** on the way. It then shows a safety report as proof.

It is a project for the module *Application Security Technologies*, to show security at **every step of the software
development life cycle (SDLC)**.

> Status: requirements and design written. All pages work. Upload and convert (Word and PowerPoint to PDF) run on
> the server; the other pages still use made-up demo data. **Not yet protected: for a developer's own computer only.**

## What it does

| Feature | What makes it safe |
| --- | --- |
| Scan to text (OCR) | Runs on our server. An outside service is used only with the user's consent, per file |
| Convert (Word or PowerPoint to PDF, PDF to images) | The file is checked first and opened in a sandbox with limits |
| Clean a file | What runs by itself is always removed. The user chooses what else to remove or keep |
| Black out personal data | The text is removed from the file, not only covered |
| Safety report and history | Says what was found, removed and kept, and when the file is deleted |
| Accounts | Password plus a required second step (passkey or emailed code), deletion of the account, notices |

## Read before writing code

| Document | What is in it |
| --- | --- |
| [Report text](docs/02-doc2all-report.md) | Requirements (FR, NFR, SR), abuse cases, threat model, screens. **The source of truth** |
| [Report PDF](docs/Doc2All-Report.pdf) | The same report, as printed |
| [Design index](docs/design/README.md) | Where each design lives and how to rebuild it |
| [Security rules](docs/design/security-rules.md) | What every feature must check, with the limits |
| [Screens](docs/design/screens.md) | The eleven screens, their views and rules |
| [Data model](docs/design/data-model.md) | What is saved, how it connects, when it is removed |
| [Server interfaces](docs/design/server-interfaces.md) | Every call the browser can make, who may make it, what is checked |
| [Development plan](docs/development.md) | Tools, code reused from our earlier project, build order |
| [Concept](docs/01-concept.md) | The first idea, in one page |

## Tools

Chosen by us (the module leaves the choice open): **Django and Django REST Framework** for the server, **React** for the
browser, **PostgreSQL** for the database (SQLite while the features are built), **LibreOffice** and **Tesseract** for
processing. All are free and open source.

## Running the app

Needs Python 3.12 or newer, Node 22.22 or newer, LibreOffice and Tesseract. No keys or passwords are needed on a
developer's computer. The commands are for Windows PowerShell, from the project folder.

Set up once:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r backend\requirements.txt
.venv\Scripts\python backend\manage.py migrate
.venv\Scripts\python backend\manage.py check_tools
npm.cmd --prefix frontend install
```

Start the server in one window:

```
.venv\Scripts\python backend\manage.py runserver 8010
```

Start the pages in a second window, then open <http://localhost:5180>:

```
npm.cmd --prefix frontend run dev
```

Upload and convert use the server; try them with the made-up files in `samples/public/`. Everything else is demo data
inside the browser.

| Demo sign-in | Value |
| --- | --- |
| User | `amos@example.com` |
| Administrator | `admin@example.com` |
| Password | `doc2all-demo-pass` |
| Every emailed code | `123456` |

A passkey is pretended. The **Demo** button in a corner of the page makes time pass, adds a security notice or starts
the demo again.

| To | Run |
| --- | --- |
| See every page without the server | `npm.cmd --prefix frontend run demo` |
| Use only the real server | set `VITE_API` to `server` before starting the pages |
| Test the server | `.venv\Scripts\python backend\manage.py test core files` |
| Check the demo server against the design | `npm.cmd --prefix frontend test` |

`check_tools` really uses LibreOffice and Tesseract on made-up pages. If they are in an unusual place, copy
`.env.example` to `.env` and set the paths. This is development mode, only for your own computer. Setting
`DJANGO_SECRET_KEY` turns it off.

## Folders

| Folder | What is in it |
| --- | --- |
| `backend/` | The Django server: `core/` (programs), `files/` (upload, convert, history) |
| `frontend/` | The React pages. `src/api/mock/` is the demo server |
| `docs/` | The report, the designs and the development plan |
| `docs/design/` | Sources and builders for the diagram, the screens and the report |
| `samples/public/` | Made-up test documents (never real personal data) |

## Rebuilding the report

Needs Python with `markdown` and `pymupdf`, and Google Chrome. Run from the project folder, in this order:

```
python -I docs/design/build_threat_model.py
python -I docs/design/build_screens.py
python -I docs/design/build_screen_shots.py
python -I docs/design/build_screens_doc.py
python -I docs/design/build_data_model.py
python -I docs/design/build_server_interfaces.py
python -I docs/design/build_report.py
```

Then print `docs/design/doc2all-report.html` to PDF with headless Chrome:

```
chrome --headless=new --no-pdf-header-footer --virtual-time-budget=10000 --print-to-pdf=<out.pdf> file:///<full path>/doc2all-report.html
```

## Ground rules (security first)

- No secrets in git. Keys and passwords live in `.env`, which is ignored. Share `.env.example` with fake values.
- No real documents in git. Test with made-up files only.
- Each piece is made to work, then protected and tested, before the next one. The threats are already in the report.
- The server decides a file's type from its name and first bytes, never the browser.
