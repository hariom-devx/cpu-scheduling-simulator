import streamlit as st
import pandas as pd
import time
from main import (
    fcfs,
    sjf_non_preemptive,
    sjf_preemptive,
    round_robin,
    priority_non_preemptive,
    draw_gantt_chart,
    get_metrics
)

st.set_page_config(page_title="CPU Scheduler", layout="wide")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 10px;
    height: 3em;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙️ Settings")

mode = st.sidebar.radio("Mode", ["Single", "Compare"])

algo_map = {
    "FCFS": fcfs,
    "SJF": sjf_non_preemptive,
    "SRTF": sjf_preemptive,
    "Round Robin": round_robin,
    "Priority": priority_non_preemptive
}

algo = st.sidebar.selectbox("Algorithm", list(algo_map.keys()))
n = st.sidebar.slider("Processes", 1, 10, 4)
quantum = st.sidebar.number_input("Quantum (RR)", 1, 10, 2)

# =========================
# HEADER
# =========================
st.title(" CPU Scheduling Simulator")
st.markdown("### SECOND YEAR PROJECT — CPU SCHEDULING SIMULATOR")

# =========================
# INPUT
# =========================
st.subheader("📥 Process Input")

data = []
for i in range(n):
    c1, c2, c3, c4 = st.columns(4)

    pid = f"P{i+1}"
    at = c2.number_input("AT", key=f"at{i}")
    bt = c3.number_input("BT", key=f"bt{i}", min_value=1)
    pr = c4.number_input("PR", key=f"pr{i}", value=1)

    c1.write(pid)

    data.append({
        "pid": pid,
        "at": int(at),
        "bt": int(bt),
        "priority": int(pr)
    })

# =========================
# RUN
# =========================
if st.button("▶ Run Simulation"):

    with st.spinner("Processing..."):
        time.sleep(1)

    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.005)
        progress.progress(i + 1)

    st.markdown("---")

    def run(name, func):
        if name == "Round Robin":
            res, tl = func(data, quantum)
        else:
            res, tl = func(data)

        df = pd.DataFrame(res)
        avg_tat, avg_wt = get_metrics(res)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"📊 {name}")
            st.dataframe(df, use_container_width=True)

        with col2:
            st.metric("Avg WT", f"{avg_wt:.2f}")
            st.metric("Avg TAT", f"{avg_tat:.2f}")

        st.info("💡 Lower Waiting Time = Better Efficiency")

        st.subheader("📈 Gantt Chart")

        fig = draw_gantt_chart(tl, name)   # ✅ FIXED
        st.pyplot(fig)                     # ✅ FIXED

        return avg_wt, avg_tat

    # =========================
    # SINGLE MODE
    # =========================
    if mode == "Single":
        run(algo, algo_map[algo])

    # =========================
    # COMPARE MODE
    # =========================
    else:
        summary = []

        for name, func in algo_map.items():
            st.markdown("##")
            wt, tat = run(name, func)
            summary.append([name, wt, tat])

        st.markdown("---")
        st.subheader("🏆 Comparison")

        df = pd.DataFrame(summary, columns=["Algorithm", "WT", "TAT"])
        st.dataframe(df)

        best = df.loc[df["WT"].idxmin()]
        st.success(f"Best: {best['Algorithm']} (WT={best['WT']:.2f})")
