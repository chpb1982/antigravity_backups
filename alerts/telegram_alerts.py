import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def send_alert(message: str):
    """
    Send an alert to a Telegram chat.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: Telegram credentials not set in .env. Logging alert instead.")
        print(f"--- ALERT ---\n{message}\n-------------")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False

def format_signal_alert(signal: dict) -> str:
    """Format signal dictionary into readable alert"""
    return f"""🚨 <b>Market Signal</b>

<b>Ticker:</b> {signal.get('ticker')}
<b>Opportunity Score:</b> {signal.get('score')}
<b>Momentum:</b> {signal.get('momentum_status')} (px_chg: {signal.get('price_change_pct')}%)
<b>Sentiment:</b> {signal.get('sentiment_status')}
<b>Vol Ratio:</b> {signal.get('volume_ratio')}x"""
