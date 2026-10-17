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
   pump timer settings.
3. **Daily treatment log** — entries with auto-computed dosing, inventory
   tracking (begin + received − used = ending), CSV export/import.

The shared mud check (Pm/Pf/Mf/calcium/hardness) is entered once and used by
both calculators.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)

Push to GitHub, then at share.streamlit.io create an app pointing at `app.py`.
Free tier works fine.

## Notes

- Products are **CT 610** (corrosion inhibitor) and **CT1000** (H2S scavenger) —
  specific vendor blends; the calculator's blend dosing is confirmed correct
  (spreadsheet notes said CT 510 — that was the typo).
- The Sidewinder pump-type lookup was fixed vs the spreadsheet (its rows 5–42
  checked the wrong cell for Simplex/Duplex).
- The H2S scavenger per-ppm chemistry is vendor-proprietary; only the v1 tier
  planning table is modeled here.
- Daily log data lives in session state (ephemeral). For crew-wide persistence,
  back it with Google Sheets or a small database.
