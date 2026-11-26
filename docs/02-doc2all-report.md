# Doc2All: Scan, Convert and Clean Your Documents Safely

## Abstract

Document converters and scanners ask users to trust them with private files, and they rarely check the file they receive or tell the user what happened to it. Doc2All is a web application that scans, converts and cleans documents, and gives the user a safety report as proof. It checks a file before opening it, removes hidden data and macros, can black out personal data, and records when the file is deleted. The work follows the software development life cycle, and every phase has its own security activity and its own evidence. This report sets out why security matters, the objectives, and what Doc2All must do and protect: 12 features, 11 non-functional requirements, 29 security requirements that can each be tested, and 18 abuse cases that describe how someone could misuse the application. **Keywords:** document security, secure file handling, secure software development life cycle, security requirements, abuse cases.

## 1. Introduction

### 1.1 Problem statement
Students, lecturers and office staff share documents all the time, and they often use free online tools to convert, scan or clean them. These tools ask people to trust them with their files and tell them nothing about what happens next. The file may stay on someone else's server, and the user cannot check.

Documents also carry more than their visible text. Office and PDF files can contain macros and scripts, author names, edit history and photo locations. A scanned page may hold ID numbers, emails and phone numbers that are converted exactly as they are.

Finally, the uploaded file is untrusted input. A file that is not what it claims to be, such as a program renamed `.pdf`, can attack the tool that opens it. Most converters never examine the file first.

### 1.2 Why security matters
Software holds people's data, and a flaw lets someone read, change or destroy it. Security is described by three goals: confidentiality (only the right people see the data), integrity (the data is not changed without permission) and availability (the service works when it is needed) (Humayun et al., 2022). A breach also damages trust. When the personal data of customers is exposed, they may stop dealing with the organisation, and the harm can be serious (Saeed & Asaad, 2022).

For a document tool the stakes are direct, because the files are the product: a contract, an ID scan or a student record. If the tool leaks a file, or passes on a hidden macro, the tool has failed at its main job.

### 1.3 Security in every step of the life cycle
Software is built in phases: requirements, design, implementation, testing, deployment and maintenance. Many teams add security at the end and fix flaws as they are found, an approach called "penetrate and patch". It leaves users to apply patches, and the cost of fixing a flaw grows with each phase it survives, so security has to be considered in all the phases (Humayun et al., 2022). Bertino et al. (2010) describe the same idea as an engineered security process: security planning, security requirements analysis, a security architecture, secure coding, security testing, and security operations and maintenance.

<!--SDLC-DIAGRAM-->

Doc2All is built this way. Each phase has one security activity and one piece of evidence that can be shown.

| Phase | Security activity | Evidence |
| --- | --- | --- |
| Requirements | Security requirements and abuse cases | A numbered list where every item can be tested |
| Design | Threat model: data-flow diagram, trust boundaries, threats and protections | The diagram and a threat table with a protection for each threat |
| Implementation | Secure coding rules: allowed-type lists, ownership checks, no secrets in code | A short checklist, and the code reviewed against it |
| Testing | One automated test per abuse case, code scan, dependency scan, dynamic scan | A test report with each finding, its fix and the retest |
| Deployment | Hardening: debug off, secrets in environment variables, HTTPS, security headers | A checklist with each item ticked |
| Maintenance | Audit log, dependency updates, incident-response note | The log format, an update routine and a one-page response plan |

## 2. Objectives

### 2.1 General objective
To give students, lecturers and office staff a safe way to convert, scan and clean their documents, by providing one web workspace that checks every file before it is opened, removes hidden data, and shows the user proof of what was done and when the file is deleted.

### 2.2 Specific objectives
The objectives follow the order in which the system is built.

