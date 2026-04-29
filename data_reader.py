import json
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from config import (
    CANDLE_FILE,
    CHART_FILE,
    DASHBOARD_TITLE,
    EQUITY_FILE,
    LOG_FILE,
    STATE_FILE,
    STRATEGY_PARAMS,
    TRADES_FILE,
)


TIME_COLUMNS = ("time", "timestamp", "datetime", "ts")


def clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return clean_value(value.item())
        except Exception:
            pass
    return value


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k): clean_value(v) for k, v in record.items()}


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    value = clean_value(value)
    if value in (None, ""):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def read_json_file(path: str, default: Any = None) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def normalize_time_column(df: pd.DataFrame) -> pd.DataFrame:
    for col in TIME_COLUMNS:
        if col in df.columns:
            if col != "time":
                df = df.rename(columns={col: "time"})
            return df
    return df


def normalize_common_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    lower_to_actual = {str(c).lower(): c for c in df.columns}
    for desired in ("open", "high", "low", "close", "volume"):
        actual = lower_to_actual.get(desired)
        if actual and actual != desired:
            rename[actual] = desired
    if rename:
        df = df.rename(columns=rename)
    return normalize_time_column(df)


def read_csv_tail(path: str, limit: int = 100) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
    except Exception:
        return []
    if df.empty:
        return []
    df = normalize_common_columns(df).tail(max(int(limit), 0))
    return [clean_record(r) for r in df.to_dict(orient="records")]


def read_state() -> Dict[str, Any]:
    state = read_json_file(STATE_FILE, default={}) or {}
    return clean_record(state) if isinstance(state, dict) else {}


def read_equity(limit: int = 500) -> List[Dict[str, Any]]:
    return read_csv_tail(EQUITY_FILE, limit)


def read_trades(limit: int = 50) -> List[Dict[str, Any]]:
    return read_csv_tail(TRADES_FILE, limit)


def read_adds(limit: int = 30) -> List[Dict[str, Any]]:
    rows = read_csv_tail(TRADES_FILE, 100000)
    adds = [r for r in rows if str(r.get("action", "")).upper() == "ADD"]
    return adds[-max(int(limit), 0):]


def read_candles(limit: int = 300) -> List[Dict[str, Any]]:
    return read_csv_tail(CANDLE_FILE, limit)


def read_logs(limit: int = 200) -> List[str]:
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return []
    return [line.rstrip("\n") for line in lines[-max(int(limit), 0):]]


def get_latest_equity_row() -> Dict[str, Any]:
    rows = read_equity(1)
    return rows[-1] if rows else {}


def calculate_risk(position: Any, last_close: Any, balance: Any) -> Dict[str, float]:
    zero = {
        "risk_amount": 0,
        "risk_pct": 0,
        "locked_profit": 0,
        "locked_profit_pct": 0,
        "distance_to_stop": 0,
        "distance_to_stop_pct": 0,
    }
    if not isinstance(position, dict) or not position:
        return zero
    side = str(position.get("side", "")).lower()
    entry = to_float(position.get("entry"), 0) or 0
    stop = to_float(position.get("stop"), 0) or 0
    size = to_float(position.get("size"), 0) or 0
    last = to_float(last_close, 0) or 0
    bal = to_float(balance, 0) or 0

    if side == "long":
        risk_amount = max(entry - stop, 0) * size
        locked_profit = max(stop - entry, 0) * size
        distance_to_stop = last - stop if last else 0
    elif side == "short":
        risk_amount = max(stop - entry, 0) * size
        locked_profit = max(entry - stop, 0) * size
        distance_to_stop = stop - last if last else 0
    else:
        return zero

    return {
        "risk_amount": risk_amount,
        "risk_pct": risk_amount / bal if bal else 0,
        "locked_profit": locked_profit,
        "locked_profit_pct": locked_profit / bal if bal else 0,
        "distance_to_stop": distance_to_stop,
        "distance_to_stop_pct": distance_to_stop / last if last else 0,
    }


def calculate_trade_stats() -> Dict[str, Any]:
    rows = read_csv_tail(TRADES_FILE, 100000)
    opens = [r for r in rows if str(r.get("action", "")).upper() == "OPEN"]
    adds = [r for r in rows if str(r.get("action", "")).upper() == "ADD"]
    closes = [r for r in rows if str(r.get("action", "")).upper() == "CLOSE"]
    return {
        "total_rows": len(rows),
        "open_count": len(opens),
        "add_count": len(adds),
        "close_count": len(closes),
        "closed_pnl": sum(to_float(r.get("pnl"), 0) or 0 for r in closes),
        "total_fee": sum(to_float(r.get("fee"), 0) or 0 for r in rows),
        "add_fee": sum(to_float(r.get("fee"), 0) or 0 for r in adds),
    }


def file_health_item(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"exists": False, "size": None, "modified": None, "path": path}
    try:
        mtime = os.path.getmtime(path)
        modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        return {"exists": True, "size": os.path.getsize(path), "modified": modified, "path": path}
    except Exception:
        return {"exists": True, "size": None, "modified": None, "path": path}


def get_file_health() -> Dict[str, Dict[str, Any]]:
    return {
        "state": file_health_item(STATE_FILE),
        "trades": file_health_item(TRADES_FILE),
        "equity": file_health_item(EQUITY_FILE),
        "log": file_health_item(LOG_FILE),
        "chart": file_health_item(CHART_FILE),
        "candles": file_health_item(CANDLE_FILE),
    }


def read_status() -> Dict[str, Any]:
    state = read_state()
    latest = get_latest_equity_row()
    position = state.get("position") if isinstance(state.get("position"), dict) else None

    balance = to_float(state.get("balance"), None)
    if balance is None:
        balance = to_float(latest.get("balance"), 0) or 0
    equity = to_float(latest.get("equity"), balance) or 0
    unrealized = to_float(latest.get("unrealized"), 0) or 0
    last_close = to_float(latest.get("close"), 0) or 0
    last_candle_ts = state.get("last_candle_ts") or latest.get("time")

    return {
        "title": DASHBOARD_TITLE,
        "state_file_exists": os.path.exists(STATE_FILE),
        "equity_file_exists": os.path.exists(EQUITY_FILE),
        "trades_file_exists": os.path.exists(TRADES_FILE),
        "log_file_exists": os.path.exists(LOG_FILE),
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_candle_ts": clean_value(last_candle_ts),
        "balance": balance,
        "equity": equity,
        "unrealized": unrealized,
        "last_close": last_close,
        "signal": clean_value(latest.get("signal")),
        "atr": clean_value(latest.get("atr")),
        "adx": clean_value(latest.get("adx")),
        "adx_weight": clean_value(latest.get("adx_weight")),
        "position": position,
        "risk": calculate_risk(position, last_close, balance),
        "trade_stats": calculate_trade_stats(),
        "file_health": get_file_health(),
        "strategy_params": STRATEGY_PARAMS,
    }