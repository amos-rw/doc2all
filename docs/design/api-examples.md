# API examples

<!-- Written by frontend/scripts/contract.mjs (npm test). Do not edit by hand. -->

What the pages send and what they expect back. The demo server in `frontend/src/api/mock/` answers like this today.
The real server must answer the same way. Long lists are cut to two entries; ids and times are shortened.

A refused call answers with the status from the [server interfaces](server-interfaces.md) and `{"error": "code", "message": "plain words"}`.

## `GET /api/session`

Who: Anyone

Answers:

```json
{
  "state": "signed_out",
  "formToken": "demo-form-token"
}
```

## `POST /api/register`

Who: Anyone

Sends:

```json
{
  "email": "new@example.com",
  "password": "doc2all-demo-pass"
}
```

Answers:

```json
{
  "next": "code"
}
```

## `POST /api/register/confirm`

Who: Anyone

Sends:

```json
{
  "email": "new@example.com",
  "code": "123456"
}
```

Answers:

```json
{
  "ok": true
}
```

## `POST /api/sign-in`

Who: Anyone

Sends:

```json
{
  "email": "amos@example.com",
  "password": "doc2all-demo-pass"
}
```

Answers:

```json
{
  "state": "password_done",
  "formToken": "demo-form-token",
  "email": "amos@example.com",
  "emailMasked": "a***@example.com",
  "role": null,
  "methods": {
    "passkey": true,
    "emailCode": true
  }
}
```

## `POST /api/sign-in/passkey/options`

Who: Password done

Answers:

```json
{
  "challenge": "c-4f1c…"
}
```

## `POST /api/sign-in/passkey`

Who: Password done

Sends:

```json
{
  "challenge": "c-4f1c…",
  "answer": "demo-passkey"
}
```

Answers:

```json
{
  "state": "signed_in",
  "formToken": "demo-form-token",
  "email": "amos@example.com",
  "emailMasked": "a***@example.com",
  "role": "user",
  "methods": {
    "passkey": true,
    "emailCode": true
  }
}
```

## `POST /api/sign-in/code/send`

Who: Password done

Answers:

```json
{
  "sentTo": "a***@example.com"
}
```

## `POST /api/sign-in/code`

Who: Password done

Sends:

```json
{
  "code": "123456"
}
```

Answers:

```json
{
  "state": "signed_in",
  "formToken": "demo-form-token",
  "email": "amos@example.com",
  "emailMasked": "a***@example.com",
  "role": "user",
  "methods": {
    "passkey": true,
    "emailCode": true
  }
}
```

## `POST /api/sign-out`

Who: Password done

Answers:

```json
{
  "state": "signed_out",
  "formToken": "demo-form-token"
}
```

## `POST /api/password/forgot`

Who: Anyone

Sends:

```json
{
  "email": "amos@example.com"
}
```

Answers:

```json
{
  "next": "code"
}
```

## `POST /api/password/reset/code`

Who: Anyone

Sends:

```json
{
  "email": "amos@example.com",
  "code": "123456"
}
```

Answers:

```json
{
  "passkeyNeeded": true,
  "challenge": "c-4f1c…"
}
```

## `POST /api/password/reset/passkey`

Who: Anyone

Sends:

```json
{
  "challenge": "c-4f1c…",
  "answer": "demo-passkey"
}
```

Answers:

```json
{
  "ok": true
}
```

## `POST /api/password/reset`

Who: Anyone

Sends:

```json
{
  "password": "doc2all-demo-pass"
}
```

Answers:

```json
{
  "ok": true
}
```

## `GET /api/me`

Who: Signed in

Answers:

```json
{
  "email": "amos@example.com",
  "settings": {
    "fileNotices": true,
    "finishSound": true
  },
  "emailCode": true,
  "passwordChangedAt": 1795689000000,
  "passkeys": [
    {
      "id": "k-laptop",
      "name": "Laptop",
      "addedAt": 1795689000000
    },
    {
      "id": "k-phone",
      "name": "Phone",
      "addedAt": 1795689000000
    }
  ],
  "sessions": [
    {
      "id": "d-this",
      "device": "This laptop",
      "lastSeenAt": 1795689000000,
      "current": true
    },
    {
      "id": "d-phone",
      "device": "Phone",
      "lastSeenAt": 1795689000000,
      "current": false
    }
  ]
}
```

