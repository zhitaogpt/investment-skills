#!/usr/bin/env python3
"""Fetch fundamental financial data for a given ticker.

Supports:
- US stocks: NVDA, AAPL, MSFT
- A-shares: 600519 → 600519.SS, 000858 → 000858.SZ
- HK stocks: 0700.HK, 9988.HK
"""

import sys
import json

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

    if any(ticker.endswith(s) for s in ['.SS', '.SZ', '.HK', '.L', '.T']):
        return ticker

    if ticker.isdigit() and len(ticker) == 6:
        if ticker.startswith('6'):
            return f"{ticker}.SS"
        elif ticker.startswith(('0', '3')):
            return f"{ticker}.SZ"
        else:
            return f"{ticker}.SS"

    if ticker.isdigit() and len(ticker) == 4:
        return f"{ticker}.HK"

    return ticker


def fetch_fundamentals(ticker: str):
    """Fetch fundamental financial data."""
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
        info = stock.info
    except Exception as e:
        print(f"ERROR: Failed to fetch data for {formatted_ticker}: {e}")
        print("Possible causes: network timeout, invalid ticker, or data unavailable.")
        sys.exit(1)

    if not info or info.get("regularMarketPrice") is None:
        print(f"WARNING: Limited data available for {formatted_ticker}. Results may be incomplete.", file=sys.stderr)

    result = {
        "ticker": formatted_ticker,
        "original_input": ticker,
        "company_name": info.get("longName", formatted_ticker),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "description": info.get("longBusinessSummary", "N/A"),
        "employees": info.get("fullTimeEmployees", "N/A"),
        "website": info.get("website", "N/A"),
        "currency": info.get("currency", "N/A"),
        "exchange": info.get("exchange", "N/A"),
    }

    # Valuation metrics
    result["valuation"] = {
        "market_cap": info.get("marketCap", "N/A"),
        "enterprise_value": info.get("enterpriseValue", "N/A"),
        "trailing_pe": info.get("trailingPE", "N/A"),
        "forward_pe": info.get("forwardPE", "N/A"),
        "peg_ratio": info.get("pegRatio", "N/A"),
        "price_to_book": info.get("priceToBook", "N/A"),
        "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
        "ev_to_revenue": info.get("enterpriseToRevenue", "N/A"),
        "ev_to_ebitda": info.get("enterpriseToEbitda", "N/A"),
    }

    # Profitability
    result["profitability"] = {
        "profit_margin": info.get("profitMargins", "N/A"),
        "operating_margin": info.get("operatingMargins", "N/A"),
        "gross_margin": info.get("grossMargins", "N/A"),
        "roe": info.get("returnOnEquity", "N/A"),
        "roa": info.get("returnOnAssets", "N/A"),
    }

    # Growth
    result["growth"] = {
        "revenue_growth": info.get("revenueGrowth", "N/A"),
        "earnings_growth": info.get("earningsGrowth", "N/A"),
        "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth", "N/A"),
    }

    # Financial health
    result["financial_health"] = {
        "total_cash": info.get("totalCash", "N/A"),
        "total_debt": info.get("totalDebt", "N/A"),
        "debt_to_equity": info.get("debtToEquity", "N/A"),
        "current_ratio": info.get("currentRatio", "N/A"),
        "quick_ratio": info.get("quickRatio", "N/A"),
        "free_cashflow": info.get("freeCashflow", "N/A"),
        "operating_cashflow": info.get("operatingCashflow", "N/A"),
    }

    # Dividends
    result["dividends"] = {
        "dividend_yield": info.get("dividendYield", "N/A"),
        "dividend_rate": info.get("dividendRate", "N/A"),
        "payout_ratio": info.get("payoutRatio", "N/A"),
    }

    # Analyst recommendations
    result["analyst_targets"] = {
        "target_high": info.get("targetHighPrice", "N/A"),
        "target_low": info.get("targetLowPrice", "N/A"),
        "target_mean": info.get("targetMeanPrice", "N/A"),
        "target_median": info.get("targetMedianPrice", "N/A"),
        "recommendation": info.get("recommendationKey", "N/A"),
        "num_analysts": info.get("numberOfAnalystOpinions", "N/A"),
    }

    # Income statement (recent)
    try:
        income = stock.income_stmt
        if income is not None and not income.empty:
            latest = income.iloc[:, 0]
            result["income_statement"] = {
                "total_revenue": _safe_val(latest, "Total Revenue"),
                "gross_profit": _safe_val(latest, "Gross Profit"),
                "operating_income": _safe_val(latest, "Operating Income"),
                "net_income": _safe_val(latest, "Net Income"),
                "ebitda": _safe_val(latest, "EBITDA"),
                "eps_basic": _safe_val(latest, "Basic EPS"),
                "eps_diluted": _safe_val(latest, "Diluted EPS"),
            }
    except Exception:
        result["income_statement"] = "Unable to fetch"

    # Balance sheet (recent)
    try:
        bs = stock.balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.iloc[:, 0]
            result["balance_sheet"] = {
                "total_assets": _safe_val(latest, "Total Assets"),
                "total_liabilities": _safe_val(latest, "Total Liabilities Net Minority Interest"),
                "stockholders_equity": _safe_val(latest, "Stockholders Equity"),
                "cash_and_equivalents": _safe_val(latest, "Cash And Cash Equivalents"),
                "total_debt_bs": _safe_val(latest, "Total Debt"),
            }
    except Exception:
        result["balance_sheet"] = "Unable to fetch"

    # Cash flow (recent)
    try:
        cf = stock.cashflow
        if cf is not None and not cf.empty:
            latest = cf.iloc[:, 0]
            result["cashflow"] = {
                "operating_cashflow": _safe_val(latest, "Operating Cash Flow"),
                "investing_cashflow": _safe_val(latest, "Investing Cash Flow"),
                "financing_cashflow": _safe_val(latest, "Financing Cash Flow"),
                "free_cashflow_cf": _safe_val(latest, "Free Cash Flow"),
                "capex": _safe_val(latest, "Capital Expenditure"),
            }
    except Exception:
        result["cashflow"] = "Unable to fetch"

    # --- Analyst Recommendations (L3) ---
    try:
        recs = stock.recommendations
        if recs is not None and not recs.empty:
            recent = recs.tail(10)
            result["recommendations"] = recent.to_dict(orient="records")
    except Exception:
        result["recommendations"] = "Unable to fetch"

    # --- Insider Transactions (L1) ---
    try:
        insiders = stock.insider_transactions
        if insiders is not None and not insiders.empty:
            result["insider_transactions"] = insiders.head(15).to_dict(orient="records")
    except Exception:
        result["insider_transactions"] = "Unable to fetch"

    # --- Institutional Holders (L3) ---
    try:
        inst = stock.institutional_holders
        if inst is not None and not inst.empty:
            result["institutional_holders"] = inst.head(10).to_dict(orient="records")
    except Exception:
        result["institutional_holders"] = "Unable to fetch"

    # --- Major Holders (L3) ---
    try:
        majors = stock.major_holders
        if majors is not None and not majors.empty:
            result["major_holders"] = majors.to_dict(orient="records")
    except Exception:
        result["major_holders"] = "Unable to fetch"

    # --- Earnings Dates with EPS surprise (L1/L2) ---
    try:
        edates = stock.earnings_dates
        if edates is not None and not edates.empty:
            result["earnings_dates"] = edates.head(8).to_dict(orient="records")
    except Exception:
        result["earnings_dates"] = "Unable to fetch"

    # --- Recent News headlines (L4) ---
    try:
        news = stock.news
        if news:
            result["news"] = [{"title": n.get("title"), "publisher": n.get("publisher"),
                               "link": n.get("link"), "date": n.get("providerPublishTime")}
                              for n in news[:10]]
    except Exception:
        result["news"] = "Unable to fetch"

    return result


def _safe_val(series, key):
    """Safely get a value from a pandas Series."""
    try:
        val = series.get(key, "N/A")
        if val is not None and val != "N/A":
            return float(val)
        return "N/A"
    except (ValueError, TypeError):
        return "N/A"


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_fundamentals.py TICKER")
        print()
        print("  TICKER:  Stock symbol")
        print("           US stocks:  NVDA, AAPL, MSFT")
        print("           A-shares:   600519 (→ 600519.SS), 000858 (→ 000858.SZ)")
        print("           HK stocks:  0700.HK, 9988.HK")
        sys.exit(1)

    ticker = sys.argv[1]
    data = fetch_fundamentals(ticker)
    print(json.dumps(data, indent=2, default=str))


if __name__ == "__main__":
    main()
