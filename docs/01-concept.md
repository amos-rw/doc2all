# Doc2All: concept

*Scan, convert and clean your documents safely.*

The first idea, in one page. The full requirements and design are in the [report](02-doc2all-report.md).

## The problem

Ordinary converters and scanners ask you to trust them with your files and tell you nothing about what happens next.

- Your file may stay on their server, and you cannot check.
- Hidden data travels with the result: the author's name, the GPS location in a photo, macros and scripts inside Office and PDF files.
- Personal details in a scanned page (ID numbers, emails, phone numbers) are converted as they are.
- The uploaded file itself is rarely examined, so a fake or booby-trapped file reaches the converter.

## Who uses it

Students, lecturers and office staff who share documents and want a clean copy they can trust. They sign in, upload a file,
pick what they need, and get the result with a short safety report. They can see only their own files and delete them at any time.

## The features

Five features, each doing its normal job and one safety job on top.

| Feature | What it does | What makes it safer than other apps |
| --- | --- | --- |
| Scan to text | Reads the text from a photo or scanned page (OCR) | Runs on our server by default, so the text does not go to an outside service unless the user agrees |
| Convert | Word or PowerPoint to PDF, PDF to images, page ranges | The file is checked before it is opened, and converted in a limited, throwaway workspace |
| Clean a file | Removes what runs by itself, and the private details the user chooses | The cleaned file is checked again to prove nothing was left behind |
| Black out personal data | Finds ID numbers, emails and phone numbers and covers them | The covered text is removed from the file, not just hidden under a black box |
| Safety report | One page per file: what was found, what was removed, when it will be deleted | The user gets proof, and deletion is logged |

## Main threats and how each is handled

This was the starting list. The full threat model is in section 4 of the report.

| Where | Threat | Planned protection |
| --- | --- | --- |
| Upload | A fake file: a program renamed to .pdf | Allowed types only, first bytes checked against the name, size limit |
| Upload | A path trick in the file name | The name is replaced by a random one, files stay in a private folder |
| Convert | A zip or Office bomb, or an endless document, uses up the server | Time, memory and page limits, one job at a time, a throwaway folder |
| Convert | The converter itself is attacked through the file | Runs as a non-admin user in a restricted workspace |
| Clean | Macros or metadata survive | The result is scanned again and the report says what was found |
| Scan | Personal text leaves the system | Local OCR by default; any outside service only with the user's consent |
| Accounts | Guessed passwords, stolen sessions | Strong password hashing, rate limiting, short-lived sessions |
| History | User A opens user B's file by changing an id | Ownership checked on every request, random ids |
| Storage | Files are kept longer than needed | Deleted after use or after a set time, every deletion logged |

## Security at every SDLC step

Each step has one security activity and one piece of evidence we can show.

| SDLC step | Security activity | Evidence we produce |
| --- | --- | --- |
| Requirements | Security requirements and abuse cases ("a stranger guesses a file link") | A numbered list where every item is testable |
| Design | Threat model: data-flow diagram, trust boundaries, STRIDE per part | The diagram and a threat table with a protection for each |
| Implementation | Secure coding: allowed-type lists, ownership checks, no secrets in code, safe database access | A short secure-coding checklist, code reviewed against it |
| Testing | One automated test per abuse case, a code scan, a dependency scan, a dynamic scan | Test report with the findings and the retest after each fix |
| Deployment | Hardening: debug off, secrets in environment variables, HTTPS, security headers | A deployment checklist with each item ticked |
| Maintenance | Audit log, dependency updates, incident-response note | The log format, an update routine, a one-page response plan |

## Author

One person. Doc2All is a web app, so there is nothing to install. We choose the programming tools and reuse working code
from our earlier project (see the [development plan](development.md)).
