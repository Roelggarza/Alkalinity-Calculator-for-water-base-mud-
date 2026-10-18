"""Corrosion & H2S dosing calculator — ported from the Cactus field model."""
import streamlit as st
import pandas as pd

from utils.auth import require_login
from utils.cache import cached_recommendation
from utils.dosing import H2S_ESCALATION_PPM
from utils.ui import header, footer

st.set_page_config(page_title="Corrosion & H2S Dosing", page_icon="🛢️", layout="centered")
require_login()

header("Corrosion & H₂S Dosing",
       "Field planning tool — enter the current mud report and trailer measurements.")

MOD_LABELS = {
    "base": "Base corrosion dose", "fluid": "Fluid modifier", "chloride": "Chloride modifier",
    "calcium": "Calcium modifier", "hardness": "Hardness modifier", "oxygen": "Oxygen modifier",
    "co2": "CO₂ modifier", "h2s_corrosion": "H₂S corrosion modifier",
    "temperature": "Temperature modifier", "ph": "pH modifier", "coupon": "Coupon modifier",
    "iron": "Iron modifier", "alkalinity": "Alkalinity modifier", "turnover": "Turnover modifier",
}

with st.container(border=True):
    st.subheader("System")
    fluid = st.selectbox("Fluid system", ["WBM", "Cut Brine", "Completion Brine", "OBM"])
    s1, s2 = st.columns(2)
    volume = s1.number_input("Active system volume (bbl)", min_value=0.0, format="%.0f", value=1900.0)
    gpm = s2.number_input("Circulation rate (gpm)", min_value=0.0, format="%.0f")
    s3, s4 = st.columns(2)
    temp = s3.number_input("Temperature (°F)", min_value=0.0, format="%.0f", value=80.0)
    ph = s4.number_input("pH", min_value=0.0, max_value=14.0, format="%.1f", value=11.0)
    s5, s6 = st.columns(2)
    chlorides = s5.number_input("Chlorides (mg/L)", min_value=0.0, format="%.0f")
    calcium = s6.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f",
                              value=float(st.session_state.get("calcium", 0.0)))
    hardness = st.number_input("Total hardness (mg/L)", min_value=0.0, format="%.1f",
                               value=float(st.session_state.get("hardness", 0.0)))

with st.container(border=True):
    st.subheader("Alkalinity (shared mud check)")
    a1, a2, a3 = st.columns(3)
    pf = a1.number_input("Pf (mL)", min_value=0.0, format="%.2f", value=float(st.session_state.get("pf", 0.0)))
    mf = a2.number_input("Mf (mL)", min_value=0.0, format="%.2f", value=float(st.session_state.get("mf", 0.0)))
    pm = a3.number_input("Pm (mL)", min_value=0.0, format="%.2f", value=float(st.session_state.get("pm", 0.0)))
    st.session_state.update({"pf": pf, "mf": mf, "pm": pm, "calcium": calcium, "hardness": hardness})

with st.container(border=True):
    st.subheader("Field measurements")
    f1, f2 = st.columns(2)
    iron = f1.number_input("Iron (mg/L) — if available", min_value=0.0, format="%.1f")
    do_ppm = f2.number_input("Dissolved oxygen (ppm) — if available", min_value=0.0, format="%.2f")
    f3, f4 = st.columns(2)
    h2s = f3.number_input("H₂S (ppm) — current reading", min_value=0.0, format="%.1f")
    coupon = f4.number_input("Coupon corrosion (MPY) — if available", min_value=0.0, format="%.1f")
    f5, f6 = st.columns(2)
    co2 = f5.selectbox("CO₂ present", ["No", "Yes"])
    pom = f6.number_input("POM / lime — when relevant (OBM)", min_value=0.0, format="%.2f")

with st.container(border=True):
    st.subheader("Trailer")
    t1, t2 = st.columns(2)
    pump_config = t1.selectbox("Pump configuration", ["Simplex", "Duplex"])
    rig = t2.text_input("Rig / well (optional)")

