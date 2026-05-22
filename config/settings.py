import os
from pathlib import Path
from dotenv import load_dotenv

# Always find .env from the project root, regardless of where the script is run
load_dotenv(Path(__file__).parent.parent / '.env')

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID',   '')

# ── Trading parameters ────────────────────────────────────────────────────────
DEFAULT_TICKER    = os.getenv('DEFAULT_TICKER',  'NIFTY')
DEFAULT_EXPIRY    = os.getenv('DEFAULT_EXPIRY',  'weekly')
DEFAULT_CAPITAL   = float(os.getenv('DEFAULT_CAPITAL',   '100000'))
MAX_DAILY_LOSS    = float(os.getenv('MAX_DAILY_LOSS',    '5000'))   # INR
MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '25000'))  # INR per trade

# PAPER_TRADING=true  → signals + Telegram only, no real orders placed
# PAPER_TRADING=false → live broker SDK used (configure in execution/order_manager.py)
PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
