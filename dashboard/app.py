import streamlit as st
import json
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="AI Trading Agent", page_icon="🤖", layout="wide")

st.title("🤖 Kraken AI Trading Agent Dashboard")

def load_bot_state():
    state_file = "logs/bot_state.json"
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return None

def load_trade_history():
    trade_file = "logs/trade_history.json"
    trades = []
    if os.path.exists(trade_file):
        with open(trade_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        trades.append(json.loads(line))
                    except:
                        pass
    return trades

state = load_bot_state()
trades = load_trade_history()

st.header("📊 Portfolio Overview")

if state:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        balance = state.get("balance", 0)
        st.metric("💰 Balance", f"${balance:,.2f}")
    with col2:
        total_pnl = state.get("total_pnl", 0)
        st.metric("📈 Total PnL", f"${total_pnl:,.2f}", delta=f"${total_pnl:,.2f}")
    with col3:
        open_pos = len(state.get("open_positions", []))
        st.metric("📂 Open Positions", open_pos)
    with col4:
        total_trades = state.get("total_trades", 0)
        st.metric("🔄 Total Trades", total_trades)
    st.header("📂 Open Positions")
    open_positions = state.get("open_positions", [])
    if open_positions:
        df_positions = pd.DataFrame(open_positions)
        st.dataframe(df_positions, use_container_width=True)
    else:
        st.info("No open positions")
else:
    st.warning("Bot has not started yet. No state file found.")
    st.info("Run the bot first: python -m core.agent")

st.header("📜 Trade History")

if trades:
    df_trades = pd.DataFrame(trades)
    st.dataframe(df_trades, use_container_width=True)
    st.subheader("💰 PnL Over Time")
    if "usd_value" in df_trades.columns:
        pnl_data = []
        running_pnl = 0
        for trade in trades:
            if trade.get("action") == "BUY":
                running_pnl -= trade.get("usd_value", 0)
            elif trade.get("action") in ["SELL", "CLOSE"]:
                running_pnl += trade.get("usd_value", 0)
            pnl_data.append({
                "timestamp": trade.get("timestamp", ""),
                "running_pnl": running_pnl
            })
        if pnl_data:
            df_pnl = pd.DataFrame(pnl_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_pnl["timestamp"],
                y=df_pnl["running_pnl"],
                mode="lines+markers",
                name="PnL",
                line=dict(color="green" if running_pnl >= 0 else "red")
            ))
            fig.update_layout(
                title="Cumulative PnL",
                xaxis_title="Time",
                yaxis_title="PnL (USD)",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
    st.subheader("📊 Trade Actions")
    if "action" in df_trades.columns:
        action_counts = df_trades["action"].value_counts()
        fig2 = go.Figure(data=[go.Pie(
            labels=action_counts.index,
            values=action_counts.values,
            marker_colors=["green", "red", "gray"]
        )])
        fig2.update_layout(title="Trade Actions Distribution")
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No trades yet. Start the bot to see trade history.")

st.header("⚙️ Bot Status")

if state:
    col1, col2 = st.columns(2)
    with col1:
        is_running = state.get("is_running", False)
        if is_running:
            st.success("🟢 Bot is RUNNING")
        else:
            st.error("🔴 Bot is STOPPED")
    with col2:
        last_check = state.get("last_check_time", "Never")
        st.info(f"Last check: {last_check}")

st.markdown("---")
st.markdown("*AI Trading Agent for LabLab.ai Hackathon | Kraken Challenge*")

if st.button("🔄 Refresh Dashboard"):
    st.rerun()