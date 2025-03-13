#!/usr/bin/env python3
# Data fetching for Stock Trading Companion

import datetime as dt
import threading
import time
import requests
import yfinance as yf
from rich.progress import Progress

def fetch_stock_data(self, ticker, period, interval, console, finnhub_enabled, alpha_vantage_enabled, financial_datasets_enabled):
    """Fetch historical stock data using yfinance"""
    try:
        self.ticker = ticker
        self.period = period
        self.interval = interval
        
        with Progress() as progress:
            task = progress.add_task(f"[cyan]Fetching data for {ticker}...", total=100)
            
            # Fetch data
            progress.update(task, advance=20)
            stock = yf.Ticker(ticker)
            self.data = stock.history(period=period, interval=interval)
            progress.update(task, advance=20)
            
            # Get company info
            try:
                self.fundamental_data["info"] = stock.info
            except:
                self.fundamental_data["info"] = {}
            
            progress.update(task, advance=10)
            
            # Reset data from other APIs
            self.alpha_vantage_data = {}
            self.financial_datasets_data = {}
            
            # Fetch data from multiple sources in parallel
            threads = []
            
            # Finnhub data
            if finnhub_enabled:
                t1 = threading.Thread(target=fetch_finnhub_data, args=(self, ticker))
                t1.start()
                threads.append(t1)
            
            # Alpha Vantage data
            if alpha_vantage_enabled:
                t2 = threading.Thread(target=fetch_alpha_vantage_data, args=(self, ticker))
                t2.start()
                threads.append(t2)
            
            # Financial Datasets data
            if financial_datasets_enabled:
                t3 = threading.Thread(target=fetch_financial_datasets_data, args=(self, ticker))
                t3.start()
                threads.append(t3)
            
            # Wait for all threads to complete
            for t in threads:
                t.join()
            
            progress.update(task, advance=50)
            
        if self.data.empty:
            console.print(f"[red]No data found for ticker {ticker}[/red]")
            return False
            
        console.print(f"[green]Successfully loaded data for {ticker}[/green]")
        return True
        
    except Exception as e:
        console.print(f"[red]Error fetching stock data: {e}[/red]")
        return False

def fetch_finnhub_data(self, ticker):
    """Fetch data from Finnhub API"""
    if not self.finnhub_enabled:
        return
        
    try:
        # Fetch company profile
        self.fundamental_data["finnhub_profile"] = self.finnhub_client.company_profile2(symbol=ticker)
        
        # Fetch recommendations
        self.fundamental_data["finnhub_recommendations"] = self.finnhub_client.recommendation_trends(ticker)
        
        # Fetch price targets
        self.fundamental_data["finnhub_price_target"] = self.finnhub_client.price_target(ticker)
        
        # Fetch news
        fetch_news(self.finnhub_client, self.ticker, self.console)
        
        # Get earnings surprises
        self.fundamental_data["finnhub_earnings"] = self.finnhub_client.company_earnings(ticker, limit=8)
        
    except Exception as e:
        self.console.print(f"[yellow]Error fetching Finnhub data: {e}[/yellow]")

def fetch_alpha_vantage_data(self, ticker):
    """Fetch data from Alpha Vantage API"""
    if not self.alpha_vantage_enabled:
        return
        
    try:
        # Get income statement
        url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={ticker}&apikey={self.alpha_vantage_key}"
        r = requests.get(url)
        if r.status_code == 200 and 'annualReports' in r.json():
            self.alpha_vantage_data["income_statement"] = r.json()
        
        # Add delay to avoid API rate limits
        time.sleep(1)
        
        # Get balance sheet
        url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={self.alpha_vantage_key}"
        r = requests.get(url)
        if r.status_code == 200 and 'annualReports' in r.json():
            self.alpha_vantage_data["balance_sheet"] = r.json()
        
        time.sleep(1)
        
        # Get cash flow
        url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={ticker}&apikey={self.alpha_vantage_key}"
        r = requests.get(url)
        if r.status_code == 200 and 'annualReports' in r.json():
            self.alpha_vantage_data["cash_flow"] = r.json()
        
        time.sleep(1)
        
        # Get earnings
        url = f"https://www.alphavantage.co/query?function=EARNINGS&symbol={ticker}&apikey={self.alpha_vantage_key}"
        r = requests.get(url)
        if r.status_code == 200 and 'annualEarnings' in r.json():
            self.alpha_vantage_data["earnings"] = r.json()
        
        time.sleep(1)
        
        # Get overview
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={self.alpha_vantage_key}"
        r = requests.get(url)
        if r.status_code == 200 and 'Symbol' in r.json():
            self.alpha_vantage_data["overview"] = r.json()
        
    except Exception as e:
        self.console.print(f"[yellow]Error fetching Alpha Vantage data: {e}[/yellow]")

def fetch_financial_datasets_data(self, ticker):
    """Fetch data from Financial Datasets API"""
    if not self.financial_datasets_enabled:
        return
        
    try:
        # This is a placeholder - replace with actual API endpoints for financialdatasets.ai
        headers = {
            "Authorization": f"Bearer {self.financial_datasets_key}",
            "Content-Type": "application/json"
        }
        
        # Example endpoint - adjust based on actual API documentation
        url = f"https://api.financialdatasets.ai/v1/stocks/{ticker}/financials"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.financial_datasets_data["financials"] = response.json()
            
        # Example for economic indicators - adjust based on actual API
        url = "https://api.financialdatasets.ai/v1/economic/indicators"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.financial_datasets_data["economic_indicators"] = response.json()
            
    except Exception as e:
        self.console.print(f"[yellow]Error fetching Financial Datasets data: {e}[/yellow]")

def fetch_news(finnhub_client, ticker, console):
    """Fetch news for the stock using Finnhub"""
    if not finnhub_client or not ticker:
        return []
        
    try:
        end_date = dt.datetime.now().strftime("%Y-%m-%d")
        start_date = (dt.datetime.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
        
        news_data = finnhub_client.company_news(ticker, _from=start_date, to=end_date)
        if len(news_data) > 10:
            news_data = news_data[:10]  # Limit to 10 recent news items
        return news_data
    except Exception as e:
        console.print(f"[yellow]Error fetching news: {e}[/yellow]")
        return []