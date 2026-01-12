#!/usr/bin/env python3
"""
S&P 500 All-Time High Analysis Script

This script tests the viral claim that "investing at all-time highs yields
better results than investing on any day" for the S&P 500.

The claim from the viral tweet:
- 1 year: 11.9% (any day) vs 13.7% (at new high)
- 2 year: 24.9% (any day) vs 28.9% (at new high)
- 3 year: 40.2% (any day) vs 48.0% (at new high)

Usage:
    python sp500_ath_analysis.py                    # Download from yfinance
    python sp500_ath_analysis.py --csv data.csv    # Load from CSV file
    python sp500_ath_analysis.py --demo            # Run with simulated data

Requirements:
    pip install yfinance pandas numpy
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def download_sp500_data(years_of_history: int = 20) -> pd.DataFrame:
    """
    Download S&P 500 historical data using yfinance.

    Args:
        years_of_history: Number of years of historical data to download.
                         Default is 20 years to ensure enough 3-year forward periods.

    Returns:
        DataFrame with S&P 500 daily price data.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("Error: yfinance not installed. Install with: pip install yfinance")
        return pd.DataFrame()

    print(f"Downloading {years_of_history} years of S&P 500 data...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=years_of_history * 365)

    try:
        # ^GSPC is the Yahoo Finance ticker for S&P 500
        sp500 = yf.download("^GSPC", start=start_date, end=end_date, progress=False)

        if sp500.empty:
            print("Warning: No data received from yfinance.")
            return pd.DataFrame()

        print(f"Downloaded {len(sp500)} trading days from {sp500.index[0].date()} to {sp500.index[-1].date()}")
        return sp500

    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()


def load_csv_data(filepath: str) -> pd.DataFrame:
    """
    Load S&P 500 data from a CSV file.

    Expected CSV format:
    - Date column (will be used as index)
    - Close column (closing price)

    Args:
        filepath: Path to the CSV file.

    Returns:
        DataFrame with S&P 500 daily price data.
    """
    print(f"Loading data from {filepath}...")

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return pd.DataFrame()

    try:
        # Try to read with common date column names
        df = pd.read_csv(filepath, parse_dates=True, index_col=0)

        # Ensure we have a Close column
        if 'Close' not in df.columns and 'close' in df.columns:
            df['Close'] = df['close']
        elif 'Close' not in df.columns and 'Adj Close' in df.columns:
            df['Close'] = df['Adj Close']

        if 'Close' not in df.columns:
            print("Error: CSV must contain a 'Close' column")
            return pd.DataFrame()

        # Sort by date
        df = df.sort_index()

        print(f"Loaded {len(df)} trading days from {df.index[0].date()} to {df.index[-1].date()}")
        return df

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return pd.DataFrame()


def generate_demo_data(years: int = 20, seed: int = 42) -> pd.DataFrame:
    """
    Generate simulated S&P 500-like data for demonstration purposes.

    Uses a geometric Brownian motion model with parameters calibrated to
    approximate historical S&P 500 behavior (approximately 10% annual return
    with ~16% annual volatility).

    Args:
        years: Number of years of data to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with simulated daily price data.
    """
    print(f"Generating {years} years of simulated S&P 500-like data for demonstration...")
    print("Note: This is SIMULATED data - use real data for actual analysis!")

    np.random.seed(seed)

    # Parameters calibrated to approximate S&P 500 historical behavior
    trading_days_per_year = 252
    total_days = years * trading_days_per_year

    annual_return = 0.10  # 10% average annual return
    annual_volatility = 0.16  # 16% annual volatility

    # Convert to daily parameters
    daily_return = annual_return / trading_days_per_year
    daily_volatility = annual_volatility / np.sqrt(trading_days_per_year)

    # Generate daily returns using geometric Brownian motion
    daily_returns = np.random.normal(daily_return, daily_volatility, total_days)

    # Starting price (arbitrary, similar to S&P 500 level ~20 years ago)
    start_price = 1000

    # Calculate cumulative price path
    prices = start_price * np.cumprod(1 + daily_returns)

    # Create date index (exclude weekends approximately)
    end_date = datetime.now()
    dates = pd.date_range(end=end_date, periods=total_days, freq='B')  # Business days

    # Create DataFrame
    df = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.005, 0.005, total_days)),
        'High': prices * (1 + np.random.uniform(0, 0.015, total_days)),
        'Low': prices * (1 - np.random.uniform(0, 0.015, total_days)),
        'Close': prices,
        'Volume': np.random.randint(1000000000, 5000000000, total_days)
    }, index=dates)

    print(f"Generated {len(df)} trading days from {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Starting price: ${start_price:.2f}, Ending price: ${prices[-1]:.2f}")

    return df


