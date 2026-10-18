"""Simple shared-password gate.

Set APP_PASSWORD as an environment variable (Railway: service -> Variables).
The value is never stored in the repo. Uses constant-time comparison and a
short lockout after repeated failures.
"""
import hmac
import os
import time

import streamlit as st

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


def expected_password():
    try:
        v = st.secrets.get("APP_PASSWORD")
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get("APP_PASSWORD")


def check_password(candidate: str, expected: str) -> bool:
    return hmac.compare_digest(candidate or "", expected or "")


def _locked():
    return time.time() < st.session_state.get("login_locked_until", 0)


def require_login():
    """Call at the top of every page. Stops execution until authenticated."""
    if st.session_state.get("authed"):
        with st.sidebar:
            st.caption("Signed in")
            if st.button("Sign out"):
                st.session_state["authed"] = False
                st.rerun()
        return

    expected = expected_password()
    if not expected:
        st.warning("APP_PASSWORD is not set — running without sign-in (dev mode). "
                   "Set it in Railway Variables before field use.")
        return

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.title("Field Dosing App")
        st.caption("Sign in to continue.")
        if _locked():
            st.error("Too many attempts — try again shortly.")
            st.stop()
        pw = st.text_input("Password", type="password")
        if st.button("Sign in", type="primary", use_container_width=True):
            if check_password(pw, expected):
                st.session_state["authed"] = True
                st.session_state["login_attempts"] = 0
                st.rerun()
            else:
                n = st.session_state.get("login_attempts", 0) + 1
                st.session_state["login_attempts"] = n
                if n >= MAX_ATTEMPTS:
                    st.session_state["login_locked_until"] = time.time() + LOCKOUT_SECONDS
                    st.session_state["login_attempts"] = 0
                st.error("Incorrect password.")
    st.stop()
