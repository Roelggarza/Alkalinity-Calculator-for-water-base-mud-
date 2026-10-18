# Deploy Runbook — Field Dosing App

Secure deployment: private GitHub repo → Railway (app + Postgres + Redis) →
Cloudflare in front (DNS + WAF + Access email gate). Secrets are generated
locally, sealed, and pasted directly into Railway — never in chat, screenshots,
git, or logs.

## Phase 1 — Make the repo private

1. Open `github.com/Roelggarza/Alkalinity-Calculator-for-water-base-mud-` →
   **Settings** → scroll to **Danger Zone** → **Change visibility** →
   **Make private** → type the repo name → confirm. A lock icon appears.
2. Sanity check: the repo should contain only `Alkalinity.py`, `.devcontainer/`,
   and the app files (`app.py`, `pages/`, `utils/`, `data/`, `docs/`).
   The field spreadsheet (real operator data) must never be committed.

## Phase 2 — Railway project

1. At railway.app, log in with the field owner's email (his project).
2. **New Project → Deploy from GitHub repo** → install the Railway GitHub App →
   select the private repo.
3. Service → **Settings → Deploy → Custom Start Command**:
   `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. **Settings → Networking → Generate Domain** → note the `*.up.railway.app`
   URL; don't share it.
5. Check **Deploy Logs** → open the Railway URL → confirm the app loads.

## Phase 3 — Postgres

1. Project canvas → **New → Database → PostgreSQL**.
2. Railway auto-generates strong credentials and injects `DATABASE_URL`.
   Reference it from the app service as `${{Postgres.DATABASE_URL}}` —
   never copy-paste it anywhere.

## Phase 4 — Redis

1. **New → Database → Redis**. `REDIS_URL` is auto-injected the same way.
2. The app uses Redis as a shared cache for dosing recommendations (1h TTL).
   It works fine without Redis too — caching is skipped if `REDIS_URL`
   is unset.

## Phase 5 — Secrets, sealed before input

Rule: plaintext secrets never touch chat, screenshots, git, or logs.

1. On your own machine (not in any chat), generate each secret:
   `openssl rand -base64 32` — run once per secret, copy straight from the terminal.
2. Railway → app service → **Variables** → paste directly as new variables.
   Railway encrypts them at rest and masks the values. Clear the terminal
   and clipboard afterward.
3. For the database URLs, never copy-paste at all — reference
   `${{Postgres.DATABASE_URL}}` and `${{Redis.REDIS_URL}}`.
4. Sealed backup (recommended): encrypt before storing anywhere —
   `age -p -o field-app-secrets.age`, paste `NAME=value` lines when prompted,
   keep the `.age` file on the NAS. Never in the repo.
5. Repo hygiene: `.gitignore` excludes `.env` and `.streamlit/secrets.toml`.
   The app reads secrets from the environment at runtime — nothing hardcoded.
6. Secrets you need:

   | Variable       | How to make it                          |
   |----------------|-----------------------------------------|
   | `APP_PASSWORD` | Owner picks it, types it directly into Railway Variables |
   | `SECRET_KEY`   | `openssl rand -base64 32`               |
   | `DATABASE_URL` | Railway Postgres (automatic)            |
   | `REDIS_URL`    | Railway Redis (automatic)               |

## Phase 6 — Cloudflare in front

1. Cloudflare dashboard → **Add site** → the domain → change nameservers at
   the registrar to Cloudflare's.
2. **DNS → Add record**: CNAME, name `dosing`, target
   `<railway-service>.up.railway.app`, proxy **ON** (orange cloud).
3. **SSL/TLS → Full (strict)**.
4. Railway → service → **Settings → Networking → Custom Domain** →
   add `dosing.<domain>` → Railway provisions the certificate.
5. Lockdown: **Zero Trust → Access → Add application → Self-hosted** →
   the domain → policy **Allow** for the owner's email (plus yours).
   Only those inboxes can reach the app.
6. Optional: **Security → WAF** → enable the managed ruleset.

## Phase 7 — Verify

- Open the Cloudflare URL → Access email login → app sign-in → app loads.
- Add a daily-log entry → confirm it persists after redeploy (Postgres).
- Rotate test: change `APP_PASSWORD` in Railway → redeploy →
  confirm the old password stops working.

Costs: Railway is usage-based after trial (a few dollars/month at this scale);
Cloudflare covers everything above on the free tier.

---

## Using Codex to help with deployment

The dashboard steps above (Railway clicks, Cloudflare DNS, pasting secrets)
need a human. Everything else can be handed to a Codex agent. Copy-paste any
of these prompts to it. Ground rules to give the agent first:

> Work on a branch, never on main. Never print, log, or commit secrets.
> Do not change the math in utils/chemistry.py or utils/dosing.py — the
> factors and dosing model are field-tuned and must stay exactly as they are.
> Ask before changing any file outside the task I give you.

**1. Local smoke test**
> Clone https://github.com/Roelggarza/Alkalinity-Calculator-for-water-base-mud-
> and get the app running locally with `pip install -r requirements.txt` then
> `streamlit run app.py`. Fix any import or startup errors you find. Report
> back exactly what you changed.

**2. Pre-deploy security review**
> Review this repo for deployment security issues: hardcoded secrets,
> credentials in git history, overly permissive CORS, missing .gitignore
> entries for .env and secrets files, debug flags left on. List everything
> you find with file and line number. Do not fix anything without asking.

**3. Railway start command check**
> Confirm the correct Railway custom start command for this Streamlit
> multipage app. The service must listen on the $PORT environment variable.
> Give me the exact string to paste into Railway's Custom Start Command field.

**4. Database wiring check**
> Using SQLAlchemy, verify that utils/db.py creates the daily_log table
> correctly against a local Postgres (or SQLite as a stand-in). Test
> add_entry, fetch_log, and clear_log round-trip. Report any schema
> mismatches. Do not touch the chemistry or dosing modules.

**5. Post-deploy verification checklist**
> Give me a curl/browser checklist to verify the deployed app: homepage
> loads over HTTPS, the sign-in gate blocks unauthenticated access,
> wrong password is rejected, and no Python stack traces leak to the page.

**6. Dependency audit**
> Check requirements.txt for known vulnerabilities and suggest pinned
> upgrades that keep the app working. Apply nothing without asking.
