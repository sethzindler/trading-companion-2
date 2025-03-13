#!/usr/bin/env python3
# Enhanced Stock Trading Companion - Main File

import os
import sys
import datetime as dt
import threading
from pathlib import Path
import configparser
import warnings
warnings.filterwarnings('ignore')

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

# Import companion modules
from config_manager import load_config
from apis import setup_apis, get_available_tickers
from data_fetcher import fetch_stock_data, fetch_news
from technical_analysis import calculate_technical_indicators, calculate_signals
from fundamental_analysis import analyze_fundamentals, analyze_alpha_vantage_data, analyze_financial_datasets_data
from sentiment_analysis import analyze_sentiment
from decision_engine import make_decision
from visualization import generate_charts, generate_fundamental_charts
from ui import display_summary, show_info, generate_report, show_available_metrics, show_help

class StockTradingCompanion:
    def __init__(self):
        self.console = Console()
        self.config = load_config(self.console)
        
        # Setup APIs
        self.finnhub_client, self.finnhub_enabled, self.alpha_vantage_key, self.alpha_vantage_enabled, \
        self.financial_datasets_key, self.financial_datasets_enabled = setup_apis(self.config, self.console)
        
        # Initialize state variables
        self.ticker = None
        self.period = "1y"
        self.interval = "1d"
        self.data = None
        self.fundamental_data = {}
        self.news_data = []
        self.alpha_vantage_data = {}
        self.financial_datasets_data = {}
        self.analysis_results = {}
        self.decision = {"action": "HOLD", "confidence": 0.0, "score": 50.0}
        self.available_tickers = get_available_tickers(self.console)
    
    def fetch_stock_data(self, ticker, period="1y", interval="1d"):
        return fetch_stock_data(
            self, ticker, period, interval, 
            self.console, self.finnhub_enabled, self.alpha_vantage_enabled, 
            self.financial_datasets_enabled
        )
        
    def fetch_news(self):
        self.news_data = fetch_news(self.finnhub_client, self.ticker, self.console)
    
    def calculate_technical_indicators(self):
        return calculate_technical_indicators(self.data, self.console)
    
    def calculate_signals(self, indicators):
        return calculate_signals(indicators, self.data, self.console)
    
    def analyze_sentiment(self):
        return analyze_sentiment(self.news_data, self.console)
    
    def analyze_fundamentals(self):
        return analyze_fundamentals(
            self.fundamental_data, self.alpha_vantage_enabled, self.alpha_vantage_data,
            self.finnhub_enabled, self.financial_datasets_enabled, self.financial_datasets_data,
            self.data, self.console
        )
    
    def analyze_alpha_vantage_data(self):
        return analyze_alpha_vantage_data(self.alpha_vantage_data, self.console)
    
    def analyze_financial_datasets_data(self):
        return analyze_financial_datasets_data(self.financial_datasets_data, self.console)
    
    def make_decision(self):
        self.decision = make_decision(
            self.data, self.config, self.calculate_technical_indicators, 
            self.calculate_signals, self.analyze_fundamentals, 
            self.analyze_sentiment, self.console
        )
        self.analysis_results = self.decision.pop('analysis_results', {})
        return self.decision
    
    def generate_charts(self):
        generate_charts(self.ticker, self.data, self.analysis_results, self.decision, self.alpha_vantage_data, self.console)
    
    def generate_fundamental_charts(self):
        generate_fundamental_charts(self.ticker, self.alpha_vantage_data, self.console)
    
    def display_summary(self):
        display_summary(
            self.data, self.ticker, self.decision, self.analysis_results, 
            self.fundamental_data, self.finnhub_enabled, self.alpha_vantage_enabled, 
            self.financial_datasets_enabled, self.console
        )
    
    def show_info(self):
        show_info(
            self.ticker, self.fundamental_data, self.alpha_vantage_enabled, 
            self.alpha_vantage_data, self.finnhub_enabled, self.console
        )
    
    def generate_report(self):
        generate_report(
            self.ticker, self.data, self.decision, self.analysis_results, 
            self.fundamental_data, self.news_data, self.finnhub_enabled, 
            self.alpha_vantage_enabled, self.financial_datasets_enabled, 
            self.make_decision, self.console
        )
    
    def show_available_metrics(self):
        show_available_metrics(
            self.ticker, self.fundamental_data, self.alpha_vantage_enabled, 
            self.alpha_vantage_data, self.finnhub_enabled, 
            self.financial_datasets_enabled, self.financial_datasets_data, 
            self.analysis_results, self.console
        )
    
    def show_help(self):
        show_help(self.console)
    
    def main_loop(self):
        """Main loop for the terminal interface"""
        session = PromptSession()
        
        # Set up autocompletion
        stock_completer = WordCompleter(self.available_tickers)
        
        # Welcome screen
        self.console.print(Panel.fit(
            "[bold cyan]Stock Trading Companion[/bold cyan]\n\n"
            "A tool to assist with stock trading decisions using multiple data sources.\n"
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
                
                elif command == "risk":
                    if len(parts) > 1:
                        risk = parts[1].lower()
                        valid_risks = ["low", "medium", "high"]
                        if risk in valid_risks:
                            self.config['PARAMETERS']['risk_tolerance'] = risk
                            self.console.print(f"[green]Risk tolerance set to {risk}[/green]")
                        else:
                            self.console.print(f"[red]Invalid risk level. Choose from {', '.join(valid_risks)}[/red]")
                    else:
                        self.console.print("[yellow]Please specify a risk level (low, medium, high)[/yellow]")
                        
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
                
                elif command == "info":
                    self.show_info()
                
                elif command == "report":
                    self.generate_report()
                
                elif command == "metrics":
                    self.show_available_metrics()
                        
                elif command == "clear":
                    # Cross-platform clear screen
                    os.system('cls' if os.name == 'nt' else 'clear')
                    
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