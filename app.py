"""
MarketBrain Command Centre
Multi-agent trading dashboard for MarketBrainPro, MAX-1 and MAX-2.
"""

import os
import math
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
import warnings
warnings.filterwarnings("ignore")

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketBrain Command Centre",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark gradient background */
.stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0d1526 50%, #0a1020 100%); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1526 0%, #111827 100%);
    border-right: 1px solid rgba(59,130,246,0.2);
}

/* Metric cards */
[data-testid="metric-container"] {
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 12px;
    padding: 16px 20px;
    backdrop-filter: blur(10px);
}
[data-testid="metric-container"] > div { color: #e2e8f0 !important; }
[data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.8rem !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 10px;
    overflow: hidden;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,23,42,0.6);
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(59,130,246,0.15);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94a3b8;
    font-weight: 500;
    font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.25) !important;
    color: #60a5fa !important;
}

/* Badges */
.badge-pro    { background: linear-gradient(135deg,#7c3aed,#6d28d9); color:#fff; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-max1   { background: linear-gradient(135deg,#0ea5e9,#0284c7); color:#fff; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-max2   { background: linear-gradient(135deg,#10b981,#059669); color:#fff; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
.badge-long   { background: rgba(16,185,129,0.2); color:#10b981; border:1px solid #10b981; padding:2px 9px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.badge-short  { background: rgba(239,68,68,0.2); color:#ef4444; border:1px solid #ef4444; padding:2px 9px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.badge-accept { background: rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.4); padding:2px 9px; border-radius:20px; font-size:0.78rem; font-weight:600; }
.badge-reject { background: rgba(239,68,68,0.10); color:#f87171; border:1px solid rgba(239,68,68,0.3); padding:2px 9px; border-radius:20px; font-size:0.78rem; font-weight:600; }

/* Section headers */
.section-header {
    font-size: 1rem;
    font-weight: 600;
    color: #60a5fa;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 12px 0 8px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(59,130,246,0.2);
}

/* Signal card */
.signal-card {
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
    backdrop-filter: blur(8px);
}

/* Score bar */
.score-bar-wrap { background: rgba(255,255,255,0.07); border-radius: 6px; height: 8px; width: 100%; margin-top: 4px; overflow: hidden; }
.score-bar      { height: 8px; border-radius: 6px; background: linear-gradient(90deg, #ec4899, #8b5cf6, #3b82f6); }

h1 { color: #f1f5f9 !important; }
h2, h3 { color: #cbd5e1 !important; }
p, li, label { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

# ─── DB Connections ─────────────────────────────────────────────────────────────
PG_USER = os.getenv("POSTGRES_USER", "pb")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")

AGENTS = {
    "MarketBrainPro":   {"db": "market_brain",      "badge": "pro",  "label": "MarketBrainPro",    "color": "#7c3aed", "threshold": 0.60},
    "MarketBrainMAX-1": {"db": "market_brain_max",  "badge": "max1", "label": "MAX-1",             "color": "#0ea5e9", "threshold": 0.60},
    "MarketBrainMAX-2": {"db": "market_brain_max2", "badge": "max2", "label": "MAX-2",             "color": "#10b981", "threshold": 0.60},
}

@st.cache_resource
def get_engine(db_name: str):
    url = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{db_name}"
    return create_engine(url, pool_pre_ping=True)

def safe_query(agent_key: str, sql: str, params: dict = None) -> pd.DataFrame:
    try:
        engine = get_engine(AGENTS[agent_key]["db"])
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except Exception as e:
        return pd.DataFrame()

# ─── Data Loaders ───────────────────────────────────────────────────────────────

def load_all_signals(agent_keys: list, days_back: int, tickers: list) -> pd.DataFrame:
    frames = []
    for ak in agent_keys:
        df = safe_query(ak, """
            SELECT
                id, timestamp, symbol, direction, score, ml_prob,
                sentiment, momentum, volume_score,
                COALESCE(news_score, NULL) AS news_score,
                regime, entry_price, stop_loss, take_profit,
                reasoning,
                COALESCE(outcome_state, 'OPEN') AS outcome_state,
                realized_pnl
            FROM trade_signals
            WHERE timestamp >= NOW() - INTERVAL ':days days'
            ORDER BY timestamp DESC
        """, {"days": days_back})
        if not df.empty:
            df["agent"] = ak
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    if tickers:
        combined = combined[combined["symbol"].isin(tickers)]
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
    return combined.sort_values("timestamp", ascending=False)


def load_system_logs(agent_keys: list, days_back: int, level_filter: str) -> pd.DataFrame:
    frames = []
    for ak in agent_keys:
        df = safe_query(ak, """
            SELECT timestamp, level, logger_name, message
            FROM system_logs
            WHERE timestamp >= NOW() - INTERVAL ':days days'
              AND (:level = 'ALL' OR level = :level)
            ORDER BY timestamp DESC
            LIMIT 500
        """, {"days": days_back, "level": level_filter})
        if not df.empty:
            df["agent"] = ak
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    combined["timestamp"] = pd.to_datetime(combined["timestamp"], utc=True)
    return combined.sort_values("timestamp", ascending=False)


def load_daily_universe(days_back: int, tickers: list) -> pd.DataFrame:
    df = safe_query("MarketBrainMAX-2", """
        SELECT date, symbol, mention_count, top_event_type
        FROM daily_universe
        WHERE date >= (CURRENT_DATE - :days)::text
        ORDER BY date DESC, mention_count DESC
    """, {"days": days_back})
    if not df.empty and tickers:
        df = df[df["symbol"].isin(tickers)]
    return df


def load_model_weights(agent_key: str) -> pd.DataFrame:
    if agent_key == "MarketBrainPro":
        return pd.DataFrame()
    return safe_query(agent_key, """
        SELECT weight_name, value, win_rate, sample_size, updated_at
        FROM model_weights ORDER BY value DESC
    """)

# ─── Helper: Gauge Chart ─────────────────────────────────────────────────────
def make_gauge(value: float, title: str, color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(value * 100, 1),
        number={"suffix": "%", "font": {"color": "#f1f5f9", "size": 28}},
        title={"text": title, "font": {"color": "#94a3b8", "size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#334155", "tickfont": {"color": "#64748b"}},
            "bar": {"color": color},
            "bgcolor": "rgba(15,23,42,0.5)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 40], "color": "rgba(239,68,68,0.12)"},
                {"range": [40, 60], "color": "rgba(234,179,8,0.12)"},
                {"range": [60, 100], "color": "rgba(16,185,129,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#f59e0b", "width": 2},
                "thickness": 0.75,
                "value": 60
            }
        }
    ))
    fig.update_layout(
        height=180, margin=dict(t=30, b=0, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter")
    )
    return fig

# ─── Header ─────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.markdown("# 🧠 MarketBrain Command Centre")
    st.markdown("<p style='color:#64748b;margin-top:-10px;font-size:0.9rem;'>Real-time signal intelligence across all agents</p>", unsafe_allow_html=True)

st.markdown("---")

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔎 Filters")

    selected_agents = st.multiselect(
        "Agent",
        options=list(AGENTS.keys()),
        default=list(AGENTS.keys()),
        format_func=lambda x: AGENTS[x]["label"]
    )

    days_back = st.select_slider(
        "Time Window",
        options=[1, 3, 7, 14, 30, 60, 90],
        value=7,
        format_func=lambda x: f"Last {x}d"
    )

    # Ticker filter — dynamically populated
    if selected_agents:
        all_tickers_frames = []
        for ak in selected_agents:
            df_t = safe_query(ak, "SELECT DISTINCT symbol FROM trade_signals ORDER BY symbol")
            if not df_t.empty:
                all_tickers_frames.append(df_t)
        all_tickers = sorted(set(
            pd.concat(all_tickers_frames)["symbol"].tolist()
        )) if all_tickers_frames else []
    else:
        all_tickers = []

    selected_tickers = st.multiselect(
        "Stock Ticker",
        options=all_tickers,
        default=[],
        placeholder="All tickers"
    )

    st.markdown("---")
    st.markdown("### ⚙️ Pipeline Thresholds")
    threshold = st.slider("Score Threshold", 0.0, 1.0, 0.60, 0.01)

    st.markdown("---")
    st.markdown("### 🌐 1-Click Deploy")
    st.markdown("""
    <a href="https://share.streamlit.io/deploy" target="_blank">
    <button style="width:100%;background:linear-gradient(135deg,#3b82f6,#1d4ed8);color:white;border:none;
    padding:10px 16px;border-radius:8px;font-family:Inter;font-weight:600;cursor:pointer;font-size:0.87rem;">
    🚀 Deploy to Streamlit Cloud
    </button></a>
    """, unsafe_allow_html=True)
    st.markdown("""
    <p style='color:#475569;font-size:0.75rem;margin-top:6px;'>
    Push this folder to GitHub, then click above to publish instantly.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ─── Load Data ──────────────────────────────────────────────────────────────────
if not selected_agents:
    st.warning("Select at least one agent from the sidebar.")
    st.stop()

with st.spinner("Loading data from all databases..."):
    df_signals = load_all_signals(selected_agents, days_back, selected_tickers)
    df_logs = load_system_logs(selected_agents, min(days_back, 3), "ALL")

# ─── KPI Bar ─────────────────────────────────────────────────────────────────────
total_scanned     = len(df_signals)
total_approved    = len(df_signals[df_signals["score"] >= threshold]) if not df_signals.empty else 0
total_rejected    = total_scanned - total_approved
unique_tickers    = df_signals["symbol"].nunique() if not df_signals.empty else 0
avg_score         = df_signals["score"].mean() if not df_signals.empty else 0.0
wins = len(df_signals[df_signals["outcome_state"] == "WIN"]) if not df_signals.empty else 0
losses = len(df_signals[df_signals["outcome_state"] == "LOSS"]) if not df_signals.empty else 0
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("📋 Signals Scanned", total_scanned)
k2.metric("✅ Approved", total_approved, delta=f"@{threshold:.0%} threshold")
k3.metric("❌ Rejected", total_rejected)
k4.metric("🎯 Unique Tickers", unique_tickers)
k5.metric("📊 Avg Score", f"{avg_score:.3f}")
k6.metric("🏆 Win Rate", f"{win_rate:.1f}%", delta=f"{wins}W / {losses}L")

st.markdown("")

# ─── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Signal Activity",
    "🤖 AI Analysis",
    "⚗️ Pipeline Breakdown",
    "📈 Analytics",
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — Signal Activity
# ════════════════════════════════════════════════════════════════
with tab1:
    if df_signals.empty:
        st.info("No signals in the selected time window. The pipeline may still be warming up.")
    else:
        st.markdown(f"<div class='section-header'>All Tickers Discovered — Last {days_back} Days</div>", unsafe_allow_html=True)

        # Build display table
        display = df_signals[[
            "timestamp", "agent", "symbol", "direction", "score",
            "regime", "entry_price", "stop_loss", "take_profit", "outcome_state"
        ]].copy()

        display["timestamp"] = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        display["score"] = display["score"].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "—")
        display["entry_price"] = display["entry_price"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
        display["stop_loss"] = display["stop_loss"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
        display["take_profit"] = display["take_profit"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "—")
        display.columns = ["Timestamp", "Agent", "Symbol", "Direction", "Score", "Regime", "Entry", "Stop Loss", "Take Profit", "Outcome"]

        def style_row(row):
            return ["background-color: rgba(16,185,129,0.06)" if row["Outcome"] == "WIN"
                    else "background-color: rgba(239,68,68,0.06)" if row["Outcome"] == "LOSS"
                    else "" for _ in row]

        styled = display.style.apply(style_row, axis=1)
        st.dataframe(styled, use_container_width=True, height=480)

        # Agent breakdown mini table
        st.markdown("")
        st.markdown("<div class='section-header'>Breakdown by Agent</div>", unsafe_allow_html=True)
        breakdown_cols = st.columns(len(selected_agents))
        for i, ak in enumerate(selected_agents):
            agent_df = df_signals[df_signals["agent"] == ak]
            with breakdown_cols[i]:
                badge_cls = f"badge-{AGENTS[ak]['badge']}"
                st.markdown(f"<span class='{badge_cls}'>{AGENTS[ak]['label']}</span>", unsafe_allow_html=True)
                st.metric("Signals", len(agent_df))
                st.metric("Tickers", agent_df["symbol"].nunique() if not agent_df.empty else 0)
                avg = agent_df["score"].mean() if not agent_df.empty else 0
                st.metric("Avg Score", f"{avg:.3f}")

        # MAX-2 Daily Universe
        df_universe = load_daily_universe(days_back, selected_tickers)
        if not df_universe.empty:
            st.markdown("")
            st.markdown("<div class='section-header'>📰 MAX-2 Daily News Universe</div>", unsafe_allow_html=True)
            st.dataframe(df_universe.rename(columns={
                "date": "Date", "symbol": "Ticker",
                "mention_count": "Mentions", "top_event_type": "Event Type"
            }), use_container_width=True, height=280)


# ════════════════════════════════════════════════════════════════
# TAB 2 — AI Analysis
# ════════════════════════════════════════════════════════════════
with tab2:
    if df_signals.empty:
        st.info("No signal data available yet.")
    else:
        st.markdown("<div class='section-header'>AI Factor Analysis — Per Signal</div>", unsafe_allow_html=True)

        # Ticker selector for detail view
        tickers_for_ai = df_signals["symbol"].unique().tolist()
        col_pick, col_agent_pick = st.columns([2,2])
        with col_pick:
            ai_ticker = st.selectbox("Select Ticker", tickers_for_ai)
        with col_agent_pick:
            ai_agent = st.selectbox("Select Agent", [a for a in selected_agents if not df_signals[(df_signals["symbol"]==ai_ticker)&(df_signals["agent"]==a)].empty] or selected_agents)

        filtered_ai = df_signals[(df_signals["symbol"] == ai_ticker) & (df_signals["agent"] == ai_agent)]

        if filtered_ai.empty:
            st.warning("No signals for this ticker/agent combination.")
        else:
            latest = filtered_ai.iloc[0]
            badge_cls = f"badge-{AGENTS[ai_agent]['badge']}"

            # Gauge row
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                ml_val = float(latest.get("ml_prob", 0) or 0)
                st.plotly_chart(make_gauge(ml_val, "ML Probability", "#3b82f6"), use_container_width=True)
            with g2:
                sent_val = (float(latest.get("sentiment", 0) or 0) + 1) / 2
                st.plotly_chart(make_gauge(sent_val, "Sentiment", "#8b5cf6"), use_container_width=True)
            with g3:
                mom_val = (float(latest.get("momentum", 0) or 0) + 1) / 2
                st.plotly_chart(make_gauge(mom_val, "Momentum", "#ec4899"), use_container_width=True)
            with g4:
                score_val = float(latest.get("score", 0) or 0)
                color_score = "#10b981" if score_val >= threshold else "#ef4444"
                st.plotly_chart(make_gauge(score_val, "Final Score", color_score), use_container_width=True)

            # AI Reasoning
            st.markdown("")
            st.markdown("<div class='section-header'>🤖 Ollama AI Reasoning</div>", unsafe_allow_html=True)
            reasoning = latest.get("reasoning") or "No AI reasoning recorded."
            direction = latest.get("direction", "—")
            dir_badge = "badge-long" if direction == "LONG" else "badge-short"
            st.markdown(f"""
            <div class='signal-card'>
              <div style='display:flex;gap:10px;align-items:center;margin-bottom:10px;'>
                <span class='{badge_cls}'>{AGENTS[ai_agent]['label']}</span>
                <span class='{dir_badge}'>{direction}</span>
                <span style='color:#94a3b8;font-size:0.85rem;'>{latest.get('timestamp','')}</span>
              </div>
              <p style='color:#cbd5e1;line-height:1.6;margin:0;'>{reasoning}</p>
            </div>
            """, unsafe_allow_html=True)

            # Historical AI scores for this ticker
            if len(filtered_ai) > 1:
                st.markdown("<div class='section-header'>Score History</div>", unsafe_allow_html=True)
                hist = filtered_ai[["timestamp","score","ml_prob","sentiment","momentum"]].copy()
                hist["timestamp"] = pd.to_datetime(hist["timestamp"]).dt.strftime("%m-%d %H:%M")
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(x=hist["timestamp"], y=hist["score"], name="Score",
                    line=dict(color="#3b82f6", width=2), mode="lines+markers"))
                fig_hist.add_trace(go.Scatter(x=hist["timestamp"], y=hist["ml_prob"], name="ML Prob",
                    line=dict(color="#8b5cf6", width=1.5, dash="dot"), mode="lines"))
                fig_hist.add_hline(y=threshold, line_dash="dash", line_color="#f59e0b",
                    annotation_text="Threshold", annotation_font_color="#f59e0b")
                fig_hist.update_layout(
                    height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,14,26,0.5)",
                    font=dict(family="Inter", color="#94a3b8"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", range=[0,1]),
                    legend=dict(bgcolor="rgba(0,0,0,0)"),
                    margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        # Factor Comparison Radar — all tickers
        st.markdown("")
        st.markdown("<div class='section-header'>Factor Heatmap — All Approved Signals</div>", unsafe_allow_html=True)
        approved_df = df_signals[df_signals["score"].fillna(0) >= threshold].copy()
        if not approved_df.empty:
            heat_data = approved_df[["symbol","agent","ml_prob","sentiment","momentum","volume_score","score"]].copy()
            heat_data["sentiment"] = (heat_data["sentiment"].fillna(0) + 1) / 2
            heat_data["momentum"] = (heat_data["momentum"].fillna(0) + 1) / 2
            heat_data = heat_data.fillna(0).round(3)
            fig_heat = px.imshow(
                heat_data[["ml_prob","sentiment","momentum","volume_score","score"]].T,
                labels=dict(x="Signal", y="Factor", color="Score"),
                x=[f"{r['symbol']} ({r['agent'][:4]})" for _, r in heat_data.iterrows()],
                y=["ML Prob","Sentiment","Momentum","Volume","Final Score"],
                color_continuous_scale="Blues",
                aspect="auto"
            )
            fig_heat.update_layout(
                height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#94a3b8"),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No approved signals to show in heatmap yet.")


# ════════════════════════════════════════════════════════════════
# TAB 3 — Pipeline Breakdown
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Pipeline Decision Breakdown — Why Accepted or Rejected</div>", unsafe_allow_html=True)

    if df_signals.empty:
        st.info("No pipeline data available yet.")
    else:
        df_pipeline = df_signals.copy()
        df_pipeline["status"] = df_pipeline["score"].apply(
            lambda s: "✅ APPROVED" if (s or 0) >= threshold else "❌ REJECTED"
        )
        df_pipeline["score_gap"] = ((df_pipeline["score"].fillna(0) - threshold) * 100).round(2)
        df_pipeline["r_r_ratio"] = (
            (df_pipeline["take_profit"].fillna(0) - df_pipeline["entry_price"].fillna(0)) /
            (df_pipeline["entry_price"].fillna(1) - df_pipeline["stop_loss"].fillna(0) + 0.0001)
        ).round(2)

        # Status filter
        status_filter = st.radio("Show", ["ALL", "✅ APPROVED", "❌ REJECTED"], horizontal=True)
        if status_filter != "ALL":
            df_pipeline = df_pipeline[df_pipeline["status"] == status_filter]

        for _, row in df_pipeline.iterrows():
            score = float(row.get("score") or 0)
            ml = float(row.get("ml_prob") or 0)
            sent = float(row.get("sentiment") or 0)
            mom = float(row.get("momentum") or 0)
            vol = float(row.get("volume_score") or 0)
            news = float(row.get("news_score") or 0) if pd.notna(row.get("news_score")) else None
            direction = row.get("direction", "—")
            status = row.get("status", "—")
            badge_cls = f"badge-{AGENTS[row['agent']]['badge']}"
            dir_badge = "badge-long" if direction == "LONG" else "badge-short"
            status_cls = "badge-accept" if "APPROVED" in status else "badge-reject"

            score_pct = int(min(score * 100, 100))
            threshold_pct = int(threshold * 100)

            st.markdown(f"""
            <div class='signal-card'>
              <div style='display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px;'>
                <span style='color:#f1f5f9;font-size:1.1rem;font-weight:700;'>{row.get('symbol','—')}</span>
                <span class='{badge_cls}'>{AGENTS[row['agent']]['label']}</span>
                <span class='{dir_badge}'>{direction}</span>
                <span class='{status_cls}'>{status}</span>
                <span style='color:#64748b;font-size:0.8rem;margin-left:auto;'>{row.get('timestamp','')}</span>
              </div>

              <div style='display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:14px;'>
                <div style='text-align:center;'>
                  <div style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;'>ML Prob</div>
                  <div style='color:#60a5fa;font-weight:700;font-size:1rem;'>{ml:.1%}</div>
                </div>
                <div style='text-align:center;'>
                  <div style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;'>Sentiment</div>
                  <div style='color:#a78bfa;font-weight:700;font-size:1rem;'>{sent:+.2f}</div>
                </div>
                <div style='text-align:center;'>
                  <div style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;'>Momentum</div>
                  <div style='color:#f472b6;font-weight:700;font-size:1rem;'>{mom:+.2f}</div>
                </div>
                <div style='text-align:center;'>
                  <div style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;'>Volume</div>
                  <div style='color:#34d399;font-weight:700;font-size:1rem;'>{vol:.2f}x</div>
                </div>
                <div style='text-align:center;'>
                  <div style='color:#94a3b8;font-size:0.72rem;text-transform:uppercase;'>Regime</div>
                  <div style='color:#fbbf24;font-weight:700;font-size:0.95rem;'>{row.get('regime','—')}</div>
                </div>
              </div>

              <div style='margin-bottom:10px;'>
                <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                  <span style='color:#94a3b8;font-size:0.78rem;'>Final Score vs Threshold ({threshold:.0%})</span>
                  <span style='color:{"#10b981" if score>=threshold else "#ef4444"};font-weight:700;font-size:0.9rem;'>{score:.3f}</span>
                </div>
                <div class='score-bar-wrap'>
                  <div class='score-bar' style='width:{score_pct}%; background:{"linear-gradient(90deg,#10b981,#34d399)" if score>=threshold else "linear-gradient(90deg,#ef4444,#f87171)"};'></div>
                </div>
                <div style='margin-top:4px;font-size:0.75rem;color:#64748b;'>
                  {"▲ +" + str(round(row.get("score_gap",0),2)) + "% above threshold" if score>=threshold else "▼ " + str(abs(round(row.get("score_gap",0),2))) + "% below threshold"}
                </div>
              </div>

              <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:10px;border-top:1px solid rgba(255,255,255,0.05);padding-top:10px;'>
                <div>
                  <div style='color:#64748b;font-size:0.72rem;'>Entry</div>
                  <div style='color:#f1f5f9;font-weight:600;'>${row.get("entry_price") or 0:.2f}</div>
                </div>
                <div>
                  <div style='color:#64748b;font-size:0.72rem;'>Stop Loss</div>
                  <div style='color:#ef4444;font-weight:600;'>${row.get("stop_loss") or 0:.2f}</div>
                </div>
                <div>
                  <div style='color:#64748b;font-size:0.72rem;'>Take Profit</div>
                  <div style='color:#10b981;font-weight:600;'>${row.get("take_profit") or 0:.2f}</div>
                </div>
                <div>
                  <div style='color:#64748b;font-size:0.72rem;'>R:R Ratio</div>
                  <div style='color:#fbbf24;font-weight:600;'>{row.get("r_r_ratio") or 0:.1f}:1</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 — Analytics
# ════════════════════════════════════════════════════════════════
with tab4:
    if df_signals.empty:
        st.info("No signals yet to analyse.")
    else:
        st.markdown("<div class='section-header'>Score Distribution by Agent</div>", unsafe_allow_html=True)
        fig_dist = go.Figure()
        for ak in selected_agents:
            agent_scores = df_signals[df_signals["agent"] == ak]["score"].dropna()
            if not agent_scores.empty:
                fig_dist.add_trace(go.Histogram(
                    x=agent_scores, name=AGENTS[ak]["label"],
                    marker_color=AGENTS[ak]["color"],
                    opacity=0.75, nbinsx=20
                ))
        fig_dist.add_vline(x=threshold, line_dash="dash", line_color="#f59e0b",
            annotation_text=f"Threshold ({threshold:.0%})", annotation_font_color="#f59e0b")
        fig_dist.update_layout(
            barmode="overlay", height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,14,26,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            xaxis=dict(title="Score", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title="Count", gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_dist, use_container_width=True)

        # Volume of signals over time
        st.markdown("<div class='section-header'>Signal Volume Over Time</div>", unsafe_allow_html=True)
        df_ts = df_signals.copy()
        df_ts["date"] = df_ts["timestamp"].dt.date
        ts_grouped = df_ts.groupby(["date","agent"]).size().reset_index(name="count")
        fig_ts = px.bar(ts_grouped, x="date", y="count", color="agent",
            color_discrete_map={ak: AGENTS[ak]["color"] for ak in AGENTS},
            barmode="group")
        fig_ts.update_layout(
            height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,14,26,0.5)",
            font=dict(family="Inter", color="#94a3b8"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", title=""),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_ts, use_container_width=True)

        # Most active tickers
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("<div class='section-header'>Top Tickers by Signal Count</div>", unsafe_allow_html=True)
            top_tickers = df_signals.groupby("symbol").size().reset_index(name="count").sort_values("count", ascending=True).tail(15)
            fig_bar = go.Figure(go.Bar(
                x=top_tickers["count"], y=top_tickers["symbol"],
                orientation="h", marker_color="#3b82f6"
            ))
            fig_bar.update_layout(
                height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,14,26,0.5)",
                font=dict(family="Inter", color="#94a3b8"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.markdown("<div class='section-header'>Model Weights — Live DB Values</div>", unsafe_allow_html=True)
            weight_agent = st.selectbox("Agent", [a for a in selected_agents if a != "MarketBrainPro"], key="weight_agent")
            df_weights = load_model_weights(weight_agent)
            if not df_weights.empty:
                fig_w = go.Figure(go.Bar(
                    x=df_weights["value"] * 100,
                    y=df_weights["weight_name"].str.replace("_factor","").str.title(),
                    orientation="h",
                    marker_color=["#3b82f6","#8b5cf6","#ec4899","#10b981","#f59e0b","#06b6d4"][:len(df_weights)],
                    text=[f"{v:.1%}" for v in df_weights["value"]],
                    textposition="inside"
                ))
                fig_w.update_layout(
                    height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(10,14,26,0.5)",
                    font=dict(family="Inter", color="#94a3b8"),
                    xaxis=dict(title="Weight %", gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    margin=dict(l=0, r=0, t=10, b=0)
                )
                st.plotly_chart(fig_w, use_container_width=True)
                if df_weights["win_rate"].notna().any():
                    wr = df_weights["win_rate"].iloc[0]
                    ss = int(df_weights["sample_size"].iloc[0]) if pd.notna(df_weights["sample_size"].iloc[0]) else 0
                    st.caption(f"🏆 Win rate used for last calibration: {wr:.1%} over {ss} signals")
            else:
                st.info("No model weights data (signals need to close first).")

        # System log viewer
        st.markdown("")
        st.markdown("<div class='section-header'>📋 Live System Logs</div>", unsafe_allow_html=True)
        log_level = st.selectbox("Log Level", ["ALL","INFO","WARNING","ERROR"], key="log_level_select")
        df_logs_filtered = load_system_logs(selected_agents, 1, log_level if log_level != "ALL" else "ALL")
        if not df_logs_filtered.empty:
            df_logs_filtered["timestamp"] = pd.to_datetime(df_logs_filtered["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(
                df_logs_filtered[["timestamp","agent","level","logger_name","message"]].rename(columns={
                    "timestamp":"Time","agent":"Agent","level":"Level",
                    "logger_name":"Logger","message":"Message"
                }),
                use_container_width=True, height=300
            )
        else:
            st.info("No log entries found. Logs appear here once pipeline cycles run.")
