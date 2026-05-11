from datetime import datetime, time as dtime
import pytz

IST          = pytz.timezone('Asia/Kolkata')
MARKET_OPEN  = dtime(9, 15)
MARKET_CLOSE = dtime(15, 30)


def now_ist():
    return datetime.now(IST)


def is_market_open():
    """Return True if NSE is currently open (Mon–Fri, 09:15–15:30 IST)."""
    now = now_ist()
    if now.weekday() >= 5:           # Saturday = 5, Sunday = 6
        return False
    t = now.time()
    return MARKET_OPEN <= t <= MARKET_CLOSE


def minutes_to_open():
    """
    Minutes until market opens today.
    Returns None on weekends, 0 if already open or past close.
    """
    now = now_ist()
    if now.weekday() >= 5:
        return None
    target = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < target:
        return int((target - now).total_seconds() / 60)
    return 0


def next_candle_wait(interval_minutes):
    """
    Seconds to sleep so that we wake up ~5 s after the next candle closes.
    E.g. for a 15-min interval at 09:22 → wait until 09:30:05.
    """
    now     = now_ist()
    elapsed = (now.minute % interval_minutes) * 60 + now.second
    return (interval_minutes * 60 - elapsed) + 5
