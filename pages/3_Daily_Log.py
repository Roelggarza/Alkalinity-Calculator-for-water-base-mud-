"""Daily treatment log — Postgres when DATABASE_URL is set, local otherwise."""
from datetime import date

import pandas as pd
import streamlit as st

from utils import db
from utils.auth import require_login
from utils.dosing import corrosion_dose, scavenger_dose, h2s_status
from utils.ui import header, footer

st.set_page_config(page_title="Daily Log", page_icon="📓", layout="wide")
require_login()

header("Daily Treatment Log", "Entries, inventory tracking, and export")

USE_DB = db.available()
if USE_DB:
    db.init_db()
    st.caption("Connected storage: shared database.")
else:
    st.caption("Local mode — set DATABASE_URL for shared storage across devices.")
    if "daily_log" not in st.session_state:
        st.session_state["daily_log"] = pd.DataFrame(columns=db.COLUMN_NAMES)


def get_log() -> pd.DataFrame:
    if USE_DB:
        return db.fetch_log()
    return st.session_state["daily_log"]


def save_row(row: dict):
    if USE_DB:
        db.add_entry(row)
    else:
        st.session_state["daily_log"] = pd.concat(
            [st.session_state["daily_log"], pd.DataFrame([row])], ignore_index=True)


with st.expander("Add daily entry"):
    d = st.date_input("Date", value=date.today())
    c1, c2, c3, c4 = st.columns(4)
    operator, rig = c1.text_input("Operator"), c2.text_input("Rig")
    well, county = c3.text_input("Well / pad"), c4.text_input("County")
    c5, c6, c7 = st.columns(3)
    fluid = c5.selectbox("Fluid system", ["WBM", "Cut Brine", "Completion Brine", "OBM", "Clearfluid"])
    volume = c6.number_input("Volume (bbl)", min_value=0.0, format="%.0f")
    gpm = c7.number_input("GPM", min_value=0.0, format="%.0f")
    c8, c9, c10 = st.columns(3)
    temp = c8.number_input("Temp (°F)", min_value=0.0, format="%.0f")
    ph = c9.number_input("pH", min_value=0.0, max_value=14.0, format="%.1f")
    chlorides = c10.number_input("Chlorides (mg/L)", min_value=0.0, format="%.0f")
    c11, c12, c13 = st.columns(3)
    calcium = c11.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f")
    hardness = c12.number_input("Hardness (mg/L)", min_value=0.0, format="%.1f")
    coupon = c13.number_input("Coupon (MPY)", min_value=0.0, format="%.1f")
    c14, c15, c16 = st.columns(3)
    pf = c14.number_input("Pf", min_value=0.0, format="%.2f")
    mf = c15.number_input("Mf", min_value=0.0, format="%.2f")
    pm = c16.number_input("Pm", min_value=0.0, format="%.2f")
    c17, c18, c19 = st.columns(3)
    iron = c17.number_input("Iron (mg/L)", min_value=0.0, format="%.1f")
    do_ppm = c18.number_input("DO (ppm)", min_value=0.0, format="%.2f")
    h2s = c19.number_input("H₂S (ppm)", min_value=0.0, format="%.1f")

    st.markdown("**Inventory (gal)**")
    i1, i2, i3 = st.columns(3)
    scav_beg, scav_rec, scav_used = (i1.number_input("Scavenger begin", min_value=0.0, format="%.1f"),
                                    i2.number_input("Scavenger received", min_value=0.0, format="%.1f"),
                                    i3.number_input("Scavenger used", min_value=0.0, format="%.1f"))
    j1, j2, j3 = st.columns(3)
    corr_beg, corr_rec, corr_used = (j1.number_input("Corrosion begin", min_value=0.0, format="%.1f"),
                                    j2.number_input("Corrosion received", min_value=0.0, format="%.1f"),
                                    j3.number_input("Corrosion used", min_value=0.0, format="%.1f"))
    k1, k2, k3 = st.columns(3)
    buster_beg, buster_rec, buster_used = (k1.number_input("H₂S buster begin", min_value=0.0, format="%.1f"),
                                          k2.number_input("H₂S buster received", min_value=0.0, format="%.1f"),
                                          k3.number_input("H₂S buster used", min_value=0.0, format="%.1f"))
    n1, n2 = st.columns(2)
    pump_notes, h2s_notes = n1.text_input("Pump setting / notes"), n2.text_input("H₂S response / notes")

    if st.button("Add entry", type="primary"):
        dose_inp = {"fluid_system": fluid, "volume_bbl": volume, "gpm": gpm, "temp_f": temp,
                    "ph": ph, "chlorides": chlorides, "calcium": calcium, "hardness": hardness,
                    "pf": pf, "mf": mf, "pm": pm, "iron": iron, "do_ppm": do_ppm,
                    "h2s_ppm": h2s, "coupon_mpy": coupon, "co2_present": "No",
                    "pom_lime": 0, "pump_config": "Simplex"}
        save_row({"date": str(d), "operator": operator, "rig": rig, "well": well, "county": county,
                  "fluid_system": fluid, "volume_bbl": volume, "gpm": gpm, "temp_f": temp, "ph": ph,
                  "chlorides": chlorides, "calcium": calcium, "hardness": hardness,
                  "pf": pf, "mf": mf, "pm": pm, "iron": iron, "do_ppm": do_ppm,
                  "h2s_ppm": h2s, "coupon_mpy": coupon,
                  "corr_gal_day": round(corrosion_dose(dose_inp), 1),
                  "scav_gal_day": round(scavenger_dose(h2s), 1),
                  "h2s_status": h2s_status(h2s),
                  "scav_beg": scav_beg, "scav_rec": scav_rec, "scav_used": scav_used,
                  "scav_end": scav_beg + scav_rec - scav_used,
                  "corr_beg": corr_beg, "corr_rec": corr_rec, "corr_used": corr_used,
                  "corr_end": corr_beg + corr_rec - corr_used,
                  "buster_beg": buster_beg, "buster_rec": buster_rec, "buster_used": buster_used,
                  "buster_end": buster_beg + buster_rec - buster_used,
                  "pump_notes": pump_notes, "h2s_notes": h2s_notes})
        st.success("Entry added.")
        st.rerun()

log = get_log()
if len(log):
    st.dataframe(log, use_container_width=True, hide_index=True)
else:
    st.info("No entries yet.")

st.subheader("Export / import")
st.download_button("Download log as CSV", log.to_csv(index=False).encode("utf-8"),
                   file_name="daily_treatment_log.csv", mime="text/csv")
up = st.file_uploader("Import CSV", type=["csv"])
if up is not None:
    imported = pd.read_csv(up)
    n = 0
    for _, r in imported.iterrows():
        save_row({c: r[c] for c in db.COLUMN_NAMES if c in r})
        n += 1
    st.success(f"Imported {n} rows.")
    st.rerun()

if len(log) and st.button("Clear log"):
    if USE_DB:
        db.clear_log()
    else:
        st.session_state["daily_log"] = pd.DataFrame(columns=db.COLUMN_NAMES)
    st.warning("Log cleared.")
    st.rerun()

footer()