def identify_all_time_highs(df: pd.DataFrame) -> pd.Series:
    """
    Identify days where the closing price was at an all-time high.

    An all-time high is defined as a day where the close price is greater than
    or equal to the maximum of all prior closing prices.

    Args:
        df: DataFrame with 'Close' column containing daily closing prices.

    Returns:
        Boolean Series indicating which days were all-time highs.
    """
    # Handle both single-level and multi-level column indices
    if isinstance(df.columns, pd.MultiIndex):
        close_prices = df['Close'].iloc[:, 0]  # Get the first (and only) ticker
    else:
        close_prices = df['Close']

    # Calculate cumulative maximum up to each day
    cummax = close_prices.expanding().max()

    # A day is an ATH if the close equals the cumulative max
    is_ath = close_prices >= cummax

    return is_ath


def calculate_forward_returns(df: pd.DataFrame, periods_days: dict) -> pd.DataFrame:
    """
    Calculate forward returns for specified holding periods.

    Args:
        df: DataFrame with 'Close' column.
        periods_days: Dictionary mapping period names to number of trading days.
                     e.g., {'1_year': 252, '2_year': 504, '3_year': 756}

    Returns:
        DataFrame with forward return columns for each period.
    """
    # Handle both single-level and multi-level column indices
    if isinstance(df.columns, pd.MultiIndex):
        close_prices = df['Close'].iloc[:, 0]
    else:
        close_prices = df['Close']

    returns_df = pd.DataFrame(index=df.index)

    for period_name, days in periods_days.items():
        # Calculate forward return: (future_price / current_price - 1) * 100
        future_prices = close_prices.shift(-days)
        forward_return = ((future_prices / close_prices) - 1) * 100
        returns_df[f'return_{period_name}'] = forward_return

    return returns_df


def analyze_returns(df: pd.DataFrame, is_ath: pd.Series, periods: list) -> dict:
    """
    Analyze returns for all days vs all-time high days.

    Args:
        df: DataFrame with forward return columns.
        is_ath: Boolean Series indicating all-time high days.
        periods: List of period names (e.g., ['1_year', '2_year', '3_year']).

    Returns:
        Dictionary containing analysis results.
    """
    results = {}

    for period in periods:
        col = f'return_{period}'

        # Filter out NaN values (days without enough forward data)
        all_days_returns = df[col].dropna()
        ath_days_returns = df.loc[is_ath, col].dropna()

        results[period] = {
            'all_days': {
                'count': len(all_days_returns),
                'mean': all_days_returns.mean(),
                'std': all_days_returns.std(),
                'median': all_days_returns.median(),
                'min': all_days_returns.min(),
                'max': all_days_returns.max(),
                'positive_pct': (all_days_returns > 0).mean() * 100,
            },
            'ath_days': {
                'count': len(ath_days_returns),
                'mean': ath_days_returns.mean(),
                'std': ath_days_returns.std(),
                'median': ath_days_returns.median(),
                'min': ath_days_returns.min(),
                'max': ath_days_returns.max(),
                'positive_pct': (ath_days_returns > 0).mean() * 100,
            }
        }

    return results