1. To define what must be protected before anything is built, by writing functional, non-functional and security requirements that can each be tested, and abuse cases that describe how the application could be misused.
2. To design the system with a threat model: a data-flow diagram, the trust boundaries, and a protection for every threat found.
3. To build accounts and private storage: sign-in with a password and a required second step (passkeys or one-time codes sent by email), email confirmation, password recovery with one-time codes, account deletion, roles, and a private area for each person, so that nobody can open another person's file.
4. To build safe upload, so that the server decides the type of every file from its name and first bytes, and rejects files that are fake, too large or too many.
5. To build conversion of Word and PowerPoint files to PDF and of PDF files to images, in a limited, throwaway workspace.
6. To build cleaning, which always removes content that runs by itself, lets the user choose what else to remove or keep, such as author data and photo locations, and checks the result again.
7. To build scan to text, which reads text from images and scanned pages on our own server, so the text does not leave the system without the user's consent.
8. To build personal-data blackout, which finds ID numbers, emails and phone numbers and removes them from the file.
9. To build the safety report, history, deletion and audit log, so the user sees what was found and removed, and every deletion is recorded.
10. To test the system with one automated test for every abuse case, together with code, dependency and dynamic scans, and to fix and retest each finding.
11. To deploy the system with a hardening checklist, and to plan its maintenance with an update routine and an incident-response note.

## 3. Requirements

### 3.1 Stakeholders
| Who | Need |
| --- | --- |
| User (student, lecturer, staff) | Convert and clean a document, and trust that nobody else sees it |
| Administrator | Run the service, see the audit log and system health, without reading user documents |
| Attacker (outside) | Wants other people's files, the server, or to stop the service |
| Attacker (signed-in user) | Wants another user's files or more than their allowed share of resources |

### 3.2 Functional requirements (what the app does)
| ID | Requirement |
| --- | --- |
| FR-01 | A person can register, sign in and sign out. |
| FR-02 | A signed-in user can upload a document. |
| FR-03 | Scan to text: read the text from an image or scanned page (OCR). |
| FR-04 | Convert: Word or PowerPoint to PDF; PDF to images. |
| FR-05 | Clean: remove content that can run, and private details such as author data and photo locations. The user sees what was found and chooses what to keep. Content that runs by itself or reaches outside is always removed. |
| FR-06 | Black out personal data: find ID numbers, emails and phone numbers and remove them from the file. |
| FR-07 | Safety report for each file: what was found, what was removed, when the file is deleted. |
| FR-08 | A user can see the history of their own files, delete any file and remove entries from the history. |
| FR-09 | Email check: when a person registers, a one-time code (OTP) sent to their email confirms the address. |
| FR-10 | Forgot password: a one-time code sent to the user's email lets them choose a new password. |
| FR-11 | Second step at sign-in: after the password, the user proves it is them with a passkey or a one-time code sent to their email. A user can add and remove passkeys. |
| FR-12 | A user can delete their account. Their files, passkeys and sessions are removed at once. |

### 3.3 Non-functional requirements (how well it works)
Non-functional requirements say how well the app must work. The security requirements in 3.5 are non-functional too. They have their own list because they are the focus of this report.

**Usability**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| NFR-01 | A user can go from upload to download in at most **4** steps: upload, choose, wait, download. | Walk through the app with a stopwatch and count the steps. |
| NFR-02 | The safety report uses plain words. Every finding has one sentence that says what it means and what was done. | Check the report of 5 sample files against a checklist, and ask 3 people to explain it back. |
| NFR-11 | When a job finishes, the app plays one short sound. The user can switch it off, and the screen always shows the same news, so nothing depends on hearing it. | Finish a job with the sound on, then off: the screen message is there both times, and the second job is silent. |

**Performance and reliability**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| NFR-03 | A typical file (up to **10** pages and **5 MB**) is checked and converted in under **30 seconds**. | Time 10 sample files. |
| NFR-04 | At least **5** users can use the app at the same time without errors. | Run 5 scripted users at once. |
| NFR-05 | If a job fails, the user sees a clear message, no partial file is kept, and the job can be started again. | Stop a job halfway: message shown, no leftover file, retry works. |

