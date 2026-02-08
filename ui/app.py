import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Bastion Security Dashboard", layout="wide")

API_BASE_URL = "http://localhost:8000"

st.title("🛡️ Bastion - LLM Security Layer")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    model_name = st.selectbox("Select LLM Model", ["gpt-2", "llama-7b", "mistral"])
    api_endpoint = st.text_input("API Endpoint", API_BASE_URL)
    
    st.divider()
    
    # Security Toggle
    security_enabled = st.toggle(
        "Enable Bastion Security",
        value=True,
        help="Toggle to enable/disable security layer"
    )
    
    if security_enabled:
        st.success("🔒 Protected Mode Active")
    else:
        st.warning("⚠️ Direct LLM Mode (No Security)")

# Main Tabs
tab1, tab2, tab3 = st.tabs(["Prompt Check", "Logs", "Rules"])

# Tab 1: Prompt Security Check
with tab1:
    st.header("Test Prompt")
    
    # Display current mode
    mode_label = "🔒 LLM via Bastion (Protected)" if security_enabled else "⚡ Direct LLM (No Security)"
    st.info(f"**Current Mode:** {mode_label}")
    
    # Single prompt input
    user_prompt = st.text_area("Enter prompt:", height=150, key="user_prompt")
    
    if st.button("Send Prompt", type="primary"):
        if not user_prompt.strip():
            st.error("Please enter a prompt")
        else:
            try:
                if security_enabled:
                    # Route through Bastion security layer
                    st.info("🔄 Checking security...")
                    response = requests.post(
                        f"{api_endpoint}/prompt/check",
                        json={"prompt": user_prompt, "model": model_name},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display security analysis
                        st.subheader("Security Analysis")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if result["safe"]:
                                st.success("✅ Safe")
                            else:
                                st.error("🚫 Blocked")
                        with col2:
                            st.metric("Threat Level", result["threat_level"].upper())
                        with col3:
                            st.metric("Details", len(result.get("details", {})))
                        
                        # Expandable details
                        with st.expander("View Details"):
                            st.json(result.get("details", {}))
                    else:
                        st.error(f"API Error: {response.status_code}")
                
                else:
                    # Direct LLM call (no security)
                    st.info("🔄 Sending to LLM directly...")
                    response = requests.post(
                        f"{api_endpoint}/chat_raw",
                        json={"prompt": user_prompt, "model": model_name},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.subheader("LLM Response")
                        st.write(result.get("response", "No response"))
                    else:
                        st.error(f"API Error: {response.status_code}")
            
            except requests.exceptions.Timeout:
                st.error("Request timeout. Is the backend running?")
            except requests.exceptions.ConnectionError:
                st.error(f"Cannot connect to {api_endpoint}. Is the backend running?")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 2: Logs
with tab2:
    st.header("Security Logs")
    if st.button("📋 Fetch Logs"):
        try:
            response = requests.get(f"{api_endpoint}/logs?limit=50")
            if response.status_code == 200:
                logs_data = response.json()
                st.info(f"Total logs: {logs_data['total']}")
                # TODO: Display logs in table format
        except Exception as e:
            st.error(f"Error fetching logs: {str(e)}")

# Tab 3: Rules Management
with tab3:
    st.header("Security Rules")
    st.info("Rule management coming soon...")
    # TODO: List, add, edit, delete rules

# Footer
st.divider()
st.caption("Bastion - Cybersecurity Hackathon Project")
