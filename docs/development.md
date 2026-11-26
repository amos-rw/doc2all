# Development plan

Read the [security rules](design/security-rules.md), the [screens](design/screens.md), the [data model](design/data-model.md) and the
[server interfaces](design/server-interfaces.md) next to this.

## Decisions

| Topic | Decision |
| --- | --- |
| Tools | Free to choose for this module. Django and Django REST Framework (server), React with Vite (browser) |
| Processing | LibreOffice and Tesseract on our server |
| Reuse | We reuse working code from our earlier project, Cohortly, then add what is missing |
| Database | PostgreSQL, with a limited app account (see the [data model](design/data-model.md)) |
| Email provider | A local test mail server for development. The deployment provider is not chosen yet |

## Code to reuse

The copies are kept on the author's computer in `reuse/cohortly/` (not in git). Copy a part into the app, adapt it, test it.
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

## Build order

1. Project skeleton, settings from environment variables, `.env.example`.
2. Accounts: register, email code, sign-in, second step, passkeys, forgot password, sessions.
3. Upload gate, private storage, owner check, audit log.
4. Features, one at a time: convert, clean, scan, black out, safety report, history and deletion.
5. Notices, settings, account deletion, administrator pages.
6. Testing: one test per abuse case, `bandit`, `pip-audit`, `npm audit`, OWASP ZAP. Record each finding, fix, retest.
7. Deployment checklist and maintenance plan.

For every step: write the threats first, build the protection, test it, then commit.
