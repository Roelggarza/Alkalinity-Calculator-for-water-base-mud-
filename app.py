"""Field Dosing App — alkalinity + corrosion/H2S for water-base mud."""
import streamlit as st

from utils.auth import require_login
from utils.ui import header, footer

st.set_page_config(page_title="Field Dosing App", page_icon="🛢️", layout="centered")
require_login()

for key, default in [("pm", 0.0), ("pf", 0.0), ("mf", 0.0),
                     ("calcium", 0.0), ("hardness", 0.0)]:
    st.session_state.setdefault(key, default)

header("Field Dosing App",
       "Alkalinity contamination response · Corrosion & H₂S dosing · Daily treatment log")

with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
        st.page_link("pages/1_Alkalinity.py", label="Alkalinity", icon="🧪")
        st.caption("Hydroxide / carbonate / bicarbonate speciation, advisories, treatments")
    with c2:
        st.page_link("pages/2_Corrosion_H2S.py", label="Corrosion & H₂S", icon="🛢️")
        st.caption("Dosing model, scavenger tiers, Sidewinder pump settings")
    with c3:
        st.page_link("pages/3_Daily_Log.py", label="Daily Log", icon="📓")
        st.caption("Treatment entries, inventory tracking, export")

with st.container(border=True):
    st.subheader("Shared mud check")
    st.caption("Entered once — used by both calculators.")
    k1, k2, k3 = st.columns(3)
    st.session_state["pm"] = k1.number_input("Pm (mL)", min_value=0.0, format="%.2f",
                                             value=float(st.session_state["pm"]), key="home_pm")
    st.session_state["pf"] = k2.number_input("Pf (mL)", min_value=0.0, format="%.2f",
                                             value=float(st.session_state["pf"]), key="home_pf")
    st.session_state["mf"] = k3.number_input("Mf (mL)", min_value=0.0, format="%.2f",
                                             value=float(st.session_state["mf"]), key="home_mf")
    k4, k5 = st.columns(2)
    st.session_state["calcium"] = k4.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f",
                                                  value=float(st.session_state["calcium"]), key="home_ca")
    st.session_state["hardness"] = k5.number_input("Hardness (mg/L)", min_value=0.0, format="%.1f",
                                                   value=float(st.session_state["hardness"]), key="home_hard")

footer()
