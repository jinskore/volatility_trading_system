import time
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def now_str():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

def parse_h0stcnt0(message: str):
    """
    체결가(H0STCNT0) 데이터 파싱
    포맷 예: "0|H0STCNT0|...|005930^123456^70600^...^0.45^...^...^...^...^1289342^..."
    """
    try:
        if not message or message[0] not in ("0", "1"):
            return None
        parts = message.split("|")
        if len(parts) < 4:
            return None
        tr_id = parts[1]
        if tr_id != "H0STCNT0":
            return None
        payload = parts[3]
        fields = payload.split("^")
        if len(fields) < 10:
            return None
        return {
            "code": fields[0],
            "time": fields[1],
            "price": float(fields[2]),
            "change_rate": fields[4],
            "volume": fields[9],
        }
    except Exception:
        return None

def cooldown_ok(last_ts_map, code: str, cooldown_sec: float) -> bool:
    now = time.time()
    last = last_ts_map.get(code, 0.0)
    if now - last < cooldown_sec:
        return False
    last_ts_map[code] = now
    return True
