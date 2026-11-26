# Development plan

Read the [security rules](design/security-rules.md), the [screens](design/screens.md), the [data model](design/data-model.md) and the
[server interfaces](design/server-interfaces.md) next to this. How to run the app is in the [README](../README.md#running-the-app).
What each call sends and answers is in the [API examples](design/api-examples.md).

## Decisions

| Topic | Decision |
| --- | --- |
| Tools | Free to choose for this module. Django 5.2 (long-term support) and Django REST Framework (server), React with Vite (browser) |
| Python | A virtual environment in `.venv`, with versions listed in `backend/requirements.txt` |
| Processing | LibreOffice and Tesseract on our server |
| Reuse | We reuse working code from our earlier project, Cohortly, then add what is missing |
| Database | SQLite while the features are built. PostgreSQL with a limited app account (see the [data model](design/data-model.md)) before release |
| Keys and tokens | Added later, with the pieces that need them: email sending, outside OCR, database password, deployment secret. The app runs on a developer's computer with none of them |
| Ports | Server 8010, browser 5180 |

## How each piece is built

The pages come first, with demo data. Then the server, functionality first, then protection, one piece at a time:

1. **Make it work.** The server answers the calls exactly as the demo server does, so the page needs no change.
2. **Protect it.** Look at what the piece really exposes. Take its rows from the threat table (report section 4.5) and its
   calls from the [server interfaces](design/server-interfaces.md). That sets how much security the piece needs.
3. **Test it**, including its abuse cases.
4. Commit. Then the next piece.

Until a piece is protected, the app stays on the developer's computer, with made-up files only.

## Kept from the first line

These cost nothing now and are hard to add later:

- No secrets and no real documents in git.
- Uploaded files go under random names into a private folder that git ignores and the web server does not serve.
- Ids in addresses are random, never counting numbers.
- Our own user model is added **before** Django's sign-in apps are switched on. Changing it afterwards is painful.

## Build order

1. Project skeleton. In `backend/` and `frontend/`.
2. All pages, working on demo data.
3. Server: upload and private storage.
4. Server features, one at a time: convert, clean, scan to text, black out, safety report, history and deletion.
5. Accounts: register, email code, sign-in, second step, passkeys, forgot password, sessions. Every file then gets an owner,
   the owner check is added, and every call that is not marked open needs a sign-in.
6. Notices, settings, account deletion, administrator pages, audit log.
7. Testing: one test per abuse case, `bandit`, `pip-audit`, `npm audit`, OWASP ZAP. Record each finding, fix, retest.
8. Deployment checklist (PostgreSQL, secrets, HTTPS, debug off) and maintenance plan.

Protections that need an account, such as the owner check and the limit per user, are added in step 5 to the pieces built before it.

## Pages and demo server

- The pages talk to the server only through `frontend/src/api/calls.js`: the 41 calls of the design.
- Demo mode answers them from `frontend/src/api/mock/`, with the design's rules (who may ask, codes, lock-out,
  confirmation, owner check). It is left out of the build when `VITE_API=server`.
- The demo rules are **not protection**. Anyone can change what runs in a browser. The server must enforce every rule.
- `frontend/src/api/passkey.js` pretends. WebAuthn replaces it with the accounts.
- When a call changes, change the design list, the demo server and `npm test` together.

## Code to reuse

The pages were written new from the designed screens. The copies are kept on the author's computer in `reuse/cohortly/` (not in git). Copy a part into the app, adapt it, test it.
Never import from that folder. The report's Implementation section must say which parts came from Cohortly.

| From Cohortly | Use it for | Change before use |
| --- | --- | --- |
| `converter/tools.py` | Running LibreOffice and Tesseract with a time limit in a temporary folder | Add memory and CPU limits, a non-administrator account, bomb checks before opening |
| `converter/views.py` | Convert endpoints, size caps, first-bytes check, throttle | Add the owner check and audit log. Keep throttle counts outside process memory |
| `converter/Dockerfile` | Container with the processing tools | Never tested. Add a non-root user and resource limits |
| Chat `services.py`: upload checks | The upload gate (extension list, first bytes, size, clean names) | Match SR-08 and SR-09 |
| Chat `services.py` and `models.py`: attachments | Private storage, random names, "not found" for outsiders | Add expiry after 24 hours |
| Chat `views.py`: attachment view | Safe downloads (headers) | Owner only |
| Chat `tests.py` | Style of one test per abuse case | Write ours for AC-01 to AC-18 |
| `LLM/usage.py` | Daily limit per user | Fit to the upload limits |
| `LLM/client.py` (image reading) | The optional outside OCR only | Off by default, consent per file |
| Frontend `tools/scan/`, `tools/docconv/` | Screen logic for scanning and converting | Restyle to our screens. Remove Cohortly-only imports. The server does the checks and processing |

## What must change from the old code

- Cohortly keeps the login token in `localStorage`, where a script on the page can read it. Doc2All should use a session in
  a secure, HTTP-only cookie, with protection against cross-site requests.
- The old dependency list is out of date (for example Django 5.0 is no longer supported, and PyPDF2 is no longer
  maintained). Start from current versions and run `pip-audit` and `npm audit`.
- Spreadsheets and CSV files are not accepted types in Doc2All.

## What is new (Cohortly does not have it)

Passkeys and emailed codes · roles · cleaning · black out · safety report · history and deletion after 24 hours ·
account deletion · notices · audit log · the finish sound.
