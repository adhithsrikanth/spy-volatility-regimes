import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Volatility Regime Analyzer",
    page_icon="📊",
    layout="wide"
)


@st.cache_data(ttl=21600)
def load_data(ticker, start_date='2010-01-01', max_retries=3):
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = (2 ** attempt) * 3
                time.sleep(wait_time)
            else:
                time.sleep(0.5)
            
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(start=start_date)
            
            if data.empty:
                if attempt < max_retries - 1:
                    try:
                        data = ticker_obj.history(period="5y")
                        if not data.empty:
                            return data['Close']
                    except:
                        pass
                    continue
                return None
            
            return data['Close']
            
        except Exception as e:
            error_msg = str(e).lower()
            error_str = str(e)
            
            is_rate_limit = (
                'rate limit' in error_msg or 
                'too many requests' in error_msg or
                '429' in error_str or
                'rate limited' in error_msg
            )
            
            if is_rate_limit:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 5
                    if attempt == 0:
                        try:
                            st.warning(f"⏳ Rate limited. Retrying in {wait_time} seconds...")
                        except:
                            pass
                    time.sleep(wait_time)
                    continue
                else:
                    try:
                        st.error(
                            "⚠️ **Yahoo Finance rate limit reached.**\n\n"
                            "Please wait 1-2 minutes and try again. "
                            "The app caches data for 6 hours to minimize API calls."
                        )
                    except:
                        pass
                    return None
            
            if attempt == max_retries - 1:
                if not is_rate_limit:
                    try:
                        st.error(f"Error downloading data for {ticker}: {str(e)[:100]}")
                    except:
                        pass
                return None
    
    return None


def compute_returns(prices):
    return np.log(prices / prices.shift(1)).dropna()


def compute_volatility(returns, window=30):
    rolling_std = returns.rolling(window=window).std()
    annualized_vol = rolling_std * np.sqrt(252)
    return annualized_vol


def classify_regimes(volatility):
    p33 = volatility.quantile(0.33)
    p67 = volatility.quantile(0.67)
    
    regimes = pd.Series(index=volatility.index, dtype='object')
    regimes[volatility <= p33] = 'Low'
    regimes[(volatility > p33) & (volatility <= p67)] = 'Medium'
    regimes[volatility > p67] = 'High'
    
    return regimes


def plot_regimes(prices, regimes):
    common_index = prices.index.intersection(regimes.index)
    prices_aligned = prices.loc[common_index]
    regimes_aligned = regimes.loc[common_index]
    
    fig = go.Figure()
    
    regime_colors = {
        'Low': 'rgba(144, 238, 144, 0.3)',
        'Medium': 'rgba(255, 215, 0, 0.3)',
        'High': 'rgba(255, 107, 107, 0.3)'
    }
    
    dates_list = list(common_index)
    current_regime = None
    start_date = None
    
    for date in dates_list:
        regime = regimes_aligned.loc[date]
        
        if pd.isna(regime):
            continue
            
        if regime != current_regime:
            if current_regime is not None and start_date is not None:
                fig.add_vrect(
                    x0=start_date,
                    x1=date,
                    fillcolor=regime_colors[current_regime],
                    layer="below",
                    line_width=0,
                )
            current_regime = regime
            start_date = date
    
    if current_regime is not None and start_date is not None:
        fig.add_vrect(
            x0=start_date,
            x1=dates_list[-1],
            fillcolor=regime_colors[current_regime],
            layer="below",
            line_width=0,
        )
    
    fig.add_trace(go.Scatter(
        x=prices_aligned.index,
        y=prices_aligned.values,
        mode='lines',
        name='Price',
        line=dict(color='black', width=2),
        hovertemplate='Date: %{x}<br>Price: $%{y:.2f}<extra></extra>'
    ))
    
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