**Compatibility and access**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| NFR-06 | The app works in the current Chrome, Edge and Firefox, and on a phone screen about **400 px** wide. | Open every page in each browser and at that width. |
| NFR-07 | Every page can be used with the keyboard alone, and text has a contrast ratio of at least **4.5:1**. | Keyboard walk-through, and a contrast checker on each page. |

**Maintainability and cost**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| NFR-08 | All automated tests run with one command, and the result is pass or fail. | Run the command on a clean copy. |
| NFR-09 | The app can be set up on a clean computer by following the README in under **30 minutes**. | Follow the README on a clean machine and time it. |
| NFR-10 | The app uses only free and open-source tools (for example LibreOffice and Tesseract). | List each tool with its licence. |

### 3.4 Assets to protect
| Asset | Why it matters | Main risk |
| --- | --- | --- |
| Uploaded documents and results | May hold personal or school data | Confidentiality |
| Accounts, passwords, passkeys and one-time codes | Open the door to the documents | Confidentiality, integrity |
| The server and the converter tools | An attack here reaches every user | Integrity, availability |
| Audit log | The proof that the app did what it says | Integrity |
| Safety reports | Users rely on them | Integrity (must be true) |

### 3.5 Security requirements
Each requirement says how it is checked. The values in **bold** are the limits the application enforces and the tests check.

**Accounts and sessions**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| SR-01 | Passwords are at least **12** characters and stored only as a slow, salted hash. | Look in the database: no readable password. Try a short password: refused. |
| SR-02 | After **5** failed sign-ins in **10 minutes**, further attempts for that account or address are refused for **15 minutes**. | Script 6 wrong logins: the 6th is refused. |
| SR-03 | A session ends after **30 minutes** without activity and on sign-out. | Wait or force the time: the old session is rejected. |
| SR-25 | One-time codes are random, **6** digits, valid for **10 minutes** and usable once. They are stored only as a hash. After **5** wrong tries a code stops working. At most **3** codes per hour are sent to one address. | Use a code twice: refused. Try 6 wrong codes: the code is dead. Ask for a 4th code in an hour: refused. |
| SR-26 | Forgot password: the answer is the same whether or not the email has an account. A reset needs the emailed code and, when the account has a second step, that step too. After a reset all sessions end and the user is told by email. | Ask for a reset with a known and an unknown email: same answer. Reset, then use the old session: rejected. |
| SR-27 | Every sign-in needs a second step after the password: a passkey or a one-time code. Passkeys are preferred. Changing the password, the email or the passkeys, or deleting the account, needs the second step again. | Sign in with the password only: no access. Change the email or delete the account without the second step: refused. |
| SR-28 | Passkeys use WebAuthn. The server stores only the public key, each sign-in uses a new random challenge that works once, and a passkey works only on the Doc2All domain. A user can have several passkeys, and the last second step cannot be removed. | Replay an old sign-in response: refused. Use the passkey on another domain: refused. |
| SR-29 | A change to the password, email or passkeys, and a sign-in on a new device, is pinned in the app until the user answers it and is also sent by email, to the address the account had before the change. A deleted account is confirmed by email. Notices about files stay in the app. A device is recognised by a random value in a cookie, and the server keeps only its hash. | Add a passkey: the notice is pinned and an email arrives. Change the email: the old address is told. Finish a job: no email is sent. |

**Access control**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| SR-04 | Every request for a file, result, report or history entry checks that the signed-in user owns it. The answer for someone else's item is "not found". | Log in as user B and request user A's item by id: refused. |
| SR-05 | File and job ids are random and not guessable (at least **128 bits**). | Check the id generator; sample ids show no pattern. |
| SR-06 | Roles: user and administrator. An administrator sees records and the audit log, with ids, but not file names or document contents. | Log in as administrator and try to open a document: refused. The records show no file name. |
| SR-07 | Every page and API call needs a signed-in user, except sign-in, registration, forgot password and the Privacy, Cookies and About pages. | Call every other address without signing in: refused. |

