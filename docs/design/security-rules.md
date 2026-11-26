# Security rules for developers

Keep this open while building. It is the short form. The exact requirements (SR), the abuse cases (AC) and how each is
checked are in the [report text](../02-doc2all-report.md), sections 3.5, 3.6 and 4.5. If they differ, the report wins.

## Always

1. **Trust nothing from the browser.** Check type, size, owner and role again on the server (TB1).
2. **One owner check**, in one place, before any file, result, report or history entry. Someone else's item is "not found" (SR-04).
3. **One door for files.** Every file enters through the upload gate.
4. Ids are random, at least 128 bits (SR-05).
5. Logs and error messages never hold document content (SR-19).
6. Secrets come from environment variables, never from the code (SR-22).
7. Write the threats first, build the protection, then write the test.

## Accounts and sessions

| Rule | Limit | Ref |
| --- | --- | --- |
| Password, stored as a slow salted hash | 12 characters or more | SR-01 |
| Failed sign-ins | 5 in 10 minutes, then refused for 15 minutes | SR-02 |
| Session ends | 30 minutes idle, and on sign-out | SR-03 |
| One-time codes, stored as a hash | 6 digits, 10 minutes, one use, 5 tries, 3 per hour per address | SR-25 |
| Forgot password | Same answer for any email, needs the passkey when there is one, ends all sessions, emails the user | SR-26 |
| Create account | Same answer for a known email, and its owner is told by email | SR-26 |
| Second step | Always. Again for changing password, email, passkeys or the email code setting, deleting the account, and answering "it was me". Counts 5 minutes | SR-27 |
| Passkeys (WebAuthn) | Only the public key is stored, new challenge each time, own domain only. Email codes can be off only with two passkeys or more. The last second step cannot be removed | SR-28 |
| Signed-in only | Everything except sign-in, registration, forgot password, Privacy, Cookies, About | SR-07 |
| Roles | Administrators see records and the audit log with ids, never file names or document content | SR-06 |

Every call the browser can make, with its checks, is in [server-interfaces.md](server-interfaces.md).

## Upload and processing

| Rule | Limit | Ref |
| --- | --- | --- |
| Allowed types, decided from name and first bytes | PDF, DOCX, PPTX, PNG, JPG | SR-08 |
| Upload size and rate | 20 MB, 100 pages, 20 uploads per user per hour | SR-09 |
| Storage | Random name, private folder the web server does not serve | SR-10 |
| Download | Only through a signed-in request with the owner check | SR-11 |
| Each job | 60 s, a memory limit, its own temporary folder, deleted at the end | SR-12 |
| Converter and OCR | Run as a non-administrator account | SR-13 |
| Bombs | Rejected before opening if expanded over 100 times or over 500 MB | SR-14 |
| The sandbox | Gets a copy and a job id. Returns findings and a result. Never touches the database (TB2) | SR-12 |

## Cleaning (SR-15)

| Group | Examples | What the app does |
| --- | --- | --- |
| Runs by itself or reaches outside | Macros, scripts that start on opening, hidden programs, remote templates | **Always removes**, even if the user asks to keep |
| Other active content | Form scripts, attached documents, embedded objects | Removes unless the user keeps it. Then the report says so and **never says all clear** |
| Private details | Author, edit history, comments, hidden text and sheets, previews | The user chooses |
| Code written as text | A code example in a study document | **Never changed** |

Scan the result again, and name in the report what was removed and what was kept.

## Black out, OCR, privacy

- Blacked-out text is removed from the file, not covered (SR-16).
- OCR runs on our server. An outside service needs clear consent for that one file (SR-17).
- Email carries only codes and notices, never document content or file names (SR-17, TB3).
- Files and results are deleted after 24 hours, or at once on request. Every deletion is logged and shown in the report (SR-18).
- Deleting an account removes files, passkeys and sessions at once. The audit log keeps entries under a random user id,
  without name or email (SR-18).
- History keeps the file name and result until the user removes them (SR-18).

## Notices and sound

- Security changes and a sign-in on a new device: pinned in the app until answered, and emailed. An email change goes to
  the old address (SR-29).
- A device is known by a random value in a needed cookie. Save only its hash (SR-29).
- Notices about files: in the app only (SR-29). There are no push notifications.
- A finished job plays one short sound that can be switched off. The screen always shows the same news (NFR-11).

## Audit log and release

- Record sign-in, upload, each step, download and deletion, with user id, time and result. Users cannot change it. The app account
  can only add and read. Each line carries a keyed fingerprint of the line before (SR-20).
- HTTPS only, with security headers (SR-21). Debug off, plain error messages (SR-23).
- Before release: no known high or critical vulnerability. Run `bandit`, `pip-audit`, `npm audit` and OWASP ZAP (SR-24).
