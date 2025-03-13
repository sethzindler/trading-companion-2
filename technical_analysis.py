#!/usr/bin/env python3
# Technical analysis for Stock Trading Companion

import numpy as np
import talib

def calculate_technical_indicators(data, console):
    """Calculate various technical indicators"""
    if data is None or data.empty:
        return {}
        
    results = {}
    try:
        # Prepare data - explicitly convert to numpy float64 arrays to prevent errors
        close_prices = data['Close'].values.astype(np.float64)
        high_prices = data['High'].values.astype(np.float64)
        low_prices = data['Low'].values.astype(np.float64)
        volume = data['Volume'].values.astype(np.float64)
        
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
            
            # AROON - Trend indicator
            results['aroon_up'], results['aroon_down'] = talib.AROON(high_prices, low_prices, timeperiod=14)
            
            # CCI - Commodity Channel Index
            results['cci'] = talib.CCI(high_prices, low_prices, close_prices, timeperiod=14)
            
            # MFI - Money Flow Index
            results['mfi'] = talib.MFI(high_prices, low_prices, close_prices, volume, timeperiod=14)
            
            # TRIX - Triple Exponential Moving Average
            results['trix'] = talib.TRIX(close_prices, timeperiod=30)
            
        return results
        
    except Exception as e:
        console.print(f"[yellow]Error calculating technical indicators: {e}[/yellow]")
        return {}

def calculate_signals(indicators, data, console):
    """Calculate trading signals based on technical indicators"""
    signals = {}
    
    try:
        if not indicators or data is None or data.empty:
            return signals
            
        latest_idx = -1
        close_price = data['Close'].iloc[latest_idx]
        
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
            
        # AROON (trend direction)
        if 'aroon_up' in indicators and 'aroon_down' in indicators:
            aroon_up = indicators['aroon_up'][latest_idx]
            aroon_down = indicators['aroon_down'][latest_idx]
            signals['aroon'] = 1 if aroon_up > aroon_down else -1
            
        # CCI (overbought/oversold)
        if 'cci' in indicators:
            cci = indicators['cci'][latest_idx]
            signals['cci'] = 1 if cci < -100 else -1 if cci > 100 else 0
            
        # MFI (Money Flow Index)
        if 'mfi' in indicators:
            mfi = indicators['mfi'][latest_idx]
            signals['mfi'] = 1 if mfi < 20 else -1 if mfi > 80 else 0
            
        # TRIX (trend and momentum)
        if 'trix' in indicators:
            trix = indicators['trix'][latest_idx]
            signals['trix'] = 1 if trix > 0 else -1 if trix < 0 else 0
        
        return signals
        
    except Exception as e:
        console.print(f"[yellow]Error calculating signals: {e}[/yellow]")
        return {}