**Upload and storage**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| SR-08 | The server decides the file type from the name and the first bytes. Only these types are accepted: **PDF, DOCX, PPTX, PNG, JPG**. A mismatch is rejected. The type sent by the browser is ignored. | Upload a program renamed `.pdf`: refused. |
| SR-09 | Upload limits: **20 MB** per file, **100** pages, **20** uploads per user per hour. | Upload over each limit: refused with a clear message. |
| SR-10 | The original file name is never used as a path. Files are stored under a random name in a private folder that the web server does not serve. | Upload `../../x.pdf`: stored under a random name, nothing written outside the folder. |
| SR-11 | Files can only be downloaded through an authenticated request that passes SR-04. | Open the storage address directly: no file is served. |

**Processing**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| SR-12 | Each job runs with a time limit (**60 s**), a memory limit and in its own temporary folder that is deleted when the job ends. | Feed a file that loops: the job stops at the limit; the folder is gone. |
| SR-13 | The converter and OCR tools run as a non-administrator account. | Check the process owner. |
| SR-14 | Compressed or Office files whose expanded size is more than **100 times** the original, or over **500 MB**, are rejected before opening. | Upload a zip bomb sample: rejected. |
| SR-15 | Content that runs by itself or reaches outside (macros, scripts that start on opening, hidden programs, remote templates) is always removed. Other active content (form scripts, attached documents, embedded objects) is removed unless the user chooses to keep it. Private details (author, edit history, comments, hidden text and sheets, previews) are removed or kept as the user chooses. Code written as text on a page is not changed. The cleaned file is scanned again, the report names what was removed and what was kept, and a file that keeps active content is never marked all clear. | Clean a sample with a macro, a form script and a code example, asking to keep everything: the macro is gone, the form script is reported as kept, the code example is unchanged, and the result is not all clear. |
| SR-16 | Blacked-out text is removed from the file, not only covered. | Extract the text from the result: the removed values are not found. |

**Privacy and retention**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| SR-17 | OCR runs on our server. Sending document text to any outside service needs the user's clear consent for that file. The email service receives only codes and notices, never document content or file names. | Watch network traffic during OCR: no outside call by default. Read a sent email: a code or notice only. |
| SR-18 | Files and results are deleted after **24 hours** by default, or at once when the user asks. Each deletion is logged and shown in the report. The history keeps the file name and the result until the user removes them. Deleting an account removes its files, passkeys and sessions at once; the audit log keeps its entries under a random user id, without the name or email. | Create a file, wait or force the time: file is gone, log entry exists. Delete an account: nothing of it is left, and its log entries hold no name or email. |
| SR-19 | Logs and error messages never contain document content. | Search the logs after a test run for words from a sample file: none. |

**Accountability and platform**

| ID | Requirement | How it is checked |
| --- | --- | --- |
| SR-20 | An audit log records sign-in, upload, each processing step, download and deletion, with user, time and result. Users cannot change or delete it, and the application can only add to it and read it. Each line carries a fingerprint of the line before, made with a server secret, so a changed line shows. | Do each action; find the entry. Try to edit it as a user and as the application: refused. Change a line directly in the database: the check reports it. |
| SR-21 | The site works over HTTPS only and sends security headers (content policy, no framing, no content-type guessing). | Run a header check on the deployed site. |
| SR-22 | Secrets (keys, passwords) are not in the code or the repository; they come from environment variables. | Run a secret scan over the repository: none found. |
| SR-23 | Debug mode is off in deployment, and errors shown to users reveal no internal details. | Trigger an error on the deployed site: a plain message only. |
| SR-24 | Before release, no known **high or critical** vulnerability remains in the code or its dependencies. | Code scan, dependency scan and dynamic scan reports. |

