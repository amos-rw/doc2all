# Server interfaces

<!-- Built by build_server_interfaces.py. Edit the builder, not this file. -->

The browser can make these 41 calls. Any other address is refused.
Interactive page: open `doc2all-server-interfaces.html` in a browser.

## Who may ask

| Level | Means |
| --- | --- |
| Anyone | No sign-in needed |
| Password done | The password was right, the second step is still waiting |
| Signed in | Both steps done |
| Owner only | Signed in, and the item is yours. Otherwise the answer is Not found |
| Confirmed | Signed in, and the second step was done again in the last 5 minutes |
| Administrator | Signed in with the administrator role |

## Checks on every call

1. **HTTPS** Nothing travels unprotected. Security headers on every answer.
2. **Is this call listed?** A call that is not marked open needs a sign-in.
3. **Form token** A change is accepted only with the token our own page holds.
4. **Session** Real, not older than 30 minutes of rest, and in the right step.
5. **Role and owner** One place decides. Someone else's item is Not found.
6. **Input** Type, size and allowed values. Extra fields are ignored.
7. **Limits** Too many tries are refused.
8. **Log and answer** Important actions are logged. Errors are plain, with no inside details.

## Getting in

| Call | What it does | Who | The server checks | From | Screen |
| --- | --- | --- | --- | --- | --- |
| `GET /api/session` | Ask who I am and get the form token | Anyone | Returns only signed out, password done or signed in | SR-03, SR-07 | 1 |
| `POST /api/register` | Create an account | Anyone | Password has 12 characters or more; Same answer when the email already has an account, its owner is told by email; At most 3 emails an hour for one address | FR-09, SR-01, SR-25, SR-26, AC-13, AC-15 | 2 |
| `POST /api/register/confirm` | Enter the emailed code | Anyone | Code matches its hash, is under 10 minutes old and unused; Dead after 5 wrong tries | FR-09, SR-25, AC-13 | 2 |
| `POST /api/sign-in` | Give email and password | Anyone | Refused after 5 failures in 10 minutes, for 15 minutes; Same message for a wrong email and a wrong password; Starts a new session key. No access yet | FR-01, SR-01, SR-02, SR-27, AC-07, AC-14 | 1 |
| `POST /api/sign-in/passkey/options` | Get a passkey challenge | Password done | A new random challenge that works once; Also used to confirm a change | SR-28 | 3 |
| `POST /api/sign-in/passkey` | Prove it with a passkey | Password done | Signature, challenge and our domain are right; New session key; A new device creates a notice and an email | FR-11, SR-28, SR-29, AC-14, AC-16 | 3 |
| `POST /api/sign-in/code/send` | Ask for an emailed code | Password done | Only if the account allows email codes; At most 3 codes an hour; Also used to confirm a change | FR-11, SR-25, AC-13 | 3 |
| `POST /api/sign-in/code` | Prove it with the code | Password done | Same code rules; New session key; A new device creates a notice and an email | FR-11, SR-25, SR-27, SR-29, AC-14 | 3 |
| `POST /api/sign-out` | Sign out | Password done | The session is destroyed on the server; Also works when fully signed in | FR-01, SR-03, AC-08 | 8 |

## Forgot password

| Call | What it does | Who | The server checks | From | Screen |
| --- | --- | --- | --- | --- | --- |
| `POST /api/password/forgot` | Ask for a reset code | Anyone | Same answer for any email; At most 3 codes an hour | FR-10, SR-25, SR-26, AC-15 | 4 |
| `POST /api/password/reset/code` | Enter the reset code | Anyone | Same code rules; Opens only the reset, never the account; Gives a passkey challenge when the account has a passkey | FR-10, SR-25, SR-26, AC-15 | 4 |
| `POST /api/password/reset/passkey` | Confirm with the passkey | Anyone | Only after the code; Needed when the account has a passkey | SR-26, SR-28, AC-15 | 4 |
| `POST /api/password/reset` | Save the new password | Anyone | Code done, and passkey done when needed; 12 characters or more; Ends every session and emails the user | FR-10, SR-01, SR-26, AC-15 | 4 |

## My account

| Call | What it does | Who | The server checks | From | Screen |
| --- | --- | --- | --- | --- | --- |
| `GET /api/me` | Read my settings, passkeys and devices | Signed in | Only my own data. No hashes or keys are sent | FR-11, SR-07 | 10 |
| `PATCH /api/me/settings` | Change file notices and sound | Signed in | Only these two can change here. Security notices stay on | NFR-11, SR-29 | 10 |
| `DELETE /api/me/sessions/{id}` | Sign out another device | Owner only | The session is mine | SR-03, SR-04, AC-08 | 10 |
| `POST /api/me/confirm` | Do the second step again | Signed in | Passkey, or emailed code if the account allows it; Same rules as sign-in; Counts for 5 minutes | SR-27, AC-18 | 10 |
| `PUT /api/me/password` | Change my password | Confirmed | 12 characters or more; Ends my other sessions, notice and email | SR-01, SR-27, SR-29, AC-18 | 10 |
| `POST /api/me/email` | Start changing my email | Confirmed | Sends a code to the new address; Same answer when that address is already in use | SR-25, SR-27 | 10 |
| `POST /api/me/email/confirm` | Finish changing my email | Confirmed | The code is right; Tells the old address | SR-27, SR-29, AC-18 | 10 |
| `POST /api/me/passkeys/options` | Get a challenge for a new passkey | Confirmed | A new random challenge that works once | SR-27, SR-28 | 10 |
| `POST /api/me/passkeys` | Add a passkey | Confirmed | The challenge is the one just given, our domain; Saves the public key only, notice and email | FR-11, SR-27, SR-28, SR-29, AC-18 | 10 |
| `DELETE /api/me/passkeys/{id}` | Remove a passkey | Confirmed | It is mine; With email codes stopped, two passkeys must stay; Notice and email | SR-04, SR-27, SR-28, SR-29, AC-18 | 10 |
| `PUT /api/me/email-code` | Allow or stop email codes | Confirmed | Stop only when the account has at least two passkeys; Notice and email | SR-27, SR-28, SR-29 | 10 |
| `DELETE /api/me` | Delete my account | Confirmed | Removes files, passkeys and sessions at once; The log keeps no name or email; Confirms by email | FR-12, SR-18, SR-27, SR-29, AC-18 | 10 |

