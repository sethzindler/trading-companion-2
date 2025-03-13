import os
import sys
import json
import time
import datetime as dt
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import finnhub
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # For environments without GUI
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import talib
from textblob import TextBlob
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.layout import Layout
from rich.text import Text
from rich import box
import configparser
import threading
import questionary
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class StockTradingCompanion:
    def __init__(self):
        self.console = Console()
        self.config = self.load_config()
        self.setup_apis()
        self.ticker = None
        self.period = "1y"
        self.interval = "1d"
        self.data = None
        self.fundamental_data = {}
        self.news_data = []
        self.analysis_results = {}
        self.decision = {"action": "HOLD", "confidence": 0.0, "score": 50.0}
        self.available_tickers = self.get_available_tickers()
        
    def load_config(self):
        """Load configuration from config.ini file or create if not exists"""
        config = configparser.ConfigParser()
        config_path = Path('config.ini')
        
        if not config_path.exists():
            self.console.print("[yellow]Config file not found. Creating default config...[/yellow]")
            config['API_KEYS'] = {
                'finnhub_key': 'YOUR_FINNHUB_API_KEY',
                'alpha_vantage_key': 'YOUR_ALPHA_VANTAGE_API_KEY',
                'financialdatasets_key': 'YOUR_FINANCIALDATASETS_KEY'
            }
            
            config['PARAMETERS'] = {
                'default_ticker': 'AAPL',
                'risk_tolerance': 'medium',  # low, medium, high
                'investment_horizon': 'medium'  # short, medium, long
            }
            
            config['TECHNICAL_ANALYSIS'] = {
                'use_sma': 'True',
                'use_ema': 'True',
                'use_macd': 'True',
                'use_rsi': 'True',
                'use_bollinger': 'True'
            }
            
            with open('config.ini', 'w') as f:
                config.write(f)
            
            self.console.print("[green]Config file created. Please edit config.ini with your API keys before proceeding.[/green]")
        
        config.read('config.ini')
        return config
        
    def setup_apis(self):
        """Setup API clients based on config"""
        try:
            self.finnhub_client = finnhub.Client(api_key=self.config['API_KEYS']['finnhub_key'])
        except:
            self.finnhub_client = None
            self.console.print("[yellow]Finnhub client not configured correctly.[/yellow]")
            
    def get_available_tickers(self):
        """Get a list of available tickers for autocomplete"""
        try:
            # Use a small sample for quick loading
            major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BAC', 'WMT', 
                            'JNJ', 'PG', 'V', 'MA', 'DIS', 'NFLX', 'INTC', 'AMD', 'CSCO', 'VZ']
            return major_tickers
        except Exception as e:
            self.console.print(f"[red]Error loading tickers: {e}[/red]")
            return ['AAPL', 'MSFT', 'GOOGL']  # Fallback to common tickers
            
    def fetch_stock_data(self, ticker, period="1y", interval="1d"):
        """Fetch historical stock data using yfinance"""
        try:
            self.ticker = ticker
            self.period = period
            self.interval = interval
            
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Fetching data for {ticker}...", total=100)
                
                # Fetch data
                progress.update(task, advance=30)
                stock = yf.Ticker(ticker)
                self.data = stock.history(period=period, interval=interval)
                progress.update(task, advance=40)
                
                # Get company info
                try:
                    self.fundamental_data["info"] = stock.info
                except:
                    self.fundamental_data["info"] = {}
                    
                progress.update(task, advance=30)
                
            if self.data.empty:
                self.console.print(f"[red]No data found for ticker {ticker}[/red]")
                return False
                
            self.console.print(f"[green]Successfully loaded data for {ticker}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error fetching stock data: {e}[/red]")
            return False
            
    def fetch_news(self):
        """Fetch news for the stock using Finnhub"""
        if not self.finnhub_client or not self.ticker:
            return
            
        try:
            end_date = dt.datetime.now().strftime("%Y-%m-%d")
            start_date = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
            
            self.news_data = self.finnhub_client.company_news(self.ticker, _from=start_date, to=end_date)
            if len(self.news_data) > 10:
                self.news_data = self.news_data[:10]  # Limit to 10 recent news items
        except Exception as e:
            self.console.print(f"[yellow]Error fetching news: {e}[/yellow]")
            
    def analyze_sentiment(self):
        """Analyze sentiment from news headlines"""
        if not self.news_data:
            return 0.5  # Neutral sentiment
            
        try:
            headlines = [news['headline'] for news in self.news_data if 'headline' in news]
            if not headlines:
                return 0.5
                
            sentiments = [TextBlob(headline).sentiment.polarity for headline in headlines]
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Normalize to 0-1 range
            normalized_sentiment = (avg_sentiment + 1) / 2
            return normalized_sentiment
            
        except Exception as e:
            self.console.print(f"[yellow]Error analyzing sentiment: {e}[/yellow]")
            return 0.5
            
    def calculate_technical_indicators(self):
        """Calculate various technical indicators"""
        if self.data is None or self.data.empty:
            return {}
            
        results = {}
        try:
            # Prepare data
            close_prices = self.data['Close'].values.astype(np.float64)
            high_prices = self.data['High'].values.astype(np.float64)
            low_prices = self.data['Low'].values.astype(np.float64)
            volume = self.data['Volume'].values.astype(np.float64)
            
            # Calculate indicators if we have enough data
            if len(close_prices) > 30:
                # SMA - Simple Moving Averages
                results['sma_20'] = talib.SMA(close_prices, timeperiod=20)
                results['sma_50'] = talib.SMA(close_prices, timeperiod=50)
                results['sma_200'] = talib.SMA(close_prices, timeperiod=200)
                
                # EMA - Exponential Moving Averages
                results['ema_12'] = talib.EMA(close_prices, timeperiod=12)
                results['ema_26'] = talib.EMA(close_prices, timeperiod=26)
                
                # MACD - Moving Average Convergence Divergence
                results['macd'], results['macd_signal'], results['macd_hist'] = talib.MACD(
                    close_prices, fastperiod=12, slowperiod=26, signalperiod=9)
                
                # RSI - Relative Strength Index
                results['rsi'] = talib.RSI(close_prices, timeperiod=14)
                
                # Bollinger Bands
                results['bb_upper'], results['bb_middle'], results['bb_lower'] = talib.BBANDS(
                    close_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
                
                # Stochastic Oscillator
                results['slowk'], results['slowd'] = talib.STOCH(
                    high_prices, low_prices, close_prices, 
                    fastk_period=14, slowk_period=3, slowk_matype=0, 
                    slowd_period=3, slowd_matype=0)
                
                # ATR - Average True Range (volatility)
                results['atr'] = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
                
                # Volume indicators
                results['obv'] = talib.OBV(close_prices, volume)
                
                # ADX - Average Directional Index (trend strength)
                results['adx'] = talib.ADX(high_prices, low_prices, close_prices, timeperiod=14)
                
            return results
            
        except Exception as e:
            self.console.print(f"[yellow]Error calculating technical indicators: {e}[/yellow]")
            return {}
            
    def calculate_signals(self, indicators):
        """Calculate trading signals based on technical indicators"""
        signals = {}
        
        try:
            if not indicators or self.data is None or self.data.empty:
                return signals
                
            latest_idx = -1
            close_price = self.data['Close'].iloc[latest_idx]
            
            # Moving Average Signals
            if 'sma_20' in indicators and 'sma_50' in indicators:
                sma_20 = indicators['sma_20'][latest_idx]
                sma_50 = indicators['sma_50'][latest_idx]
                
                # Golden Cross / Death Cross (using latest values)
                signals['ma_cross'] = 1 if sma_20 > sma_50 else -1
                
                # Price vs. MA
                signals['price_vs_sma50'] = 1 if close_price > sma_50 else -1
                
                if 'sma_200' in indicators:
                    sma_200 = indicators['sma_200'][latest_idx]
                    signals['price_vs_sma200'] = 1 if close_price > sma_200 else -1
            
            # MACD Signal
            if all(k in indicators for k in ['macd', 'macd_signal']):
                macd = indicators['macd'][latest_idx]
                macd_signal = indicators['macd_signal'][latest_idx]
                
                signals['macd'] = 1 if macd > macd_signal else -1
                
                # MACD Histogram
                if 'macd_hist' in indicators:
                    macd_hist = indicators['macd_hist'][latest_idx]
                    signals['macd_hist'] = 1 if macd_hist > 0 else -1
            
            # RSI Signal
            if 'rsi' in indicators:
                rsi = indicators['rsi'][latest_idx]
                
                signals['rsi'] = 0  # Neutral
                if rsi < 30:
                    signals['rsi'] = 1  # Oversold - bullish
                elif rsi > 70:
                    signals['rsi'] = -1  # Overbought - bearish
            
            # Bollinger Bands
            if all(k in indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']):
                bb_upper = indicators['bb_upper'][latest_idx]
                bb_lower = indicators['bb_lower'][latest_idx]
                
                signals['bollinger'] = 0  # Neutral
                if close_price > bb_upper:
                    signals['bollinger'] = -1  # Price above upper band - potential reversal/bearish
                elif close_price < bb_lower:
                    signals['bollinger'] = 1  # Price below lower band - potential reversal/bullish
            
            # Stochastic
            if all(k in indicators for k in ['slowk', 'slowd']):
                slowk = indicators['slowk'][latest_idx]
                slowd = indicators['slowd'][latest_idx]
                
                signals['stoch'] = 0  # Neutral
                if slowk < 20 and slowd < 20:
                    signals['stoch'] = 1  # Oversold
                elif slowk > 80 and slowd > 80:
                    signals['stoch'] = -1  # Overbought
                    
                # Stochastic crossover
                signals['stoch_cross'] = 1 if slowk > slowd else -1
            
            # ADX (trend strength)
            if 'adx' in indicators:
                adx = indicators['adx'][latest_idx]
                signals['trend_strength'] = 1 if adx > 25 else 0
            
            return signals
            
        except Exception as e:
            self.console.print(f"[yellow]Error calculating signals: {e}[/yellow]")
            return {}
    
    def analyze_fundamentals(self):
        """Analyze fundamental data"""
        if not self.fundamental_data or "info" not in self.fundamental_data:
            return {}
            
        results = {}
        try:
            info = self.fundamental_data["info"]
            
            # Key metrics
            metrics = [
                'trailingPE', 'forwardPE', 'priceToBook', 'pegRatio',
                'debtToEquity', 'returnOnEquity', 'returnOnAssets',
                'profitMargins', 'targetMeanPrice', 'recommendationMean'
            ]
            
            for metric in metrics:
                if metric in info and info[metric] is not None:
                    results[metric] = info[metric]
            
            # Calculate additional metrics & signals
            if 'trailingPE' in results and 'forwardPE' in results:
                # Whether forward PE is better than trailing (growth expectation)
                results['pe_trend'] = results['forwardPE'] < results['trailingPE']
            
            if 'targetMeanPrice' in results and 'currentPrice' in info:
                current = info['currentPrice']
                target = results['targetMeanPrice']
                results['price_target_diff'] = ((target - current) / current) * 100
            
            if 'recommendationMean' in results:
                # Convert 1-5 scale to -1 to 1 signal (1=Strong Buy, 5=Strong Sell)
                rec = results['recommendationMean']
                results['analyst_signal'] = 1 - (rec - 1) / 2  # Map 1->1, 3->0, 5->-1
            
            return results
            
        except Exception as e:
            self.console.print(f"[yellow]Error analyzing fundamentals: {e}[/yellow]")
            return {}
            
    def make_decision(self):
        """Make a trading decision based on all analyses"""
        if self.data is None or self.data.empty:
            return {"action": "NO DATA", "confidence": 0.0, "score": 50.0}
            
        # 1. Get technical signals
        indicators = self.calculate_technical_indicators()
        tech_signals = self.calculate_signals(indicators)
        
        # 2. Get fundamental signals
        fund_analysis = self.analyze_fundamentals()
        
        # 3. Get sentiment score
        sentiment = self.analyze_sentiment()
        
        # Weight configuration 
        weights = {
            'technical': 0.6,
            'fundamental': 0.3,
            'sentiment': 0.1
        }
        
        # Store all analysis for display
        self.analysis_results = {
            'technical': tech_signals,
            'fundamental': fund_analysis,
            'sentiment': sentiment,
            'indicators': indicators
        }
        
        # Calculate technical score (-100 to 100)
        tech_score = 0
        if tech_signals:
            # Count bullish vs bearish signals
            signal_count = len(tech_signals)
            if signal_count > 0:
                bullish_signals = sum(1 for s in tech_signals.values() if s > 0)
                bearish_signals = sum(1 for s in tech_signals.values() if s < 0)
                
                tech_score = ((bullish_signals - bearish_signals) / signal_count) * 100
        
        # Calculate fundamental score (-100 to 100)
        fund_score = 50  # Neutral by default
        if fund_analysis:
            fund_signals = []
            
            # Price target difference
            if 'price_target_diff' in fund_analysis:
                target_diff = fund_analysis['price_target_diff']
                # Convert to -1 to 1 scale
                target_signal = min(max(target_diff / 20, -1), 1)  # Cap at ±20%
                fund_signals.append(target_signal)
            
            # Analyst recommendation
            if 'analyst_signal' in fund_analysis:
                fund_signals.append(fund_analysis['analyst_signal'])
            
            # PE ratio trend
            if 'pe_trend' in fund_analysis:
                fund_signals.append(0.5 if fund_analysis['pe_trend'] else -0.5)
            
            if fund_signals:
                avg_fund_signal = sum(fund_signals) / len(fund_signals)
                fund_score = 50 + (avg_fund_signal * 50)
        
        # Calculate sentiment score (0-100)
        sent_score = sentiment * 100
        
        # Weighted final score
        final_score = (
            tech_score * weights['technical'] + 
            fund_score * weights['fundamental'] + 
            sent_score * weights['sentiment']
        )
        
        # Normalize to 0-100 range
        final_score = min(max(final_score, 0), 100)
        
        # Determine action and confidence
        action = "HOLD"
        if final_score >= 70:
            action = "BUY"
            confidence = (final_score - 70) / 30 * 100  # Scale to percentage
        elif final_score <= 30:
            action = "SELL"
            confidence = (30 - final_score) / 30 * 100  # Scale to percentage
        else:
            action = "HOLD"
            # Higher confidence when closer to 50 (middle of hold range)
            confidence = (1 - abs(final_score - 50) / 20) * 100
        
        decision = {
            "action": action,
            "confidence": round(confidence, 2),
            "score": round(final_score, 2)
        }
        
        self.decision = decision
        return decision
    
    def generate_charts(self):
        """Generate charts for technical analysis"""
        if self.data is None or self.data.empty:
            return
            
        try:
            indicators = self.analysis_results.get('indicators', {})
            if not indicators:
                indicators = self.calculate_technical_indicators()
                
            # Create a directory for charts if it doesn't exist
            os.makedirs('charts', exist_ok=True)
            
            # Price chart with moving averages
            plt.figure(figsize=(12, 8))
            
            # Plot price
            plt.subplot(3, 1, 1)
            plt.plot(self.data.index, self.data['Close'], label='Close Price')
            
            # Plot moving averages
            if 'sma_20' in indicators:
                plt.plot(self.data.index, indicators['sma_20'], label='SMA 20', linestyle='--')
            if 'sma_50' in indicators:
                plt.plot(self.data.index, indicators['sma_50'], label='SMA 50', linestyle='--')
            if 'sma_200' in indicators:
                plt.plot(self.data.index, indicators['sma_200'], label='SMA 200', linestyle='--')
            
            plt.title(f'{self.ticker} - Price Chart')
            plt.legend()
            plt.grid(True)
            
            # RSI
            plt.subplot(3, 1, 2)
            if 'rsi' in indicators:
                plt.plot(self.data.index, indicators['rsi'], label='RSI', color='purple')
                plt.axhline(y=70, color='r', linestyle='-', alpha=0.3)
                plt.axhline(y=30, color='g', linestyle='-', alpha=0.3)
            plt.title('RSI (14)')
            plt.legend()
            plt.grid(True)
            
            # MACD
            plt.subplot(3, 1, 3)
            if all(k in indicators for k in ['macd', 'macd_signal', 'macd_hist']):
                plt.plot(self.data.index, indicators['macd'], label='MACD')
                plt.plot(self.data.index, indicators['macd_signal'], label='Signal')
                plt.bar(self.data.index, indicators['macd_hist'], label='Histogram', alpha=0.3)
            plt.title('MACD')
            plt.legend()
            plt.grid(True)
            
            plt.tight_layout()
            chart_path = f'charts/{self.ticker}_analysis.png'
            plt.savefig(chart_path)
            plt.close()
            
            self.console.print(f"[green]Charts saved to {chart_path}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Error generating charts: {e}[/red]")
    
    def display_summary(self):
        """Display a summary of the analysis"""
        if self.data is None or self.data.empty:
            self.console.print("[yellow]No data available for summary[/yellow]")
            return
            
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="decision", ratio=2),
            Layout(name="metrics", ratio=3)
        )
        
        # Header
        current_price = self.data['Close'].iloc[-1]
        prev_close = self.data['Close'].iloc[-2] if len(self.data) > 1 else current_price
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100
        
        header_text = Text()
        header_text.append(f"\n{self.ticker} - ", style="bold")
        header_text.append(f"${current_price:.2f} ", style="bold cyan")
        
        if price_change >= 0:
            header_text.append(f"▲ ${price_change:.2f} ({price_change_pct:.2f}%)", style="green")
        else:
            header_text.append(f"▼ ${abs(price_change):.2f} ({price_change_pct:.2f}%)", style="red")
            
        layout["header"].update(Panel(header_text, title="Stock Overview"))
        
        # Decision panel
        decision_color = {
            "BUY": "green",
            "SELL": "red",
            "HOLD": "yellow"
        }.get(self.decision["action"], "white")
        
        decision_text = Text()
        decision_text.append(f"\nRECOMMENDATION: ", style="bold")
        decision_text.append(f"{self.decision['action']}\n\n", style=f"bold {decision_color}")
        decision_text.append(f"Confidence: {self.decision['confidence']:.2f}%\n")
        decision_text.append(f"Score: {self.decision['score']:.2f}/100\n")
        
        # Add score gauge
        score = self.decision["score"]
        gauge_width = 20
        gauge_fill = int((score / 100) * gauge_width)
        
        decision_text.append("\nBearish ")
        for i in range(gauge_width):
            if i < gauge_fill:
                decision_text.append("█", style="green" if score > 50 else "red")
            else:
                decision_text.append("░")
        decision_text.append(" Bullish")
        
        layout["decision"].update(Panel(decision_text, title="Trading Decision"))
        
        # Metrics panel
        metrics_table = Table(show_header=True, box=box.SIMPLE)
        metrics_table.add_column("Indicator", style="cyan")
        metrics_table.add_column("Value", style="white")
        metrics_table.add_column("Signal", style="white")
        
        # Technical indicators
        tech_signals = self.analysis_results.get('technical', {})
        indicators = self.analysis_results.get('indicators', {})
        
        if 'rsi' in indicators:
            rsi_value = indicators['rsi'][-1]
            rsi_signal = "Oversold (Bullish)" if rsi_value < 30 else "Overbought (Bearish)" if rsi_value > 70 else "Neutral"
            rsi_color = "green" if rsi_value < 30 else "red" if rsi_value > 70 else "yellow"
            metrics_table.add_row("RSI (14)", f"{rsi_value:.2f}", f"[{rsi_color}]{rsi_signal}[/{rsi_color}]")
        
        if all(k in indicators for k in ['macd', 'macd_signal']):
            macd_value = indicators['macd'][-1]
            macd_signal_value = indicators['macd_signal'][-1]
            macd_signal = "Bullish" if macd_value > macd_signal_value else "Bearish"
            macd_color = "green" if macd_value > macd_signal_value else "red"
            metrics_table.add_row("MACD", f"{macd_value:.2f}", f"[{macd_color}]{macd_signal}[/{macd_color}]")
        
        # Moving averages
        if 'sma_50' in indicators:
            sma_50 = indicators['sma_50'][-1]
            ma_signal = "Bullish" if current_price > sma_50 else "Bearish"
            ma_color = "green" if current_price > sma_50 else "red"
            metrics_table.add_row("Price vs SMA(50)", f"{sma_50:.2f}", f"[{ma_color}]{ma_signal}[/{ma_color}]")
        
        # Fundamental metrics
        fund_analysis = self.analysis_results.get('fundamental', {})
        
        for key, name in [
            ('trailingPE', 'P/E Ratio'),
            ('priceToBook', 'Price/Book'),
            ('returnOnEquity', 'ROE'),
            ('targetMeanPrice', 'Price Target')
        ]:
            if key in fund_analysis:
                metrics_table.add_row(name, f"{fund_analysis[key]:.2f}", "")
        
        # Sentiment
        sentiment = self.analysis_results.get('sentiment', 0.5) * 100
        sentiment_signal = "Bullish" if sentiment > 60 else "Bearish" if sentiment < 40 else "Neutral"
        sentiment_color = "green" if sentiment > 60 else "red" if sentiment < 40 else "yellow"
        metrics_table.add_row("News Sentiment", f"{sentiment:.1f}%", f"[{sentiment_color}]{sentiment_signal}[/{sentiment_color}]")
        
        layout["metrics"].update(Panel(metrics_table, title="Key Metrics"))
        
        # Footer
        time_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        layout["footer"].update(Panel(f"Analysis Time: {time_str}", title="Information"))
        
        # Render layout
        self.console.print(layout)
        
    def show_help(self):
        """Display help information"""
        help_text = """
        Stock Trading Companion - Command Reference
        
        Commands:
        - symbol <ticker>     : Load data for a new ticker symbol (e.g., symbol AAPL)
        - analyze             : Analyze current stock and make trading decision
        - charts              : Generate and save technical analysis charts
        - news                : Show recent news for current stock
        - help                : Show this help message
        - exit                : Exit the program
        
        Options:
        - period <period>     : Set data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        - interval <interval> : Set data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        
        Examples:
        > symbol MSFT         : Load Microsoft stock data
        > period 6mo          : Set period to 6 months
        > interval 1d         : Set interval to daily
        > analyze             : Analyze the stock
        """
        
        self.console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def main_loop(self):
        """Main loop for the terminal interface"""
        session = PromptSession()
        
        # Set up autocompletion
        stock_completer = WordCompleter(self.available_tickers)
        
        # Welcome screen
        self.console.print(Panel.fit(
            "[bold cyan]Stock Trading Companion[/bold cyan]\n\n"
            "A tool to assist with stock trading decisions.\n"
            "Type [green]help[/green] for available commands.",
            title="Welcome",
            border_style="blue"
        ))
        
        # Default stock
        default_ticker = self.config['PARAMETERS'].get('default_ticker', 'AAPL')
        self.console.print(f"[yellow]Loading default stock: {default_ticker}[/yellow]")
        self.fetch_stock_data(default_ticker)
        
        # Main loop
        while True:
            try:
                user_input = session.prompt("stock-companion> ", completer=stock_completer)
                parts = user_input.strip().split()
                
                if not parts:
                    continue
                
                command = parts[0].lower()
                
                # Handle commands
                if command == "exit" or command == "quit":
                    break
                    
                elif command == "help":
                    self.show_help()
                    
                elif command == "symbol" or command == "ticker":
                    if len(parts) > 1:
                        ticker = parts[1].upper()
                        self.fetch_stock_data(ticker)
                    else:
                        self.console.print("[yellow]Please specify a ticker symbol[/yellow]")
                        
                elif command == "period":
                    if len(parts) > 1:
                        period = parts[1]
                        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
                        if period in valid_periods:
                            self.period = period
                            self.console.print(f"[green]Period set to {period}[/green]")
                            self.fetch_stock_data(self.ticker, period=self.period, interval=self.interval)
                        else:
                            self.console.print(f"[red]Invalid period. Choose from {', '.join(valid_periods)}[/red]")
                    else:
                        self.console.print("[yellow]Please specify a period[/yellow]")
                        
                elif command == "interval":
                    if len(parts) > 1:
                        interval = parts[1]
                        valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
                        if interval in valid_intervals:
                            self.interval = interval
                            self.console.print(f"[green]Interval set to {interval}[/green]")
                            self.fetch_stock_data(self.ticker, period=self.period, interval=self.interval)
                        else:
                            self.console.print(f"[red]Invalid interval. Choose from {', '.join(valid_intervals)}[/red]")
                    else:
                        self.console.print("[yellow]Please specify an interval[/yellow]")
                        
                elif command == "analyze":
                    if self.data is not None and not self.data.empty:
                        self.fetch_news()  # Get fresh news
                        self.make_decision()
                        self.display_summary()
                    else:
                        self.console.print("[red]No data loaded. Use 'symbol <ticker>' to load a stock.[/red]")
                        
                elif command == "charts":
                    if self.data is not None and not self.data.empty:
                        self.generate_charts()
                        self.console.print("[green]Charts generated successfully. Check the 'charts' folder.[/green]")
                    else:
                        self.console.print("[red]No data loaded. Use 'symbol <ticker>' to load a stock.[/red]")
                        
                elif command == "news":
                    if self.ticker:
                        self.fetch_news()
                        if self.news_data:
                            self.console.print(Panel(f"[bold]Recent News for {self.ticker}[/bold]", border_style="blue"))
                            for i, news in enumerate(self.news_data[:5], 1):
                                headline = news.get('headline', 'No headline')
                                date = dt.datetime.fromtimestamp(news.get('datetime', 0)).strftime('%Y-%m-%d')
                                url = news.get('url', '')
                                self.console.print(f"[bold cyan]{i}.[/bold cyan] [yellow]{date}[/yellow] - {headline}")
                                self.console.print(f"   [dim blue]{url}[/dim blue]\n")
                        else:
                            self.console.print("[yellow]No recent news found.[/yellow]")
                    else:
                        self.console.print("[red]No ticker selected. Use 'symbol <ticker>' first.[/red]")
                        
                elif command == "clear":
                    clear()
                    
                else:
                    self.console.print(f"[red]Unknown command: {command}. Type 'help' for assistance.[/red]")
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit the program.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

def main():
    """Entry point for the application"""
    try:
        companion = StockTradingCompanion()
        companion.main_loop()
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())