### 3.6 Abuse cases
An abuse case is a story of someone misusing the app. Each one is matched to the requirements that stop it and to the test that checks it.

| ID | Who | What they try | Stopped by | Test |
| --- | --- | --- | --- | --- |
| AC-01 | Stranger | Guess or reuse a file link to read a file | SR-04, SR-05, SR-07, SR-11 | Request ids without sign-in and as another user |
| AC-02 | Signed-in user | Change the id in the address to open another user's file | SR-04, SR-05 | User B requests user A's id |
| AC-03 | Attacker | Upload a program renamed `.pdf` | SR-08 | Upload fake files; expect refusal |
| AC-04 | Attacker | Use a file name with `..` to write outside the folder | SR-10 | Upload path-trick names |
| AC-05 | Attacker | Upload a zip or Office bomb to use up the server | SR-09, SR-12, SR-14 | Upload bomb sample; server stays up |
| AC-06 | Attacker | Craft a file to attack the converter and run code | SR-12, SR-13 | Run converter as limited user; check what it can reach |
| AC-07 | Attacker | Guess passwords by trying many | SR-01, SR-02 | Scripted wrong logins |
| AC-08 | Attacker | Steal or keep using an old session | SR-03 | Reuse an expired session |
| AC-09 | Signed-in user | Send many uploads to block others | SR-09, SR-12 | Exceed the hourly limit |
| AC-10 | Curious administrator | Read users' documents | SR-06, SR-20 | Administrator requests a document |
| AC-11 | Careless app | Keep files too long or leak content in logs | SR-18, SR-19 | Check deletion and log content |
| AC-12 | User (by mistake) | Share a file that still has hidden data or personal text | SR-15, SR-16 | Clean and black-out checks on samples |
| AC-13 | Attacker | Guess a one-time code, or flood someone's mailbox with codes | SR-25 | Try wrong codes; ask for many codes |
| AC-14 | Attacker | Sign in with a stolen or guessed password | SR-27, SR-28 | Password only: no access |
| AC-15 | Attacker | Use forgot password to take over an account, or to find which emails have accounts | SR-26, SR-27 | Reset with known and unknown emails; reset without the second step |
| AC-16 | Attacker | Build a fake site that collects codes or passkey sign-ins | SR-21, SR-28 | Use a passkey on another domain |
| AC-17 | Attacker | Send a file with a script that starts on opening, hoping the user keeps it | SR-15 | Ask to keep everything: it is still removed |
| AC-18 | Attacker | Use an open session to delete the account or change how it signs in, without the owner noticing | SR-27, SR-29 | Try without the second step; check the notice and the email |

### 3.7 Traceability
Each feature points to the requirements that protect it.

| Feature | Security requirements |
| --- | --- |
| Accounts (FR-01, FR-09, FR-10, FR-11, FR-12) | SR-01, SR-02, SR-03, SR-07, SR-18, SR-25, SR-26, SR-27, SR-28, SR-29 |
| Upload (FR-02) | SR-08, SR-09, SR-10, SR-11, SR-14 |
| Scan to text (FR-03) | SR-12, SR-13, SR-17 |
| Convert (FR-04) | SR-12, SR-13, SR-14 |
| Clean (FR-05) | SR-15 |
| Black out (FR-06) | SR-16 |
| Report and history (FR-07, FR-08) | SR-04, SR-05, SR-18, SR-19, SR-20 |
| Whole system | SR-06, SR-21, SR-22, SR-23, SR-24 |

## 4. Design

The design turns the requirements into a threat model. A threat model asks three questions: where does the data go, where does it cross a line we do not trust, and what could go wrong at each stop. The answers are a data-flow diagram, three trust boundaries, and a table that gives every threat a protection.

### 4.1 Data-flow diagram

