#!/usr/bin/env python3
"""Fetch A-share fundamental financial data via AKShare.

Usage:
    python3 scripts/fetch_ashare_fundamentals.py TICKER

Examples:
    python3 scripts/fetch_ashare_fundamentals.py 600519
    python3 scripts/fetch_ashare_fundamentals.py 000858
    python3 scripts/fetch_ashare_fundamentals.py 300750.SZ

Output JSON fields are compatible with fetch_fundamentals.py (yfinance version).

Data sources (all via AKShare / East Money):
    - stock_individual_info_em: company info, market cap, industry
    - stock_financial_abstract: key financial metrics (revenue, profit, ROE, etc.)
    - stock_financial_analysis_indicator: detailed financial ratios
"""

import sys
import json

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


def _safe_float(val):
    """Safely convert a value to float, return 'N/A' on failure."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    try:
        return float(val)
    except (ValueError, TypeError):
        return "N/A"


def _get_abstract_row(df, category, metric_name):
    """Get the latest value from stock_financial_abstract for a given metric.

    The DataFrame has columns: ['选项', '指标', '20250930', '20250630', ...]
    We look for the row matching (category, metric_name) and return the first
    non-NaN date column value (most recent period).
    """
    mask = (df["选项"] == category) & (df["指标"] == metric_name)
    rows = df[mask]
    if rows.empty:
        return "N/A", "N/A"

    row = rows.iloc[0]
    # Date columns start at index 2
    date_cols = [c for c in df.columns[2:] if c.isdigit() and len(c) == 8]
    for col in date_cols:
        val = row.get(col)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            period = f"{col[:4]}-{col[4:6]}-{col[6:]}"
            return _safe_float(val), period
    return "N/A", "N/A"


def _get_abstract_value(df, category, metric_name):
    """Get just the value (no period) from stock_financial_abstract."""
    val, _ = _get_abstract_row(df, category, metric_name)
    return val


def _get_annual_value(df, category, metric_name):
    """Get the latest full-year (1231) value from stock_financial_abstract."""
    mask = (df["选项"] == category) & (df["指标"] == metric_name)
    rows = df[mask]
    if rows.empty:
        return "N/A"

    row = rows.iloc[0]
    date_cols = [c for c in df.columns[2:]
                 if c.isdigit() and len(c) == 8 and c.endswith("1231")]
    for col in date_cols:
        val = row.get(col)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            return _safe_float(val)
    return "N/A"


def _get_abstract_value_and_period(df, category, metric_name):
    """Get value and reporting period from stock_financial_abstract."""
    return _get_abstract_row(df, category, metric_name)


def _get_growth_rate(df, category, metric_name):
    """Calculate YoY growth rate from stock_financial_abstract.

    Compares the latest annual figure with the prior year annual figure.
    Annual periods end in '1231'.
    """
    mask = (df["选项"] == category) & (df["指标"] == metric_name)
    rows = df[mask]
    if rows.empty:
        return "N/A"

    row = rows.iloc[0]
    date_cols = [c for c in df.columns[2:] if c.isdigit() and len(c) == 8 and c.endswith("1231")]
    annual_vals = []
    for col in date_cols:
        val = row.get(col)
        if val is not None and not (isinstance(val, float) and pd.isna(val)):
            try:
                annual_vals.append(float(val))
            except (ValueError, TypeError):
                continue
        if len(annual_vals) == 2:
            break

    if len(annual_vals) == 2 and annual_vals[1] != 0:
        return round((annual_vals[0] / annual_vals[1] - 1), 4)
    return "N/A"


def fetch_ashare_fundamentals(ticker: str):
    """Fetch A-share fundamental data using AKShare APIs."""
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

    # --- 1. Company basic info via stock_individual_info_em ---
    company_name = display_ticker
    market_cap = "N/A"
    float_market_cap = "N/A"
    industry = "N/A"
    total_shares = "N/A"
    float_shares = "N/A"
    listing_date = "N/A"

    try:
        info_df = ak.stock_individual_info_em(symbol=code)
        info_map = dict(zip(info_df["item"], info_df["value"]))
        for k, v in info_map.items():
            if "简称" in k:
                company_name = str(v)
            elif "总市值" in k:
                market_cap = _safe_float(v)
            elif "流通市值" in k:
                float_market_cap = _safe_float(v)
            elif k == "行业":
                industry = str(v)
            elif "总股本" in k:
                total_shares = _safe_float(v)
            elif "流通股" in k:
                float_shares = _safe_float(v)
            elif "上市时间" in k:
                listing_date = str(v)
    except Exception as e:
        print(f"[WARN] Could not fetch company info: {e}", file=sys.stderr)

    # --- 2. Financial abstract via stock_financial_abstract ---
    abstract_df = None
    latest_period = "N/A"
    try:
        abstract_df = ak.stock_financial_abstract(symbol=code)
        # Determine latest reporting period from column names
        date_cols = [c for c in abstract_df.columns[2:] if c.isdigit() and len(c) == 8]
        if date_cols:
            lp = date_cols[0]
            latest_period = f"{lp[:4]}-{lp[4:6]}-{lp[6:]}"
    except Exception as e:
        print(f"[WARN] Could not fetch financial abstract: {e}", file=sys.stderr)

    # --- 3. Financial analysis indicators ---
    indicator_df = None
    try:
        indicator_df = ak.stock_financial_analysis_indicator(symbol=code, start_year="2023")
    except Exception as e:
        print(f"[WARN] Could not fetch financial indicators: {e}", file=sys.stderr)

    # === Build result dict (compatible with fetch_fundamentals.py output) ===

    result = {
        "ticker": display_ticker,
        "original_input": ticker,
        "company_name": company_name,
        "sector": "N/A",
        "industry": industry,
        "description": "N/A",
        "employees": "N/A",
        "website": "N/A",
        "currency": "CNY",
        "exchange": "Shanghai" if exchange == ".SS" else "Shenzhen",
        "data_source": "akshare",
        "latest_report_period": latest_period,
        "listing_date": listing_date,
        "total_shares": total_shares,
        "float_shares": float_shares,
    }

    # --- Valuation metrics ---
    # Get current price from stock_individual_info_em (already fetched above)
    current_price = "N/A"
    try:
        price_info = ak.stock_individual_info_em(symbol=code)
        price_map = dict(zip(price_info["item"], price_info["value"]))
        for k, v in price_map.items():
            if k == "最新":
                current_price = _safe_float(v)
                break
    except Exception:
        pass

    pe_ratio = "N/A"
    pb_ratio = "N/A"

    # Use annual EPS from financial abstract for trailing PE
    if abstract_df is not None and current_price != "N/A":
        # Get the latest full-year (1231) EPS
        annual_eps = _get_annual_value(abstract_df, "常用指标", "基本每股收益")
        annual_bvps = _get_abstract_value(abstract_df, "常用指标", "每股净资产")

        if annual_eps != "N/A" and annual_eps != 0:
            pe_ratio = round(current_price / annual_eps, 2)
        if annual_bvps != "N/A" and annual_bvps != 0:
            pb_ratio = round(current_price / annual_bvps, 2)
    elif indicator_df is not None and not indicator_df.empty and current_price != "N/A":
        # Fallback: use indicator_df (may be quarterly)
        eps = _safe_float(indicator_df.iloc[0].get("摊薄每股收益(元)"))
        bvps = _safe_float(indicator_df.iloc[0].get("每股净资产_调整前(元)"))
        if eps != "N/A" and eps != 0:
            pe_ratio = round(current_price / eps, 2)
        if bvps != "N/A" and bvps != 0:
            pb_ratio = round(current_price / bvps, 2)

    result["valuation"] = {
        "market_cap": market_cap,
        "float_market_cap": float_market_cap,
        "trailing_pe": pe_ratio,
        "forward_pe": "N/A",
        "peg_ratio": "N/A",
        "price_to_book": pb_ratio,
        "price_to_sales": "N/A",
        "ev_to_revenue": "N/A",
        "ev_to_ebitda": "N/A",
    }

    # --- Profitability ---
    if abstract_df is not None:
        gross_margin = _get_abstract_value(abstract_df, "常用指标", "毛利率")
        roe = _get_abstract_value(abstract_df, "常用指标", "净资产收益率(ROE)")
        roa = _get_abstract_value(abstract_df, "常用指标", "总资产报酬率(ROA)")
        net_margin = _get_abstract_value(abstract_df, "常用指标", "销售净利率")
        operating_margin = _get_abstract_value(abstract_df, "盈利能力", "营业利润率")

        result["profitability"] = {
            "profit_margin": _pct_to_ratio(net_margin),
            "operating_margin": _pct_to_ratio(operating_margin),
            "gross_margin": _pct_to_ratio(gross_margin),
            "roe": _pct_to_ratio(roe),
            "roa": _pct_to_ratio(roa),
        }
    else:
        result["profitability"] = {k: "N/A" for k in
                                    ["profit_margin", "operating_margin", "gross_margin", "roe", "roa"]}

    # --- Growth ---
    if abstract_df is not None:
        rev_growth = _get_abstract_value(abstract_df, "成长能力", "营业总收入增长率")
        profit_growth = _get_abstract_value(abstract_df, "成长能力", "归属母公司净利润增长率")
        # Also compute from raw figures
        rev_growth_calc = _get_growth_rate(abstract_df, "常用指标", "营业总收入")
        profit_growth_calc = _get_growth_rate(abstract_df, "常用指标", "归母净利润")

        result["growth"] = {
            "revenue_growth": _pct_to_ratio(rev_growth) if rev_growth != "N/A" else rev_growth_calc,
            "earnings_growth": _pct_to_ratio(profit_growth) if profit_growth != "N/A" else profit_growth_calc,
            "earnings_quarterly_growth": "N/A",
        }
    else:
        result["growth"] = {k: "N/A" for k in
                            ["revenue_growth", "earnings_growth", "earnings_quarterly_growth"]}

    # --- Financial health ---
    if abstract_df is not None:
        current_ratio = _get_abstract_value(abstract_df, "财务风险", "流动比率")
        quick_ratio = _get_abstract_value(abstract_df, "财务风险", "速动比率")
        debt_ratio = _get_abstract_value(abstract_df, "常用指标", "资产负债率")
        equity = _get_abstract_value(abstract_df, "常用指标", "股东权益合计(净资产)")
        ocf = _get_abstract_value(abstract_df, "常用指标", "经营现金流量净额")

        # debt_to_equity = debt_ratio / (1 - debt_ratio) * 100 if debt_ratio is available
        dte = "N/A"
        if debt_ratio != "N/A":
            dr = debt_ratio / 100.0 if debt_ratio > 1 else debt_ratio
            if dr < 1:
                dte = round(dr / (1 - dr) * 100, 2)

        result["financial_health"] = {
            "total_cash": "N/A",
            "total_debt": "N/A",
            "debt_to_equity": dte,
            "asset_liability_ratio": debt_ratio,
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "free_cashflow": "N/A",
            "operating_cashflow": ocf,
            "net_assets": equity,
        }
    else:
        result["financial_health"] = {k: "N/A" for k in
                                       ["total_cash", "total_debt", "debt_to_equity",
                                        "asset_liability_ratio", "current_ratio", "quick_ratio",
                                        "free_cashflow", "operating_cashflow", "net_assets"]}

    # --- Dividends ---
    result["dividends"] = {
        "dividend_yield": "N/A",
        "dividend_rate": "N/A",
        "payout_ratio": "N/A",
    }
    if indicator_df is not None and not indicator_df.empty:
        payout = _safe_float(indicator_df.iloc[0].get("股息发放率(%)"))
        result["dividends"]["payout_ratio"] = _pct_to_ratio(payout)

    # --- Analyst targets (not available from akshare basic APIs) ---
    result["analyst_targets"] = {
        "target_high": "N/A",
        "target_low": "N/A",
        "target_mean": "N/A",
        "target_median": "N/A",
        "recommendation": "N/A",
        "num_analysts": "N/A",
    }

    # --- Income statement (from financial abstract) ---
    if abstract_df is not None:
        revenue, rev_period = _get_abstract_value_and_period(abstract_df, "常用指标", "营业总收入")
        cost = _get_abstract_value(abstract_df, "常用指标", "营业成本")
        net_profit = _get_abstract_value(abstract_df, "常用指标", "净利润")
        net_profit_parent = _get_abstract_value(abstract_df, "常用指标", "归母净利润")
        deducted_profit = _get_abstract_value(abstract_df, "常用指标", "扣非净利润")
        eps_basic = _get_abstract_value(abstract_df, "常用指标", "基本每股收益")

        gross_profit = "N/A"
        if revenue != "N/A" and cost != "N/A":
            gross_profit = round(revenue - cost, 2)

        result["income_statement"] = {
            "reporting_period": rev_period,
            "total_revenue": revenue,
            "operating_cost": cost,
            "gross_profit": gross_profit,
            "net_income": net_profit,
            "net_income_to_parent": net_profit_parent,
            "net_income_deducted": deducted_profit,
            "eps_basic": eps_basic,
            "eps_diluted": "N/A",
            "operating_income": "N/A",
            "ebitda": "N/A",
        }
    else:
        result["income_statement"] = "Unable to fetch"

    # --- Balance sheet (from financial abstract) ---
    if abstract_df is not None:
        equity_val = _get_abstract_value(abstract_df, "常用指标", "股东权益合计(净资产)")
        goodwill = _get_abstract_value(abstract_df, "常用指标", "商誉")
        bvps = _get_abstract_value(abstract_df, "常用指标", "每股净资产")

        result["balance_sheet"] = {
            "total_assets": "N/A",
            "stockholders_equity": equity_val,
            "goodwill": goodwill,
            "book_value_per_share": bvps,
            "cash_and_equivalents": "N/A",
            "total_debt_bs": "N/A",
        }

        # Try to get total_assets from indicator_df
        if indicator_df is not None and not indicator_df.empty:
            total_assets = _safe_float(indicator_df.iloc[0].get("总资产(元)"))
            result["balance_sheet"]["total_assets"] = total_assets
    else:
        result["balance_sheet"] = "Unable to fetch"

    # --- Cash flow (from financial abstract) ---
    if abstract_df is not None:
        ocf_val = _get_abstract_value(abstract_df, "常用指标", "经营现金流量净额")
        ocf_per_share = _get_abstract_value(abstract_df, "常用指标", "每股现金流")

        result["cashflow"] = {
            "operating_cashflow": ocf_val,
            "operating_cashflow_per_share": ocf_per_share,
            "investing_cashflow": "N/A",
            "financing_cashflow": "N/A",
            "free_cashflow_cf": "N/A",
            "capex": "N/A",
        }
    else:
        result["cashflow"] = "Unable to fetch"

    # --- Per-share metrics ---
    if abstract_df is not None:
        result["per_share"] = {
            "eps_basic": _get_abstract_value(abstract_df, "常用指标", "基本每股收益"),
            "bvps": _get_abstract_value(abstract_df, "常用指标", "每股净资产"),
            "ocf_per_share": _get_abstract_value(abstract_df, "常用指标", "每股现金流"),
            "undistributed_profit_per_share": _get_abstract_value(abstract_df, "每股指标", "每股未分配利润"),
        }

    # --- Key ratios summary ---
    if abstract_df is not None:
        result["key_ratios"] = {
            "roe": _get_abstract_value(abstract_df, "常用指标", "净资产收益率(ROE)"),
            "roa": _get_abstract_value(abstract_df, "常用指标", "总资产报酬率(ROA)"),
            "gross_margin_pct": _get_abstract_value(abstract_df, "常用指标", "毛利率"),
            "net_margin_pct": _get_abstract_value(abstract_df, "常用指标", "销售净利率"),
            "expense_ratio_pct": _get_abstract_value(abstract_df, "常用指标", "期间费用率"),
            "asset_liability_ratio_pct": _get_abstract_value(abstract_df, "常用指标", "资产负债率"),
            "current_ratio": _get_abstract_value(abstract_df, "财务风险", "流动比率"),
            "quick_ratio": _get_abstract_value(abstract_df, "财务风险", "速动比率"),
            "inventory_turnover_days": _get_abstract_value(abstract_df, "营运能力", "存货周转天数"),
            "receivable_turnover_days": _get_abstract_value(abstract_df, "营运能力", "应收账款周转天数"),
        }

    # --- Fund Flow / 资金流向 (L5) ---
    try:
        fund_flow = ak.stock_individual_fund_flow(stock=code, market="sh" if exchange == ".SS" else "sz")
        if fund_flow is not None and not fund_flow.empty:
            recent_flow = fund_flow.tail(5)
            result["fund_flow"] = recent_flow.to_dict(orient="records")
    except Exception:
        result["fund_flow"] = "Unable to fetch"

    # --- Margin Trading / 融资融券 (L5) ---
    try:
        if exchange == ".SS":
            margin = ak.stock_margin_detail_sse(date="recent")
        else:
            margin = ak.stock_margin_detail_szse(date="recent")
        if margin is not None and not margin.empty:
            stock_margin = margin[margin["标的证券代码"] == code]
            if not stock_margin.empty:
                result["margin_trading"] = stock_margin.head(5).to_dict(orient="records")
    except Exception:
        result["margin_trading"] = "Unable to fetch"

    return result


def _pct_to_ratio(val):
    """Convert percentage value to ratio (e.g., 50.0 -> 0.5). Pass through N/A."""
    if val == "N/A" or val is None:
        return "N/A"
    try:
        v = float(val)
        if abs(v) > 1:
            # Likely already a percentage, convert to ratio
            return round(v / 100.0, 4)
        return v
    except (ValueError, TypeError):
        return "N/A"


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fetch_ashare_fundamentals.py TICKER")
        print()
        print("  TICKER:  A-share code (e.g. 600519, 000858, 300750.SZ)")
        print()
        print("  Output is JSON compatible with fetch_fundamentals.py")
        sys.exit(1)

    ticker = sys.argv[1]
    data = fetch_ashare_fundamentals(ticker)
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
