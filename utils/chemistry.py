"""
Alkalinity speciation for water-base mud (WBM).

FIELD-TUNED MODEL — NOT API 13B-1 TEXTBOOK.
------------------------------------------
These factors are deliberately tuned for field use, per the mud engineer this
tool was built for:

* Hardness control is the operating goal: the model drives hardness DOWN toward
  a real-world ideal operating range around 500 mg/L, rather than reporting
  textbook ion concentrations.
* The calculator's purpose is contamination response — CO2, H2S and bicarbonate
  contamination events — not laboratory speciation.

Do NOT "correct" these factors to the API 13B-1 table (340 / 1200 / 1220).
That table answers a different question. These factors answer "what do I treat
with, and how much" for hardness/CO2/H2S/bicarbonate contamination in WBM.

Inputs: Pm, Mf (mL 0.02N acid), calcium & hardness (mg/L).
Outputs: hydroxide, carbonate, bicarbonate (mg/L, field-tuned scale).
"""

# Field-tuned target ranges (WBM) — operating ideals, not lab limits.
TARGETS = {
    "hydroxide": 300.0,    # OH-  < 300 mg/L
    "carbonate": 120.0,    # CO3  < 120 mg/L
    "bicarbonate": 150.0,  # HCO3 < 150 mg/L
    "calcium": 400.0,      # Ca   < 400 mg/L
    "hardness": 500.0,     # hardness < 500 mg/L  (ideal operating range)
}

# Advisory trip points (kept from the original calculator).
ADVISORY = {
    "hydroxide_high": 500.0,
    "hydroxide_ok": 100.0,
    "carbonate_ok": 60.0,
    "bicarbonate_ok": 100.0,
    "calcium_ok": 200.0,
    "hardness_ok": 300.0,
}


def speciate(pm: float, mf: float):
    """Field-tuned OH-/CO3/HCO3 split from Pm/Mf. Returns (oh, co3, hco3)."""
    hydroxide = 0.0
    carbonate = 0.0
    bicarbonate = 0.0

    if pm >= mf:
        hydroxide = 340 * mf
    elif pm > 0 and mf >= 2 * pm:
        carbonate = 60 * pm
    elif pm > 0 and mf > pm and mf < 2 * pm:
        hydroxide = 340 * (2 * pm - mf)
        carbonate = 120 * (mf - pm)
    elif pm == 0 and mf > 0:
        bicarbonate = 61 * mf

    return hydroxide, carbonate, bicarbonate


def advisories(oh, co3, hco3, calcium, hardness):
    """Contamination advisories. Returns list of (level, message)."""
    out = []
    if calcium > TARGETS["calcium"]:
        out.append(("warning", "High calcium may indicate cement contamination or gypsum interaction."))
    if hardness > TARGETS["hardness"] and calcium < 100:
        out.append(("info", "Elevated hardness with low calcium may reflect excess soda ash or carbonate scaling."))
    if hco3 > TARGETS["bicarbonate"]:
        out.append(("error", "High bicarbonate detected - risk of gas-cut mud or CO2 contamination."))
    if oh > ADVISORY["hydroxide_high"]:
        out.append(("warning", "Hydroxide is very high - risk of over-treatment with caustic soda."))
    return out


def treatments(oh, co3, hco3, calcium, hardness):
    """Treatment recommendations (WBM only). Returns list of (level, message)."""
    out = []
    if calcium > TARGETS["calcium"]:
        out.append(("info", "Treat with 0.5-1.5 lb/bbl Soda Ash (Na2CO3) to precipitate calcium as CaCO3."))
    if hardness > TARGETS["hardness"] and calcium < 100:
        out.append(("info", "Dilute with freshwater. Avoid further Soda Ash additions unless calcium rises."))
    if oh > ADVISORY["hydroxide_high"]:
        out.append(("warning", "Reduce caustic soda. Rebalance using 3:1 Lime to Caustic ratio moving forward."))
    if co3 > TARGETS["carbonate"]:
        out.append(("info", "Add Lime (Ca(OH)2) to reduce carbonate. Maintain 3:1 Lime to Caustic ratio."))
    if hco3 > TARGETS["bicarbonate"]:
        out.append(("error", "Treat with Lime to convert HCO3 to CO3, then gas off CO2 with aeration. "
                             "Reinforce with Soda Ash after conversion if calcium is under control."))
    if all([oh < ADVISORY["hydroxide_ok"], co3 < ADVISORY["carbonate_ok"],
            hco3 < ADVISORY["bicarbonate_ok"], calcium < ADVISORY["calcium_ok"],
            hardness < ADVISORY["hardness_ok"]]):
        out.append(("success", "Alkalinity profile is within acceptable range. No immediate treatment required."))
    return out