Figure 4.1 follows one file from the browser to its deletion. The numbered circles are the steps described in section 4.2. The red dashed lines are the trust boundaries described in section 4.3.

<!--DFD-->

### 4.2 The journey in ten steps

1. **You sign in.** Password first. Five wrong tries lock the account for 15 minutes.
2. **A second step proves it is you.** A passkey on your device, or a one-time code sent to your email. The same code lets you reset a forgotten password.
3. **You upload a file.** The upload gate checks what the file really is, not what its name says.
4. **It goes into a locked folder.** The file is saved under a random name that nobody can guess.
5. **It opens inside a sandbox.** The job manager sends a copy into a sealed box. If the file is bad, the damage stays inside.
6. **Reading a scan stays on our server.** An outside service receives the text only if the user agrees, for that one file.
7. **Only results come out.** Findings and the cleaned file come back. The sandbox never touches the database.
8. **You get your file.** The file and a short report of what was removed and what was kept, shown only to you.
9. **Then it disappears.** A timer deletes everything after 24 hours, or sooner if the user asks.
10. **Every step is logged.** Each step adds a line to an audit log that nobody can edit.

### 4.3 Trust boundaries

| Boundary | Between | Rule |
| --- | --- | --- |
| TB1 | Browser and server | Nothing from the browser is trusted. The type, size, owner and role are checked again on the server. |
| TB2 | Server and sandbox | The file may be dangerous, so it is opened in a sealed box. The runner gets a copy and a job id, and returns only findings and a result file. |
| TB3 | Server and outside services | The email service receives only codes and notices, never document content or file names. Document text goes outside only if the user agrees, for that one file. |

### 4.4 Design rules

1. **One door for files.** Every file comes in through the upload gate, so the checks live in one place.
2. **Two steps to sign in.** A password is never enough. A passkey is preferred, and a one-time code by email is the other choice.
3. **The runner knows little.** It gets one copy of one file and a job id. It never touches the database or another user's files.
4. **One owner check.** One place asks who owns what, before any report or download.
5. **Outside is off.** OCR and every processing step run on our server. The only outside service used by default is email, and it carries codes and notices only.

### 4.5 Threats and protections

Each row names a part of the diagram, the threats there, the protection, and the requirements and abuse cases it comes from. The letters are the STRIDE kinds of threat: S spoofing, T tampering, R repudiation, I information disclosure, D denial of service, E elevation of privilege.