## `PATCH /api/me/settings`

Who: Signed in

Sends:

```json
{
  "finishSound": false
}
```

Answers:

```json
{
  "fileNotices": true,
  "finishSound": false
}
```

## `DELETE /api/me/sessions/{id}`

Who: Owner only

Answers:

```json
{
  "ok": true
}
```

## `POST /api/me/confirm`

Who: Signed in

Sends:

```json
{
  "method": "passkey",
  "challenge": "c-4f1c…",
  "answer": "demo-passkey"
}
```

Answers:

```json
{
  "confirmedUntil": 1795689000000
}
```

## `PUT /api/me/password`

Who: Confirmed

Sends:

```json
{
  "password": "doc2all-demo-pass"
}
```

Answers:

```json
{
  "ok": true
}
```

## `POST /api/me/email`

Who: Confirmed

Sends:

```json
{
  "email": "moved@example.com"
}
```

Answers:

```json
{
  "next": "code"
}
```

## `POST /api/me/email/confirm`

Who: Confirmed

Sends:

```json
{
  "code": "123456"
}
```

Answers:

```json
{
  "email": "moved@example.com"
}
```

## `POST /api/me/passkeys/options`

Who: Confirmed

Answers:

```json
{
  "challenge": "c-4f1c…"
}
```

## `POST /api/me/passkeys`

Who: Confirmed

Sends:

```json
{
  "challenge": "c-4f1c…",
  "answer": "demo-passkey",
  "name": "Tablet"
}
```

Answers:

```json
{
  "id": "k-4f1c…",
  "name": "Tablet",
  "addedAt": 1795689000000
}
```

## `DELETE /api/me/passkeys/{id}`

Who: Confirmed

Answers:

```json
{
  "ok": true
}
```

## `PUT /api/me/email-code`

Who: Confirmed

Sends:

```json
{
  "allowed": false
}
```

Answers:

```json
{
  "emailCode": false
}
```

## `DELETE /api/me`

Who: Confirmed

Answers:

```json
{
  "ok": true
}
```

## `POST /api/files`

Who: Signed in

Sends:

```json
(the file, as form field "file")
```

Answers:

```json
{
  "id": "f-4f1c…",
  "name": "contract.docx",
  "kind": "docx",
  "size": 5,
  "expiresAt": 1795689000000,
  "allowed": [
    "convert",
    "clean"
  ]
}
```

## `GET /api/files/{id}/check`

Who: Owner only

Answers:

```json
{
  "groups": [
    {
      "key": "active",
      "rule": "always",
      "title": "Runs by itself or reaches outside",
      "detail": "1 macro, 1 remote template",
      "remove": true
    },
    {
      "key": "attached",
      "rule": "keepable",
      "title": "Attached files and objects",
      "detail": "1 spreadsheet. If you keep it, I cannot say All clear.",
      "remove": true
    }
  ]
}
```

## `GET /api/files/{id}/matches`

Who: Owner only

Answers:

```json
{
  "title": "Employment letter",
  "person": "Name: A. Person",
  "matches": [
    {
      "id": "m1",
      "kind": "ids",
      "label": "ID",
      "value": "1 0000 0 0000000 0 00"
    },
    {
      "id": "m2",
      "kind": "phones",
      "label": "Phone",
      "value": "+250 700 000 000"
    }
  ]
}
```

## `POST /api/jobs`

Who: Owner only

Sends:

```json
{
  "fileId": "f-4f1c…",
  "actions": [
    "clean",
    "convert"
  ],
  "keep": [
    "attached",
    "active"
  ]
}
```

Answers:

```json
{
  "id": "j-4f1c…"
}
```

## `GET /api/jobs/{id}`

Who: Owner only

Answers:

```json
{
  "id": "j-4f1c…",
  "status": "done",
  "progress": 1,
  "steps": [
    {
      "label": "I checked what the file really is",
      "state": "done"
    },
    {
      "label": "I opened a copy in the sandbox",
      "state": "done"
    }
  ]
}
```

