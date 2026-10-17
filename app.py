"""Field Dosing App — alkalinity + corrosion/H2S for water-base mud.

Home page. Shared mud-check inputs live in st.session_state so the
Alkalinity and Corrosion/H2S pages work from the same numbers.
"""
import streamlit as st

st.set_page_config(page_title="Field Dosing App (WBM)", layout="centered")

# Shared mud-check state (written by the Alkalinity page, read by Dosing).
for key, default in [("pm", 0.0), ("pf", 0.0), ("mf", 0.0),
                     ("calcium", 0.0), ("hardness", 0.0)]:
    st.session_state.setdefault(key, default)

st.title("🛢️ Field Dosing App (WBM)")
st.markdown(
    "One app for the trailer: **alkalinity contamination** response "
    "(hardness / CO2 / H2S / bicarbonate) and **corrosion + H2S dosing** "
    "with Sidewinder pump settings, plus the **daily treatment log**."
)

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/1_Alkalinity.py", label="🧪 Alkalinity", icon="🧪")
    st.caption("Pm/Pf/Mf speciation, advisories, treatments")
with col2:
    st.page_link("pages/2_Corrosion_H2S.py", label="🛢️ Corrosion + H₂S", icon="🛢️")
    st.caption("Dosing model, scavenger tiers, pump settings")
with col3:
    st.page_link("pages/3_Daily_Log.py", label="📓 Daily Log", icon="📓")
    st.caption("Treatment log with inventory + CSV export")

st.divider()
st.markdown("### 🧪 Shared mud check")
st.caption("Entered once here, used by both calculators.")
c1, c2, c3 = st.columns(3)
st.session_state["pm"] = c1.number_input("Pm (mL)", min_value=0.0, format="%.2f",
                                         value=float(st.session_state["pm"]), key="home_pm")
st.session_state["pf"] = c2.number_input("Pf (mL)", min_value=0.0, format="%.2f",
                                         value=float(st.session_state["pf"]), key="home_pf")
st.session_state["mf"] = c3.number_input("Mf (mL)", min_value=0.0, format="%.2f",
                                         value=float(st.session_state["mf"]), key="home_mf")
c4, c5 = st.columns(2)
st.session_state["calcium"] = c4.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f",
                                              value=float(st.session_state["calcium"]), key="home_ca")
st.session_state["hardness"] = c5.number_input("Hardness (mg/L)", min_value=0.0, format="%.1f",
                                               value=float(st.session_state["hardness"]), key="home_hard")

st.divider()
st.caption("Field-tuned models for WBM contamination response. Verify dosing against the current "
           "mud report before treating. H2S > 100 ppm: escalate per the H2S response plan.")