| Where | Threat | Protection | Comes from |
| --- | --- | --- | --- |
| Browser<br>S | Anyone can pretend to be a user, or send anything at all. | The server trusts nothing from the browser. Type, size, owner and role are checked again. | SR-07, SR-08 |
| Step 1 · Sign-in details<br>S, I | Someone tries many passwords, or reads one on its way. | 12 or more characters, stored as slow salted hashes. Lock for 15 minutes after 5 failures. HTTPS only. | SR-01, SR-02, SR-21, AC-07 |
| Step 1 · Sign-in and sessions<br>S, R | An old or stolen session keeps working, and nobody can tell who signed in. | Sessions end after 30 minutes idle and on sign-out. Every sign-in is logged. | SR-03, SR-20, AC-08 |
| Step 2 · Second step and passkeys<br>S, E | A stolen or phished password is enough to sign in. A fake site collects a code. | A second step is always required. A passkey works only on our own domain and never leaves the device. The server keeps only a public key. | SR-21, SR-27, SR-28, AC-14, AC-16 |
| Step 2 · One-time codes by email<br>S, I, D | Someone guesses a code, floods a mailbox with codes, or learns which emails have accounts. | Codes are random, last 10 minutes, work once and die after 5 wrong tries. Only 3 are sent per hour. The email carries only the code. | SR-17, SR-25, SR-26, AC-13, AC-15 |
| Step 2 · Forgot password<br>S, E | A reset is used to take over an account, or to skip the second step. | A reset needs the emailed code and, when set, the second step. The answer is the same for unknown emails. All sessions end after a reset, and the user is told by email. | SR-26, SR-27, AC-15 |
| Step 2 · Account changes<br>S, R | Someone at an open session deletes the account or changes how it signs in, and the owner does not notice. | The second step is asked again. A notice is pinned in the app and emailed. Emails never hold document content or file names. | SR-27, SR-29, AC-18 |
| Step 3 · File and choices<br>T, S | A program renamed .pdf. A name like ../../x.pdf. An upload with no sign-in. | The server decides the type from the name and first bytes. The name becomes a random one. Sign-in is needed. | SR-07, SR-08, SR-10, AC-03, AC-04 |
| Step 3 · Upload gate<br>D | A zip or Office bomb, or a flood of uploads, uses up the server. | 20 MB, 100 pages, 20 uploads an hour. Files that expand over 100 times are rejected before opening. | SR-09, SR-14, AC-05, AC-09 |
| Step 4 · Private files<br>I | A guessed link or a direct address shows someone a file. | Random 128-bit ids. A private folder the web server does not serve. Downloads only through the owner check. | SR-05, SR-10, SR-11, AC-01 |
| Step 9 · Deletion timer<br>I | Files stay longer than needed. | Deleted after 24 hours, or at once on request. Each deletion is logged and shown in the report. | SR-18, AC-11 |
| Database<br>I, E | User A opens user B's record by changing an id. An administrator reads documents. | Owner check on every request, with "not found" for others. Administrators see records and ids, never file names or contents. | SR-04, SR-06, AC-02, AC-10 |
| Job manager<br>I, R | Another user's report or result is opened. A step happens with no record. | Owner check before every report or download. Each step goes to the audit log. | SR-04, SR-20, AC-02 |
| Steps 5 and 7 · Into and out of the sandbox<br>T, E | A crafted file attacks the converter and tries to reach the rest of the server. | The runner gets a job id and a copy in a throwaway folder. It returns only findings and a result, and never touches the database. | SR-12, SR-13, AC-06 |
| Step 5 · Runner (sandbox)<br>D, E, T | An endless document. Code running as administrator. Macros or personal text that survive. | 60 second and memory limits. A non-administrator account. The cleaned file is scanned again. Blacked-out text is removed from the file. | SR-12, SR-13, SR-15, SR-16, AC-05, AC-06, AC-12 |
| Step 5 · Cleaning choices<br>T, E | A harmful script stays in a file because the user chose to keep it, or the report calls such a file clean. | Content that runs by itself is always removed. Other active content is removed unless the user keeps it, and then the report says so and never shows all clear. | SR-15, AC-17 |
| Step 6 · Outside OCR<br>I | Personal text leaves our system. | OCR runs on our server. An outside service is used only with the user's clear consent for that file. | SR-17 |
| Step 8 · Report and download<br>I | A stranger or another user downloads a file. | Signed-in request, owner check, random ids. HTTPS with security headers. | SR-04, SR-11, SR-21, AC-01, AC-02 |
| Step 10 · Audit log<br>T, R, I | A log line is edited or deleted. Document text leaks into the logs. | Users cannot change the log, the application can only add to it, and a changed line shows. Logs and error messages never hold document content. | SR-19, SR-20, AC-11 |

All 18 abuse cases and 26 of the 29 security requirements are placed in this table. SR-22, SR-23 and SR-24 (secrets, debug mode and scans) apply to the whole build and release, so they are handled in sections 5, 6 and 7.

### 4.6 Screens

The screens show how a person meets these protections. Figure 4.2 maps all eleven, and the six that carry the most security decisions follow at full size, in light mode on a computer. The design also fits a phone about 400 px wide (NFR-06).

<!--SCREENS-->

