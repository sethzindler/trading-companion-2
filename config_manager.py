#!/usr/bin/env python3
# Configuration management for Stock Trading Companion

import configparser
from pathlib import Path

def load_config(console):
    """Load configuration from config.ini file or create if not exists"""
    config = configparser.ConfigParser()
    config_path = Path('config.ini')
    
    if not config_path.exists():
        console.print("[yellow]Config file not found. Creating default config...[/yellow]")
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
        
        config['ANALYSIS_WEIGHTS'] = {
            'technical_weight': '0.5',
            'fundamental_weight': '0.3',
            'sentiment_weight': '0.1',
            'economic_indicators_weight': '0.1'
        }
        
        with open('config.ini', 'w') as f:
            config.write(f)
        
        console.print("[green]Config file created. Please edit config.ini with your API keys before proceeding.[/green]")
    
    config.read('config.ini')
    return config