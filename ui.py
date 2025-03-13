#!/usr/bin/env python3
# UI components for Stock Trading Companion

import os
import datetime as dt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

def display_summary(data, ticker, decision, analysis_results, fundamental_data, 
                    finnhub_enabled, alpha_vantage_enabled, financial_datasets_enabled, console):
    """Display a summary of the analysis"""
    if data is None or data.empty:
        console.print("[yellow]No data available for summary[/yellow]")
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
    current_price = data['Close'].iloc[-1]
    prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
    price_change = current_price - prev_close
    price_change_pct = (price_change / prev_close) * 100
    
    header_text = Text()
    header_text.append(f"\n{ticker} - ", style="bold")
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
    }.get(decision["action"], "white")
    
    decision_text = Text()
    decision_text.append(f"\nRECOMMENDATION: ", style="bold")
    decision_text.append(f"{decision['action']}\n\n", style=f"bold {decision_color}")
    decision_text.append(f"Confidence: {decision['confidence']:.2f}%\n")
    decision_text.append(f"Score: {decision['score']:.2f}/100\n")
    
    # Add score gauge
    score = decision["score"]
    gauge_width = 20
    gauge_fill = int((score / 100) * gauge_width)
    
    decision_text.append("\nBearish ")
    for i in range(gauge_width):
        if i < gauge_fill:
            decision_text.append("█", style="green" if score > 50 else "red")
        else:
            decision_text.append("░")
    decision_text.append(" Bullish")
    
    # Add component scores if available
    if 'component_scores' in decision:
        components = decision['component_scores']
        decision_text.append("\n\nComponent Scores:")
        for name, value in components.items():
            if name != 'weights':  # Skip weights
                color = "green" if value > 60 else "red" if value < 40 else "yellow"
                decision_text.append(f"\n{name.replace('_', ' ').title()}: ")
                decision_text.append(f"{value:.1f}", style=color)
    
    layout["decision"].update(Panel(decision_text, title="Trading Decision"))
    
    # Metrics panel
    metrics_table = Table(show_header=True, box=box.SIMPLE)
    metrics_table.add_column("Indicator", style="cyan")
    metrics_table.add_column("Value", style="white")
    metrics_table.add_column("Signal", style="white")
    
    # Technical indicators
    tech_signals = analysis_results.get('technical', {})
    indicators = analysis_results.get('indicators', {})
    
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
    
    if 'sma_200' in indicators:
        sma_200 = indicators['sma_200'][-1]
        ma_signal = "Bullish" if current_price > sma_200 else "Bearish"
        ma_color = "green" if current_price > sma_200 else "red"
        metrics_table.add_row("Price vs SMA(200)", f"{sma_200:.2f}", f"[{ma_color}]{ma_signal}[/{ma_color}]")
    
    # Show ADX (trend strength)
    if 'adx' in indicators:
        adx_value = indicators['adx'][-1]
        trend_strength = "Strong" if adx_value > 25 else "Weak"
        trend_color = "cyan" if adx_value > 25 else "yellow"
        metrics_table.add_row("ADX (Trend Strength)", f"{adx_value:.2f}", f"[{trend_color}]{trend_strength}[/{trend_color}]")
    
    # Fundamental metrics
    fund_analysis = analysis_results.get('fundamental', {})
    
    # Add metrics from different data sources with source labels
    
    # Price targets
    price_target_sources = []
    if 'targetMeanPrice' in fund_analysis:
        price_target_sources.append(("Yahoo", fund_analysis['targetMeanPrice']))
    if 'AnalystTargetPrice' in fund_analysis:
        price_target_sources.append(("Alpha Vantage", float(fund_analysis['AnalystTargetPrice'])))
    if 'finnhub_price_target' in fundamental_data and 'targetMean' in fundamental_data['finnhub_price_target']:
        price_target_sources.append(("Finnhub", fundamental_data['finnhub_price_target']['targetMean']))
    
    if price_target_sources:
        for source, target in price_target_sources:
            upside = ((target - current_price) / current_price) * 100
            target_color = "green" if upside > 5 else "red" if upside < -5 else "yellow"
            metrics_table.add_row(
                f"Price Target ({source})",
                f"${target:.2f}",
                f"[{target_color}]{upside:.1f}% {'upside' if upside >= 0 else 'downside'}[/{target_color}]"
            )
    
    # PE Ratio
    pe_sources = []
    if 'trailingPE' in fund_analysis:
        pe_sources.append(("Yahoo", fund_analysis['trailingPE']))
    if 'PERatio' in fund_analysis:
        pe_sources.append(("Alpha Vantage", float(fund_analysis['PERatio'])))
    
    if pe_sources:
        for source, pe in pe_sources:
            pe_color = "green" if 10 <= pe <= 25 else "yellow"
            metrics_table.add_row(f"P/E Ratio ({source})", f"{pe:.2f}", "")
    
    # Growth metrics
    if 'RevenueGrowthYoY' in fund_analysis:
        growth = fund_analysis['RevenueGrowthYoY']
        growth_color = "green" if growth > 10 else "red" if growth < 0 else "yellow"
        metrics_table.add_row(
            "Revenue Growth (YoY)",
            f"{growth:.2f}%",
            f"[{growth_color}]{'Strong' if growth > 15 else 'Moderate' if growth > 5 else 'Weak'}[/{growth_color}]"
        )
    
    # Financial health
    if 'financial_health_score' in fund_analysis:
        health = fund_analysis['financial_health_score']
        health_color = "green" if health > 70 else "red" if health < 40 else "yellow"
        metrics_table.add_row(
            "Financial Health",
            f"{health:.1f}/100",
            f"[{health_color}]{'Strong' if health > 70 else 'Moderate' if health > 40 else 'Weak'}[/{health_color}]"
        )
    
    # Sentiment
    sentiment = analysis_results.get('sentiment', 0.5) * 100
    sentiment_signal = "Bullish" if sentiment > 60 else "Bearish" if sentiment < 40 else "Neutral"
    sentiment_color = "green" if sentiment > 60 else "red" if sentiment < 40 else "yellow"
    metrics_table.add_row("News Sentiment", f"{sentiment:.1f}%", f"[{sentiment_color}]{sentiment_signal}[/{sentiment_color}]")
    
    # Economic indicators if available
    if 'economic_environment_score' in fund_analysis:
        eco_score = fund_analysis['economic_environment_score']
        eco_color = "green" if eco_score > 60 else "red" if eco_score < 40 else "yellow"
        metrics_table.add_row(
            "Economic Environment",
            f"{eco_score:.1f}/100",
            f"[{eco_color}]{'Favorable' if eco_score > 60 else 'Unfavorable' if eco_score < 40 else 'Neutral'}[/{eco_color}]"
        )
    
    layout["metrics"].update(Panel(metrics_table, title="Key Metrics"))
    
    # Footer showing data sources
    data_sources = []
    if data is not None and not data.empty:
        data_sources.append("Yahoo Finance")
    if finnhub_enabled:
        data_sources.append("Finnhub")
    if alpha_vantage_enabled:
        data_sources.append("Alpha Vantage")
    if financial_datasets_enabled:
        data_sources.append("Financial Datasets")
    
    source_text = "Data Sources: " + ", ".join(data_sources)
    time_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer_text = f"{source_text}\nAnalysis Time: {time_str}"
    
    layout["footer"].update(Panel(footer_text, title="Information"))
    
    # Render layout
    console.print(layout)

