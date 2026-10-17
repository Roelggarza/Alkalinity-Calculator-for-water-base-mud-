"""Daily treatment log — entries, inventory math, CSV export/import."""
import streamlit as st
import pandas as pd
from datetime import date

from utils.dosing import corrosion_dose, scavenger_dose, h2s_status

st.set_page_config(page_title="Daily Treatment Log", layout="wide")
st.title("📓 Daily Treatment Log")

COLS = ["date", "operator", "rig", "well", "county", "fluid_system", "volume_bbl", "gpm",
        "temp_f", "ph", "chlorides", "calcium", "hardness", "pf", "mf", "pm",
        "iron", "do_ppm", "h2s_ppm", "coupon_mpy",
        "corr_gal_day", "scav_gal_day", "h2s_status",
        "scav_beg", "scav_rec", "scav_used", "scav_end",
        "corr_beg", "corr_rec", "corr_used", "corr_end",
        "buster_beg", "buster_rec", "buster_used", "buster_end",
        "pump_notes", "h2s_notes"]

if "daily_log" not in st.session_state:
    st.session_state["daily_log"] = pd.DataFrame(columns=COLS)

# === ADD ENTRY ===
with st.expander("➕ Add daily entry", expanded=False):
    d = st.date_input("Date", value=date.today())
    c1, c2, c3 = st.columns(3)
    operator = c1.text_input("Operator")
    rig = c2.text_input("Rig")
    well = c3.text_input("Well / Pad")
    c4, c5, c6 = st.columns(3)
    county = c4.text_input("County")
    fluid = c5.selectbox("Fluid System", ["WBM", "Cut Brine", "Completion Brine", "OBM", "Clearfluid"])
    volume = c6.number_input("Volume (bbl)", min_value=0.0, format="%.0f")
    c7, c8, c9 = st.columns(3)
    gpm = c7.number_input("GPM", min_value=0.0, format="%.0f")
    temp = c8.number_input("Temp (°F)", min_value=0.0, format="%.0f")
    ph = c9.number_input("pH", min_value=0.0, max_value=14.0, format="%.1f")
    c10, c11, c12 = st.columns(3)
    chlorides = c10.number_input("Chlorides (mg/L)", min_value=0.0, format="%.0f")
    calcium = c11.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f")
    hardness = c12.number_input("Hardness (mg/L)", min_value=0.0, format="%.1f")
    c13, c14, c15 = st.columns(3)
    pf = c13.number_input("Pf", min_value=0.0, format="%.2f")
    mf = c14.number_input("Mf", min_value=0.0, format="%.2f")
    pm = c15.number_input("Pm", min_value=0.0, format="%.2f")
    c16, c17, c18 = st.columns(3)
    iron = c16.number_input("Iron (mg/L)", min_value=0.0, format="%.1f")
    do_ppm = c17.number_input("DO (ppm)", min_value=0.0, format="%.2f")
    h2s = c18.number_input("H₂S (ppm)", min_value=0.0, format="%.1f")
    coupon = st.number_input("Coupon (MPY)", min_value=0.0, format="%.1f")

    st.markdown("**Inventory (gal)**")
    i1, i2, i3 = st.columns(3)
    scav_beg = i1.number_input("Scavenger begin", min_value=0.0, format="%.1f")
    scav_rec = i2.number_input("Scavenger received", min_value=0.0, format="%.1f")
    scav_used = i3.number_input("Scavenger used", min_value=0.0, format="%.1f")
    j1, j2, j3 = st.columns(3)
    corr_beg = j1.number_input("Corrosion begin", min_value=0.0, format="%.1f")
    corr_rec = j2.number_input("Corrosion received", min_value=0.0, format="%.1f")
    corr_used = j3.number_input("Corrosion used", min_value=0.0, format="%.1f")
    k1, k2, k3 = st.columns(3)
    buster_beg = k1.number_input("H₂S Buster begin", min_value=0.0, format="%.1f")
    buster_rec = k2.number_input("H₂S Buster received", min_value=0.0, format="%.1f")
    buster_used = k3.number_input("H₂S Buster used", min_value=0.0, format="%.1f")

    pump_notes = st.text_input("Pump setting / notes")
    h2s_notes = st.text_input("H₂S response / notes")

    if st.button("Add entry"):
        dose_inp = {"fluid_system": fluid, "volume_bbl": volume, "gpm": gpm, "temp_f": temp,
                    "ph": ph, "chlorides": chlorides, "calcium": calcium, "hardness": hardness,
                    "pf": pf, "mf": mf, "pm": pm, "iron": iron, "do_ppm": do_ppm,
                    "h2s_ppm": h2s, "coupon_mpy": coupon, "co2_present": "No",
                    "pom_lime": 0, "pump_config": "Simplex"}
        corr = corrosion_dose(dose_inp)
        scav = scavenger_dose(h2s)
        row = {"date": str(d), "operator": operator, "rig": rig, "well": well, "county": county,
               "fluid_system": fluid, "volume_bbl": volume, "gpm": gpm, "temp_f": temp, "ph": ph,
               "chlorides": chlorides, "calcium": calcium, "hardness": hardness,
               "pf": pf, "mf": mf, "pm": pm, "iron": iron, "do_ppm": do_ppm,
               "h2s_ppm": h2s, "coupon_mpy": coupon,
               "corr_gal_day": round(corr, 1), "scav_gal_day": round(scav, 1),
               "h2s_status": h2s_status(h2s),
               "scav_beg": scav_beg, "scav_rec": scav_rec, "scav_used": scav_used,
               "scav_end": scav_beg + scav_rec - scav_used,
               "corr_beg": corr_beg, "corr_rec": corr_rec, "corr_used": corr_used,
               "corr_end": corr_beg + corr_rec - corr_used,
               "buster_beg": buster_beg, "buster_rec": buster_rec, "buster_used": buster_used,
               "buster_end": buster_beg + buster_rec - buster_used,
               "pump_notes": pump_notes, "h2s_notes": h2s_notes}
        st.session_state["daily_log"] = pd.concat(
            [st.session_state["daily_log"], pd.DataFrame([row])], ignore_index=True)
        st.success("Entry added.")

# === TABLE ===
log = st.session_state["daily_log"]
if len(log):
    st.dataframe(log, use_container_width=True, hide_index=True)
else:
    st.info("No entries yet. Add the first one above, or import a CSV below.")

# === EXPORT / IMPORT ===
st.markdown("### 📤 Export / Import")
st.download_button("📥 Download log as CSV", log.to_csv(index=False).encode("utf-8"),
                   file_name="daily_treatment_log.csv", mime="text/csv")
up = st.file_uploader("Import CSV (same columns)", type=["csv"])
if up is not None:
    imported = pd.read_csv(up)
    st.session_state["daily_log"] = pd.concat([log, imported], ignore_index=True)
    st.success(f"Imported {len(imported)} rows.")

if len(log) and st.button("🗑️ Clear log"):
    st.session_state["daily_log"] = pd.DataFrame(columns=COLS)
    st.warning("Log cleared.")
