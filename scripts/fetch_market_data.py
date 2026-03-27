#!/usr/bin/env python3
"""Fetch market data and technical indicators for a given ticker.

Supports:
- US stocks: NVDA, AAPL, MSFT
- A-shares: 600519 → 600519.SS, 000858 → 000858.SZ
- HK stocks: 0700.HK, 9988.HK
"""

import sys
import json
from datetime import datetime, timedelta

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


def format_ticker(ticker: str) -> str:
    """Auto-format ticker for different markets.

    - Pure letters → US stock (unchanged)
    - 6 digits starting with 6 → Shanghai (.SS)
    - 6 digits starting with 0/3 → Shenzhen (.SZ)
    - Already has .HK/.SS/.SZ suffix → unchanged
    """
    ticker = ticker.strip().upper()

    # Already has market suffix
    if any(ticker.endswith(s) for s in ['.SS', '.SZ', '.HK', '.L', '.T']):
        return ticker

    # Pure digits — A-share
    if ticker.isdigit() and len(ticker) == 6:
        if ticker.startswith('6'):
            return f"{ticker}.SS"  # Shanghai
        elif ticker.startswith(('0', '3')):
            return f"{ticker}.SZ"  # Shenzhen
        else:
            # Try Shanghai first for other codes
            return f"{ticker}.SS"

    # 4-digit number — could be HK stock
    if ticker.isdigit() and len(ticker) == 4:
        return f"{ticker}.HK"

    # Default: US stock (pure letters)
    return ticker


def fetch_stock_data(ticker: str, end_date: str = None, lookback_days: int = 90):
    """Fetch stock price data and basic info."""
    if not HAS_YFINANCE:
        print("ERROR: yfinance not installed. Please install it:")
        print("  pip install yfinance")
        print("  # or: pip3 install yfinance")
        sys.exit(1)

    formatted_ticker = format_ticker(ticker)
    if formatted_ticker != ticker:
        print(f"[INFO] Ticker formatted: {ticker} → {formatted_ticker}", file=sys.stderr)

    try:
        stock = yf.Ticker(formatted_ticker)
    except Exception as e:
        print(f"ERROR: Failed to create ticker object for {formatted_ticker}: {e}")
        sys.exit(1)

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            print(f"ERROR: Invalid date format '{end_date}'. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        end = datetime.now()
    start = end - timedelta(days=lookback_days)

    try:
        hist = stock.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
    except Exception as e:
        print(f"ERROR: Failed to fetch data for {formatted_ticker}: {e}")
        print("Possible causes: network timeout, invalid ticker, or market data unavailable.")
        sys.exit(1)

    if hist.empty:
        print(f"ERROR: No data found for {formatted_ticker}")
        if ticker.isdigit():
            alt = f"{ticker}.SZ" if formatted_ticker.endswith('.SS') else f"{ticker}.SS"
            print(f"TIP: Try the other exchange? {alt}")
        sys.exit(1)

    # Basic info
    try:
        info = stock.info
    except Exception:
        info = {}

    result = {
        "ticker": formatted_ticker,
        "original_input": ticker,
        "company_name": info.get("longName", formatted_ticker),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "currency": info.get("currency", "N/A"),
        "exchange": info.get("exchange", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
        "forward_pe": info.get("forwardPE", "N/A"),
        "price_data": {
            "current_price": float(hist["Close"].iloc[-1]),
            "week_high": float(hist["Close"].tail(5).max()),
            "week_low": float(hist["Close"].tail(5).min()),
            "month_high": float(hist["Close"].tail(22).max()) if len(hist) >= 22 else None,
            "month_low": float(hist["Close"].tail(22).min()) if len(hist) >= 22 else None,
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
        },
        "volume": {
            "avg_volume": info.get("averageVolume", "N/A"),
            "latest_volume": int(hist["Volume"].iloc[-1]),
        },
    }

    # Calculate technical indicators
    closes = hist["Close"]

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

    # MACD
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

    # Bollinger Bands (20-day)
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
    recent = hist.tail(10)[["Open", "High", "Low", "Close", "Volume"]]
    result["recent_prices"] = recent.to_string()

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_market_data.py TICKER [END_DATE] [LOOKBACK_DAYS]")
        print()
        print("  TICKER:        Stock symbol")
        print("                 US stocks:  NVDA, AAPL, MSFT")
        print("                 A-shares:   600519 (→ 600519.SS), 000858 (→ 000858.SZ)")
        print("                 HK stocks:  0700.HK, 9988.HK")
        print("  END_DATE:      Analysis date in YYYY-MM-DD format (default: today)")
        print("  LOOKBACK_DAYS: Number of days to look back (default: 90)")
        sys.exit(1)

    ticker = sys.argv[1]
    end_date = sys.argv[2] if len(sys.argv) > 2 else None
    lookback = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    data = fetch_stock_data(ticker, end_date, lookback)
    print(json.dumps(data, indent=2, default=str))


if __name__ == "__main__":
    main()
