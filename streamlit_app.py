"""
Streamlit Web Dashboard for Volatility Regime Analysis

Interactive dashboard for visualizing market volatility regimes.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

# Page config must be first Streamlit command
st.set_page_config(
    page_title="Volatility Regime Analyzer",
    page_icon="📊",
    layout="wide"
)


@st.cache_data(ttl=7200)  # Cache for 2 hours to reduce API calls
def load_data(ticker, start_date='2010-01-01', max_retries=3):
    """
    Download price data for the given ticker with retry logic.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    start_date : str
        Start date for data download
    max_retries : int
        Maximum number of retry attempts
    
    Returns:
    --------
    pd.Series
        Adjusted close prices indexed by date
    """
    for attempt in range(max_retries):
        try:
            # Add delay before each attempt to avoid rate limiting
            if attempt > 0:
                wait_time = (2 ** attempt) * 3  # Exponential backoff: 6s, 12s, 24s
                time.sleep(wait_time)
            else:
                # Small delay even on first attempt to be respectful
                time.sleep(0.5)
            
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(start=start_date, progress=False)
            
            if data.empty:
                # Try with a shorter period if full history fails
                if attempt < max_retries - 1:
                    continue
                return None
            
            return data['Close']
            
        except Exception as e:
            error_msg = str(e).lower()
            error_str = str(e)
            
            # Handle rate limiting specifically - check multiple variations
            is_rate_limit = (
                'rate limit' in error_msg or 
                'too many requests' in error_msg or
                '429' in error_str or
                'rate limited' in error_msg
            )
            
            if is_rate_limit:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5  # Wait 5s, 10s, 20s
                    # Only show warning on first retry to avoid spam
                    if attempt == 0:
                        try:
                            st.warning(f"⏳ Rate limited. Retrying in {wait_time} seconds...")
                        except:
                            pass  # If not in Streamlit context, skip
                    time.sleep(wait_time)
                    continue
                else:
                    # All retries failed
                    try:
                        st.error(
                            "⚠️ **Yahoo Finance rate limit reached.**\n\n"
                            "Please wait 1-2 minutes and try again. "
                            "The app caches data for 1 hour to reduce API calls."
                        )
                    except:
                        pass
                    return None
            
            # Handle other errors (only show on final attempt, and never for rate limits)
            if attempt == max_retries - 1:
                # Never show raw error messages for rate limits
                if not is_rate_limit:
                    try:
                        st.error(f"Error downloading data for {ticker}: {str(e)[:100]}")
                    except:
                        pass
                # For rate limits, we already showed a user-friendly message above
                return None
    
    return None


def compute_returns(prices):
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


def compute_volatility(returns, window=30):
    """
    Compute rolling annualized volatility.
    
    Parameters:
    -----------
    returns : pd.Series
        Daily log returns
    window : int
        Rolling window size in days
    
    Returns:
    --------
    pd.Series
        Annualized volatility (252 trading days per year)
    """
    rolling_std = returns.rolling(window=window).std()
    annualized_vol = rolling_std * np.sqrt(252)
    return annualized_vol


def classify_regimes(volatility):
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
    p33 = volatility.quantile(0.33)
    p67 = volatility.quantile(0.67)
    
    regimes = pd.Series(index=volatility.index, dtype='object')
    regimes[volatility <= p33] = 'Low'
    regimes[(volatility > p33) & (volatility <= p67)] = 'Medium'
    regimes[volatility > p67] = 'High'
    
    return regimes


def plot_regimes(prices, regimes):
    """
    Create interactive Plotly chart with price and regime shading.
    
    Parameters:
    -----------
    prices : pd.Series
        Price series
    regimes : pd.Series
        Regime classification series
    
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive plotly figure
    """
    # Align prices and regimes
    common_index = prices.index.intersection(regimes.index)
    prices_aligned = prices.loc[common_index]
    regimes_aligned = regimes.loc[common_index]
    
    # Create figure
    fig = go.Figure()
    
    # Define regime colors
    regime_colors = {
        'Low': 'rgba(144, 238, 144, 0.3)',      # Light green
        'Medium': 'rgba(255, 215, 0, 0.3)',     # Gold
        'High': 'rgba(255, 107, 107, 0.3)'      # Light red
    }
    
    # Add background shading for each regime
    # Convert index to list for iteration
    dates_list = list(common_index)
    current_regime = None
    start_date = None
    
    for date in dates_list:
        regime = regimes_aligned.loc[date]
        
        if pd.isna(regime):
            continue
            
        if regime != current_regime:
            # End previous region if it exists
            if current_regime is not None and start_date is not None:
                fig.add_vrect(
                    x0=start_date,
                    x1=date,
                    fillcolor=regime_colors[current_regime],
                    layer="below",
                    line_width=0,
                )
            # Start new region
            current_regime = regime
            start_date = date
    
    # Handle final region
    if current_regime is not None and start_date is not None:
        fig.add_vrect(
            x0=start_date,
            x1=dates_list[-1],
            fillcolor=regime_colors[current_regime],
            layer="below",
            line_width=0,
        )
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=prices_aligned.index,
        y=prices_aligned.values,
        mode='lines',
        name='Price',
        line=dict(color='black', width=2),
        hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': f'{prices_aligned.index[0].strftime("%Y")}-Present Price with Volatility Regimes',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': 'black'}
        },
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        hovermode='x unified',
        height=600,
        showlegend=False,
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
        yaxis=dict(showgrid=True, gridcolor='lightgray', gridwidth=1),
    )
    
    return fig


def get_regime_stats(regimes):
    """
    Calculate summary statistics for volatility regimes.
    
    Parameters:
    -----------
    regimes : pd.Series
        Regime classification series
    
    Returns:
    --------
    dict
        Dictionary with regime counts and percentages
    """
    regime_counts = regimes.value_counts()
    total_days = len(regimes)
    
    stats = {}
    for regime in ['Low', 'Medium', 'High']:
        count = regime_counts.get(regime, 0)
        stats[regime] = {
            'count': count,
            'percentage': (count / total_days) * 100 if total_days > 0 else 0
        }
    
    return stats


# Streamlit app
def main():
    
    # Sidebar
    st.sidebar.header("Settings")
    
    ticker = st.sidebar.text_input(
        "Ticker Symbol",
        value="SPY",
        help="Enter a stock ticker symbol (e.g., SPY, AAPL, MSFT)"
    ).upper()
    
    window = st.sidebar.selectbox(
        "Rolling Window (days)",
        options=[20, 30, 60],
        index=1,  # Default to 30
        help="Number of days for rolling volatility calculation"
    )
    
    # Main content
    st.title("Volatility Regime Analyzer")
    st.markdown("""
    This dashboard visualizes market volatility regimes by classifying rolling volatility 
    into three categories:
    - **Low Volatility**: Bottom 33% of volatility distribution
    - **Medium Volatility**: Middle 33%
    - **High Volatility**: Top 33%
    
    The background shading indicates the current volatility regime, helping identify 
    periods of market stability versus turbulence.
    """)
    
    # Info about rate limiting
    with st.expander("ℹ️ About Rate Limiting"):
        st.info(
            "This app uses Yahoo Finance data. If you see rate limit errors, please wait "
            "1-2 minutes before trying again. Data is cached for 2 hours to minimize API calls."
        )
    
    # Load and process data
    if ticker:
        # Use a placeholder to show loading state
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            with st.spinner(f"Loading data for {ticker}..."):
                prices = load_data(ticker)
        
        # Clear any previous error messages
        status_placeholder.empty()
        
        if prices is None or prices.empty:
            st.error(
                f"⚠️ **Could not load data for {ticker}**\n\n"
                "This could be due to:\n"
                "- Rate limiting (please wait 1-2 minutes and try again)\n"
                "- Invalid ticker symbol\n"
                "- Network connectivity issues\n\n"
                "💡 **Tip:** The app caches data for 2 hours. If you just tried multiple tickers, "
                "wait a moment before trying again."
            )
            return
            
            # Compute metrics
            returns = compute_returns(prices)
            volatility = compute_volatility(returns, window=window)
            regimes = classify_regimes(volatility)
            
            # Display summary statistics
            stats = get_regime_stats(regimes)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Low Volatility",
                    f"{stats['Low']['count']} days",
                    f"{stats['Low']['percentage']:.1f}%"
                )
            with col2:
                st.metric(
                    "Medium Volatility",
                    f"{stats['Medium']['count']} days",
                    f"{stats['Medium']['percentage']:.1f}%"
                )
            with col3:
                st.metric(
                    "High Volatility",
                    f"{stats['High']['count']} days",
                    f"{stats['High']['percentage']:.1f}%"
                )
            
            # Create and display plot
            fig = plot_regimes(prices, regimes)
            st.plotly_chart(fig, use_container_width=True)
            
            # Legend
            st.markdown("---")
            st.markdown("### Legend")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("🟢 **Low Volatility**: Bottom 33% of volatility")
            with col2:
                st.markdown("🟡 **Medium Volatility**: Middle 33%")
            with col3:
                st.markdown("🔴 **High Volatility**: Top 33%")
            
            # Data info
            st.markdown("---")
            st.caption(f"Data range: {prices.index[0].strftime('%Y-%m-%d')} to {prices.index[-1].strftime('%Y-%m-%d')} | "
                      f"Total trading days: {len(prices)} | "
                      f"Rolling window: {window} days")


if __name__ == "__main__":
    main()

