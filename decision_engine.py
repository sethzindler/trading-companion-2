#!/usr/bin/env python3
# Decision engine for Stock Trading Companion

def make_decision(data, config, calculate_technical_indicators, calculate_signals, 
                  analyze_fundamentals, analyze_sentiment, console):
    """Make a trading decision based on all analyses from multiple data sources"""
    if data is None or data.empty:
        return {"action": "NO DATA", "confidence": 0.0, "score": 50.0}
        
    # 1. Get technical signals
    indicators = calculate_technical_indicators()
    tech_signals = calculate_signals(indicators)
    
    # 2. Get comprehensive fundamental analysis
    fund_analysis = analyze_fundamentals()
    
    # 3. Get sentiment score
    sentiment = analyze_sentiment()
    
    # 4. Get economic indicators (if available from Financial Datasets)
    economic_score = fund_analysis.get('economic_environment_score', 50)
    
    # Configure weights based on config file or defaults
    try:
        weights = {
            'technical': float(config['ANALYSIS_WEIGHTS'].get('technical_weight', 0.5)),
            'fundamental': float(config['ANALYSIS_WEIGHTS'].get('fundamental_weight', 0.3)),
            'sentiment': float(config['ANALYSIS_WEIGHTS'].get('sentiment_weight', 0.1)),
            'economic': float(config['ANALYSIS_WEIGHTS'].get('economic_indicators_weight', 0.1))
        }
        
        # Normalize weights to sum to 1
        weight_sum = sum(weights.values())
        if weight_sum > 0:
            for key in weights:
                weights[key] /= weight_sum
        
    except (KeyError, ValueError):
        # Default weights if config is invalid
        weights = {
            'technical': 0.5,
            'fundamental': 0.3,
            'sentiment': 0.1,
            'economic': 0.1
        }
    
    # Store all analysis for display
    analysis_results = {
        'technical': tech_signals,
        'fundamental': fund_analysis,
        'sentiment': sentiment,
        'indicators': indicators
    }
    
    # Calculate technical score (0-100)
    tech_score = 50  # Neutral by default
    if tech_signals:
        # Count bullish vs bearish signals
        signal_count = len(tech_signals)
        if signal_count > 0:
            bullish_signals = sum(1 for s in tech_signals.values() if s > 0)
            bearish_signals = sum(1 for s in tech_signals.values() if s < 0)
            neutral_signals = signal_count - bullish_signals - bearish_signals
            
            # Calculate weighted score
            # Give more weight to strong signals from key indicators
            weighted_bullish = bullish_signals
            weighted_bearish = bearish_signals
            
            # Add extra weight to important signals
            key_indicators = ['macd', 'rsi', 'price_vs_sma200', 'bollinger']
            for indicator in key_indicators:
                if indicator in tech_signals:
                    if tech_signals[indicator] > 0:
                        weighted_bullish += 0.5
                    elif tech_signals[indicator] < 0:
                        weighted_bearish += 0.5
            
            # Calculate normalized score (0-100)
            normalized_score = (weighted_bullish - weighted_bearish) / (signal_count + len(key_indicators) * 0.5) * 50 + 50
            tech_score = min(max(normalized_score, 0), 100)
    
    # Calculate fundamental score (0-100)
    fund_score = 50  # Neutral by default
    if fund_analysis:
        fund_signals = []
        
        # 1. Price target signals
        target_signals = []
        
        if 'price_target_diff' in fund_analysis:
            target_diff = fund_analysis['price_target_diff']
            # Scale -20% to +20% to 0-100 scale
            normalized_target = min(max((target_diff + 20) / 40 * 100, 0), 100)
            target_signals.append(normalized_target)
        
        if 'finnhub_target_diff' in fund_analysis:
            finnhub_diff = fund_analysis['finnhub_target_diff']
            normalized_target = min(max((finnhub_diff + 20) / 40 * 100, 0), 100)
            target_signals.append(normalized_target)
        
        if target_signals:
            fund_signals.append(sum(target_signals) / len(target_signals))
        
        # 2. Analyst recommendations
        analyst_signals = []
        
        if 'analyst_signal' in fund_analysis:
            # Convert -1 to 1 scale to 0 to 100
            analyst_score = (fund_analysis['analyst_signal'] + 1) / 2 * 100
            analyst_signals.append(analyst_score)
        
        if 'analyst_consensus_score' in fund_analysis:
            analyst_signals.append(fund_analysis['analyst_consensus_score'])
        
        if analyst_signals:
            fund_signals.append(sum(analyst_signals) / len(analyst_signals))
        
        # 3. Financial health indicators
        health_signals = []
        
        if 'financial_health_score' in fund_analysis:
            health_signals.append(fund_analysis['financial_health_score'])
        
        # Include other health metrics
        if 'DebtToEquity' in fund_analysis:
            dte = fund_analysis['DebtToEquity']
            # Lower is better: 0=100, 2=0
            dte_score = max(0, min(100, (2 - dte) * 50))
            health_signals.append(dte_score)
        
        if 'CurrentRatio' in fund_analysis:
            cr = fund_analysis['CurrentRatio']
            # Higher is better: 0=0, 2=100
            cr_score = max(0, min(100, cr * 50))
            health_signals.append(cr_score)
        
        if health_signals:
            fund_signals.append(sum(health_signals) / len(health_signals))
        
        # 4. Growth indicators
        growth_signals = []
        
        if 'growth_score' in fund_analysis:
            growth_signals.append(fund_analysis['growth_score'])
        
        if 'RevenueGrowthYoY' in fund_analysis:
            rev_growth = fund_analysis['RevenueGrowthYoY']
            # Scale -20% to +40% to 0-100
            growth_score = min(max((rev_growth + 20) / 60 * 100, 0), 100)
            growth_signals.append(growth_score)
        
        if 'earnings_surprise_score' in fund_analysis:
            growth_signals.append(fund_analysis['earnings_surprise_score'])
        
        if growth_signals:
            fund_signals.append(sum(growth_signals) / len(growth_signals))
        
        # 5. Valuation indicators (PE ratio etc)
        valuation_signals = []
        
        if 'PERatio' in fund_analysis:
            pe = fund_analysis['PERatio']
            # Optimal PE around 15, too low or too high is worse
            pe_score = 100 - min(100, abs(pe - 15) * 5)
            valuation_signals.append(pe_score)
        
        if 'trailingPE' in fund_analysis:
            pe = fund_analysis['trailingPE']
            pe_score = 100 - min(100, abs(pe - 15) * 5)
            valuation_signals.append(pe_score)
        
        if 'PEGRatio' in fund_analysis:
            peg = fund_analysis['PEGRatio']
            # Optimal PEG around 1, lower is better
            peg_score = 100 - min(100, max(0, peg - 1) * 50)
            valuation_signals.append(peg_score)
        
        if valuation_signals:
            fund_signals.append(sum(valuation_signals) / len(valuation_signals))
        
        # Calculate overall fundamental score if we have signals
        if fund_signals:
            fund_score = sum(fund_signals) / len(fund_signals)
    
    # Calculate sentiment score (0-100)
    sent_score = sentiment * 100
    
    # Combine all scores with appropriate weights
    weighted_scores = [
        tech_score * weights['technical'],
        fund_score * weights['fundamental'],
        sent_score * weights['sentiment'],
        economic_score * weights['economic']
    ]
    
    # Final score (0-100)
    final_score = sum(weighted_scores)
    
    # Add debug information for display
    component_scores = {
        'technical_score': tech_score,
        'fundamental_score': fund_score,
        'sentiment_score': sent_score,
        'economic_score': economic_score,
        'weights': weights
    }
    
    # Determine action and confidence
    risk_tolerance = config['PARAMETERS'].get('risk_tolerance', 'medium')
    
    # Adjust thresholds based on risk tolerance
    if risk_tolerance == 'low':
        buy_threshold = 75
        sell_threshold = 25
    elif risk_tolerance == 'high':
        buy_threshold = 65
        sell_threshold = 35
    else:  # medium
        buy_threshold = 70
        sell_threshold = 30
    
    # Determine action
    action = "HOLD"
    if final_score >= buy_threshold:
        action = "BUY"
        confidence = (final_score - buy_threshold) / (100 - buy_threshold) * 100
    elif final_score <= sell_threshold:
        action = "SELL"
        confidence = (sell_threshold - final_score) / sell_threshold * 100
    else:
        action = "HOLD"
        # Higher confidence when closer to 50 (middle of hold range)
        mid_point = (buy_threshold + sell_threshold) / 2
        confidence = (1 - abs(final_score - mid_point) / ((buy_threshold - sell_threshold) / 2)) * 100
    
    decision = {
        "action": action,
        "confidence": round(confidence, 2),
        "score": round(final_score, 2),
        "component_scores": {
            "technical": round(tech_score, 2),
            "fundamental": round(fund_score, 2),
            "sentiment": round(sent_score, 2),
            "economic": round(economic_score, 2)
        },
        "analysis_results": analysis_results
    }
    
    return decision