## `GET /api/jobs/{id}/report`

Who: Owner only

Answers:

```json
{
  "jobId": "j-4f1c…",
  "fileId": "f-4f1c…",
  "fileName": "contract.docx",
  "actions": [
    "clean",
    "convert"
  ],
  "outcome": "kept",
  "findings": [
    {
      "ok": true,
      "title": "A macro was removed",
      "detail": "The file had a hidden program in it. It is gone.",
      "tag": "Removed"
    },
    {
      "ok": false,
      "title": "Attached files and objects: kept",
      "detail": "You chose to keep them. I cannot promise they are safe.",
      "tag": "Kept"
    }
  ],
  "expiresAt": 1795689000000,
  "fileDeleted": false
}
```

## `GET /api/files/{id}/download`

Who: Owner only

Answers:

```json
(the file itself, with its name in Content-Disposition)
```

## `DELETE /api/files/{id}`

Who: Owner only

Answers:

```json
{
  "deletedAt": 1795689000000
}
```

## `GET /api/history`

Who: Signed in

Answers:

```json
{
  "items": [
    {
      "id": "j-4f1c…",
      "jobId": "j-4f1c…",
      "fileId": "f-4f1c…",
      "name": "contract.docx",
      "did": "Clean, convert",
      "outcome": "kept",
      "expiresAt": 1795689000000,
      "deleted": true
    },
    {
      "id": "j-4f1c…",
      "jobId": "j-4f1c…",
      "fileId": "f-4f1c…",
      "name": "notes.pdf",
      "did": "Black out",
      "outcome": "clear",
      "expiresAt": 1795689000000,
      "deleted": false
    }
  ]
}
```

## `DELETE /api/history/{id}`

Who: Owner only

Answers:

```json
{
  "ok": true
}
```

## `GET /api/notices`

Who: Signed in

Answers:

```json
{
  "items": [
    {
      "id": "n-4f1c…",
      "userId": "u-7f3a",
      "kind": "file",
      "title": "contract.docx is ready",
      "security": false,
      "pinned": false,
      "read": false,
      "at": 1795689000000,
      "detail": "Shown here in the app only."
    },
    {
      "id": "n-4f1c…",
      "userId": "u-7f3a",
      "kind": "security",
      "title": "A passkey was removed: Laptop",
      "security": true,
      "pinned": true,
      "read": false,
      "at": 1795689000000,
      "detail": "Was this you? This stays here until you answer."
    }
  ]
}
```

## `POST /api/notices/read`

Who: Signed in

Answers:

```json
{
  "ok": true
}
```

## `POST /api/notices/{id}/mine`

Who: Confirmed

Answers:

```json
{
  "ok": true
}
```

## `POST /api/notices/{id}/not-mine`

Who: Owner only

Answers:

```json
{
  "next": "change_password"
}
```

## `GET /api/admin/audit`

Who: Administrator

Answers:

```json
{
  "lines": [
    {
      "id": "a-4f1c…",
      "at": 1795689000000,
      "userId": "u-1a90",
      "action": "Sign-in",
      "targetId": "u-1a90",
      "result": "OK"
    },
    {
      "id": "a-4f1c…",
      "at": 1795689000000,
      "userId": "u-5b2e",
      "action": "Delete account",
      "targetId": "u-5b2e",
      "result": "OK"
    }
  ]
}
```

## `GET /api/admin/records`

Who: Administrator

Answers:

```json
{
  "users": [
    {
      "id": "u-7f3a",
      "role": "user",
      "createdAt": 1795689000000,
      "files": 4,
      "jobs": 6
    },
    {
      "id": "u-1a90",
      "role": "admin",
      "createdAt": 1795689000000,
      "files": 0,
      "jobs": 0
    }
  ],
  "jobs": [
    {
      "id": "j-4f1c…",
      "userId": "u-7f3a",
      "action": "clean, convert",
      "result": "kept",
      "at": 1795689000000
    },
    {
      "id": "j-4f1c…",
      "userId": "u-7f3a",
      "action": "blackout",
      "result": "clear",
      "at": 1795689000000
    }
  ]
}
```