## Files and work

| Call | What it does | Who | The server checks | From | Screen |
| --- | --- | --- | --- | --- | --- |
| `POST /api/files` | Upload a file | Signed in | Type from the name and first bytes; 20 MB, 100 pages, 20 uploads an hour; Bomb check before opening; Random name in the private folder | FR-02, SR-05, SR-08, SR-09, SR-10, SR-14, AC-03, AC-04, AC-05, AC-09 | 5 |
| `GET /api/files/{id}/check` | See what is hidden in the file | Owner only | Opened in the sandbox with limits; Values are shown to the owner and never saved | FR-05, SR-04, SR-12, SR-13, SR-19, AC-06 | 5 |
| `GET /api/files/{id}/matches` | See personal data to black out | Owner only | Opened in the sandbox; Matches are never saved | FR-06, SR-04, SR-12, SR-19 | 5 |
| `POST /api/jobs` | Start convert, clean, scan or black out | Owner only | The file is mine and still there; What runs by itself is removed whatever the request says; Outside OCR only with consent for this file; 60 seconds, memory limit, own folder | FR-03, FR-04, FR-05, FR-06, SR-04, SR-12, SR-13, SR-15, SR-16, SR-17, AC-05, AC-06, AC-12, AC-17 | 5, 6 |
| `GET /api/jobs/{id}` | Ask if the work is finished | Owner only | The job is mine; An error is a short code, never file content | NFR-05, SR-04, SR-19, SR-23, AC-02 | 5 |
| `GET /api/jobs/{id}/report` | Read the safety report | Owner only | The job is mine; Counts and actions only | FR-07, SR-04, SR-15, AC-02, AC-12 | 7 |
| `GET /api/files/{id}/download` | Download a file | Owner only | The file is mine and not deleted; Safe download headers; Written to the log | SR-04, SR-11, SR-20, SR-21, AC-01, AC-02 | 7, 8 |
| `DELETE /api/files/{id}` | Delete a file now | Owner only | The content is removed; Written to the log | FR-08, SR-04, SR-18, AC-11 | 9 |
| `GET /api/history` | List my files | Signed in | Only my own entries | FR-08, SR-04, AC-02 | 8 |
| `DELETE /api/history/{id}` | Remove an entry from History | Owner only | The entry is mine; Any content still there is deleted too | FR-08, SR-04, SR-18, AC-11 | 8 |

## Notices

| Call | What it does | Who | The server checks | From | Screen |
| --- | --- | --- | --- | --- | --- |
| `GET /api/notices` | Read my notices | Signed in | Only my own | SR-04, SR-29 | 8 |
| `POST /api/notices/read` | Mark notices as read | Signed in | Only my own. A pinned notice stays pinned | SR-29 | 8 |
| `POST /api/notices/{id}/mine` | Answer: yes, it was me | Confirmed | The notice is mine; Removes the pin | SR-27, SR-29, AC-18 | 8 |
| `POST /api/notices/{id}/not-mine` | Answer: no, secure my account | Owner only | Ends every other session; Opens the password change | SR-03, SR-29, AC-18 | 8 |

## Administrator

| Call | What it does | Who | The server checks | From | Screen |
| --- | --- | --- | --- | --- | --- |
| `GET /api/admin/audit` | Read the audit log | Administrator | Administrator role; Read only. No call can change a line | SR-06, SR-20, AC-10 | 11 |
| `GET /api/admin/records` | See records of users and jobs | Administrator | Ids, times and results only; No file names and no content | SR-06, SR-19, AC-10 | 11 |

## When the server says no

| Answer | Means |
| --- | --- |
| 400 | Something in the request is wrong |
| 401 | Sign in first |
| 403 | Do the second step again |
| 404 | Not found. Also the answer for another person's item and for admin pages without the role |
| 429 | Too many tries, come back later |

## No call for these

- **Delete after 24 hours:** A server timer. No call starts or stops it.
- **Make an administrator:** A command on the server. No call can give the role.
- **Check the audit log fingerprints:** A command on the server.
- **The sandbox runner:** Receives a job and a copy of the file. It has no address the browser can reach.

## Decisions

- **Reset with a passkey:** If the account has a passkey, a password reset asks for it too. Someone who gets into the mailbox still cannot take the account. With email codes only, the emailed code is the second step, so a passkey protects better.
- **Lost passkey:** Email codes can be stopped only while the account has at least two passkeys. If one device is lost, the other still opens the account. Losing every passkey and forgetting the password locks the account for good.
- **Yes, it was me:** This answer asks for the second step again. A person at your open computer cannot hide a security notice.
- **Confirmed time:** A second step done again counts for 5 minutes. Long enough to make a change, short enough to be safe.
- **Create account:** A known email gets the same answer, and its owner is told by email. Nobody can use this form to find which emails have accounts.
