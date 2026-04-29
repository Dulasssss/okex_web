BASE_DIR = "/home/danglingbo/multi_okex"

STATE_FILE = f"{BASE_DIR}/paper_state.json"
TRADES_FILE = f"{BASE_DIR}/paper_trades.csv"
EQUITY_FILE = f"{BASE_DIR}/paper_equity.csv"
LOG_FILE = f"{BASE_DIR}/paper.log"
CHART_FILE = f"{BASE_DIR}/paper_chart.png"
CANDLE_FILE = f"{BASE_DIR}/data/BTCUSDT_15m.csv"

DASHBOARD_TITLE = "OKX BTC/USDT 15m Paper Trading Dashboard"

STRATEGY_PARAMS = {
    "TIMEFRAME": "15m",
    "SHORT_MA": 7,
    "LONG_MA": 30,
    "ATR_PERIOD": 14,
    "VOL_THRESHOLD": 0.003,
    "MAX_ADDS": 1,
    "ADD_RISK_PER_TRADE": 0.003,
    "MAX_TOTAL_RISK": 0.015,
    "ADD_ATR_STEP": 2.0,
    "ADD_ADX_THRESHOLD": 35,
    "RISK_PER_TRADE": 0.01,
    "ATR_MULTIPLIER": 2.0,
    "MAX_LEVERAGE": 3.0,
    "TRAILING_STOP_ENABLED": True,
    "REALTIME_STOP_ENABLED": True,
    "REALTIME_STOP_POLL_SECONDS": 5,
}