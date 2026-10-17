# Ledger Vote — Secure Hybrid Blockchain E-Voting System

A biometric-secured, blockchain-verified electronic voting platform: face recognition (MediaPipe + InsightFace), a custom SHA-256 blockchain, and a fraud-detection layer, all backing a full election-management workflow.

Built as a final-year engineering / portfolio project. **Not** built on Ethereum or Hyperledger — the blockchain here is a from-scratch SHA-256 hash chain implemented specifically for this system (see `backend/app/blockchain/`).

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS, React Router, Axios, React Hook Form, react-webcam, Chart.js, Framer Motion, Lucide icons |
| Backend | Flask, SQLAlchemy, Alembic, Flask-JWT-Extended, Flask-CORS, Flask-Limiter, bcrypt |
| Biometrics | MediaPipe (face detection + liveness), InsightFace/ArcFace (face embeddings) |
| Database | Neon (managed serverless PostgreSQL) |
| Blockchain | Custom SHA-256 hash chain (no external blockchain framework) |

---

## Features

- **Three roles**: Super Admin, Election Admin, Voter — JWT auth with bcrypt password hashing, refresh token rotation, account lockout after repeated failed attempts.
- **Election lifecycle**: draft → scheduled → live → paused → closed, with candidate/eligibility management locked once an election goes live.
- **Face registration & verification**: MediaPipe detects/counts faces and checks liveness (blink + head-turn); InsightFace generates 512-d embeddings, AES-encrypted at rest. Cross-voter duplicate-face detection prevents the same person registering multiple accounts.
- **Face registration & verification is the sole biometric method.** MediaPipe/InsightFace-driven, required before a voter can cast a vote.
- **Fraud detection**: duplicate votes, multiple simultaneous sessions, multiple devices, excessive failed attempts, liveness failures — each logged with a severity score; an aggregate score can block a vote outright.
- **Custom blockchain**: every cast vote becomes a block, SHA-256-linked to the previous block. Tampering with any block's contents is detectable — either immediately (unrecomputed hash mismatch) or at the very next block's link (if an attacker also re-hashes to cover their tracks). See `backend/tests/test_blockchain.py`.
- **Admin dashboard**: election/candidate management, voter verification, fraud monitoring, blockchain explorer (with a one-click full-chain integrity check), audit logs, results (with PDF/Excel export).

---

## Project structure

```
evoting-system/
├── backend/     Flask API — see backend/migrations/reference_schema.sql for the DB schema
├── frontend/    React app (Vite)
└── docker-compose.yml
```

---

## Local setup (no Docker)

### 1. Database

This project uses **Neon** (managed Postgres), not a local Postgres install:
1. Create a free project at neon.tech.
2. Copy the connection string from the dashboard (looks like `postgresql://user:pass@ep-xxxx.aws.neon.tech/dbname?sslmode=require`).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `DATABASE_URL` → your Neon connection string
- `SECRET_KEY`, `JWT_SECRET_KEY` → generate with `python -c "import secrets; print(secrets.token_hex(32))"` (run twice, use a different value for each)
- `FIELD_ENCRYPTION_KEY` → generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

Then:
```bash
flask db upgrade
flask create-super-admin --name "Your Name" --email admin@example.com --password "Str0ng!Pass1"
flask seed-demo-data      # optional: creates a sample Election Admin + draft election
flask run
```

**Windows note:** `insightface` needs a C++ compiler to build from source. Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (check "Desktop development with C++") before `pip install -r requirements.txt` if you hit a compiler error.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. The Vite dev server proxies `/api` to `http://localhost:5000` (see `vite.config.js`) — keep the backend running.

---

## Docker (alternative to local setup)

```bash
docker compose up --build
```
Backend on `:5000`, frontend on `:80`. `backend/.env` still needs to be filled in first (same as above) — Docker Compose reads it via `env_file`. Run migrations once the containers are up:
```bash
docker compose exec backend flask db upgrade
docker compose exec backend flask create-super-admin --name "Your Name" --email admin@example.com --password "Str0ng!Pass1"
```

---

## Useful CLI commands

```bash
flask create-super-admin --name NAME --email EMAIL --password PASSWORD
flask seed-demo-data                              # sample election admin + draft election
flask revoke-voter-sessions --email EMAIL         # force-logout a voter everywhere
flask reset-voter-biometrics --email EMAIL        # clear a voter's face enrollment
flask reset-voter-test-data --email EMAIL         # both of the above in one command
flask wipe-test-data [--yes]                      # wipe ALL voters/elections/votes/blocks/logs (keeps admin accounts)
```

## Testing

```bash
cd backend
pytest -v
```
Covers: blockchain tamper detection, election lifecycle state machine, fraud scoring logic, and face embedding matching/encryption. All pure-logic tests — no live DB/webcam needed to run them.

For testing the full biometric + voting flow against a **real** webcam, see `backend/scripts/`:
- `check_face_setup.py` — sanity-checks MediaPipe/InsightFace work on your machine
- `setup_vote_test_election.py` + `/dev/vote-test` (dev-mode only route) — scripted election setup, then a browser page to complete face registration and vote with a real webcam

---

## Known limitations (stated honestly, not hidden)

- **Liveness detection is heuristic**, not a dedicated anti-spoofing model. It defeats static photos and careless replay attempts; it is not a claim of defeating sophisticated real-time deepfakes.
- **Vote anonymity tradeoff**: `voter_id` is stored on the `Vote` row (not just the eligibility check) to enforce one-vote-per-election at the database level and support audit/dispute resolution — the same tradeoff most real-world verifiable e-voting systems make. Full anonymity would need a separate eligibility ledger decoupled from vote content.
- **Face duplicate-check is a linear scan** across all registered voters at registration time (not per-vote). Fine at single-election-roll scale; a system with millions of voters would need approximate nearest-neighbor indexing (e.g. pgvector) instead.

---

## License

Student engineering project — no license asserted beyond what your institution requires for submission.
