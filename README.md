# 🧠 MarketBrain Command Centre

A real-time trading signal dashboard connecting to all three MarketBrain agents.

## Features
- **3-agent unified view** — MarketBrainPro, MAX-1, MAX-2
- **Filter** by Agent, Stock Ticker, Time Window, Score Threshold
- **Signal Activity** — all discovered tickers with timestamps
- **AI Analysis** — sentiment gauges, ML probability, Ollama reasoning
- **Pipeline Breakdown** — score vs threshold with accept/reject cards
- **Analytics** — score distribution, signal volume, model weight charts

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Requires PostgreSQL running locally with databases:
- `market_brain` (MarketBrainPro)
- `market_brain_max` (MAX-1)
- `market_brain_max2` (MAX-2)

## Deploy to Streamlit Cloud (1-click)

1. Fork or push this repo to your GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → select `app.py` → Deploy
4. Add secrets in the Streamlit Cloud dashboard:

```toml
POSTGRES_USER = "your_user"
POSTGRES_PASSWORD = "your_password"
POSTGRES_HOST = "your-cloud-db-host"
```

> For cloud deployment, expose your PostgreSQL instance publicly or use a managed cloud DB (e.g. Supabase, Neon, Railway).
