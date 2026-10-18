# Field Dosing App (WBM)

One Streamlit app combining two field tools for water-base mud:

1. **Alkalinity contamination calculator** — Pm/Pf/Mf speciation into hydroxide,
   carbonate, bicarbonate with contamination advisories and WBM treatment
   recommendations. **Field-tuned model** (see `utils/chemistry.py`): the factors
   are deliberately tuned for hardness control (ideal operating range ~500 mg/L)
   and CO2/H2S/bicarbonate contamination response — not API 13B-1 textbook
   speciation. Do not "correct" them without the mud engineer.
2. **Corrosion & H2S dosing calculator** — 14-modifier dosing model producing
   CT 610 corrosion inhibitor gal/day (clamped 10–75), tiered CT1000 H2S
   scavenger dosing, H2S escalation status, hydraulics, and closest Sidewinder
   pump timer settings. Products are specific vendor blends; the blend dosing
   is confirmed correct.
3. **Daily treatment log** — entries with auto-computed dosing, inventory
   tracking (begin + received − used = ending), CSV export/import. Uses
   Postgres when `DATABASE_URL` is set, otherwise local session storage.

The shared mud check (Pm/Pf/Mf/calcium/hardness) is entered once and used by
both calculators.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Railway)

See `docs/DEPLOY.md` for the full runbook: private repo, Railway + Postgres +
Redis, Cloudflare in front, sealed secrets.

Quick version:

```bash
# Railway service start command:
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Environment variables:

| Variable       | Source                          | Purpose                        |
|----------------|---------------------------------|--------------------------------|
| `DATABASE_URL` | Railway Postgres (auto)         | Shared daily-log storage       |
| `REDIS_URL`    | Railway Redis (auto)            | Dosing-result cache            |
| `APP_PASSWORD` | You (sealed, see DEPLOY.md)     | Sign-in gate for the app       |
| `SECRET_KEY`   | You (sealed)                    | Session signing                |

## Notes

- The Sidewinder pump-type lookup was fixed vs the spreadsheet (its rows 5–42
  checked the wrong cell for Simplex/Duplex).
- The H2S scavenger per-ppm chemistry is vendor-proprietary; only the v1 tier
  planning table is modeled here.
- `Alkalinity.py` at the repo root is the original single-file app, kept for
  reference. The multipage app deploys from `app.py`.
