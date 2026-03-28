#!/usr/bin/env python3
"""Fetch A-share market data and technical indicators via AKShare.

Usage:
    python3 scripts/fetch_ashare_market.py TICKER [END_DATE] [LOOKBACK_DAYS]

Examples:
    python3 scripts/fetch_ashare_market.py 600519
    python3 scripts/fetch_ashare_market.py 000858 2026-03-27 120
    python3 scripts/fetch_ashare_market.py 600519.SS

Output JSON fields are compatible with fetch_market_data.py, plus:
    - turnover_rate: latest day turnover rate (%)
"""

import sys
import json
from datetime import datetime, timedelta

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# AKShare column names (Chinese) - defined as constants
# stock_zh_a_hist columns:
#   0:日期 1:股票代码 2:开盘 3:收盘 4:最高 5:最低
#   6:成交量 7:成交额 8:振幅 9:涨跌幅 10:涨跌额 11:换手率
COL_DATE = 0
COL_CODE = 1
COL_OPEN = 2
COL_CLOSE = 3
COL_HIGH = 4
COL_LOW = 5
COL_VOLUME = 6
COL_AMOUNT = 7
COL_AMPLITUDE = 8
COL_PCT_CHANGE = 9
COL_PRICE_CHANGE = 10
COL_TURNOVER = 11


def _col(df, idx):
    """Access DataFrame column by position index."""
    return df.iloc[:, idx]


def format_ticker(ticker: str) -> str:
    """Normalise ticker to pure 6-digit code for AKShare.

    600519.SS -> 600519
    000858.SZ -> 000858
    600519    -> 600519
    """
    ticker = ticker.strip()
    for suffix in (".SS", ".SZ", ".ss", ".sz"):
        if ticker.endswith(suffix):
            return ticker[: -len(suffix)]
    return ticker


def detect_exchange(code: str) -> str:
    """Return exchange suffix based on A-share code prefix."""
    if code.startswith("6"):
        return ".SS"  # Shanghai
    elif code.startswith("0") or code.startswith("3"):
        return ".SZ"  # Shenzhen
    return ".SS"