inp = {
    "fluid_system": fluid, "volume_bbl": volume, "gpm": gpm, "temp_f": temp, "ph": ph,
    "chlorides": chlorides, "calcium": calcium, "hardness": hardness,
    "pf": pf, "mf": mf, "pm": pm, "pom_lime": pom, "iron": iron, "do_ppm": do_ppm,
    "h2s_ppm": h2s, "coupon_mpy": coupon, "co2_present": co2, "pump_config": pump_config,
}
rec = cached_recommendation(inp)

st.subheader("Dosing model")
with st.expander("Modifier breakdown"):
    st.dataframe(
        pd.DataFrame([{"Modifier": MOD_LABELS[k], "gal/day": f"{v:.1f}"}
                      for k, v in rec["modifiers"].items()]),
        use_container_width=True, hide_index=True)
    st.caption("Corrosion dose = base + modifiers, clamped to the 10–75 gal/day planning range.")

st.subheader("Recommendation")
r1, r2 = st.columns(2)
r1.metric("Corrosion inhibitor CT 610", f"{rec['corrosion_gal_day']:.1f} gal/day")
r2.metric("Corrosion pump rate", f"{rec['corrosion_gal_hr']:.2f} gal/hr")
r3, r4 = st.columns(2)
r3.metric("Blended H₂S scavenger (CT1000)", f"{rec['scavenger_gal_day']:.1f} gal/day")
r4.metric("Scavenger pump rate", f"{rec['scavenger_gal_hr']:.2f} gal/hr")

if h2s and h2s > H2S_ESCALATION_PPM:
    st.error(f"H₂S status: {rec['h2s_status']}")
elif h2s and h2s > 0:
    st.warning(f"H₂S status: {rec['h2s_status']}")
else:
    st.info(f"H₂S status: {rec['h2s_status']}")

st.subheader("Sidewinder trailer — closest timer setting")
st.caption("Chart values are approximate — field-verify pump output.")
for label, s in [("Corrosion inhibitor CT 610", rec["corrosion_setting"]),
                 ("CT1000 scavenger", rec["scavenger_setting"])]:
    with st.container(border=True):
        st.markdown(f"**{label}**")
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Plunger", s["plunger"])
        q2.metric("ON / OFF", f"{s['on_sec']}s / {s['off_sec']}s")
        q3.metric("Actual", f"{s['actual_gal_day']:.1f} gal/day")
        q4.metric("Difference", f"{s['diff_gal_day']:+.1f} gal/day")

st.subheader("Hydraulics")
h1, h2 = st.columns(2)
h1.metric("Circulation", f"{rec['circulation_bbl_hr']:.1f} bbl/hr")
h2.metric("System turnovers", f"{rec['turnovers_per_hr']:.2f} /hr")
h3, h4 = st.columns(2)
h3.metric("Corrosion normalized", f"{rec['corrosion_norm']:.2f} gal/100 bbl/day")
h4.metric("Scavenger normalized", f"{rec['scavenger_norm']:.2f} gal/100 bbl/day")

st.subheader("Export")
out = pd.DataFrame({
    "Parameter": ["Rig/Well", "Fluid system", "Volume (bbl)", "Corrosion CT 610 (gal/day)",
                  "Corrosion pump (gal/hr)", "Scavenger (gal/day)", "Scavenger pump (gal/hr)",
                  "H2S status", "Pump config",
                  "Corr plunger", "Corr ON/OFF (s)", "Scav plunger", "Scav ON/OFF (s)"],
    "Value": [rig, fluid, volume, round(rec["corrosion_gal_day"], 2), round(rec["corrosion_gal_hr"], 2),
              round(rec["scavenger_gal_day"], 2), round(rec["scavenger_gal_hr"], 2),
              rec["h2s_status"], pump_config,
              rec["corrosion_setting"]["plunger"],
              f"{rec['corrosion_setting']['on_sec']}/{rec['corrosion_setting']['off_sec']}",
              rec["scavenger_setting"]["plunger"],
              f"{rec['scavenger_setting']['on_sec']}/{rec['scavenger_setting']['off_sec']}"],
})
st.download_button("Download recommendation as CSV", out.to_csv(index=False).encode("utf-8"),
                   file_name="dosing_recommendation.csv", mime="text/csv")

footer()
