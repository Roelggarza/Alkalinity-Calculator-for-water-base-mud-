# Compliance Checklist — Field Dosing App (internal use)

Internal field tool for a small crew. Not legal advice — for regulatory
questions beyond this list, consult a professional. Review this file
quarterly; update it when the operation changes.

## Before first deploy

- [ ] Dad's fork is **private** (Settings → Danger Zone → Change visibility).
- [ ] The field spreadsheet (real operator/rig/well data) is **not** in the repo.
- [ ] `APP_PASSWORD` set in Railway Variables — dad chose it and typed it
      directly. Never in chat, screenshots, or git.
- [ ] `SECRET_KEY` generated with `openssl rand -base64 32`, in Railway Variables.
- [ ] Cloudflare **Access email gate** on: dad + current crew emails only.
- [ ] Cloudflare **SSL Full (strict)**; WAF managed ruleset enabled.
- [ ] Postgres + Redis provisioned; app reads `DATABASE_URL` / `REDIS_URL`
      from the environment (referenced as `${{Postgres.DATABASE_URL}}`,
      never copy-pasted).
- [ ] Pre-deploy security review prompt (bottom of `docs/DEPLOY.md`) came back clean.
- [ ] Dad ran the app on his phone against a known day: dosing numbers match
      the spreadsheet.

## Access control (ongoing)

- [ ] Access list = current crew only. Remove anyone who leaves **within 24h**
      (Cloudflare Access + new `APP_PASSWORD`).
- [ ] Rotate `APP_PASSWORD` quarterly and on any crew change.
- [ ] Railway project members: dad + maintainer only.
- [ ] GitHub collaborators on the fork: dad + maintainer only.

## Data handling

- [ ] A daily-log entry is made for **every** treatment decision — the log is
      the record.
- [ ] CSV export of the log saved weekly as a second copy (NAS).
- [ ] Railway Postgres backups confirmed on; retention noted.
- [ ] No operator/rig/well data shared outside the crew (including screenshots).

## Model safety

- [ ] **No changes** to `utils/chemistry.py` or `utils/dosing.py` without the
      mud engineer's explicit sign-off. The factors are field-tuned, not textbook.
- [ ] Any math change is tested against the spreadsheet on 3+ known days
      **before** deploy.
- [ ] Recommendations are planning aids — the mud engineer makes the final
      call (stated in the app footer).
- [ ] Chemical handling follows the product **SDS**, not the app. The app never
      replaces safety data sheets or site procedures.

## If something goes wrong

- [ ] **App down** → fall back to the spreadsheet; contact the maintainer.
- [ ] **Suspected password leak** → change `APP_PASSWORD` in Railway →
      redeploy → confirm the old password fails.
- [ ] **Suspected bad data** → export the log CSV immediately (preserve the
      record), then investigate.
- [ ] **Secrets in git history** → rotate every secret, purge with
      `git filter-repo`, force-push, and treat old values as compromised.

## Quarterly review (15 minutes)

- [ ] Rotate `APP_PASSWORD` and `SECRET_KEY`.
- [ ] Review Cloudflare Access email list, Railway members, GitHub collaborators.
- [ ] Confirm a Postgres backup exists and restores.
- [ ] Confirm the repo is still private and no secrets are in git history.
- [ ] Confirm this checklist is still accurate.
