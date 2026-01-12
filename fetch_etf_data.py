#!/usr/bin/env python3
"""
Fetch historical data for UPRO, TECL, TQQ (leveraged ETFs)
Run this script locally to download data, then use with sp500_ath_analysis.py

Usage:
    python fetch_etf_data.py
    python sp500_ath_analysis.py --csv upro_data.csv
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

TICKERS = {
    'UPRO': 'ProShares UltraPro S&P500 (3x)',
    'TECL': 'Direxion Daily Technology Bull 3x',
    'TQQ': 'ProShares UltraPro QQQ (3x)',  # Note: TQQ doesn't exist, TQQQ does
    'TQQQ': 'ProShares UltraPro QQQ (3x)',
    '^GSPC': 'S&P 500 Index',
}

def fetch_data(ticker, years=10):
    """Fetch historical data for a ticker."""
    print(f"Fetching {ticker} ({TICKERS.get(ticker, 'Unknown')})...")

    try:
        data = yf.download(ticker, period=f"{years}y", progress=False)

        if len(data) == 0:
            print(f"  No data for {ticker}")
            return None

        # Clean up column names if MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        print(f"  Got {len(data)} days: {data.index[0].date()} to {data.index[-1].date()}")
        print(f"  Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")

        return data

    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("=" * 60)
    print("Fetching Leveraged ETF Historical Data")
    print("=" * 60)
    print()

    results = {}

    # Fetch all tickers
    for ticker in ['UPRO', 'TECL', 'TQQQ', '^GSPC']:
        data = fetch_data(ticker, years=15)
        if data is not None:
            results[ticker] = data

            # Save to CSV
            filename = f"{ticker.replace('^', '')}_data.csv".lower()

            # Prepare clean DataFrame
            clean_df = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            clean_df.index.name = 'Date'
            clean_df.to_csv(filename)
            print(f"  Saved to {filename}")
        print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)

    for ticker, data in results.items():
        filename = f"{ticker.replace('^', '')}_data.csv".lower()
        print(f"{ticker}: {len(data)} days -> {filename}")

    print()
    print("To analyze with the ATH script:")
    print("  python sp500_ath_analysis.py --csv gspc_data.csv")
    print("  python sp500_ath_analysis.py --csv upro_data.csv")
    print("  python sp500_ath_analysis.py --csv tecl_data.csv")
    print("  python sp500_ath_analysis.py --csv tqqq_data.csv")

if __name__ == "__main__":
    main()
