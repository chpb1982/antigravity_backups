import streamlit as st
import pandas as pd
import sys
import os

# Ensure project root is in path so we can import database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import load_all_signals

st.set_page_config(page_title="AI Trading Command Center", layout="wide", page_icon="📈")

st.title("AI Trading Command Center")

# Load data
raw_data = load_all_signals()

if not raw_data:
    st.info("No signals found in the database. Run main.py to generate signals.")
else:
    df = pd.DataFrame(raw_data)
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Signals Logged", len(df))
    
    # Latest scan data
    latest_timestamp = df['timestamp'].max()
    latest_df = df[df['timestamp'] == latest_timestamp]
    top_ticker = latest_df.sort_values(by="score", ascending=False).iloc[0]['ticker'] if not latest_df.empty else "N/A"
    
    col2.metric("Latest Top Signal", top_ticker)
    col3.metric("Last Updated", latest_timestamp)
    
    st.markdown("---")
    
    st.subheader("Top Signals (Latest Run)")
    if not latest_df.empty:
        # Style dataframe for the dashboard
        display_cols = ['ticker', 'score', 'sentiment_status', 'momentum_status', 'volume_ratio', 'price_change_pct']
        st.dataframe(latest_df[display_cols].sort_values(by="score", ascending=False), use_container_width=True)
    
    st.markdown("---")
    
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Momentum Watchlist")
        momentum_df = latest_df[latest_df['momentum_status'].isin(['Strong', 'Rising'])]
        if not momentum_df.empty:
            st.dataframe(momentum_df[['ticker', 'momentum_status', 'volume_ratio']], use_container_width=True)
        else:
            st.write("No strong/rising momentum detected.")
            
    with colB:
        st.subheader("Catalyst Watchlist")
        catalyst_df = latest_df[latest_df['sentiment_status'] == 'Bullish']
        if not catalyst_df.empty:
            st.dataframe(catalyst_df[['ticker', 'sentiment_status', 'score']], use_container_width=True)
        else:
            st.write("No bullish catalysts detected.")
            
    st.markdown("---")
    st.subheader("Signal History (All)")
    st.dataframe(df.drop(columns=['id'], errors='ignore'), use_container_width=True)
