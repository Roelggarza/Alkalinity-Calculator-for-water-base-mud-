"""Corrosion & H2S dosing calculator — ported from the Cactus field spreadsheet."""
import streamlit as st
import pandas as pd

from utils.dosing import full_recommendation, H2S_ESCALATION_PPM

st.set_page_config(page_title="Corrosion & H2S Dosing", layout="centered")
st.title("🛢️ Corrosion & H₂S Dosing Calculator")
st.caption("Field planning tool — enter the current mud report and trailer measurements.")

MOD_LABELS = {
    "base": "Base corrosion dose", "fluid": "Fluid modifier", "chloride": "Chloride modifier",
    "calcium": "Calcium modifier", "hardness": "Hardness modifier", "oxygen": "Oxygen modifier",
    "co2": "CO₂ modifier", "h2s_corrosion": "H₂S corrosion modifier",
    "temperature": "Temperature modifier", "ph": "pH modifier", "coupon": "Coupon modifier",
    "iron": "Iron modifier", "alkalinity": "Alkalinity modifier", "turnover": "Turnover modifier",
}

# === INPUTS ===
st.header("🧪 Inputs")
fluid = st.selectbox("Fluid System", ["WBM", "Cut Brine", "Completion Brine", "OBM"])
volume = st.number_input("Active System Volume (bbl)", min_value=0.0, format="%.0f", value=1900.0)
gpm = st.number_input("Circulation Rate (gpm)", min_value=0.0, format="%.0f")
temp = st.number_input("Temperature (°F)", min_value=0.0, format="%.0f", value=80.0)
ph = st.number_input("pH", min_value=0.0, max_value=14.0, format="%.1f", value=11.0)
chlorides = st.number_input("Chlorides (mg/L)", min_value=0.0, format="%.0f")
calcium = st.number_input("Calcium (mg/L) — mud report", min_value=0.0, format="%.1f",
                          value=float(st.session_state.get("calcium", 0.0)))
hardness = st.number_input("Total Hardness (mg/L) — mud report", min_value=0.0, format="%.1f",
                           value=float(st.session_state.get("hardness", 0.0)))

st.subheader("Alkalinity (shared mud check)")
c1, c2, c3 = st.columns(3)
pf = c1.number_input("Pf (mL)", min_value=0.0, format="%.2f", value=float(st.session_state.get("pf", 0.0)))
mf = c2.number_input("Mf (mL)", min_value=0.0, format="%.2f", value=float(st.session_state.get("mf", 0.0)))
pm = c3.number_input("Pm (mL)", min_value=0.0, format="%.2f", value=float(st.session_state.get("pm", 0.0)))
st.session_state.update({"pf": pf, "mf": mf, "pm": pm, "calcium": calcium, "hardness": hardness})

st.subheader("Field measurements")
iron = st.number_input("Iron (mg/L) — if available", min_value=0.0, format="%.1f")
do_ppm = st.number_input("Dissolved Oxygen (ppm) — if available", min_value=0.0, format="%.2f")
h2s = st.number_input("H₂S (ppm) — current field reading", min_value=0.0, format="%.1f")
coupon = st.number_input("Coupon Corrosion (MPY) — latest coupon if available", min_value=0.0, format="%.1f")
co2 = st.selectbox("CO₂ Present", ["No", "Yes"])
pom = st.number_input("POM / Lime — use when relevant (OBM)", min_value=0.0, format="%.2f")

st.subheader("Trailer")
pump_config = st.selectbox("Pump Configuration", ["Simplex", "Duplex"])
rig = st.text_input("Rig / Well (optional)")

inp = {
    "fluid_system": fluid, "volume_bbl": volume, "gpm": gpm, "temp_f": temp, "ph": ph,
    "chlorides": chlorides, "calcium": calcium, "hardness": hardness,
    "pf": pf, "mf": mf, "pm": pm, "pom_lime": pom, "iron": iron, "do_ppm": do_ppm,
    "h2s_ppm": h2s, "coupon_mpy": coupon, "co2_present": co2, "pump_config": pump_config,
}
rec = full_recommendation(inp)