def show_info(ticker, fundamental_data, alpha_vantage_enabled, alpha_vantage_data, 
              finnhub_enabled, console):
    """Show detailed company information"""
    if not ticker:
        console.print("[red]No ticker selected. Use 'symbol <ticker>' first.[/red]")
        return
        
    company_info = {}
    
    # Get info from Yahoo Finance
    if fundamental_data and "info" in fundamental_data:
        yf_info = fundamental_data["info"]
        for key in ['longName', 'sector', 'industry', 'website', 'longBusinessSummary']:
            if key in yf_info:
                company_info[key] = yf_info[key]
    
    # Get info from Alpha Vantage if available
    if alpha_vantage_enabled and 'overview' in alpha_vantage_data:
        av_info = alpha_vantage_data['overview']
        for key in ['Name', 'Description', 'Exchange', 'Sector', 'Industry', 'Address', 'FullTimeEmployees']:
            if key in av_info:
                company_info[f"AV_{key}"] = av_info[key]
    
    # Get info from Finnhub if available
    if finnhub_enabled and 'finnhub_profile' in fundamental_data:
        fh_info = fundamental_data['finnhub_profile']
        for key in ['name', 'exchange', 'ipo', 'marketCapitalization', 'shareOutstanding']:
            if key in fh_info:
                company_info[f"FH_{key}"] = fh_info[key]
    
    # Create a rich panel with company information
    if company_info:
        info_text = ""
        
        # Company name and basic information
        if 'longName' in company_info:
            info_text += f"[bold cyan]{company_info['longName']}[/bold cyan]\n\n"
        elif 'AV_Name' in company_info:
            info_text += f"[bold cyan]{company_info['AV_Name']}[/bold cyan]\n\n"
        
        # Sector and industry
        if 'sector' in company_info and 'industry' in company_info:
            info_text += f"[bold]Sector:[/bold] {company_info['sector']} | [bold]Industry:[/bold] {company_info['industry']}\n\n"
        elif 'AV_Sector' in company_info and 'AV_Industry' in company_info:
            info_text += f"[bold]Sector:[/bold] {company_info['AV_Sector']} | [bold]Industry:[/bold] {company_info['AV_Industry']}\n\n"
        
        # Market cap and other financials from Finnhub
        if 'FH_marketCapitalization' in company_info:
            market_cap = company_info['FH_marketCapitalization']
            info_text += f"[bold]Market Cap:[/bold] ${market_cap:,.2f}M\n"
        
        if 'FH_shareOutstanding' in company_info:
            shares = company_info['FH_shareOutstanding']
            info_text += f"[bold]Shares Outstanding:[/bold] {shares:,.2f}M\n\n"
        
        # Website
        if 'website' in company_info:
            info_text += f"[bold]Website:[/bold] {company_info['website']}\n\n"
        
        # Business summary
        if 'longBusinessSummary' in company_info:
            info_text += "[bold]Business Summary:[/bold]\n"
            info_text += f"{company_info['longBusinessSummary']}\n"
        elif 'AV_Description' in company_info:
            info_text += "[bold]Business Description:[/bold]\n"
            info_text += f"{company_info['AV_Description']}\n"
        
        console.print(Panel(info_text, title=f"Company Information: {ticker}", border_style="blue"))
    else:
        console.print("[yellow]No detailed company information available.[/yellow]")

