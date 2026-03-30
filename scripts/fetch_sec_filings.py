#!/usr/bin/env python3
"""Fetch recent SEC filings for a given US stock ticker.

Usage:
    python3 scripts/fetch_sec_filings.py TICKER [DAYS]

Examples:
    python3 scripts/fetch_sec_filings.py NVDA           # last 90 days (default)
    python3 scripts/fetch_sec_filings.py AAPL 180        # last 180 days
    python3 scripts/fetch_sec_filings.py MSFT 30         # last 30 days

Output: JSON with recent SEC filings (8-K, 10-K, 10-Q, etc.)

Data source: SEC EDGAR full-text search API (free, no API key required).
Note: SEC requires a User-Agent header with company name and contact email.
Rate limit: 10 requests/second.
"""

import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta

# SEC requires identifying User-Agent
SEC_USER_AGENT = "InvestmentResearchBot/1.0 (contact@example.com)"
SEC_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

# 8-K item type descriptions for common event types
ITEM_8K_DESCRIPTIONS = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.04": "Triggering Events (Acceleration of Obligations)",
    "2.05": "Costs Associated with Exit or Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Transfer",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Election of Directors or Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


def fetch_sec_filings(ticker: str, days: int = 90):
    """Fetch recent SEC filings for a US stock ticker.

    Args:
        ticker: US stock ticker symbol (e.g., NVDA, AAPL)
        days: Number of days to look back (default 90)

    Returns:
        dict with filing results
    """
    ticker = ticker.strip().upper()

    # Remove any suffix (e.g., .SS, .SZ, .HK) — SEC only covers US stocks
    if "." in ticker:
        base = ticker.split(".")[0]
        if not base.isalpha():
            return {
                "ticker": ticker,
                "error": "SEC EDGAR only supports US stock tickers. "
                         "For A-shares use cninfo.com.cn, for HK use HKEX.",
                "filings": []
            }
        ticker = base

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Build search URL
    params = {
        "q": f'"{ticker}"',
        "dateRange": "custom",
        "startdt": start_date.strftime("%Y-%m-%d"),
        "enddt": end_date.strftime("%Y-%m-%d"),
        "forms": "8-K,10-K,10-Q,S-1,DEF 14A,SC 13D,SC 13G,4",
    }

    url = f"{SEC_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    result = {
        "ticker": ticker,
        "search_period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "days": days,
        "source": "SEC EDGAR (efts.sec.gov)",
        "filings": [],
    }

    try:
        req = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Try the alternative EDGAR full-text search API
        alt_url = f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(ticker)}&forms=8-K,10-K,10-Q,4"
        try:
            req = urllib.request.Request(alt_url, headers={"User-Agent": SEC_USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            result["error"] = f"SEC EDGAR API error: {e}"
            # Fallback: try EDGAR company search
            return _fallback_company_search(ticker, days, result)
    except Exception as e:
        result["error"] = f"Network error: {e}"
        return _fallback_company_search(ticker, days, result)

    # Parse results
    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        # Try fallback
        return _fallback_company_search(ticker, days, result)

    for hit in hits[:20]:  # Limit to 20 most recent
        source = hit.get("_source", {})
        filing = _parse_filing(source, ticker)
        if filing:
            result["filings"].append(filing)

    result["total_found"] = len(result["filings"])
    return result


def _fallback_company_search(ticker: str, days: int, result: dict):
    """Fallback: use EDGAR company filings API."""
    # Try the submissions API which is more reliable
    cik_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type=&dateb=&owner=include&count=1&search_text=&action=getcompany&output=atom"

    try:
        # Use the EDGAR full-text search with simpler query
        search_url = f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(ticker)}&forms=8-K,10-K,10-Q"
        req = urllib.request.Request(search_url, headers={"User-Agent": SEC_USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        hits = data.get("hits", {}).get("hits", [])
        for hit in hits[:20]:
            source = hit.get("_source", {})
            filing = _parse_filing(source, ticker)
            if filing:
                result["filings"].append(filing)
    except Exception:
        pass

    # If still no results, provide a helpful message
    if not result["filings"]:
        result["note"] = (
            f"No filings found via EDGAR API for '{ticker}'. "
            "This may happen if the ticker doesn't match EDGAR's company name. "
            "Try searching manually at https://www.sec.gov/cgi-bin/browse-edgar"
            f"?company={ticker}&CIK=&type=&dateb=&owner=include&count=40&search_text=&action=getcompany"
        )

    result["total_found"] = len(result["filings"])
    return result


def _parse_filing(source: dict, ticker: str) -> dict:
    """Parse a single filing from EDGAR search results."""
    form_type = source.get("form_type", source.get("file_type", ""))
    filed_date = source.get("file_date", source.get("date_filed", ""))
    company = source.get("entity_name", source.get("display_names", [""])[0] if source.get("display_names") else "")
    description = source.get("display_description", source.get("file_description", ""))

    # Build filing URL
    file_num = source.get("file_num", "")
    accession = source.get("accession_no", source.get("accession_number", ""))

    filing_url = ""
    if accession:
        acc_clean = accession.replace("-", "")
        filing_url = f"https://www.sec.gov/Archives/edgar/data/{acc_clean[:10]}/{accession}"

    filing = {
        "form_type": form_type,
        "filed_date": filed_date,
        "company": company,
        "description": description,
    }

    if filing_url:
        filing["url"] = filing_url

    # For 8-K filings, try to identify the event type
    if form_type == "8-K" and description:
        items = []
        for item_code, item_desc in ITEM_8K_DESCRIPTIONS.items():
            if item_code in description or item_desc.lower() in description.lower():
                items.append(f"Item {item_code}: {item_desc}")
        if items:
            filing["event_types"] = items

    return filing


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/fetch_sec_filings.py TICKER [DAYS]")
        print()
        print("  TICKER:  US stock ticker (e.g., NVDA, AAPL, MSFT)")
        print("  DAYS:    Number of days to look back (default: 90)")
        print()
        print("Output: JSON with recent SEC filings (8-K, 10-K, 10-Q, etc.)")
        print()
        print("Note: Only supports US-listed stocks (SEC EDGAR).")
        print("      For A-shares, search site:cninfo.com.cn via WebSearch.")
        print("      For HK stocks, search HKEX filings via WebSearch.")
        sys.exit(1)

    ticker = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    data = fetch_sec_filings(ticker, days)
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()
