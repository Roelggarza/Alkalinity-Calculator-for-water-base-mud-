"""
Corrosion & H2S dosing model — ported from the Cactus 172 field spreadsheet.

Two fixes vs the spreadsheet are baked in (documented, intentional):
1. Sidewinder pump-type lookup: the sheet's rows 5-42 checked the wrong cell
   for Simplex/Duplex (copy-down bug). Here every row uses the pump setting.
2. Product naming unified to CT 610 (was CT 610 in the calculator, CT 510 in
   the notes). Confirmed correct by the field engineer 2026-10-17: CT 610 and
   CT1000 are specific product blends and the calculator's blend dosing is correct.

Everything else is a faithful port of the v1 model, including the tiered H2S
scavenger table. The per-ppm scavenger chemistry is vendor-proprietary
("active chemistry hidden" in the sheet) and is NOT reverse-engineered here.
"""

import csv
import os

CHART_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sidewinder_chart.csv")

BASE_CORROSION_DOSE = 15.0      # gal/day model constant
CORROSION_MIN, CORROSION_MAX = 10.0, 75.0
H2S_ESCALATION_PPM = 100.0      # >100 ppm: escalate, no blend scavenger


def modifiers(inp):
    """All 14 dosing modifiers. `inp` is a dict of field inputs. Returns dict."""
    m = {}
    m["base"] = BASE_CORROSION_DOSE
    m["fluid"] = 3.0 if inp.get("fluid_system") in ("Cut Brine", "Completion Brine") else 0.0

    cl = inp.get("chlorides") or 0
    m["chloride"] = 10.0 if cl >= 150000 else 7.0 if cl >= 100000 else 4.0 if cl >= 50000 else 0.0

    ca = inp.get("calcium") or 0
    m["calcium"] = 7.0 if ca >= 30000 else 4.0 if ca >= 10000 else 0.0

    th = inp.get("hardness") or 0
    m["hardness"] = 5.0 if th >= 30000 else 2.0 if th >= 10000 else 0.0

    do = inp.get("do_ppm") or 0
    m["oxygen"] = 12.0 if do >= 2 else 8.0 if do >= 1 else 4.0 if do >= 0.5 else 0.0

    m["co2"] = 8.0 if inp.get("co2_present") == "Yes" else 0.0

    h2s = inp.get("h2s_ppm") or 0
    m["h2s_corrosion"] = 5.0 if h2s >= 100 else 2.0 if h2s > 0 else 0.0

    t = inp.get("temp_f") or 0
    m["temperature"] = 10.0 if t >= 225 else 7.0 if t >= 175 else 4.0 if t >= 150 else 0.0

    ph = inp.get("ph")
    m["ph"] = 10.0 if (ph is not None and ph < 7.5) else 5.0 if (ph is not None and ph < 8.5) else 0.0

    coupon = inp.get("coupon_mpy") or 0
    m["coupon"] = 15.0 if coupon >= 5 else 8.0 if coupon >= 2 else 0.0

    fe = inp.get("iron") or 0
    m["iron"] = 8.0 if fe >= 100 else 3.0 if fe >= 25 else 0.0

    if inp.get("fluid_system") == "OBM":
        pom = inp.get("pom_lime") or 0
        m["alkalinity"] = 4.0 if pom < 1 else 0.0
    else:
        pf = inp.get("pf") or 0
        mf = inp.get("mf") or 0
        pm = inp.get("pm") or 0
        m["alkalinity"] = (4.0 if pf < 0.5 else 0.0) + (3.0 if mf < 1 else 0.0) + (3.0 if pm < 1 else 0.0)

    gpm = inp.get("gpm") or 0
    vol = inp.get("volume_bbl") or 0
    turnover = (gpm * 60 / 42) / vol if vol else 0
    m["turnover"] = 5.0 if turnover > 2 else 0.0

    return m


def corrosion_dose(inp):
    """Corrosion inhibitor CT 610 gal/day, clamped to the 10-75 planning range."""
    total = sum(modifiers(inp).values())
    return min(CORROSION_MAX, max(CORROSION_MIN, total))


def scavenger_dose(h2s_ppm):
    """Blended CT1000 H2S scavenger gal/day by H2S tier (v1 planning table)."""
    h2s = h2s_ppm or 0
    if h2s > 100 or h2s <= 0:
        return 0.0
    if h2s <= 25:
        return 12.0
    if h2s <= 50:
        return 20.0
    if h2s <= 75:
        return 30.0
    return 40.0


def h2s_status(h2s_ppm):
    h2s = h2s_ppm or 0
    if h2s > 100:
        return "ESCALATE - CleanTech 680 H2S Buster"
    if h2s == 0:
        return "No H2S treatment indicated"
    return "Run CT1000 scavenger"


def hydraulics(gpm, volume_bbl):
    circ = (gpm or 0) * 60 / 42
    return {
        "circulation_bbl_hr": circ,
        "turnovers_per_hr": circ / volume_bbl if volume_bbl else 0,
    }


def load_chart():
    with open(CHART_PATH, newline="") as f:
        return list(csv.DictReader(f))


def closest_setting(target_qt_day, pump_config):
    """Closest Sidewinder timer setting for a target qt/day.

    FIX vs spreadsheet: pump_config (Simplex/Duplex) applies to EVERY chart row.
    """
    col = "simplex_qt_day" if pump_config == "Simplex" else "duplex_qt_day"
    best, best_diff = None, None
    for row in load_chart():
        chart_qt = float(row[col])
        diff = abs(chart_qt - target_qt_day)
        if best_diff is None or diff < best_diff:
            best, best_diff = row, diff
    actual_gal_day = float(best[col]) / 4.0
    return {
        "plunger": best["plunger"],
        "on_sec": int(best["on_sec"]),
        "off_sec": int(best["off_sec"]),
        "chart_qt_day": float(best[col]),
        "actual_gal_day": actual_gal_day,
        "diff_gal_day": actual_gal_day - target_qt_day / 4.0,
    }


def full_recommendation(inp):
    """Everything the Field Calculator output section produces."""
    corr = corrosion_dose(inp)
    scav = scavenger_dose(inp.get("h2s_ppm"))
    hyd = hydraulics(inp.get("gpm"), inp.get("volume_bbl"))
    vol = inp.get("volume_bbl") or 0
    pump = inp.get("pump_config") or "Simplex"
    return {
        "modifiers": modifiers(inp),
        "corrosion_gal_day": corr,
        "corrosion_gal_hr": corr / 24,
        "scavenger_gal_day": scav,
        "scavenger_gal_hr": scav / 24,
        "h2s_status": h2s_status(inp.get("h2s_ppm")),
        "circulation_bbl_hr": hyd["circulation_bbl_hr"],
        "turnovers_per_hr": hyd["turnovers_per_hr"],
        "corrosion_norm": corr / vol * 100 if vol else 0,   # gal/100 bbl/day
        "scavenger_norm": scav / vol * 100 if vol else 0,
        "corrosion_setting": closest_setting(corr * 4, pump),
        "scavenger_setting": closest_setting(scav * 4, pump),
    }