def compute_transition_matrix(regimes):
    regimes_clean = regimes.dropna()
    if len(regimes_clean) < 2:
        return None
    
    current_regimes = regimes_clean[:-1].values
    next_regimes = regimes_clean[1:].values
    
    transition_df = pd.DataFrame({
        'From': current_regimes,
        'To': next_regimes
    })
    
    transition_matrix = pd.crosstab(
        transition_df['From'],
        transition_df['To'],
        normalize='index'
    )
    
    regime_order = ['Low', 'Medium', 'High']
    transition_matrix = transition_matrix.reindex(
        index=regime_order,
        columns=regime_order,
        fill_value=0
    )
    
    return transition_matrix


def plot_transition_heatmap(transition_matrix):
    fig = go.Figure(data=go.Heatmap(
        z=transition_matrix.values,
        x=transition_matrix.columns,
        y=transition_matrix.index,
        colorscale='Blues',
        text=transition_matrix.values,
        texttemplate='%{text:.1%}',
        textfont={"size": 14},
        colorbar=dict(title="Probability", tickformat='.0%')
    ))
    
    fig.update_layout(
        title={
            'text': 'Regime Transition Probability Matrix',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16, 'color': 'black'}
        },
        xaxis_title='To Regime',
        yaxis_title='From Regime',
        height=400,
        yaxis=dict(autorange='reversed')
    )
    
    return fig


def main():
    st.sidebar.header("Settings")
    
    ticker = st.sidebar.text_input(
        "Ticker Symbol",
        value="SPY",
        help="Enter a stock ticker symbol (e.g., SPY, AAPL, MSFT)"
    ).upper()
    
    window = st.sidebar.selectbox(
        "Rolling Window (days)",
        options=[20, 30, 60],
        index=1,
        help="Number of days for rolling volatility calculation"
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh Data", help="Clear cache and reload data from Yahoo Finance"):
        st.cache_data.clear()
        st.sidebar.success("Cache cleared! Data will be reloaded.")
        st.rerun()
    
    st.title("Volatility Regime Analyzer")
    st.markdown("""
    This dashboard visualizes market volatility regimes by classifying rolling volatility 
    into three categories:
    - 🟢 **Low Volatility**: Bottom 33% of volatility distribution
    - 🟡 **Medium Volatility**: Middle 33%
    - 🔴 **High Volatility**: Top 33%
    
    The background shading indicates the current volatility regime, helping identify 
    periods of market stability versus turbulence.
    """)
    
    if ticker:
        status_placeholder = st.empty()
        
        with status_placeholder.container():
            with st.spinner(f"Loading data for {ticker}..."):
                prices = load_data(ticker=ticker)
        
        status_placeholder.empty()
        
        if prices is None or prices.empty:
            st.error(
                f"⚠️ **Could not load data for {ticker}**\n\n"
                "This could be due to:\n"
                "- Rate limiting (please wait 1-2 minutes and try again)\n"
                "- Invalid ticker symbol\n"
                "- Network connectivity issues\n\n"
                "💡 **Tip:** The app caches data for 6 hours. If you just tried multiple tickers, "
                "wait a moment before trying again."
            )
            return
        
        returns = compute_returns(prices)
        volatility = compute_volatility(returns, window=window)
        regimes = classify_regimes(volatility)
        
        stats = get_regime_stats(regimes)
        
        st.markdown(f"### Statistics for {ticker}")
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
        
        fig = plot_regimes(prices, regimes)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Regime Transition Matrix")
        
        transition_matrix = compute_transition_matrix(regimes)
        
        if transition_matrix is not None:
            heatmap_fig = plot_transition_heatmap(transition_matrix)
            st.plotly_chart(heatmap_fig, use_container_width=True)
            
            st.caption(
                "Transition probabilities show how likely each regime is to persist or change. "
                "Higher values on the diagonal indicate regime persistence, while off-diagonal values "
                "show transition likelihoods between different volatility states."
            )
        else:
            st.info("Insufficient data to compute transition matrix.")
        
        st.markdown("---")
        st.caption(f"Data range: {prices.index[0].strftime('%Y-%m-%d')} to {prices.index[-1].strftime('%Y-%m-%d')} | "
                  f"Total trading days: {len(prices)} | "
                  f"Rolling window: {window} days")


if __name__ == "__main__":
    main()
