"""Shared UI helpers — one clean, professional look across all pages."""
import streamlit as st


def header(title: str, subtitle: str | None = None):
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    st.divider()


def footer():
    st.divider()
    st.caption("Field Dosing App · WBM · Verify all dosing against the current mud report before treating.")