# === MODIFIER BREAKDOWN ===
st.header("🧮 Dosing Model")
mod_df = pd.DataFrame(
    [{"Modifier": MOD_LABELS[k], "gal/day": f"{v:.1f}"} for k, v in rec["modifiers"].items()]
)
st.dataframe(mod_df, use_container_width=True, hide_index=True)
st.caption(f"Corrosion dose = base + modifiers, clamped to 10–75 gal/day planning range.")

# === RECOMMENDATION ===
st.header("📋 Field Recommendation")
r1, r2 = st.columns(2)
r1.metric("Corrosion Inhibitor CT 610", f"{rec['corrosion_gal_day']:.1f} gal/day")
r2.metric("Corrosion pump rate", f"{rec['corrosion_gal_hr']:.2f} gal/hr")
r3, r4 = st.columns(2)
r3.metric("Blended H₂S Scavenger", f"{rec['scavenger_gal_day']:.1f} gal/day")
r4.metric("Scavenger pump rate", f"{rec['scavenger_gal_hr']:.2f} gal/hr")

status = rec["h2s_status"]
if h2s and h2s > H2S_ESCALATION_PPM:
    st.error(f"🚨 H₂S Treatment Status: {status}")
elif h2s and h2s > 0:
    st.warning(f"⚠️ H₂S Treatment Status: {status}")
else:
    st.info(f"ℹ️ H₂S Treatment Status: {status}")

# === SIDEWINDER ===
st.header("⏱️ Sidewinder Dosing Trailer — Closest Timer Setting")
st.caption("Chart values are approximate — field-verify pump output.")
for label, s in [("Corrosion Inhibitor CT 610", rec["corrosion_setting"]),
                 ("CT1000 Scavenger", rec["scavenger_setting"])]:
    st.markdown(f"**{label}** — target {s['chart_qt_day'] + s['diff_gal_day'] * 4:.1f} qt/day")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Plunger", s["plunger"])
    sc2.metric("ON / OFF (sec)", f"{s['on_sec']} / {s['off_sec']}")
    sc3.metric("Actual", f"{s['actual_gal_day']:.1f} gal/day")
    sc4.metric("Difference", f"{s['diff_gal_day']:+.1f} gal/day")

# === HYDRAULICS ===
st.header("🌊 Hydraulics / Normalization")
h1, h2 = st.columns(2)
h1.metric("Circulation", f"{rec['circulation_bbl_hr']:.1f} bbl/hr")
h2.metric("System turnovers", f"{rec['turnovers_per_hr']:.2f} /hr")
h3, h4 = st.columns(2)
h3.metric("Corrosion normalized", f"{rec['corrosion_norm']:.2f} gal/100 bbl/day")
h4.metric("Scavenger normalized", f"{rec['scavenger_norm']:.2f} gal/100 bbl/day")

# === EXPORT ===
st.header("📤 Export")
out = {
    "Parameter": ["Rig/Well", "Fluid System", "Volume (bbl)", "Corrosion CT 610 (gal/day)",
                  "Corrosion pump (gal/hr)", "Scavenger (gal/day)", "Scavenger pump (gal/hr)",
                  "H2S status", "Pump config",
                  "Corr plunger", "Corr ON/OFF (s)", "Scav plunger", "Scav ON/OFF (s)"],
    "Value": [rig, fluid, volume, round(rec["corrosion_gal_day"], 2), round(rec["corrosion_gal_hr"], 2),
              round(rec["scavenger_gal_day"], 2), round(rec["scavenger_gal_hr"], 2),
              status, pump_config,
              rec["corrosion_setting"]["plunger"],
              f"{rec['corrosion_setting']['on_sec']}/{rec['corrosion_setting']['off_sec']}",
              rec["scavenger_setting"]["plunger"],
              f"{rec['scavenger_setting']['on_sec']}/{rec['scavenger_setting']['off_sec']}"],
}
st.download_button("📥 Download recommendation as CSV",
                   pd.DataFrame(out).to_csv(index=False).encode("utf-8"),
                   file_name="dosing_recommendation.csv", mime="text/csv")
