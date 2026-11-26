# Security testing: upload and convert

Method: first make the piece work, then attack it with harmless trick files and requests, add protections, and attack it
again. Tested on 26 November 2026 on Windows 11 with LibreOffice 26.8.3 and Django 5.2. The trick files are built by
[`backend/files/attacks.py`](../../backend/files/attacks.py); they only reach a listener and files that the test makes.

The attacks are repeated as automated tests in [`backend/files/test_security.py`](../../backend/files/test_security.py).

## Found and fixed

These eight attacks **worked** on the first version (commit `9b3274e`) and are stopped now.

| # | What was tried | Before | Protection added | Ref | Test |
| --- | --- | --- | --- | --- | --- |
| 1 | An OpenDocument file (which can carry macros) renamed `.docx` | Accepted | The server looks inside: the main part of that kind must be there, other document families are refused | SR-08, AC-03 | `LookInsideTests` |
| 2 | A bomb: 602 KB that grows to 600 MB | Accepted | Refused before opening if it grows over 100 times or over 500 MB, has over 2000 parts, is damaged or locked, or declares XML entities | SR-14, AC-05 | `LookInsideTests` |
| 3 | A document of 150 pages | Converted | Nothing is kept from a result over 100 pages; over 100 slides is refused at upload | SR-09, AC-05 | `OutsideReachTests`, `LookInsideTests` |
| 4 | 25 uploads in a row | All accepted | 20 an hour for one network address; one job per file and 5 jobs at once | SR-09, AC-09 | `LimitTests` |
| 5 | Another website sending an upload through the user's browser | Accepted | A form token on every change, checked together with the page's address; the token cookie is hidden from scripts | SR-21 | `FormTokenTests` |
| 6 | A 30 MB request | Read in full, then refused | Refused from its stated size, before it is read | SR-09, AC-09 | `LimitTests` |
| 7 | A converter program reading the server's secrets | Possible | Programs get a clean environment with only what they need to start | SR-22, AC-06 | `ProgramLimitTests` |
| 8 | A program taking 1.4 GB of memory | Possible | A memory limit (1 GB) and a limit on the number of processes | SR-12, AC-05 | `ProgramLimitTests` |

## Tried and already stopped

These did **not** work even on the first version: LibreOffice, with its usual settings, fetched nothing. The trick files
were checked to be valid, because the same picture stored inside the file does appear in the PDF.

| What was tried | Extra walls added anyway, so we do not depend on a default |
| --- | --- |
| A Word or PowerPoint picture, or a Word template, fetched from a web address | The copy that is opened has its outside links blocked; LibreOffice is told to block untrusted links and has a network proxy that leads nowhere |
| A picture or text file taken from the server's disk into the PDF | Same, and fields that fetch (`INCLUDETEXT`, `INCLUDEPICTURE`, `DDE` and others) are emptied, also when cut into pieces |
| Macros | Left out of the copy; macros are switched off in LibreOffice's settings |

## Also added

- Each job works with its **own copy** of a clean LibreOffice settings folder, made at server start from our own text.
  Nothing is carried from one file to the next.
- Documents are never opened by an **administrator** account (SR-13).
- A **timer** deletes content after 24 hours even when nobody uses the app, and removes left-over files (SR-18, AC-11).
- An **audit log** records upload, conversion, download, deletion and removal with ids only. Lines are chained with keyed
  fingerprints; `manage.py check_audit` reports a changed or removed line (SR-19, SR-20).
- Downloads are saved, never run in the page, and are not cached (SR-21). Outside development the server insists on HTTPS.

## What is still open

| Open point | Why it matters | Planned |
| --- | --- | --- |
| No accounts, so no owner check | Anyone using this server sees every file (AC-01, AC-02) | With the accounts |
| LibreOffice runs under the same user as the server, with no wall around files or network except the ones above | A flaw inside LibreOffice would get that user's access (AC-06, partly open) | A separate runner in a container at deployment |
| Limits count per network address | Behind one proxy, all users share them | Per user, with the accounts |
| PDF pages are not counted and pictures are not looked into | No work is done on them yet | With the PDF, clean and scan pieces |
| The newest audit lines can be cut off unnoticed, and the database account may still change lines | Known limit of the chain | Add-only database account with PostgreSQL |
| Memory limit on Linux, and the HTTPS settings | Written but never run | Deployment |
| Names, comments and hidden text stay in the converted PDF | The report says so | The cleaning piece |
