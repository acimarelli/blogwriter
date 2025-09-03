import streamlit as st
import json
import os
from blogwriter.utils.flow_plotter import plot_flow
from blogwriter.utils.logger import FlowLogger

st.set_page_config(page_title="Audit & Flow Tracker", layout="wide")
st.title("🔍 CrewAI Audit Dashboard")

log_files = sorted([f for f in os.listdir("logs") if f.endswith(".json")])
selected_log = st.selectbox("Seleziona Log Flow", log_files)

if selected_log:
    with open(os.path.join("logs", selected_log)) as f:
        log_data = json.load(f)

    st.markdown(f"### Flow: `{log_data['flow']}` - `{log_data['timestamp']}`")

    steps = log_data.get("steps", [])

    for i, step in enumerate(steps):
        with st.expander(f"Step {i+1}: {step['task']} [{step['agent']}] @ {step['time']}"):
            st.json({"Input": step['input'], "Output": step['output']})

    from blogwriter.utils.flow_plotter import plot_flow
    flow_img = plot_flow(os.path.join("logs", selected_log))
    st.image(flow_img, caption="Diagramma di esecuzione del flow")

    st.subheader("📈 Metriche del Flow")
    logger = FlowLogger(log_data['flow'])
    logger.entries = steps
    metrics = logger.summarize_metrics()
    st.json(metrics)
