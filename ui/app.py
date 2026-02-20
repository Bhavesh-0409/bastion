import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000"

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Bastion Security Dashboard",
    layout="wide"
)

st.markdown("""
<style>
pre code {
    white-space: pre-wrap !important;
    word-break: break-word !important;
}
.stCodeBlock {
    overflow-x: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TOP NAV BAR --------------------
st.markdown("""
<div style="
    background-color:#111827;
    padding:14px 24px;
    border-bottom:1px solid #1f2937;
    display:flex;
    justify-content:space-between;
    align-items:center;
">
    <div style="font-size:18px;font-weight:600;color:#f9fafb;">
        Bastion Security
    </div>
    <div style="color:#9ca3af;font-size:14px;">
        Environment: <span style="color:#2563eb;font-weight:600;">Production</span>
        &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
        Org: Acme Corp
    </div>
</div>
""", unsafe_allow_html=True)

st.title("Bastion — LLM Security Enforcement Layer")

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.header("Configuration")

    model_name = st.selectbox(
        "Model",
        ["distilbert-security"]
    )

    st.divider()

    security_enabled = st.toggle(
        "Enable Bastion Security",
        value=True
    )

    if security_enabled:
        st.success("Protected mode active")
    else:
        st.warning("Unprotected mode")

# -------------------- HELPERS --------------------

def render_system_state(data):
    st.subheader("System State")

    col1, col2, col3 = st.columns(3)

    col1.metric("Instruction Depth", data["instruction_depth"])
    col2.metric("Violation Type", data["violation_type"])
    col3.metric("Integrity Score", data["integrity_score"])


def render_prompt_stream(violations):
    st.subheader("Prompt Stream")

    if not violations:
        st.code("No policy violations detected.")
    else:
        logs = []
        for v in violations:
            logs.append(f"{v.get('rule_name')} — severity: {v.get('severity')}")
        st.code("\n".join(logs))


def render_execution_timeline(decision):
    st.subheader("Execution Flow")

    steps = [
        "Scanning input",
        "Detecting policy violations",
        "Evaluating risk",
        "Execution decision"
    ]

    for step in steps:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(step)
        with col2:
            st.text("Completed")
        time.sleep(0.1)

    st.divider()

    if decision == "block":
        st.text("Execution: Denied (policy enforcement)")
    else:
        st.text("Execution: Allowed")


def render_risk_assessment(risk_score):
    st.subheader("Risk Assessment")

    percent = int(risk_score * 100)

    st.markdown(f"""
    <div style="
        background-color:#111827;
        padding:20px;
        border-radius:10px;
        border:1px solid #1f2937;
    ">
        <div style="font-size:14px;color:#9ca3af;">Risk Score</div>
        <div style="font-size:32px;font-weight:600;color:{'#ef4444' if percent>60 else '#16a34a'};">
            {percent}%
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_execution_output(data):
    st.subheader("Execution Output")

    if data["decision"] == "block":
        output = (
            "Execution Result: Denied\n"
            "Observed Model Behavior:\n"
            "- Malicious intent detected\n"
            "- Policy enforcement active\n"
            "- Execution blocked"
        )
    else:
        output = (
            "Execution Result: Allowed\n"
            "Observed Model Behavior:\n"
            "- No blocking conditions triggered\n"
            "- Execution proceeded"
        )

    st.code(output)


# -------------------- MAIN UI --------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Request Analysis",
    "Audit Trail",
    "Enforcement Differential",
    "Policy Engine"
])

# -------------------- TAB 1 --------------------
with tab1:
    st.header("Prompt Execution")

    user_prompt = st.text_area(
        "Prompt",
        height=120,
        placeholder="Enter a prompt to evaluate..."
    )

    if st.button("Run Analysis", type="primary"):

        if not user_prompt.strip():
            st.warning("Please enter a prompt before execution.")
        else:
            try:
                response = requests.post(
                    f"{API_URL}/analyze",
                    json={
                        "prompt": user_prompt,
                        "bastion_enabled": security_enabled,
                        "model": model_name
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    st.divider()
                    render_system_state(data)

                    st.divider()
                    render_prompt_stream(data["violations"])

                    st.divider()
                    render_execution_timeline(data["decision"])

                    st.divider()
                    render_risk_assessment(data["risk_score"])

                    st.divider()
                    render_execution_output(data)

                    st.subheader("Request Summary")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Policy Triggered:** {data['violation_type']}")
                        st.markdown(f"**Confidence Score:** {data['confidence']}")

                    with col2:
                        st.markdown(f"**Enforcement Action:** {data['decision'].upper()}")
                        st.markdown(f"**Timestamp:** {data['timestamp']}")

                else:
                    st.error(response.text)

            except Exception as e:
                st.error(f"Backend connection failed: {e}")


# -------------------- TAB 2 --------------------
with tab2:
    st.header("Audit Trail")

    try:
        response = requests.get(f"{API_URL}/logs/recent")

        if response.status_code == 200:
            logs = response.json()["logs"]

            if not logs:
                st.info("No audit logs yet.")
            else:
                formatted = []
                for log in logs:
                    formatted.append(
                        f"{log['timestamp']}  |  risk={log['risk_score']}  |  decision={log['decision']}"
                    )
                st.code("\n".join(formatted))
        else:
            st.error("Failed to fetch logs.")

    except:
        st.error("Backend not reachable.")


# -------------------- TAB 3 --------------------
with tab3:
    st.header("Enforcement Differential")
    st.caption("Observed model response under current enforcement configuration.")

    user_input = st.text_area(
        "Enter Prompt",
        height=120,
        placeholder="Type a prompt to evaluate..."
    )

    if st.button("Evaluate Prompt", type="primary"):

        if not user_input.strip():
            st.warning("Please enter a prompt.")
        else:
            response = requests.post(
                f"{API_URL}/analyze",
                json={
                    "prompt": user_input,
                    "bastion_enabled": security_enabled,
                    "model": model_name
                }
            )

            if response.status_code == 200:
                data = response.json()

                st.subheader("Model Response")

                if security_enabled:
                    st.success("Bastion Enforcement: Enabled")
                else:
                    st.error("Bastion Enforcement: Disabled")

                formatted_output = f"""
model: {model_name}
enforcement: {"enabled" if security_enabled else "disabled"}

decision: {data['decision']}
risk_score: {data['risk_score']}

response:
Execution {'blocked by Bastion' if data['decision']=='block' else 'allowed'}
"""
                st.code(formatted_output)


# -------------------- TAB 4 --------------------
with tab4:
    st.header("Policy Engine")
    st.caption("Policy configuration interface coming soon.")

st.divider()
st.caption("Bastion — Policy Enforcement & Prompt Security Layer")