def print_results(results: dict, tweet_claims: dict, is_demo: bool = False):
    """
    Print formatted results comparing analysis to tweet claims.

    Args:
        results: Dictionary containing analysis results.
        tweet_claims: Dictionary containing the claimed values from the tweet.
        is_demo: Whether the results are from demo/simulated data.
    """
    print("\n" + "=" * 80)
    print("S&P 500 ALL-TIME HIGH INVESTMENT ANALYSIS")
    if is_demo:
        print("*** USING SIMULATED DATA FOR DEMONSTRATION ***")
    print("=" * 80)

    print("\n" + "-" * 80)
    print("COMPARISON TABLE: Average Forward Returns (%)")
    print("-" * 80)

    header = f"{'Period':<12} | {'Any Day':<12} | {'At ATH':<12} | {'Diff':<10} | {'Tweet Any':<12} | {'Tweet ATH':<12}"
    print(header)
    print("-" * 80)

    period_labels = {
        '1_year': '1 Year',
        '2_year': '2 Year',
        '3_year': '3 Year'
    }

    for period in ['1_year', '2_year', '3_year']:
        any_day = results[period]['all_days']['mean']
        at_ath = results[period]['ath_days']['mean']
        diff = at_ath - any_day
        tweet_any = tweet_claims[period]['any_day']
        tweet_ath = tweet_claims[period]['at_ath']

        row = f"{period_labels[period]:<12} | {any_day:>10.1f}% | {at_ath:>10.1f}% | {diff:>+8.1f}% | {tweet_any:>10.1f}% | {tweet_ath:>10.1f}%"
        print(row)

    print("-" * 80)

    # Sample sizes
    print("\n" + "-" * 80)
    print("SAMPLE SIZES")
    print("-" * 80)

    for period in ['1_year', '2_year', '3_year']:
        all_n = results[period]['all_days']['count']
        ath_n = results[period]['ath_days']['count']
        ath_pct = (ath_n / all_n) * 100 if all_n > 0 else 0
        print(f"{period_labels[period]}: {all_n:,} total days | {ath_n:,} ATH days ({ath_pct:.1f}%)")

    # Standard deviations
    print("\n" + "-" * 80)
    print("VOLATILITY: Standard Deviation of Returns (%)")
    print("-" * 80)

    header = f"{'Period':<12} | {'Any Day Std':<15} | {'ATH Day Std':<15}"
    print(header)
    print("-" * 50)

    for period in ['1_year', '2_year', '3_year']:
        any_std = results[period]['all_days']['std']
        ath_std = results[period]['ath_days']['std']
        row = f"{period_labels[period]:<12} | {any_std:>13.1f}% | {ath_std:>13.1f}%"
        print(row)

    # Positive return percentage
    print("\n" + "-" * 80)
    print("PROBABILITY OF POSITIVE RETURNS (%)")
    print("-" * 80)

    header = f"{'Period':<12} | {'Any Day':<15} | {'At ATH':<15}"
    print(header)
    print("-" * 50)

    for period in ['1_year', '2_year', '3_year']:
        any_pos = results[period]['all_days']['positive_pct']
        ath_pos = results[period]['ath_days']['positive_pct']
        row = f"{period_labels[period]:<12} | {any_pos:>13.1f}% | {ath_pos:>13.1f}%"
        print(row)

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT: Does the viral tweet claim hold up?")
    print("=" * 80)

    claim_supported = True
    for period in ['1_year', '2_year', '3_year']:
        any_day = results[period]['all_days']['mean']
        at_ath = results[period]['ath_days']['mean']

        if at_ath > any_day:
            status = "SUPPORTED"
            symbol = "[YES]"
        else:
            status = "NOT SUPPORTED"
            symbol = "[NO]"
            claim_supported = False

        print(f"{period_labels[period]}: ATH returns ({at_ath:.1f}%) > Any day returns ({any_day:.1f}%)? {symbol} {status}")

    print("\n" + "-" * 80)
    if claim_supported:
        print("CONCLUSION: The viral tweet's claim IS SUPPORTED by the data!")
        print("Investing at all-time highs historically yielded better average returns")
        print("than investing on any random day for all three time periods.")
    else:
        print("CONCLUSION: The viral tweet's claim is NOT fully supported by the data.")
        print("At least one time period shows investing at ATH did not outperform.")
    print("-" * 80)

    # Additional context
    print("\n" + "-" * 80)
    print("IMPORTANT CAVEATS")
    print("-" * 80)
    print("1. Past performance does not guarantee future results")
    print("2. This analysis uses historical data which may not reflect future market conditions")
    print("3. Transaction costs, taxes, and inflation are not considered")
    print("4. The analysis assumes buy-and-hold strategy with no rebalancing")
    print("5. Results may vary depending on the exact date range analyzed")
    if is_demo:
        print("6. *** This analysis used SIMULATED data - results are for demonstration only ***")
    print("-" * 80)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze S&P 500 returns: All-time highs vs any day',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sp500_ath_analysis.py              # Download data from yfinance
  python sp500_ath_analysis.py --csv sp500.csv  # Load data from CSV file
  python sp500_ath_analysis.py --demo       # Use simulated data for demo
  python sp500_ath_analysis.py --years 30   # Download 30 years of data
        """
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Path to CSV file with S&P 500 data (must have Date index and Close column)'
    )

    parser.add_argument(
        '--demo',
        action='store_true',
        help='Use simulated data for demonstration (when network unavailable)'
    )

    parser.add_argument(
        '--years',
        type=int,
        default=20,
        help='Years of historical data to analyze (default: 20)'
    )

    return parser.parse_args()


def main():
    """Main function to run the S&P 500 ATH analysis."""

    args = parse_arguments()

    # Define holding periods in trading days (approximately 252 trading days per year)
    periods_days = {
        '1_year': 252,
        '2_year': 504,
        '3_year': 756
    }

    # Tweet claims for comparison
    tweet_claims = {
        '1_year': {'any_day': 11.9, 'at_ath': 13.7},
        '2_year': {'any_day': 24.9, 'at_ath': 28.9},
        '3_year': {'any_day': 40.2, 'at_ath': 48.0},
    }

    is_demo = False

    # Step 1: Load data based on source
    if args.csv:
        df = load_csv_data(args.csv)
    elif args.demo:
        df = generate_demo_data(years=args.years)
        is_demo = True
    else:
        # Try to download, fall back to demo if it fails
        df = download_sp500_data(years_of_history=args.years)
        if df.empty:
            print("\n" + "=" * 60)
            print("Could not download data. Running with simulated data instead.")
            print("Use --csv to load from a file, or --demo to explicitly use simulation.")
            print("=" * 60 + "\n")
            df = generate_demo_data(years=args.years)
            is_demo = True

    if df.empty:
        print("Error: No data available. Please check your data source.")
        return None

    # Step 2: Identify all-time highs
    print("\nIdentifying all-time highs...")
    is_ath = identify_all_time_highs(df)
    total_ath_days = is_ath.sum()
    print(f"Found {total_ath_days:,} all-time high days out of {len(df):,} total trading days ({100*total_ath_days/len(df):.1f}%)")

    # Step 3: Calculate forward returns
    print("\nCalculating forward returns for 1, 2, and 3 year periods...")
    returns_df = calculate_forward_returns(df, periods_days)

    # Step 4: Analyze returns
    print("Analyzing returns for all days vs ATH days...")
    results = analyze_returns(returns_df, is_ath, list(periods_days.keys()))

    # Step 5: Print results
    print_results(results, tweet_claims, is_demo)

    return results


if __name__ == "__main__":
    main()
