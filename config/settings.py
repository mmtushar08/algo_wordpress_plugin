import os
from dotenv import load_dotenv

load_dotenv()

# ── Angel One SmartAPI ────────────────────────────────────────────────────────
ANGEL_API_KEY    = os.getenv('ANGEL_API_KEY',    '')
ANGEL_CLIENT_ID  = os.getenv('ANGEL_CLIENT_ID',  '')
ANGEL_PASSWORD   = os.getenv('ANGEL_PASSWORD',   '')
ANGEL_TOTP_TOKEN = os.getenv('ANGEL_TOTP_TOKEN', '')   # TOTP secret from Angel One app

# ── Telegram ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID',   '')

# ── Trading parameters ────────────────────────────────────────────────────────
DEFAULT_TICKER     = os.getenv('DEFAULT_TICKER',  'NIFTY')
DEFAULT_EXPIRY     = os.getenv('DEFAULT_EXPIRY',  'weekly')
DEFAULT_CAPITAL    = float(os.getenv('DEFAULT_CAPITAL',    '100000'))
MAX_DAILY_LOSS     = float(os.getenv('MAX_DAILY_LOSS',     '5000'))   # INR — engine stops if exceeded
MAX_POSITION_SIZE  = float(os.getenv('MAX_POSITION_SIZE',  '25000'))  # INR — per trade cap

# PAPER_TRADING=true  → signals + Telegram only, no real orders
# PAPER_TRADING=false → live orders via Angel One API  (use with caution)
PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
