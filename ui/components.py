import streamlit as st

def render_threat_badge(threat_level: str):
    """Render threat level badge"""
    colors = {
        "safe": "🟢",
        "warning": "🟡",
        "blocked": "🔴"
    }
    return colors.get(threat_level, "⚪")

def render_violation_table(violations: list):
    """Render violations in table format"""
    if not violations:
        st.info("No violations detected")
        return
    
    # TODO: Format violations into DataFrame and display
    st.table(violations)

def render_logs_table(logs: list):
    """Render logs in table format"""
    if not logs:
        st.info("No logs available")
        return
    
    # TODO: Format logs into DataFrame and display
    st.table(logs)
