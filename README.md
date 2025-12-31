# SPY Volatility Regime Visualization

A clean Python project that visualizes market volatility regimes for stocks from 2010 to present. Available as both a command-line script and an interactive Streamlit web dashboard.

## Features

- Downloads daily adjusted close price data using yfinance
- Computes daily log returns
- Calculates rolling annualized volatility (configurable window: 20, 30, or 60 days)
- Classifies volatility into three regimes (Low/Medium/High) based on percentiles
- Creates visualizations showing:
  - Price over time
  - Background shading by volatility regime
  - Clear legend and title
- Prints summary statistics for each regime

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command-Line Script

```bash
python volatility_regimes.py
```

The script will:
1. Download SPY data from 2010 to present
2. Compute volatility metrics
3. Classify regimes
4. Generate and save a visualization to `outputs/spy_volatility_regimes.png`
5. Print summary statistics

### Streamlit Web Dashboard

```bash
streamlit run streamlit_app.py
```

The interactive dashboard provides:
- **Sidebar controls**:
  - Ticker input (default: SPY, supports any ticker)
  - Rolling window selector (20, 30, or 60 days)
- **Main panel**:
  - Interactive Plotly chart with zoom/pan capabilities
  - Summary statistics (metrics for each regime)
  - Legend explaining volatility regimes
  - Data range information

The dashboard automatically recalculates when inputs change, with data caching for performance.

## Output

### Command-Line Script
- **Visualization**: `outputs/spy_volatility_regimes.png` - High-resolution plot showing price with volatility regime shading
- **Console Output**: Summary statistics showing the frequency of each volatility regime

### Streamlit Dashboard
- Interactive web interface accessible at `http://localhost:8501`
- Real-time updates when parameters change
- Interactive charts with hover tooltips

## Project Structure

```
spy_volatility_regimes/
├── volatility_regimes.py    # Command-line script
├── streamlit_app.py         # Streamlit web dashboard
├── requirements.txt          # Dependencies
├── README.md                 # This file
└── outputs/                  # Generated visualizations
    └── spy_volatility_regimes.png
```

## Methodology

1. **Data Download**: Uses yfinance to fetch adjusted close prices
2. **Returns Calculation**: Computes daily log returns (ln(P_t / P_{t-1}))
3. **Volatility**: Rolling standard deviation of returns, annualized by multiplying by √252
4. **Regime Classification**: 
   - Low: Bottom 33% of volatility distribution
   - Medium: Middle 33%
   - High: Top 33%
5. **Visualization**: Price line with background shading indicating current volatility regime

