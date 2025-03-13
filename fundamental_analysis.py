#!/usr/bin/env python3
# Fundamental analysis for Stock Trading Companion

def analyze_fundamentals(fundamental_data, alpha_vantage_enabled, alpha_vantage_data,
                         finnhub_enabled, financial_datasets_enabled, financial_datasets_data,
                         data, console):
    """Analyze fundamental data combining Yahoo Finance, Alpha Vantage, and Finnhub data"""
    results = {}
    
    # 1. Get data from Yahoo Finance
    if fundamental_data and "info" in fundamental_data:
        try:
            info = fundamental_data["info"]
            
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
        except Exception as e:
            console.print(f"[yellow]Error analyzing Yahoo Finance data: {e}[/yellow]")
    
    # 2. Add Alpha Vantage fundamental data
    if alpha_vantage_enabled:
        try:
            av_results = analyze_alpha_vantage_data(alpha_vantage_data, console)
            
            # Merge with existing results, prioritizing more detailed Alpha Vantage data
            for key, value in av_results.items():
                results[key] = value
                
            # Add special signals from Alpha Vantage data
            if 'FinancialHealthScore' in av_results:
                results['financial_health_score'] = av_results['FinancialHealthScore']
            
            if 'RevenueGrowthYoY' in av_results and 'NetIncomeGrowthYoY' in av_results:
                # Calculate growth score (0-100)
                rev_growth = min(max(av_results['RevenueGrowthYoY'], -50), 50)  # Cap at -50% to 50%
                inc_growth = min(max(av_results['NetIncomeGrowthYoY'], -50), 50)  # Cap at -50% to 50%
                
                # Normalize to 0-100 range
                rev_score = (rev_growth + 50) / 100 * 100
                inc_score = (inc_growth + 50) / 100 * 100
                
                # Combined growth score (revenue weighted more)
                results['growth_score'] = rev_score * 0.6 + inc_score * 0.4
        except Exception as e:
            console.print(f"[yellow]Error incorporating Alpha Vantage data: {e}[/yellow]")
    
    # 3. Add Finnhub data
    if finnhub_enabled:
        try:
            # Use price targets if available
            if "finnhub_price_target" in fundamental_data:
                price_target = fundamental_data["finnhub_price_target"]
                
                if 'targetMean' in price_target:
                    target_mean = price_target['targetMean']
                    current_price = data['Close'].iloc[-1]
                    
                    # Calculate potential upside/downside
                    results['finnhub_target_diff'] = ((target_mean - current_price) / current_price) * 100
            
            # Use recommendation trends
            if "finnhub_recommendations" in fundamental_data and fundamental_data["finnhub_recommendations"]:
                recs = fundamental_data["finnhub_recommendations"][0]  # Most recent
                
                # Calculate sentiment score from recommendations (0-100 scale)
                if all(k in recs for k in ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']):
                    strong_buy = recs['strongBuy'] * 100
                    buy = recs['buy'] * 75
                    hold = recs['hold'] * 50
                    sell = recs['sell'] * 25
                    strong_sell = recs['strongSell'] * 0
                    
                    total_ratings = recs['strongBuy'] + recs['buy'] + recs['hold'] + recs['sell'] + recs['strongSell']
                    
                    if total_ratings > 0:
                        results['analyst_consensus_score'] = (strong_buy + buy + hold + sell + strong_sell) / total_ratings
            
            # Use earnings surprises
            if "finnhub_earnings" in fundamental_data and fundamental_data["finnhub_earnings"]:
                earnings = fundamental_data["finnhub_earnings"]
                
                # Calculate surprise score
                surprise_sum = 0
                count = 0
                
                for quarter in earnings[:4]:  # Last 4 quarters
                    if 'surprisePercent' in quarter:
                        surprise_sum += quarter['surprisePercent']
                        count += 1
                
                if count > 0:
                    avg_surprise = surprise_sum / count
                    # Normalize to 0-100 scale with 0% surprise at 50
                    results['earnings_surprise_score'] = min(max(50 + avg_surprise * 5, 0), 100)
                    
        except Exception as e:
            console.print(f"[yellow]Error incorporating Finnhub data: {e}[/yellow]")
    
    # 4. Add Financial Datasets data
    if financial_datasets_enabled:
        try:
            fd_results = analyze_financial_datasets_data(financial_datasets_data, console)
            
            # Add economic indicators and other metrics
            for key, value in fd_results.items():
                results[key] = value
        except Exception as e:
            console.print(f"[yellow]Error incorporating Financial Datasets data: {e}[/yellow]")
    
    return results

def analyze_alpha_vantage_data(alpha_vantage_data, console):
    """Analyze fundamental data from Alpha Vantage"""
    if not alpha_vantage_data:
        return {}
        
    results = {}
    try:
        # Extract key financial metrics
        
        # From Overview (company metadata)
        if 'overview' in alpha_vantage_data:
            overview = alpha_vantage_data['overview']
            
            metrics = [
                'PERatio', 'PEGRatio', 'BookValue', 'DividendPerShare',
                'DividendYield', 'EPS', 'ProfitMargin', 'OperatingMarginTTM',
                'ReturnOnAssetsTTM', 'ReturnOnEquityTTM', 'RevenueTTM',
                'GrossProfitTTM', 'DilutedEPSTTM', 'QuarterlyEarningsGrowthYOY',
                'QuarterlyRevenueGrowthYOY', 'AnalystTargetPrice',
                'TrailingPE', 'ForwardPE', 'PriceToSalesRatioTTM',
                'PriceToBookRatio', 'EVToRevenue', 'EVToEBITDA', 'Beta',
                '52WeekHigh', '52WeekLow'
            ]
            
            for metric in metrics:
                if metric in overview and overview[metric] not in ['None', '']:
                    try:
                        results[metric] = float(overview[metric])
                    except:
                        # Handle non-numeric values
                        results[metric] = overview[metric]
        
        # From Income Statement
        if 'income_statement' in alpha_vantage_data:
            income = alpha_vantage_data['income_statement']
            if 'annualReports' in income and len(income['annualReports']) > 0:
                latest = income['annualReports'][0]
                
                # Calculate Revenue Growth YoY if we have at least 2 years of data
                if len(income['annualReports']) > 1:
                    current_revenue = float(latest['totalRevenue'])
                    previous_revenue = float(income['annualReports'][1]['totalRevenue'])
                    results['RevenueGrowthYoY'] = ((current_revenue - previous_revenue) / previous_revenue) * 100
                
                # Calculate Net Income Growth YoY
                if len(income['annualReports']) > 1:
                    current_income = float(latest['netIncome'])
                    previous_income = float(income['annualReports'][1]['netIncome'])
                    results['NetIncomeGrowthYoY'] = ((current_income - previous_income) / previous_income) * 100
        
        # From Balance Sheet
        if 'balance_sheet' in alpha_vantage_data:
            balance = alpha_vantage_data['balance_sheet']
            if 'annualReports' in balance and len(balance['annualReports']) > 0:
                latest = balance['annualReports'][0]
                
                # Calculate Debt-to-Equity ratio
                if 'totalShareholderEquity' in latest and 'shortLongTermDebtTotal' in latest:
                    equity = float(latest['totalShareholderEquity'])
                    debt = float(latest['shortLongTermDebtTotal'])
                    if equity > 0:
                        results['DebtToEquity'] = debt / equity
                
                # Calculate Current Ratio
                if 'totalCurrentAssets' in latest and 'totalCurrentLiabilities' in latest:
                    current_assets = float(latest['totalCurrentAssets'])
                    current_liabilities = float(latest['totalCurrentLiabilities'])
                    if current_liabilities > 0:
                        results['CurrentRatio'] = current_assets / current_liabilities
        
        # From Cash Flow
        if 'cash_flow' in alpha_vantage_data:
            cash_flow = alpha_vantage_data['cash_flow']
            if 'annualReports' in cash_flow and len(cash_flow['annualReports']) > 0:
                latest = cash_flow['annualReports'][0]
                
                # Free Cash Flow
                if 'operatingCashflow' in latest and 'capitalExpenditures' in latest:
                    operating_cash = float(latest['operatingCashflow'])
                    capex = float(latest['capitalExpenditures'])
                    results['FreeCashFlow'] = operating_cash - capex
        
        # Calculate financial health score (simplified)
        financial_health_score = 0
        count = 0
        
        # Profitability
        if 'ReturnOnEquityTTM' in results:
            roe = results['ReturnOnEquityTTM']
            if roe > 15:
                financial_health_score += 2
            elif roe > 10:
                financial_health_score += 1
            count += 1
        
        # Growth
        if 'RevenueGrowthYoY' in results:
            rev_growth = results['RevenueGrowthYoY']
            if rev_growth > 20:
                financial_health_score += 2
            elif rev_growth > 10:
                financial_health_score += 1
            count += 1
        
        # Valuation
        if 'PERatio' in results:
            pe = results['PERatio']
            if 5 < pe < 15:
                financial_health_score += 1
            count += 1
        
        # Debt
        if 'DebtToEquity' in results:
            dte = results['DebtToEquity']
            if dte < 0.5:
                financial_health_score += 2
            elif dte < 1:
                financial_health_score += 1
            count += 1
        
        # Liquidity
        if 'CurrentRatio' in results:
            cr = results['CurrentRatio']
            if cr > 1.5:
                financial_health_score += 1
            count += 1
        
        # Calculate overall score if we have at least 3 metrics
        if count >= 3:
            results['FinancialHealthScore'] = (financial_health_score / (count * 2)) * 100
        
        return results
        
    except Exception as e:
        console.print(f"[yellow]Error analyzing Alpha Vantage data: {e}[/yellow]")
        return {}

def analyze_financial_datasets_data(financial_datasets_data, console):
    """Analyze data from Financial Datasets"""
    if not financial_datasets_data:
        return {}
        
    results = {}
    try:
        # Parse financial data from financialdatasets.ai
        # Note: This is a placeholder - adjust based on actual API response structure
        if 'financials' in financial_datasets_data:
            financials = financial_datasets_data['financials']
            # Extract relevant metrics based on your API's structure
            # Example:
            if 'metrics' in financials:
                metrics = financials['metrics']
                for key, value in metrics.items():
                    results[key] = value
            
        # Extract economic indicators that might affect the stock
        if 'economic_indicators' in financial_datasets_data:
            indicators = financial_datasets_data['economic_indicators']
            # Process economic indicators - adjust based on your API's structure
            
            # Example economic indicators that might affect decision:
            economic_score = 0
            count = 0
            
            # Sample indicators - replace with actual data from your API
            indicator_mapping = {
                'fed_rate': {'value': 0, 'threshold': 4.5, 'impact': -1},  # Higher rates often negative
                'gdp_growth': {'value': 0, 'threshold': 2.0, 'impact': 1},  # Higher growth often positive
                'inflation': {'value': 0, 'threshold': 3.0, 'impact': -1},  # Higher inflation often negative
                'unemployment': {'value': 0, 'threshold': 4.0, 'impact': -1},  # Higher unemployment often negative
            }
            
            # Find and update values from the API response
            for indicator_name, indicator_data in indicator_mapping.items():
                if indicator_name in indicators:
                    indicator_data['value'] = indicators[indicator_name]
                    
                    # Evaluate the indicator
                    if indicator_data['impact'] > 0:  # Positive impact indicator
                        if indicator_data['value'] > indicator_data['threshold']:
                            economic_score += 1
                        else:
                            economic_score -= 1
                    else:  # Negative impact indicator
                        if indicator_data['value'] > indicator_data['threshold']:
                            economic_score -= 1
                        else:
                            economic_score += 1
                            
                    count += 1
                    results[f"{indicator_name}_impact"] = economic_score
            
            # Calculate overall economic environment score if we have data
            if count > 0:
                results['economic_environment_score'] = (economic_score / count) * 50 + 50  # Scale to 0-100
        
        return results
        
    except Exception as e:
        console.print(f"[yellow]Error analyzing Financial Datasets data: {e}[/yellow]")
        return {}