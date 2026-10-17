"""Alkalinity contamination calculator (WBM only)."""
import streamlit as st
import pandas as pd

from utils.chemistry import speciate, advisories, treatments, TARGETS

st.set_page_config(page_title="Alkalinity Contamination Calculator", layout="centered")
st.title("🛢️ Alkalinity Contamination Calculator (WBM Only)")
st.caption("Field-tuned for hardness control and CO₂/H₂S/bicarbonate contamination "
           "response — not API textbook speciation.")

# === INPUT ===
st.header("🧪 Input Mud Check Values")

pm = st.number_input("Phenolphthalein Alkalinity (Pm)", min_value=0.0, format="%.2f",
                     value=float(st.session_state.get("pm", 0.0)))
pf = st.number_input("Filtrate Alkalinity (Pf)", min_value=0.0, format="%.2f",
                     value=float(st.session_state.get("pf", 0.0)))
mf = st.number_input("M Alkalinity (Mf)", min_value=0.0, format="%.2f",
                     value=float(st.session_state.get("mf", 0.0)))
calcium = st.number_input("Calcium (mg/L)", min_value=0.0, format="%.1f",
                          value=float(st.session_state.get("calcium", 0.0)))
hardness = st.number_input("Hardness (mg/L)", min_value=0.0, format="%.1f",
                           value=float(st.session_state.get("hardness", 0.0)))

# keep the shared mud check in sync
st.session_state["pm"], st.session_state["pf"] = pm, pf
st.session_state["mf"], st.session_state["calcium"], st.session_state["hardness"] = mf, calcium, hardness

if pm > mf:
    st.warning("⚠️ Pm exceeds Mf — check the titration. Treated as all-hydroxide below.")

# === SPECIATION ===
hydroxide, carbonate, bicarbonate = speciate(pm, mf)

st.markdown("### 🧾 Alkalinity Species Breakdown")
col1, col2, col3 = st.columns(3)
col1.metric("Hydroxide (OH⁻)", f"{hydroxide:.2f} mg/L")
col2.metric("Carbonate (CO₃²⁻)", f"{carbonate:.2f} mg/L")
col3.metric("Bicarbonate (HCO₃⁻)", f"{bicarbonate:.2f} mg/L")

# === TARGETS ===
st.markdown("#### 🎯 Recommended Target Ranges (WBM)")
st.markdown(f"""
- **OH⁻ (Hydroxide):** < {TARGETS['hydroxide']:.0f} mg/L
- **CO₃²⁻ (Carbonate):** < {TARGETS['carbonate']:.0f} mg/L
- **HCO₃⁻ (Bicarbonate):** < {TARGETS['bicarbonate']:.0f} mg/L
- **Calcium:** < {TARGETS['calcium']:.0f} mg/L
- **Hardness:** < {TARGETS['hardness']:.0f} mg/L (ideal operating range)
""")

# === ADVISORIES ===
st.markdown("### ⚠️ Contamination Advisory")
found = False
for level, msg in advisories(hydroxide, carbonate, bicarbonate, calcium, hardness):
    found = True
    {"warning": st.warning, "info": st.info, "error": st.error}[level](msg)
if not found:
    st.success("✅ No contamination flags on this mud check.")

# === TREATMENTS ===
st.markdown("### 🧪 Recommended Treatment Options (WBM Only)")
for level, msg in treatments(hydroxide, carbonate, bicarbonate, calcium, hardness):
    {"warning": st.warning, "info": st.info, "error": st.error, "success": st.success}[level](msg)

st.markdown("### ⚖️ Treatment Ratio Advisory")
st.markdown("""
All caustic soda additions should be paired with **3 parts Lime for every 1 part Caustic** in WBM systems.

This prevents runaway alkalinity, emulsion instability, and downstream bicarbonate contamination.
""")

# === EXPORT ===
st.markdown("### 📤 Export Results")
df = pd.DataFrame({
    "Parameter": ["Pm", "Pf", "Mf", "Calcium", "Hardness", "Hydroxide", "Carbonate", "Bicarbonate"],
    "Value": [pm, pf, mf, calcium, hardness, hydroxide, carbonate, bicarbonate],
})
st.download_button("📥 Download Results as CSV", df.to_csv(index=False).encode("utf-8"),
                   file_name="alkalinity_report.csv", mime="text/csv")
