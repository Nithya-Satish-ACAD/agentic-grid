import streamlit as st
import httpx
import pandas as pd
import time

# Page configuration
st.set_page_config(
    page_title="P2P Energy Grid Monitor",
    page_icon="⚡",
    layout="wide",
)

# --- API Clients ---
SOLAR_AGENT_URL = "http://localhost:8001"
UTILITY_AGENT_URL = "http://localhost:8000"

# --- Helper Functions ---
def get_agent_status(agent_url: str):
    """Fetches the status from an agent's /status endpoint."""
    try:
        response = httpx.get(f"{agent_url}/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        return {"error": str(e)}

def post_to_agent(agent_url: str, endpoint: str):
    """Makes a POST request to a specific agent endpoint."""
    try:
        response = httpx.post(f"{agent_url}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        st.error(f"Failed to post to {endpoint}: {e}")
        return None

def tail_log(log_file: str, lines: int = 20):
    """Tails the last N lines of a log file."""
    try:
        with open(log_file, 'r') as f:
            return f.readlines()[-lines:]
    except FileNotFoundError:
        return [f"Log file not found: {log_file}"]
    except Exception as e:
        return [f"Error reading log file: {e}"]

# --- Main App ---
st.title("P2P Energy Grid Monitor ⚡")

st.markdown("---")

# --- Control Panel ---
with st.container():
    st.header("Agent Control Panel")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Trigger Fault in Solar Agent"):
            post_to_agent(SOLAR_AGENT_URL, "/debug/set_fault")
            st.toast("Fault signal sent to Solar Agent!")
    with col2:
        if st.button("Trigger Beckn Discovery"):
            post_to_agent(SOLAR_AGENT_URL, "/beckn/trigger-search")
            st.toast("Beckn discovery signal sent to Solar Agent!")

st.markdown("---")

# --- Agent Status ---
with st.container():
    st.header("Live Agent Status")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Solar Agent")
        solar_status_placeholder = st.empty()
    with col2:
        st.subheader("Utility Agent")
        utility_status_placeholder = st.empty()

st.markdown("---")

# --- Live Logs ---
with st.container():
    st.header("Live Agent Logs")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Solar Agent Log")
        solar_log_placeholder = st.empty()
    with col2:
        st.subheader("Utility Agent Log")
        utility_log_placeholder = st.empty()


# --- Main auto-updating loop ---
while True:
    solar_status = get_agent_status(SOLAR_AGENT_URL)
    utility_status = get_agent_status(UTILITY_AGENT_URL)

    with solar_status_placeholder.container():
        st.json(solar_status)

    with utility_status_placeholder.container():
        st.json(utility_status)
        
    solar_log_lines = tail_log("../solar_agent.log")
    utility_log_lines = tail_log("../utility_agent.log")

    with solar_log_placeholder.container():
        st.code("".join(solar_log_lines), language="log")

    with utility_log_placeholder.container():
        st.code("".join(utility_log_lines), language="log")

    time.sleep(2) 