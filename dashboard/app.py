import streamlit as st
import subprocess
import json
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Kraken AI Trading Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
    .stApp { background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 50%, #0a0f1a 100%); font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }
    .hero-title { font-family: 'Inter', sans-serif; font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #00d4ff 0%, #7b2ff7 50%, #ff2d55 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 0.2rem; letter-spacing: -0.02em; }
    .hero-subtitle { font-family: 'Inter', sans-serif; font-size: 1rem; color: #8b949e; text-align: center; margin-bottom: 2rem; font-weight: 400; }
    .glass-card { background: rgba(22, 27, 34, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem; transition: all 0.3s ease; }
    .glass-card:hover { border-color: rgba(0, 212, 255, 0.3); box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1); }
    .metric-card { background: rgba(22, 27, 34, 0.9); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 1.5rem; text-align: center; position: relative; overflow: hidden; }
    .metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 16px 16px 0 0; }
    .metric-card.balance::before { background: linear-gradient(90deg, #00d4ff, #0088ff); }
    .metric-card.pnl-positive::before { background: linear-gradient(90deg, #00ff88, #00cc66); }
    .metric-card.pnl-negative::before { background: linear-gradient(90deg, #ff4444, #ff2222); }
    .metric-card.positions::before { background: linear-gradient(90deg, #7b2ff7, #9945ff); }
    .metric-card.trades::before { background: linear-gradient(90deg, #ff9500, #ffb800); }
    .metric-label { font-size: 0.8rem; font-weight: 500; color: #8b949e; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem; }
    .metric-value { font-family: 'JetBrains Mono', monospace; font-size: 2rem; font-weight: 700; color: #f0f6fc; line-height: 1.2; }
    .metric-value.green { color: #00ff88; } .metric-value.red { color: #ff4444; } .metric-value.blue { color: #00d4ff; } .metric-value.purple { color: #9945ff; } .metric-value.orange { color: #ffb800; }
    .metric-delta { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 500; margin-top: 0.3rem; }
    .metric-delta.positive { color: #00ff88; } .metric-delta.negative { color: #ff4444; }
    .section-header { font-family: 'Inter', sans-serif; font-size: 1.3rem; font-weight: 700; color: #f0f6fc; margin-top: 2rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 10px; }
    .section-line { flex: 1; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0.1), transparent); }
    .trade-card { background: rgba(22, 27, 34, 0.6); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; }
    .trade-buy { border-left: 3px solid #00ff88; } .trade-sell { border-left: 3px solid #ff4444; } .trade-close { border-left: 3px solid #ffb800; }
    .custom-footer { text-align: center; padding: 2rem 0 1rem 0; color: #484f58; font-size: 0.8rem; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 3rem; }
    .refresh-badge { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #484f58; text-align: center; margin-top: 0.5rem; }
    ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; } ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>
""", unsafe_allow_html=True)


def run_cli_command(command):
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return {}


def load_portfolio_status():
    return run_cli_command("kraken paper status -o json")


def load_trade_history():
    return run_cli_command("kraken paper history -o json")


portfolio = load_portfolio_status()
history = load_trade_history()

st.markdown('<div class="hero-title">⚡ Kraken AI Trading Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Autonomous Paper Trading • Powered by PRISM Signals & Technical Analysis</div>', unsafe_allow_html=True)


st.markdown('<div class="section-header">Portfolio Overview <div class="section-line"></div></div>', unsafe_allow_html=True)

balance = portfolio.get("balance", portfolio.get("equity", 10000))
unrealized_pnl = portfolio.get("unrealized_pnl", portfolio.get("pnl", 0))
open_positions = portfolio.get("open_positions", portfolio.get("positions", []))

total_trades = len(history) if isinstance(history, list) else 0
starting_balance = 10000
pnl_pct = ((balance - starting_balance) / starting_balance) * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card balance">
        <div class="metric-label">💰 Total Equity</div>
        <div class="metric-value blue">${balance:,.2f}</div>
        <div class="metric-delta {'positive' if pnl_pct >= 0 else 'negative'}">
            {'▲' if pnl_pct >= 0 else '▼'} {pnl_pct:+.2f}% from start
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    pnl_class = "pnl-positive" if unrealized_pnl >= 0 else "pnl-negative"
    pnl_color = "green" if unrealized_pnl >= 0 else "red"
    st.markdown(f"""
    <div class="metric-card {pnl_class}">
        <div class="metric-label">📈 Unrealized PnL</div>
        <div class="metric-value {pnl_color}">${unrealized_pnl:+,.2f}</div>
        <div class="metric-delta {'positive' if unrealized_pnl >= 0 else 'negative'}">
            {'▲ Profit' if unrealized_pnl >= 0 else '▼ Loss'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card positions">
        <div class="metric-label">📂 Open Positions</div>
        <div class="metric-value purple">{len(open_positions)}</div>
        <div class="metric-delta" style="color: #8b949e;">active</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card trades">
        <div class="metric-label">🔄 Total Trades</div>
        <div class="metric-value orange">{total_trades}</div>
        <div class="metric-delta" style="color: #8b949e;">executed</div>
    </div>
    """, unsafe_allow_html=True)


if history and isinstance(history, list):
    st.markdown('<div class="section-header">📊 Performance <div class="section-line"></div></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["💰 PnL Chart", "📊 Trade Analysis"])
    
    with tab1:
        pnl_data = []
        running_cash = 10000.0
        held_crypto = 0.0
        for trade in history:
            amount = trade.get("amount", trade.get("volume", 0))
            price = trade.get("price", 0)
            action = trade.get("action", trade.get("type", "")).upper()
            usd_value = amount * price
            
            if action == "BUY":
                running_cash -= usd_value
                held_crypto += amount
            elif action in ["SELL", "CLOSE"]:
                running_cash += usd_value
                held_crypto -= amount
            
            current_value = running_cash + (held_crypto * price) if price > 0 else running_cash
            total_pnl = current_value - 10000
            
            pnl_data.append({
                "timestamp": trade.get("timestamp", trade.get("time", "")),
                "pnl": total_pnl
            })
        
        if pnl_data:
            df_pnl = pd.DataFrame(pnl_data)
            final_pnl = pnl_data[-1]["pnl"]
            is_positive = final_pnl >= 0
            line_color = "#00ff88" if is_positive else "#ff4444"
            fill_color = "rgba(0, 255, 136, 0.1)" if is_positive else "rgba(255, 68, 68, 0.1)"
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_pnl["timestamp"],
                y=df_pnl["pnl"],
                mode="lines",
                name="PnL",
                line=dict(color=line_color, width=2.5),
                fill="tozeroy",
                fillcolor=fill_color,
            ))
            fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)", line_width=1)
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.03)", title="", showgrid=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.03)", title="PnL (USD)", tickprefix="$", zeroline=False),
                margin=dict(l=0, r=0, t=20, b=0),
                height=400,
                showlegend=False,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        df_trades = pd.DataFrame(history)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            if "action" in df_trades.columns or "type" in df_trades.columns:
                col = "action" if "action" in df_trades.columns else "type"
                action_counts = df_trades[col].str.upper().value_counts()
                colors = ["#00ff88" if a == "BUY" else "#ff4444" for a in action_counts.index]
                
                fig2 = go.Figure(data=[go.Pie(
                    labels=action_counts.index,
                    values=action_counts.values,
                    hole=0.65,
                    marker_colors=colors,
                    textinfo="label+percent",
                    textfont=dict(size=13, family="Inter"),
                )])
                fig2.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#8b949e"),
                    margin=dict(l=0, r=0, t=30, b=0),
                    height=300,
                    showlegend=False,
                    annotations=[dict(text="Actions", x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#f0f6fc")]
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        with col_chart2:
            if "amount" in df_trades.columns:
                fig3 = go.Figure()
                colors_bar = ["#00ff88" if t.get("action", t.get("type", "")).upper() == "BUY" else "#ff4444" for t in history]
                fig3.add_trace(go.Bar(
                    x=list(range(1, len(history) + 1)),
                    y=[t.get("price", 0) * t.get("amount", t.get("volume", 0)) for t in history],
                    marker_color=colors_bar,
                    marker_line_width=0,
                    opacity=0.8
                ))
                fig3.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#8b949e"),
                    xaxis=dict(title="Trade #", gridcolor="rgba(255,255,255,0.03)"),
                    yaxis=dict(title="USD Value", tickprefix="$", gridcolor="rgba(255,255,255,0.03)"),
                    margin=dict(l=0, r=0, t=30, b=0),
                    height=300,
                    showlegend=False
                )
                st.plotly_chart(fig3, use_container_width=True)


st.markdown('<div class="section-header">📜 Trade History <div class="section-line"></div></div>', unsafe_allow_html=True)

if history and isinstance(history, list):
    for trade in reversed(history[-20:]):
        action = trade.get("action", trade.get("type", "N/A")).upper()
        amount = trade.get("amount", trade.get("volume", 0))
        price = trade.get("price", 0)
        timestamp = trade.get("timestamp", trade.get("time", ""))
        
        if action == "BUY":
            action_color = "#00ff88"
            action_class = "trade-buy"
            icon = "🟢"
        elif action in ["SELL", "CLOSE"]:
            action_color = "#ff4444"
            action_class = "trade-sell"
            icon = "🔴"
        else:
            action_color = "#ffb800"
            action_class = "trade-close"
            icon = "🟡"
        
        st.markdown(f"""
        <div class="trade-card {action_class}">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 1.2rem;">{icon}</span>
                <div>
                    <div>
                        <span style="color: {action_color}; font-weight: 700;">{action}</span>
                        <span style="color: #f0f6fc; font-weight: 600; margin-left: 6px;">SOLUSD</span>
                    </div>
                    <div style="color: #484f58; font-size: 0.75rem; margin-top: 2px;">{timestamp}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="color: #f0f6fc; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem;">${price:,.2f}</div>
                <div style="color: #8b949e; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">{amount:.6f} • ${price * amount:,.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 2rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">⏳</div>
        <div style="color: #8b949e;">No trades yet — Agent is analyzing the market</div>
    </div>
    """, unsafe_allow_html=True)


col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    st.markdown("""
    <div class="glass-card">
        <div style="color: #00d4ff; font-weight: 600; margin-bottom: 8px;">📊 Signal Sources</div>
        <div style="color: #8b949e; font-size: 0.85rem; line-height: 1.8;">
            • PRISM AI Signals — <span style="color: #00d4ff;">40%</span><br>
            • Technical Indicators — <span style="color: #9945ff;">30%</span><br>
            • Risk Metrics — <span style="color: #ffb800;">20%</span><br>
            • Market Momentum — <span style="color: #ff2d55;">10%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_s2:
    st.markdown("""
    <div class="glass-card">
        <div style="color: #00ff88; font-weight: 600; margin-bottom: 8px;">🛡️ Risk Controls</div>
        <div style="color: #8b949e; font-size: 0.85rem; line-height: 1.8;">
            • Max trade: <span style="color: #f0f6fc;">$100</span><br>
            • Stop loss: <span style="color: #ff4444;">5%</span><br>
            • Take profit: <span style="color: #00ff88;">10%</span><br>
            • Max positions: <span style="color: #f0f6fc;">3</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_s3:
    st.markdown("""
    <div class="glass-card">
        <div style="color: #9945ff; font-weight: 600; margin-bottom: 8px;">⚡ Decision Thresholds</div>
        <div style="color: #8b949e; font-size: 0.85rem; line-height: 1.8;">
            • Buy signal: <span style="color: #00ff88;">score ≥ +60</span><br>
            • Sell signal: <span style="color: #ff4444;">score ≤ -60</span><br>
            • Hold zone: <span style="color: #ffb800;">-59 to +59</span><br>
            • Range: <span style="color: #f0f6fc;">-100 to +100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("""
<div class="custom-footer">
    <div style="margin-bottom: 0.5rem;">
        <span style="color: #00d4ff;">⚡</span> Kraken AI Trading Agent
        <span style="color: #484f58; margin: 0 8px;">•</span>
        LabLab.ai Hackathon 2026
        <span style="color: #484f58; margin: 0 8px;">•</span>
        Kraken Challenge
    </div>
    <div style="font-size: 0.7rem;">
        Built with Python • PRISM API • Kraken CLI • Streamlit
    </div>
</div>
""", unsafe_allow_html=True)

col_r1, col_r2, col_r3 = st.columns([1, 1, 1])
with col_r2:
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()