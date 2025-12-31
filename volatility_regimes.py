"""
SPY Volatility Regime Visualization

This script downloads SPY data, computes volatility regimes, and visualizes
price movements with regime shading.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from datetime import datetime


def download_spy_data(start_date='2010-01-01'):
    """
    Download daily adjusted close price data for SPY.
    
    Parameters:
    -----------
    start_date : str
        Start date for data download (YYYY-MM-DD format)
    
    Returns:
    --------
    pd.Series
        Adjusted close prices indexed by date
    """
    print(f"Downloading SPY data from {start_date} to present...")
    ticker = yf.Ticker("SPY")
    data = ticker.history(start=start_date)
    
    if data.empty:
        raise ValueError("No data downloaded. Check date range and ticker symbol.")
    
    return data['Close']


def compute_log_returns(prices):
    """
    Compute daily log returns from price series.
    
    Parameters:
    -----------
    prices : pd.Series
        Price series
    
    Returns:
    --------
    pd.Series
        Daily log returns
    """
    return np.log(prices / prices.shift(1)).dropna()


def compute_rolling_volatility(returns, window=30):
    """
    Compute rolling annualized volatility.
    
    Parameters:
    -----------
    returns : pd.Series
        Daily log returns
    window : int
        Rolling window size in days (default: 30)
    
    Returns:
    --------
    pd.Series
        Annualized volatility (252 trading days per year)
    """
    # Compute rolling standard deviation and annualize
    rolling_std = returns.rolling(window=window).std()
    annualized_vol = rolling_std * np.sqrt(252)
    return annualized_vol


def classify_volatility_regimes(volatility):
    """
    Classify volatility into three regimes based on percentiles.
    
    Parameters:
    -----------
    volatility : pd.Series
        Rolling volatility series
    
    Returns:
    --------
    pd.Series
        Regime labels: 'Low', 'Medium', 'High'
    """
    # Compute 33rd and 67th percentiles
    p33 = volatility.quantile(0.33)
    p67 = volatility.quantile(0.67)
    
    # Classify regimes
    regimes = pd.Series(index=volatility.index, dtype='object')
    regimes[volatility <= p33] = 'Low'
    regimes[(volatility > p33) & (volatility <= p67)] = 'Medium'
    regimes[volatility > p67] = 'High'
    
    return regimes


def plot_volatility_regimes(prices, regimes, output_dir='outputs'):
    """
    Create visualization with price plot and regime shading.
    
    Parameters:
    -----------
    prices : pd.Series
        Price series
    regimes : pd.Series
        Regime classification series
    output_dir : str
        Directory to save the figure
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Align prices and regimes on same index
    common_index = prices.index.intersection(regimes.index)
    prices_aligned = prices.loc[common_index]
    regimes_aligned = regimes.loc[common_index]
    
    # Plot price line
    ax.plot(prices_aligned.index, prices_aligned.values, 
            color='black', linewidth=1.5, label='SPY Price', zorder=3)
    
    # Shade background by regime
    regime_colors = {'Low': '#90EE90', 'Medium': '#FFD700', 'High': '#FF6B6B'}
    
    # Create shading regions for consecutive periods with same regime
    dates_list = list(common_index)
    current_regime = None
    start_idx = 0
    
    for i, date in enumerate(dates_list):
        regime = regimes_aligned.loc[date]
        
        if pd.isna(regime):
            continue
            
        if regime != current_regime:
            # End previous region if it exists
            if current_regime is not None and i > start_idx:
                ax.axvspan(dates_list[start_idx], date, 
                          color=regime_colors[current_regime], 
                          alpha=0.3, zorder=0)
            # Start new region
            current_regime = regime
            start_idx = i
    
    # Handle final region
    if current_regime is not None and start_idx < len(dates_list):
        ax.axvspan(dates_list[start_idx], dates_list[-1], 
                  color=regime_colors[current_regime], 
                  alpha=0.3, zorder=0)
    
    # Formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('SPY Price (USD)', fontsize=12, fontweight='bold')
    ax.set_title('SPY Price with Volatility Regimes (2010-Present)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', zorder=1)
    
    # Create legend
    legend_elements = [
        mpatches.Patch(facecolor='#90EE90', alpha=0.3, label='Low Volatility'),
        mpatches.Patch(facecolor='#FFD700', alpha=0.3, label='Medium Volatility'),
        mpatches.Patch(facecolor='#FF6B6B', alpha=0.3, label='High Volatility'),
        plt.Line2D([0], [0], color='black', linewidth=1.5, label='SPY Price')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
    
    # Rotate x-axis labels for readability
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save figure
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    filename = output_path / 'spy_volatility_regimes.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nFigure saved to: {filename}")
    
    plt.close()


def print_summary_statistics(regimes):
    """
    Print summary statistics for volatility regimes.
    
    Parameters:
    -----------
    regimes : pd.Series
        Regime classification series
    """
    print("\n" + "="*50)
    print("Volatility Regime Summary Statistics")
    print("="*50)
    
    regime_counts = regimes.value_counts()
    total_days = len(regimes)
    
    for regime in ['Low', 'Medium', 'High']:
        count = regime_counts.get(regime, 0)
        percentage = (count / total_days) * 100
        print(f"{regime:10s} Volatility: {count:5d} days ({percentage:5.2f}%)")
    
    print("="*50 + "\n")


def main():
    """Main execution function."""
    # Download data
    prices = download_spy_data(start_date='2010-01-01')
    
    # Feature engineering
    returns = compute_log_returns(prices)
    volatility = compute_rolling_volatility(returns, window=30)
    
    # Regime classification
    regimes = classify_volatility_regimes(volatility)
    
    # Print summary statistics
    print_summary_statistics(regimes)
    
    # Create visualization
    plot_volatility_regimes(prices, regimes, output_dir='outputs')
    
    print("Analysis complete!")


if __name__ == "__main__":
    main()