| Screen | View | Title | What it shows | Requirements |
| --- | --- | --- | --- | --- |
| 1 | normal | Sign-in | A wrong email and a wrong password give the same message. Five wrong tries lock the account for 15 minutes. | SR-01, SR-02, SR-21, AC-07 |
| 3 | choose | Second step | A password is never enough. The passkey is the first choice, and a code by email is the other. | FR-11, SR-27, SR-28, AC-14, AC-16 |
| 5 | clean | Clean options | The user sees what was found. What runs by itself is always removed, and the user chooses the rest. | FR-05, SR-15, AC-17 |
| 7 | clear | Safety report | Each finding says what it means and what was done, and when the file is deleted. | FR-07, SR-15, SR-18, NFR-02 |
| 8 | pinned | History | Only the owner's files are listed. A security notice stays pinned until the user answers it. | FR-08, SR-04, SR-18, SR-29 |
| 11 | record | Audit log (administrator) | An administrator sees who did what and when, never the content of a document. | SR-06, SR-19, SR-20, AC-10 |

### 4.7 Data model

Figure 4.9 shows what Doc2All saves and how the pieces connect. The records are kept in a PostgreSQL database. File contents are kept in a private folder outside it.

<!--DATA-->

| Table | What it saves | What protects it | Requirements |
| --- | --- | --- | --- |
| Users | Email, role, settings, password hash | Only a slow, salted hash of the password | SR-01, SR-06, SR-27 |
| Passkeys | Public key, name, dates | The private key never leaves the device | SR-28 |
| One-time codes | Purpose, expiry, wrong tries | Only a hash of the code, made with a server secret | SR-25, SR-26 |
| Sessions | Who is signed in, second step, last activity | Random key in an HTTP-only cookie, ends after 30 minutes idle | SR-03, SR-27 |
| Known devices | Device name, first and last use | Only a hash of the random cookie value | SR-29 |
| Attempt counters | Sign-ins, codes sent, uploads | Hashed email or address, removed after 24 hours | SR-02, SR-09, SR-25 |
| Files | Name, type, size, deletion time | Random id, owner check, random name on disk | SR-04, SR-05, SR-10, SR-18 |
| Jobs | Action, choices, consent, status | Owner check, error codes without content | SR-12, SR-15, SR-17 |
| Safety reports | Result of a job | Reached only through the job's owner | SR-04, SR-15 |
| Findings | Kind, how many, what was done | The value that was found is never saved | SR-15, SR-19 |
| Notices | Kind, pinned, answered | Shown only to their owner | SR-29 |
| Audit log | Time, user id, action, target id, result | Only added to, each line fingerprints the one before, no name, email or file name | SR-19, SR-20 |

The application's database account can read and write these tables, but on the audit log it can only add and read. A separate setup account creates and changes the tables and is not used while the application runs. The sandbox runner has no database access.

| Data | Removed when |
| --- | --- |
| File contents (uploads and results) | After 24 hours, or at once when the user deletes the file |
| File records, jobs, reports, findings | The user removes them from the history, or deletes the account |
| One-time codes | They are used, or 10 minutes pass |
| Sessions | The user signs out, or 30 minutes pass without activity |
| Attempt counters | After 24 hours |
| Users, passkeys, known devices, notices | The account is deleted |
| Audit log | It stays, without any name, email, file name or content |

## References
- Humayun, M., Jhanjhi, N. Z., Almufareh, M. F., & Khalil, M. I. (2022). Security threat and vulnerability assessment and measurement in secure software development. *Computers, Materials & Continua*, 71(3). https://doi.org/10.32604/cmc.2022.019289
- Saeed, V. A., & Asaad, R. R. (2022). Cyber security threats, vulnerability, challenges with proposed solution. *Applied Computing Journal*, 2(4), 227-244. https://doi.org/10.52098/acj.202260
- Bertino, E., Martino, L., Paci, F., & Squicciarini, A. (2010). *Security for Web Services and Service-Oriented Architectures*. Springer. https://doi.org/10.1007/978-3-540-87742-4
