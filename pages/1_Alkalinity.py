"""Alkalinity contamination calculator (WBM only)."""
import streamlit as st
import pandas as pd

from utils.auth import require_login
from utils.chemistry import speciate, advisories, treatments, TARGETS
from utils.ui import header, footer

st.set_page_config(page_title="Alkalinity", page_icon="🧪", layout="centered")
require_login()

header("Alkalinity Contamination Calculator",
       "Water-base mud · field-tuned for hardness control and CO₂ / H₂S / bicarbonate response")

with st.container(border=True):
    st.subheader("Mud check values")
    pm = st.number_input("Phenolphthalein alkalinity, Pm (mL)", min_value=0.0, format="%.2f",
                         value=float(st.session_state.get("pm", 0.0)))
    pf = st.number_input("Filtrate alkalinity, Pf (mL)", min_value=0.0, format="%.2f",
                         value=float(st.session_state.get("pf", 0.0)))
    mf = st.number_input("M alkalinity, Mf (mL)", min_value=0.0, format="%.2f",
                         value=float(st.session_state.get("mf", 0.0)))
    c1, c2 = st.columns(2)
    calcium = c1.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f",
                              value=float(st.session_state.get("calcium", 0.0)))
    hardness = c2.number_input("Hardness (mg/L)", min_value=0.0, format="%.1f",
                               value=float(st.session_state.get("hardness", 0.0)))

st.session_state.update({"pm": pm, "pf": pf, "mf": mf, "calcium": calcium, "hardness": hardness})

if pm > mf:
    st.warning("Pm exceeds Mf — check the titration. Treated as all-hydroxide below.")

hydroxide, carbonate, bicarbonate = speciate(pm, mf)

st.subheader("Species breakdown")
m1, m2, m3 = st.columns(3)
m1.metric("Hydroxide (OH⁻)", f"{hydroxide:.2f} mg/L")
m2.metric("Carbonate (CO₃²⁻)", f"{carbonate:.2f} mg/L")
m3.metric("Bicarbonate (HCO₃⁻)", f"{bicarbonate:.2f} mg/L")

with st.expander("Target ranges (WBM)"):
    st.markdown(f"""
- Hydroxide (OH⁻): < {TARGETS['hydroxide']:.0f} mg/L
- Carbonate (CO₃²⁻): < {TARGETS['carbonate']:.0f} mg/L
- Bicarbonate (HCO₃⁻): < {TARGETS['bicarbonate']:.0f} mg/L
- Calcium: < {TARGETS['calcium']:.0f} mg/L
- Hardness: < {TARGETS['hardness']:.0f} mg/L (ideal operating range)
""")

st.subheader("Contamination advisory")
flags = advisories(hydroxide, carbonate, bicarbonate, calcium, hardness)
if flags:
    for level, msg in flags:
        {"warning": st.warning, "info": st.info, "error": st.error}[level](msg)
else:
    st.success("No contamination flags on this mud check.")

st.subheader("Recommended treatment (WBM only)")
for level, msg in treatments(hydroxide, carbonate, bicarbonate, calcium, hardness):
    {"warning": st.warning, "info": st.info, "error": st.error, "success": st.success}[level](msg)

with st.expander("Treatment ratio advisory"):
    st.markdown("All caustic soda additions should be paired with **3 parts lime for every "
                "1 part caustic** in WBM systems. This prevents runaway alkalinity, emulsion "
                "instability, and downstream bicarbonate contamination.")

st.subheader("Export")
df = pd.DataFrame({
    "Parameter": ["Pm", "Pf", "Mf", "Calcium", "Hardness", "Hydroxide", "Carbonate", "Bicarbonate"],
    "Value": [pm, pf, mf, calcium, hardness, hydroxide, carbonate, bicarbonate],
})
st.download_button("Download results as CSV", df.to_csv(index=False).encode("utf-8"),
                   file_name="alkalinity_report.csv", mime="text/csv")

footer()