def generate_report(ticker, data, decision, analysis_results, fundamental_data, news_data,
                    finnhub_enabled, alpha_vantage_enabled, financial_datasets_enabled,
                    make_decision, console):
    """Generate a comprehensive analysis report"""
    if not ticker or data is None or data.empty:
        console.print("[red]No data available for report. Load a ticker first.[/red]")
        return
        
    try:
        # Make sure we have the latest analysis
        make_decision()
        
        # Create the report directory if it doesn't exist
        os.makedirs('reports', exist_ok=True)
        
        # Report filename
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/{ticker}_analysis_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            # Report header
            f.write(f"=========================================================\n")
            f.write(f"  STOCK TRADING COMPANION - ANALYSIS REPORT\n")
            f.write(f"  {ticker} - {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"=========================================================\n\n")
            
            # Trading decision
            f.write(f"RECOMMENDATION: {decision['action']}\n")
            f.write(f"Confidence: {decision['confidence']:.2f}%\n")
            f.write(f"Score: {decision['score']:.2f}/100\n\n")
            
            # Current price information
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2] if len(data) > 1 else current_price
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            
            f.write(f"Current Price: ${current_price:.2f}\n")
            f.write(f"Change: {'+' if price_change >= 0 else ''}{price_change:.2f} ({price_change_pct:.2f}%)\n\n")
            
            # Component scores
            if 'component_scores' in decision:
                f.write(f"COMPONENT ANALYSIS:\n")
                f.write(f"------------------\n")
                for name, value in decision['component_scores'].items():
                    if name != 'weights':
                        f.write(f"{name.replace('_', ' ').title()}: {value:.2f}/100\n")
                f.write("\n")
            
            # Technical Analysis
            f.write(f"TECHNICAL ANALYSIS:\n")
            f.write(f"------------------\n")
            tech_signals = analysis_results.get('technical', {})
            indicators = analysis_results.get('indicators', {})
            
            # Count bullish/bearish/neutral signals
            if tech_signals:
                bullish = sum(1 for v in tech_signals.values() if v > 0)
                bearish = sum(1 for v in tech_signals.values() if v < 0)
                neutral = sum(1 for v in tech_signals.values() if v == 0)
                total = len(tech_signals)
                
                f.write(f"Signal Summary: {bullish} bullish, {bearish} bearish, {neutral} neutral (total: {total})\n\n")
            
            # Key indicators
            if 'rsi' in indicators:
                rsi_value = indicators['rsi'][-1]
                rsi_signal = "Oversold (Bullish)" if rsi_value < 30 else "Overbought (Bearish)" if rsi_value > 70 else "Neutral"
                f.write(f"RSI (14): {rsi_value:.2f} - {rsi_signal}\n")
            
            if all(k in indicators for k in ['macd', 'macd_signal']):
                macd_value = indicators['macd'][-1]
                macd_signal_value = indicators['macd_signal'][-1]
                macd_status = "Bullish" if macd_value > macd_signal_value else "Bearish"
                f.write(f"MACD: {macd_value:.2f} vs Signal {macd_signal_value:.2f} - {macd_status}\n")
            
            if 'sma_50' in indicators and 'sma_200' in indicators:
                sma_50 = indicators['sma_50'][-1]
                sma_200 = indicators['sma_200'][-1]
                ma_signal = "Golden Cross (Bullish)" if sma_50 > sma_200 else "Death Cross (Bearish)"
                f.write(f"Moving Averages: SMA50 {sma_50:.2f} vs SMA200 {sma_200:.2f} - {ma_signal}\n")
                
                price_vs_ma = "Above key MAs (Bullish)" if current_price > sma_50 and current_price > sma_200 else \
                              "Below key MAs (Bearish)" if current_price < sma_50 and current_price < sma_200 else \
                              "Mixed MA signals"
                f.write(f"Price vs MAs: {price_vs_ma}\n")
            
            f.write("\n")
            
            # Fundamental Analysis
            f.write(f"FUNDAMENTAL ANALYSIS:\n")
            f.write(f"--------------------\n")
            fundamentals = analysis_results.get('fundamental', {})
            
            # Price targets from different sources
            f.write("Price Targets:\n")
            targets_found = False
            
            if 'targetMeanPrice' in fundamentals:
                target = fundamentals['targetMeanPrice']
                upside = ((target - current_price) / current_price) * 100
                f.write(f"  Yahoo Finance: ${target:.2f} ({upside:.2f}% {'upside' if upside >= 0 else 'downside'})\n")
                targets_found = True
            
            if 'AnalystTargetPrice' in fundamentals:
                try:
                    target = float(fundamentals['AnalystTargetPrice'])
                    upside = ((target - current_price) / current_price) * 100
                    f.write(f"  Alpha Vantage: ${target:.2f} ({upside:.2f}% {'upside' if upside >= 0 else 'downside'})\n")
                    targets_found = True
                except:
                    pass
            
            if 'finnhub_price_target' in fundamental_data and 'targetMean' in fundamental_data['finnhub_price_target']:
                target = fundamental_data['finnhub_price_target']['targetMean']
                upside = ((target - current_price) / current_price) * 100
                f.write(f"  Finnhub: ${target:.2f} ({upside:.2f}% {'upside' if upside >= 0 else 'downside'})\n")
                targets_found = True
            
            if not targets_found:
                f.write("  No price targets available\n")
            
            f.write("\n")
            
            # Valuation metrics
            f.write("Valuation Metrics:\n")
            valuation_found = False
            
            for label, key in [
                ("P/E Ratio", "trailingPE"),
                ("Forward P/E", "forwardPE"),
                ("PEG Ratio", "pegRatio"),
                ("Price/Book", "priceToBook"),
                ("Price/Sales", "PriceToSalesRatioTTM")
            ]:
                if key in fundamentals:
                    f.write(f"  {label}: {fundamentals[key]:.2f}\n")
                    valuation_found = True
            
            if not valuation_found:
                f.write("  No valuation metrics available\n")
            
            f.write("\n")
            
            # Growth metrics
            f.write("Growth & Performance:\n")
            growth_found = False
            
            for label, key in [
                ("Revenue Growth YoY", "RevenueGrowthYoY"),
                ("Net Income Growth YoY", "NetIncomeGrowthYoY"),
                ("Return on Equity", "returnOnEquity"),
                ("Profit Margin", "profitMargins")
            ]:
                if key in fundamentals:
                    value = fundamentals[key]
                    if "Growth" in label or "Margin" in label:
                        f.write(f"  {label}: {value:.2f}%\n")
                    else:
                        f.write(f"  {label}: {value:.2f}\n")
                    growth_found = True
            
            if not growth_found:
                f.write("  No growth metrics available\n")
            
            f.write("\n")
            
            # Financial health
            f.write("Financial Health:\n")
            health_found = False
            
            if 'financial_health_score' in fundamentals:
                score = fundamentals['financial_health_score']
                rating = "Strong" if score >= 70 else "Moderate" if score >= 40 else "Weak"
                f.write(f"  Overall Financial Health: {score:.1f}/100 ({rating})\n")
                health_found = True
            
            for label, key in [
                ("Debt-to-Equity", "DebtToEquity"),
                ("Current Ratio", "CurrentRatio"),
                ("Quick Ratio", "QuickRatio")
            ]:
                if key in fundamentals:
                    f.write(f"  {label}: {fundamentals[key]:.2f}\n")
                    health_found = True
            
            if not health_found:
                f.write("  No financial health metrics available\n")
            
            f.write("\n")
            
            # Sentiment and News Analysis
            f.write("SENTIMENT ANALYSIS:\n")
            f.write("------------------\n")
            sentiment = analysis_results.get('sentiment', 0.5) * 100
            sentiment_rating = "Bullish" if sentiment > 60 else "Bearish" if sentiment < 40 else "Neutral"
            
            f.write(f"News Sentiment Score: {sentiment:.1f}/100 ({sentiment_rating})\n\n")
            
            # Recent news headlines
            if news_data:
                f.write("Recent News Headlines:\n")
                for i, news in enumerate(news_data[:5], 1):
                    if 'headline' in news and 'datetime' in news:
                        date = dt.datetime.fromtimestamp(news['datetime']).strftime('%Y-%m-%d')
                        f.write(f"  {i}. {date} - {news['headline']}\n")
                f.write("\n")
            
            # Economic Environment
            if 'economic_environment_score' in fundamentals:
                f.write("ECONOMIC ENVIRONMENT:\n")
                f.write("--------------------\n")
                eco_score = fundamentals['economic_environment_score']
                eco_rating = "Favorable" if eco_score > 60 else "Unfavorable" if eco_score < 40 else "Neutral"
                
                f.write(f"Economic Environment Score: {eco_score:.1f}/100 ({eco_rating})\n\n")
                
                # List specific economic indicators if available
                indicators_found = False
                for key in fundamentals:
                    if key.endswith('_impact') and 'economic' in key:
                        indicator = key.replace('_impact', '').replace('economic_', '')
                        impact = fundamentals[key]
                        impact_str = "Positive" if impact > 0 else "Negative" if impact < 0 else "Neutral"
                        f.write(f"  {indicator.title()}: {impact_str} impact on stock\n")
                        indicators_found = True
                
                if not indicators_found:
                    f.write("  No specific economic indicators available\n")
                
                f.write("\n")
            
            # Data sources used
            f.write("DATA SOURCES:\n")
            f.write("------------\n")
            data_sources = []
            if data is not None and not data.empty:
                data_sources.append("Yahoo Finance")
            if finnhub_enabled:
                data_sources.append("Finnhub")
            if alpha_vantage_enabled:
                data_sources.append("Alpha Vantage")
            if financial_datasets_enabled:
                data_sources.append("Financial Datasets")
            
            f.write(", ".join(data_sources) + "\n\n")
            
            # Report footer
            f.write(f"=========================================================\n")
            f.write(f"This report was generated using the Stock Trading Companion.\n")
            f.write(f"Time: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"=========================================================\n")
        
        console.print(f"[green]Report saved to {report_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")

def show_available_metrics(ticker, fundamental_data, alpha_vantage_enabled, alpha_vantage_data,
                          finnhub_enabled, financial_datasets_enabled, financial_datasets_data,
                          analysis_results, console):
    """Show what metrics are available from each data source"""
    if not ticker:
        console.print("[red]No ticker selected. Use 'symbol <ticker>' first.[/red]")
        return
        
    table = Table(title=f"Available Metrics for {ticker}")
    table.add_column("Source", style="cyan")
    table.add_column("Available Metrics", style="green")
    table.add_column("Count", style="yellow")
    
    # Yahoo Finance metrics
    if fundamental_data and "info" in fundamental_data:
        yf_metrics = list(fundamental_data["info"].keys())
        table.add_row(
            "Yahoo Finance",
            ", ".join(sorted(yf_metrics)[:10]) + f"... (+{len(yf_metrics)-10} more)",
            str(len(yf_metrics))
        )
    else:
        table.add_row("Yahoo Finance", "None", "0")
    
    # Alpha Vantage metrics
    if alpha_vantage_enabled and alpha_vantage_data:
        av_metrics = []
        for category, data in alpha_vantage_data.items():
            if category == 'overview' and isinstance(data, dict):
                av_metrics.extend(data.keys())
            elif category in ['income_statement', 'balance_sheet', 'cash_flow']:
                if 'annualReports' in data and data['annualReports']:
                    av_metrics.extend(data['annualReports'][0].keys())
        
        av_metrics = list(set(av_metrics))  # Remove duplicates
        if av_metrics:
            table.add_row(
                "Alpha Vantage",
                ", ".join(sorted(av_metrics)[:10]) + f"... (+{len(av_metrics)-10} more)",
                str(len(av_metrics))
            )
        else:
            table.add_row("Alpha Vantage", "None", "0")
    else:
        table.add_row("Alpha Vantage", "None (API not enabled)", "0")
    
    # Finnhub metrics
    if finnhub_enabled and fundamental_data:
        finnhub_metrics = []
        for key in fundamental_data.keys():
            if key.startswith('finnhub_'):
                finnhub_data = fundamental_data[key]
                if isinstance(finnhub_data, dict):
                    finnhub_metrics.extend(finnhub_data.keys())
        
        finnhub_metrics = list(set(finnhub_metrics))  # Remove duplicates
        if finnhub_metrics:
            table.add_row(
                "Finnhub",
                ", ".join(sorted(finnhub_metrics)[:10]) + f"... (+{len(finnhub_metrics)-10} more)",
                str(len(finnhub_metrics))
            )
        else:
            table.add_row("Finnhub", "None", "0")
    else:
        table.add_row("Finnhub", "None (API not enabled)", "0")
    
    # Financial Datasets metrics
    if financial_datasets_enabled and financial_datasets_data:
        fd_metrics = []
        for category, data in financial_datasets_data.items():
            if isinstance(data, dict):
                fd_metrics.extend(data.keys())
        
        fd_metrics = list(set(fd_metrics))  # Remove duplicates
        if fd_metrics:
            table.add_row(
                "Financial Datasets",
                ", ".join(sorted(fd_metrics)[:10]) + f"... (+{len(fd_metrics)-10} more)",
                str(len(fd_metrics))
            )
        else:
            table.add_row("Financial Datasets", "None", "0")
    else:
        table.add_row("Financial Datasets", "None (Not enabled)", "0")
    
    # Analysis results
    if analysis_results:
        analysis_metrics = []
        for category, data in analysis_results.items():
            if isinstance(data, dict):
                analysis_metrics.extend([f"{category}.{key}" for key in data.keys()])
            else:
                analysis_metrics.append(category)
        
        if analysis_metrics:
            table.add_row(
                "Analysis Results",
                ", ".join(sorted(analysis_metrics)[:10]) + f"... (+{len(analysis_metrics)-10} more)",
                str(len(analysis_metrics))
            )
        else:
            table.add_row("Analysis Results", "None", "0")
    else:
        table.add_row("Analysis Results", "None (Analysis not run)", "0")
    
    # Display the table
    console.print(table)

def show_help(console):
    """Display help information"""
    help_text = """
    Stock Trading Companion - Command Reference
    
    Commands:
    - symbol <ticker>     : Load data for a new ticker symbol (e.g., symbol AAPL)
    - analyze             : Analyze current stock and make trading decision
    - charts              : Generate and save technical analysis charts
    - news                : Show recent news for current stock
    - info                : Show detailed company information
    - report              : Generate comprehensive analysis report
    - metrics             : Show available metrics from all data sources
    - help                : Show this help message
    - exit                : Exit the program
    
    Options:
    - period <period>     : Set data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    - interval <interval> : Set data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
    - risk <level>        : Set risk tolerance (low, medium, high)
    
    Examples:
    > symbol MSFT         : Load Microsoft stock data
    > period 6mo          : Set period to 6 months
    > interval 1d         : Set interval to daily
    > analyze             : Analyze the stock
    > charts              : Generate technical analysis charts
    > info                : Show detailed company information
    """
    
    console.print(Panel(help_text, title="Help", border_style="blue"))

def display_technical_indicators(ticker, data, indicators, console):
    """Display detailed technical indicators"""
    if not ticker or data is None or data.empty:
        console.print("[red]No data available for technical indicators. Load a ticker first.[/red]")
        return
    
    if not indicators or len(indicators) == 0:
        console.print("[yellow]No technical indicators have been calculated.[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Technical Indicators for {ticker}")
    table.add_column("Indicator", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Signal", style="white")
    
    # Current price info
    current_price = data['Close'].iloc[-1]
    table.add_row("Current Price", f"${current_price:.2f}", "")
    
    # RSI
    if 'rsi' in indicators and len(indicators['rsi']) > 0:
        rsi_value = indicators['rsi'][-1]
        rsi_signal = "Oversold (Bullish)" if rsi_value < 30 else "Overbought (Bearish)" if rsi_value > 70 else "Neutral"
        rsi_color = "green" if rsi_value < 30 else "red" if rsi_value > 70 else "yellow"
        table.add_row("RSI (14)", f"{rsi_value:.2f}", f"[{rsi_color}]{rsi_signal}[/{rsi_color}]")
    
    # MACD
    if all(k in indicators for k in ['macd', 'macd_signal']) and len(indicators['macd']) > 0:
        macd_value = indicators['macd'][-1]
        macd_signal_value = indicators['macd_signal'][-1]
        macd_hist = macd_value - macd_signal_value
        
        macd_signal = "Bullish" if macd_value > macd_signal_value else "Bearish"
        macd_color = "green" if macd_value > macd_signal_value else "red"
        table.add_row("MACD", f"{macd_value:.2f}", f"[{macd_color}]{macd_signal}[/{macd_color}]")
        table.add_row("MACD Signal", f"{macd_signal_value:.2f}", "")
        table.add_row("MACD Histogram", f"{macd_hist:.2f}", f"[{'green' if macd_hist > 0 else 'red'}]{'Positive' if macd_hist > 0 else 'Negative'}[/]")
    
    # Moving Averages
    for period in [20, 50, 100, 200]:
        key = f'sma_{period}'
        if key in indicators and len(indicators[key]) > 0:
            ma_value = indicators[key][-1]
            ma_signal = "Bullish" if current_price > ma_value else "Bearish"
            ma_color = "green" if current_price > ma_value else "red"
            table.add_row(
                f"SMA ({period})", 
                f"{ma_value:.2f}", 
                f"[{ma_color}]{ma_signal}[/{ma_color}]"
            )
    
    # EMA
    for period in [12, 26]:
        key = f'ema_{period}'
        if key in indicators and len(indicators[key]) > 0:
            ema_value = indicators[key][-1]
            ema_signal = "Bullish" if current_price > ema_value else "Bearish"
            ema_color = "green" if current_price > ema_value else "red"
            table.add_row(
                f"EMA ({period})",
                f"{ema_value:.2f}",
                f"[{ema_color}]{ema_signal}[/{ema_color}]"
            )
    
    # Bollinger Bands
    if all(k in indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']) and len(indicators['bb_middle']) > 0:
        upper = indicators['bb_upper'][-1]
        middle = indicators['bb_middle'][-1]
        lower = indicators['bb_lower'][-1]
        
        bb_signal = "Overbought (Bearish)" if current_price > upper else \
                   "Oversold (Bullish)" if current_price < lower else \
                   "Neutral"
        bb_color = "red" if current_price > upper else "green" if current_price < lower else "yellow"
        
        table.add_row("Bollinger Band Upper", f"{upper:.2f}", "")
        table.add_row("Bollinger Band Middle", f"{middle:.2f}", "")
        table.add_row("Bollinger Band Lower", f"{lower:.2f}", "")
        table.add_row("BB Position", f"{((current_price - lower) / (upper - lower) * 100):.1f}%", f"[{bb_color}]{bb_signal}[/{bb_color}]")
    
    # ADX (Trend Strength)
    if 'adx' in indicators and len(indicators['adx']) > 0:
        adx_value = indicators['adx'][-1]
        trend_strength = "Very Strong" if adx_value > 50 else \
                        "Strong" if adx_value > 25 else \
                        "Weak" if adx_value > 20 else \
                        "Absent/Ranging"
        
        trend_color = "bright_cyan" if adx_value > 50 else \
                     "cyan" if adx_value > 25 else \
                     "yellow" if adx_value > 20 else \
                     "red"
                     
        table.add_row("ADX (Trend Strength)", f"{adx_value:.2f}", f"[{trend_color}]{trend_strength}[/{trend_color}]")
    
    # Directional Indicators (DI)
    if all(k in indicators for k in ['plus_di', 'minus_di']) and len(indicators['plus_di']) > 0:
        plus_di = indicators['plus_di'][-1]
        minus_di = indicators['minus_di'][-1]
        
        di_signal = "Bullish" if plus_di > minus_di else "Bearish"
        di_color = "green" if plus_di > minus_di else "red"
        
        table.add_row("DI+ (14)", f"{plus_di:.2f}", "")
        table.add_row("DI- (14)", f"{minus_di:.2f}", "")
        table.add_row("DI Signal", f"+DI {'>' if plus_di > minus_di else '<'} -DI", f"[{di_color}]{di_signal}[/{di_color}]")
    
    # Stochastic Oscillator
    if all(k in indicators for k in ['slowk', 'slowd']) and len(indicators['slowk']) > 0:
        k_value = indicators['slowk'][-1]
        d_value = indicators['slowd'][-1]
        
        stoch_signal = "Overbought (Bearish)" if k_value > 80 else \
                      "Oversold (Bullish)" if k_value < 20 else \
                      "Neutral"
        stoch_color = "red" if k_value > 80 else "green" if k_value < 20 else "yellow"
        
        crossover = "Bullish" if k_value > d_value else "Bearish"
        crossover_color = "green" if k_value > d_value else "red"
        
        table.add_row("Stochastic %K", f"{k_value:.2f}", f"[{stoch_color}]{stoch_signal}[/{stoch_color}]")
        table.add_row("Stochastic %D", f"{d_value:.2f}", "")
        table.add_row("Stochastic Crossover", f"%K {'>' if k_value > d_value else '<'} %D", f"[{crossover_color}]{crossover}[/{crossover_color}]")
    
    # OBV (On Balance Volume)
    if 'obv' in indicators and len(indicators['obv']) > 1:
        obv_current = indicators['obv'][-1]
        obv_prev = indicators['obv'][-2]
        obv_change = obv_current - obv_prev
        
        obv_signal = "Increasing (Bullish)" if obv_change > 0 else "Decreasing (Bearish)"
        obv_color = "green" if obv_change > 0 else "red"
        
        table.add_row("On Balance Volume", f"{obv_current:,.0f}", f"[{obv_color}]{obv_signal}[/{obv_color}]")
    
    # Display the table
    console.print(table)