def fetch_ashare_data(ticker: str, end_date: str = None, lookback_days: int = 90):
    """Fetch A-share price data, company info and compute technical indicators."""
    if not HAS_AKSHARE:
        print("ERROR: akshare not installed. Install with:", file=sys.stderr)
        print("  pip install akshare", file=sys.stderr)
        sys.exit(1)

    if not HAS_PANDAS:
        print("ERROR: pandas not installed. Install with:", file=sys.stderr)
        print("  pip install pandas", file=sys.stderr)
        sys.exit(1)

    code = format_ticker(ticker)
    exchange = detect_exchange(code)
    display_ticker = f"{code}{exchange}"

    if code != ticker:
        print(f"[INFO] Ticker formatted: {ticker} -> {code}", file=sys.stderr)

    # --- Date range ---
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            print(f"ERROR: Invalid date format '{end_date}'. Use YYYY-MM-DD.",
                  file=sys.stderr)
            sys.exit(1)
    else:
        end_dt = datetime.now()

    start_dt = end_dt - timedelta(days=lookback_days)
    start_str = start_dt.strftime("%Y%m%d")
    end_str = end_dt.strftime("%Y%m%d")

    # --- K-line data via stock_zh_a_hist ---
    try:
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_str,
            end_date=end_str,
            adjust="qfq",
        )
    except Exception as e:
        print(f"ERROR: Failed to fetch K-line data for {code}: {e}",
              file=sys.stderr)
        sys.exit(1)

    if df is None or df.empty:
        print(f"ERROR: No K-line data returned for {code} "
              f"({start_str} ~ {end_str})", file=sys.stderr)
        sys.exit(1)

    # --- Company info via stock_individual_info_em ---
    company_name = display_ticker
    market_cap = "N/A"
    industry = "N/A"
    float_market_cap = "N/A"
    try:
        info_df = ak.stock_individual_info_em(symbol=code)
        info_map = dict(zip(info_df["item"], info_df["value"]))
        # Keys: 股票简称, 总市值, 流通市值, 行业
        for k, v in info_map.items():
            if k.endswith("简称"):
                company_name = str(v)
            elif "总市值" in k:
                market_cap = v
            elif "流通市值" in k:
                float_market_cap = v
            elif k == "行业":
                industry = str(v)
    except Exception as e:
        print(f"[WARN] Could not fetch company info: {e}", file=sys.stderr)

    # --- Build closes / volumes series (access by column index) ---
    closes = _col(df, COL_CLOSE).astype(float)
    opens = _col(df, COL_OPEN).astype(float)
    highs = _col(df, COL_HIGH).astype(float)
    lows = _col(df, COL_LOW).astype(float)
    volumes = _col(df, COL_VOLUME).astype(float)
    turnover_rates = _col(df, COL_TURNOVER).astype(float)

    # --- Basic result dict (compatible with fetch_market_data.py) ---
    result = {
        "ticker": display_ticker,
        "original_input": ticker,
        "company_name": company_name,
        "sector": "N/A",
        "industry": industry,
        "market_cap": market_cap,
        "float_market_cap": float_market_cap,
        "currency": "CNY",
        "exchange": "Shanghai" if exchange == ".SS" else "Shenzhen",
        "pe_ratio": "N/A",
        "forward_pe": "N/A",
        "data_source": "akshare",
        "price_data": {
            "current_price": float(closes.iloc[-1]),
            "week_high": float(closes.tail(5).max()),
            "week_low": float(closes.tail(5).min()),
            "month_high": float(closes.tail(22).max()) if len(closes) >= 22 else None,
            "month_low": float(closes.tail(22).min()) if len(closes) >= 22 else None,
            "52w_high": float(closes.max()),
            "52w_low": float(closes.min()),
        },
        "volume": {
            "avg_volume": int(volumes.mean()),
            "latest_volume": int(volumes.iloc[-1]),
        },
        "turnover_rate": float(turnover_rates.iloc[-1]),
    }

    # --- Technical Indicators ---

    # Moving averages
    if len(closes) >= 5:
        result["ma_5"] = float(closes.tail(5).mean())
    if len(closes) >= 20:
        result["ma_20"] = float(closes.tail(20).mean())
    if len(closes) >= 50:
        result["ma_50"] = float(closes.tail(50).mean())

    # RSI (14-day)
    if len(closes) >= 15:
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        result["rsi_14"] = float(rsi.iloc[-1])

    # MACD (12, 26, 9)
    if len(closes) >= 26:
        ema12 = closes.ewm(span=12, adjust=False).mean()
        ema26 = closes.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        result["macd"] = {
            "macd": float(macd.iloc[-1]),
            "signal": float(signal.iloc[-1]),
            "histogram": float((macd - signal).iloc[-1]),
        }

    # Bollinger Bands (20-day, 2 std)
    if len(closes) >= 20:
        sma20 = closes.rolling(window=20).mean()
        std20 = closes.rolling(window=20).std()
        result["bollinger"] = {
            "upper": float((sma20 + 2 * std20).iloc[-1]),
            "middle": float(sma20.iloc[-1]),
            "lower": float((sma20 - 2 * std20).iloc[-1]),
        }

    # Recent price changes
    if len(closes) >= 2:
        result["change_1d"] = f"{((closes.iloc[-1] / closes.iloc[-2]) - 1) * 100:.2f}%"
    if len(closes) >= 6:
        result["change_1w"] = f"{((closes.iloc[-1] / closes.iloc[-6]) - 1) * 100:.2f}%"
    if len(closes) >= 23:
        result["change_1m"] = f"{((closes.iloc[-1] / closes.iloc[-23]) - 1) * 100:.2f}%"

    # Recent price history (last 10 trading days)
    col_names = list(df.columns)
    date_col = col_names[COL_DATE]
    open_col = col_names[COL_OPEN]
    high_col = col_names[COL_HIGH]
    low_col = col_names[COL_LOW]
    close_col = col_names[COL_CLOSE]
    vol_col = col_names[COL_VOLUME]
    turn_col = col_names[COL_TURNOVER]
    recent_df = df.tail(10)[[date_col, open_col, high_col, low_col, close_col, vol_col, turn_col]].copy()
    recent_df.columns = ["Date", "Open", "High", "Low", "Close", "Volume", "Turnover%"]
    result["recent_prices"] = recent_df.to_string(index=False)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fetch_ashare_market.py TICKER [END_DATE] [LOOKBACK_DAYS]")
        print()
        print("  TICKER:        A-share code (e.g. 600519, 000858, 600519.SS)")
        print("  END_DATE:      YYYY-MM-DD (default: today)")
        print("  LOOKBACK_DAYS: days of history (default: 90)")
        sys.exit(1)

    ticker = sys.argv[1]
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    lookback = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    data = fetch_ashare_data(ticker, end_date, lookback)
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
