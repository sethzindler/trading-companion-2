#!/usr/bin/env python3
# API setup and management for Stock Trading Companion

import finnhub

def setup_apis(config, console):
    """Setup API clients based on config"""
    # Finnhub API setup
    finnhub_client = None
    finnhub_enabled = False
    
    try:
        finnhub_key = config['API_KEYS']['finnhub_key']
        if finnhub_key and finnhub_key != 'YOUR_FINNHUB_API_KEY':
            finnhub_client = finnhub.Client(api_key=finnhub_key)
            finnhub_enabled = True
        else:
            console.print("[yellow]Finnhub API not configured.[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Finnhub client setup error: {e}[/yellow]")
        
    # Alpha Vantage API setup
    alpha_vantage_key = None
    alpha_vantage_enabled = False
    
    try:
        alpha_key = config['API_KEYS']['alpha_vantage_key']
        if alpha_key and alpha_key != 'YOUR_ALPHA_VANTAGE_API_KEY':
            alpha_vantage_key = alpha_key
            alpha_vantage_enabled = True
        else:
            console.print("[yellow]Alpha Vantage API not configured.[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Alpha Vantage setup error: {e}[/yellow]")
        
    # Financial Datasets API setup
    financial_datasets_key = None
    financial_datasets_enabled = False
    
    try:
        fd_key = config['API_KEYS']['financialdatasets_key']
        if fd_key and fd_key != 'YOUR_FINANCIALDATASETS_KEY':
            financial_datasets_key = fd_key
            financial_datasets_enabled = True
        else:
            console.print("[yellow]Financial Datasets API not configured.[/yellow]")
    except Exception as e:
        console.print(f"[yellow]Financial Datasets setup error: {e}[/yellow]")
    
    return finnhub_client, finnhub_enabled, alpha_vantage_key, alpha_vantage_enabled, financial_datasets_key, financial_datasets_enabled

def get_available_tickers(console):
    """Get a list of available tickers for autocomplete"""
    try:
        # Use a small sample for quick loading
        major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'JPM', 'BAC', 'WMT', 
                        'JNJ', 'PG', 'V', 'MA', 'DIS', 'NFLX', 'INTC', 'AMD', 'CSCO', 'VZ']
        return major_tickers
    except Exception as e:
        console.print(f"[red]Error loading tickers: {e}[/red]")
        return ['AAPL', 'MSFT', 'GOOGL']  # Fallback to common tickers