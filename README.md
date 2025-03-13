# Trading Companion 2

A comprehensive stock analysis and trading decision tool with multi-source data integration and visualization capabilities.

## Features

- **Multi-Source Data Integration**: Connect to Yahoo Finance, Finnhub, Alpha Vantage, and Financial Datasets API
- **Technical Analysis**: 15+ technical indicators including MACD, RSI, Bollinger Bands, Stochastic Oscillator, and more
- **Fundamental Analysis**: Access company financials, growth metrics, analyst recommendations, and price targets
- **Sentiment Analysis**: Analyze news sentiment to supplement technical and fundamental data
- **Decision Engine**: Get data-driven BUY/SELL/HOLD recommendations with confidence scores
- **Data Visualization**: Generate detailed technical and fundamental analysis charts
- **Reporting**: Export comprehensive analysis reports for your records

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Integration](#api-integration)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Clone the Repository

```bash
git clone https://github.com/sethzindler/trading-companion-2.git
cd trading-companion-2
```

### Setup Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### API Keys Setup

Create a `config.ini` file in the root directory (or edit the existing one) with your API keys:

## Quick Start

1. Run the main application:

```bash
python main.py
```

2. The application will start in terminal mode with a command-line interface
3. By default, it loads data for AAPL (or whatever ticker is set in your config.ini)
4. Type `help` to see all available commands

## Configuration

### API Key Setup

Trading Companion 2 supports multiple financial data providers:

1. **Yahoo Finance** (Default, no API key required)
2. **Finnhub API** - Get a free API key at [Finnhub.io](https://finnhub.io/)
3. **Alpha Vantage API** - Get a free API key at [Alpha Vantage](https://www.alphavantage.co/)
4. **Financial Datasets API** - Optional, can be configured if you have access

### Analysis Settings

Customize the analysis parameters in the `config.ini` file:

1. **Risk Tolerance**: Set to "low", "medium", or "high" to adjust buy/sell thresholds
2. **Default Ticker**: Set your preferred default stock symbol
3. **Analysis Weights**: Adjust the importance of technical, fundamental, sentiment, and economic indicators
4. **Technical Indicators**: Enable/disable specific technical indicators

## Usage Guide

### Terminal Commands

The application is operated through a command-line interface. Here are the available commands:

```
- symbol <ticker>     : Load data for a new ticker symbol (e.g., symbol AAPL)
- analyze             : Analyze current stock and make trading decision
- charts              : Generate and save technical analysis charts
- news                : Show recent news for current stock
- info                : Show detailed company information
- report              : Generate comprehensive analysis report
- metrics             : Show available metrics from all data sources
- period <period>     : Set data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
- interval <interval> : Set data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
- risk <level>        : Set risk tolerance (low, medium, high)
- help                : Show help message
- exit                : Exit the program
```

### Analyzing a Stock

```bash
# Load a stock
symbol MSFT

# Set the time period and interval
period 6mo
interval 1d

# Run the analysis
analyze

# Generate technical and fundamental charts
charts

# View recent news
news

# View company information
info

# Generate a detailed report
report
```

## API Integration

Trading Companion 2 integrates with several financial APIs to provide comprehensive data.

### Yahoo Finance (yfinance)

Used for:
- Historical price data
- Basic company information
- Quick metrics like P/E ratio, market cap, etc.

No API key required.

### Finnhub API

Used for:
- News articles and sentiment analysis
- Analyst recommendations
- Price targets
- Earnings surprises

```python
# Example of data fetched from Finnhub
finnhub_client = finnhub.Client(api_key="YOUR_FINNHUB_API_KEY")
news = finnhub_client.company_news('AAPL', _from="2023-01-01", to="2023-01-31")
recommendations = finnhub_client.recommendation_trends('AAPL')
price_target = finnhub_client.price_target('AAPL')
```

### Alpha Vantage API

Used for:
- Detailed financial statements (income statement, balance sheet, cash flow)
- Company overview and fundamentals
- Growth metrics and valuations

```python
# Example of Alpha Vantage data usage
url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=AAPL&apikey=YOUR_ALPHA_VANTAGE_API_KEY"
income_statement = requests.get(url).json()
```

## Data Analysis and Decision Engine

Trading Companion 2 uses a sophisticated decision engine that analyzes multiple factors:

1. **Technical Analysis**: Evaluates price patterns and momentum using indicators like MACD, RSI, and moving averages
2. **Fundamental Analysis**: Assesses company financials, valuation metrics, and growth potential
3. **Sentiment Analysis**: Gauges market sentiment through news headlines
4. **Economic Indicators**: Considers broader market conditions (when available)

The decision engine then:
1. Calculates individual scores for each analysis component
2. Applies configurable weights to each component
3. Produces a final score (0-100) and recommendation (BUY/SELL/HOLD)
4. Provides a confidence percentage for the recommendation

## Technical Indicators

Trading Companion 2 calculates the following technical indicators:

- Simple Moving Averages (SMA) - 20, 50, 200 periods
- Exponential Moving Averages (EMA) - 12, 26 periods
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- Bollinger Bands
- Stochastic Oscillator
- ADX (Average Directional Index)
- AROON Indicator
- CCI (Commodity Channel Index)
- MFI (Money Flow Index)
- OBV (On Balance Volume)
- TRIX (Triple Exponential Moving Average)
- ATR (Average True Range)

## Visualization

The application generates:
1. **Technical Analysis Charts**: Price with moving averages, RSI, MACD, Stochastic, and volume indicators
2. **Fundamental Charts**: Revenue growth, net income, assets vs liabilities, and debt-to-equity ratio

Charts are saved to the `charts/` directory.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please:
- Open an [Issue](https://github.com/sethzindler/trading-companion-2/issues)

---

Made with ❤️ by Seth Zindler