# API Reference

Base URL (local dev): `http://localhost:5000/api`

All responses share one shape:
```json
{ "success": true, "message": "...", "data": { ... } }
{ "success": false, "message": "...", "errors": { ... } }
```

Authenticated endpoints expect `Authorization: Bearer <access_token>`.

---

## Auth — `/api/auth`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/register` | — | Voter self-registration. Auto-logs-in (returns tokens) so the client can continue straight into biometric registration. |
| POST | `/login` | — | Body: `{ email, password, role }`, role in `super_admin`, `election_admin`, `voter`. Rate-limited (5/min). |
| POST | `/refresh` | Refresh token | Rotates the refresh token (old one is revoked). |
| POST | `/logout` | Access token | Revokes the current session. |
| GET | `/me` | Access token | Returns the current user, including `has_face_registered` / `is_verified`. |

## Elections — `/api/elections`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `` | — | Public list (drafts hidden). Query: `?status=`. |
| GET | `/<id>` | — | Public single election. |
| GET | `/admin` | Admin | Full list, respecting per-object permission (Election Admins only see elections assigned to them). |
| GET | `/admin/<id>` | Admin | Full detail incl. eligible voter count, assigned admins. |
| POST | `` | Admin | Create (status starts `draft`). |
| PUT | `/<id>` | Admin | Only while `draft`/`scheduled`. |
| DELETE | `/<id>` | Admin | Only while `draft`. |
| POST | `/<id>/start` | Admin | Requires 2+ candidates. |
| POST | `/<id>/pause` `/resume` `/close` | Admin | Lifecycle transitions — see `app/services/election_lifecycle.py` for the full state machine. |
| PUT | `/<id>/eligible-voters` | Admin | Body: `{ voter_ids: [...] }` — uses the human-readable `voter_id`, not the internal UUID. Replaces the full list. |

## Candidates — `/api`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/elections/<id>/candidates` | — | Public. |
| POST | `/elections/<id>/candidates` | Admin | Only while election is `draft`/`scheduled`. |
| PUT | `/candidates/<id>` | Admin | Same restriction. |
| DELETE | `/candidates/<id>` | Admin | Same restriction. |

## Voter admin management — `/api/admin/voters`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `` | Admin | List/search/paginate. Query: `?search=&is_verified=&is_active=`. |
| GET | `/<id>` | Admin | Single voter detail. |
| POST | `/<id>/verify` | Admin | Marks voter eligible to be added to elections. |
| POST | `/<id>/suspend` | Admin | Body: `{ reason }`. |
| POST | `/<id>/reactivate` | Admin | Clears suspension + failed-attempt lockout. |
| POST | `/<id>/revoke-sessions` | Admin | Force-logout everywhere. |
| POST | `/<id>/reset-biometrics` | Admin | Deletes stored face embedding. |

## Face recognition — `/api/face`

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/register` | Voter | Body: `{ images: [base64...] }` (5+ usable frames needed). Rejects if the face matches a different voter's already-registered face. |
| POST | `/verify` | Voter | Body: `{ images: [base64...], election_id? }`. Runs multi-face gate then liveness then identity match, in that order. |

## Voting — `/api`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/elections/<id>/vote-status` | Voter | Returns `has_voted`, `is_eligible`, `can_vote_now`. |
| POST | `/elections/<id>/vote` | Voter | Body: `{ candidate_id, face_images: [base64...] }`. Runs: eligibility, then fraud pre-check, then face verification, then hash, then block creation — all in one transaction. Rate-limited (3/min). |

## Blockchain explorer — `/api/blockchain`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `` | Admin | Paginated block list, newest first. |
| GET | `/verify` | Admin | Full-chain integrity check, returns `chain_valid` plus any invalid block indices/reasons. |
| GET | `/search` | Admin | Query: one of `transaction_id`, `hash`, `election_id`. |

## Fraud monitoring — `/api/fraud`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `` | Admin | Query: `?severity=&is_resolved=`. |
| POST | `/<id>/resolve` | Admin | Body: `{ notes }`. |

## Audit logs — `/api/audit`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `` | Admin | Query: `?action=` (substring match, e.g. `vote.cast`). |

## Results — `/api`

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/elections/<id>/results` | — | Public once election is `closed`. Includes vote tally, winner, participation percentage, and a fresh blockchain-verification check for that election. |
| GET | `/elections/<id>/results/export/pdf` | — | Downloads a formatted PDF. |
| GET | `/elections/<id>/results/export/excel` | — | Downloads an .xlsx workbook. |

---

## Roles reference

| Role | Can do |
|---|---|
| `super_admin` | Everything an Election Admin can, for any election, plus (via CLI) create other admin accounts. |
| `election_admin` | Manage only elections explicitly assigned to them: CRUD, lifecycle, candidates, eligibility, voter verification/suspension, fraud/audit/blockchain visibility. |
| `voter` | Register, verify biometrics, view elections, cast one vote per election they're eligible for. |
