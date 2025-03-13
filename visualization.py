#!/usr/bin/env python3
# Visualization for Stock Trading Companion

import os
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # For environments without GUI

def generate_charts(ticker, data, analysis_results, decision, alpha_vantage_data, console):
    """Generate enhanced charts for technical analysis with multiple indicators"""
    if data is None or data.empty:
        return
        
    try:
        indicators = analysis_results.get('indicators', {})
        if not indicators:
            return
            
        # Create a directory for charts if it doesn't exist
        os.makedirs('charts', exist_ok=True)
        
        # Create a more comprehensive visualization
        fig = plt.figure(figsize=(14, 10))
        
        # Define more grid spaces for additional indicators
        gs = plt.GridSpec(5, 1, height_ratios=[3, 1, 1, 1, 1], hspace=0.15)
        
        # 1. Price chart with moving averages
        ax1 = plt.subplot(gs[0])
        ax1.plot(data.index, data['Close'], label='Close Price', linewidth=1.5)
        
        # Plot moving averages
        if 'sma_20' in indicators:
            ax1.plot(data.index, indicators['sma_20'], label='SMA 20', linestyle='--', linewidth=1)
        if 'sma_50' in indicators:
            ax1.plot(data.index, indicators['sma_50'], label='SMA 50', linestyle='--', linewidth=1)
        if 'sma_200' in indicators:
            ax1.plot(data.index, indicators['sma_200'], label='SMA 200', linestyle='--', linewidth=1)
        
        # Plot Bollinger Bands
        if all(k in indicators for k in ['bb_upper', 'bb_middle', 'bb_lower']):
            ax1.plot(data.index, indicators['bb_upper'], label='Bollinger Upper', color='gray', alpha=0.5)
            ax1.plot(data.index, indicators['bb_middle'], label='Bollinger Middle', color='gray', alpha=0.5)
            ax1.plot(data.index, indicators['bb_lower'], label='Bollinger Lower', color='gray', alpha=0.5)
            # Fill between upper and lower bands
            ax1.fill_between(data.index, indicators['bb_upper'], indicators['bb_lower'], color='gray', alpha=0.1)
        
        # Add volume as bars on the same chart but with a secondary y-axis
        ax1v = ax1.twinx()
        ax1v.bar(data.index, data['Volume'], color='lightgray', alpha=0.5, width=0.8)
        ax1v.set_ylabel('Volume')
        ax1v.grid(False)
        
        # Add decision recommendation as a text box
        if decision:
            action = decision.get('action', 'HOLD')
            score = decision.get('score', 50)
            conf = decision.get('confidence', 0)
            
            color = 'green' if action == 'BUY' else 'red' if action == 'SELL' else 'goldenrod'
            
            # Create a text box in a strategic position
            props = dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8)
            text = f'Recommendation: {action}\nScore: {score:.1f}/100\nConfidence: {conf:.1f}%'
            ax1.text(0.02, 0.05, text, transform=ax1.transAxes, fontsize=10,
                    verticalalignment='bottom', horizontalalignment='left',
                    bbox=props, color=color, fontweight='bold')
        
        ax1.set_title(f'{ticker} - Technical Analysis', fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.set_ylabel('Price')
        ax1.grid(True, alpha=0.3)
        ax1.set_xticklabels([])  # Remove x-axis labels for this subplot
        
        # 2. RSI
        ax2 = plt.subplot(gs[1], sharex=ax1)
        if 'rsi' in indicators:
            ax2.plot(data.index, indicators['rsi'], label='RSI', color='purple', linewidth=1.2)
            ax2.axhline(y=70, color='r', linestyle='-', alpha=0.3)
            ax2.axhline(y=30, color='g', linestyle='-', alpha=0.3)
            # Fill overbought regions
            ax2.fill_between(data.index, 70, indicators['rsi'], 
                            where=(indicators['rsi'] >= 70), color='red', alpha=0.3)
            # Fill oversold regions
            ax2.fill_between(data.index, 30, indicators['rsi'], 
                            where=(indicators['rsi'] <= 30), color='green', alpha=0.3)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('RSI')
        ax2.grid(True, alpha=0.3)
        ax2.set_xticklabels([])  # Remove x-axis labels for this subplot
        
        # 3. MACD
        ax3 = plt.subplot(gs[2], sharex=ax1)
        if all(k in indicators for k in ['macd', 'macd_signal', 'macd_hist']):
            ax3.plot(data.index, indicators['macd'], label='MACD', color='blue', linewidth=1.2)
            ax3.plot(data.index, indicators['macd_signal'], label='Signal', color='red', linewidth=1)
            
            # Color the histogram bars based on value
            pos = indicators['macd_hist'] > 0
            neg = indicators['macd_hist'] <= 0
            
            ax3.bar(data.index[pos], indicators['macd_hist'][pos], color='green', alpha=0.5, width=0.8)
            ax3.bar(data.index[neg], indicators['macd_hist'][neg], color='red', alpha=0.5, width=0.8)
            
            ax3.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax3.set_ylabel('MACD')
        ax3.grid(True, alpha=0.3)
        ax3.set_xticklabels([])  # Remove x-axis labels for this subplot
        
        # 4. Stochastic Oscillator
        ax4 = plt.subplot(gs[3], sharex=ax1)
        if 'slowk' in indicators and 'slowd' in indicators:
            ax4.plot(data.index, indicators['slowk'], label='%K', color='blue', linewidth=1.2)
            ax4.plot(data.index, indicators['slowd'], label='%D', color='red', linewidth=1)
            ax4.axhline(y=80, color='r', linestyle='-', alpha=0.3)
            ax4.axhline(y=20, color='g', linestyle='-', alpha=0.3)
            # Fill overbought regions
            ax4.fill_between(data.index, 80, 100, color='red', alpha=0.1)
            # Fill oversold regions
            ax4.fill_between(data.index, 0, 20, color='green', alpha=0.1)
        ax4.set_ylim(0, 100)
        ax4.set_ylabel('Stoch')
        ax4.grid(True, alpha=0.3)
        ax4.set_xticklabels([])  # Remove x-axis labels for this subplot
        
        # 5. Money Flow Index or ATR
        ax5 = plt.subplot(gs[4], sharex=ax1)
        if 'mfi' in indicators:
            ax5.plot(data.index, indicators['mfi'], label='MFI', color='darkgreen', linewidth=1.2)
            ax5.axhline(y=80, color='r', linestyle='-', alpha=0.3)
            ax5.axhline(y=20, color='g', linestyle='-', alpha=0.3)
            ax5.set_ylim(0, 100)
            ax5.set_ylabel('MFI')
        elif 'atr' in indicators:
            # Normalize ATR by price for better visualization
            norm_atr = (indicators['atr'] / data['Close']) * 100
            ax5.plot(data.index, norm_atr, label='ATR %', color='darkorange', linewidth=1.2)
            ax5.set_ylabel('ATR %')
        ax5.grid(True, alpha=0.3)
        
        # Format the x-axis dates for the last subplot
        fig.autofmt_xdate()
        
        # Add a super title with the stock name and date range
        start_date = data.index[0].strftime('%Y-%m-%d')
        end_date = data.index[-1].strftime('%Y-%m-%d')
        plt.suptitle(f"{ticker}: {start_date} to {end_date}", fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        chart_path = f'charts/{ticker}_technical_analysis.png'
        plt.savefig(chart_path, dpi=150)
        
        # Create a second chart for fundamental metrics if we have Alpha Vantage data
        if alpha_vantage_data:
            generate_fundamental_charts(ticker, alpha_vantage_data, console)
        
        plt.close('all')  # Close all figures to free memory
        
        console.print(f"[green]Charts saved to {chart_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error generating charts: {e}[/red]")

def generate_fundamental_charts(ticker, alpha_vantage_data, console):
    """Generate charts for fundamental analysis based on Alpha Vantage data"""
    try:
        if not alpha_vantage_data:
            return
            
        # Check for income statement data
        if 'income_statement' not in alpha_vantage_data or 'annualReports' not in alpha_vantage_data['income_statement']:
            return
            
        # Get annual reports
        reports = alpha_vantage_data['income_statement']['annualReports']
        if len(reports) < 2:
            return
            
        # Create figure for fundamental data
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Extract years and key metrics
        years = [report['fiscalDateEnding'].split('-')[0] for report in reports]
        years.reverse()  # Show oldest to newest
        
        # Revenue and Net Income
        revenues = [float(report['totalRevenue']) / 1_000_000 for report in reports]
        revenues.reverse()
        net_incomes = [float(report['netIncome']) / 1_000_000 for report in reports]
        net_incomes.reverse()
        
        ax1 = axes[0, 0]
        ax1.bar(years, revenues, color='blue', alpha=0.7, label='Revenue')
        ax1.set_title('Annual Revenue (in millions)', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # Add growth percentage on top of bars
        for i in range(1, len(revenues)):
            growth = ((revenues[i] - revenues[i-1]) / revenues[i-1]) * 100
            color = 'green' if growth >= 0 else 'red'
            ax1.annotate(f"{growth:.1f}%", 
                        xy=(years[i], revenues[i]),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        color=color,
                        fontweight='bold')
        
        ax2 = axes[0, 1]
        ax2.bar(years, net_incomes, color='green', alpha=0.7, label='Net Income')
        ax2.set_title('Annual Net Income (in millions)', fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        # Add growth percentage on top of bars
        for i in range(1, len(net_incomes)):
            if net_incomes[i-1] != 0:  # Avoid division by zero
                growth = ((net_incomes[i] - net_incomes[i-1]) / abs(net_incomes[i-1])) * 100
                color = 'green' if growth >= 0 else 'red'
                ax2.annotate(f"{growth:.1f}%", 
                            xy=(years[i], net_incomes[i]),
                            xytext=(0, 5),
                            textcoords="offset points",
                            ha='center', va='bottom',
                            color=color,
                            fontweight='bold')
        
        # Get balance sheet data if available
        if 'balance_sheet' in alpha_vantage_data and 'annualReports' in alpha_vantage_data['balance_sheet']:
            balance_reports = alpha_vantage_data['balance_sheet']['annualReports']
            if len(balance_reports) >= 2:
                # Extract assets and liabilities
                balance_years = [report['fiscalDateEnding'].split('-')[0] for report in balance_reports]
                balance_years.reverse()
                
                total_assets = [float(report['totalAssets']) / 1_000_000 for report in balance_reports]
                total_assets.reverse()
                
                total_liabilities = [float(report['totalLiabilities']) / 1_000_000 for report in balance_reports]
                total_liabilities.reverse()
                
                # Equity
                equity = [a - l for a, l in zip(total_assets, total_liabilities)]
                
                ax3 = axes[1, 0]
                ax3.bar(balance_years, total_assets, color='blue', alpha=0.6, label='Assets')
                ax3.bar(balance_years, total_liabilities, color='red', alpha=0.6, label='Liabilities')
                ax3.set_title('Assets vs Liabilities (in millions)', fontweight='bold')
                ax3.legend()
                ax3.grid(axis='y', alpha=0.3)
                
                # Calculate debt-to-equity ratio
                dte_ratios = []
                for report in balance_reports:
                    if 'shortLongTermDebtTotal' in report and 'totalShareholderEquity' in report:
                        debt = float(report['shortLongTermDebtTotal'])
                        equity_val = float(report['totalShareholderEquity'])
                        if equity_val > 0:
                            dte_ratios.append(debt / equity_val)
                        else:
                            dte_ratios.append(None)
                    else:
                        dte_ratios.append(None)
                
                dte_ratios.reverse()
                
                ax4 = axes[1, 1]
                x = range(len(balance_years))
                valid_indices = [i for i, r in enumerate(dte_ratios) if r is not None]
                valid_years = [balance_years[i] for i in valid_indices]
                valid_ratios = [dte_ratios[i] for i in valid_indices]
                
                if valid_ratios:
                    ax4.bar(valid_years, valid_ratios, color='purple', alpha=0.7)
                    ax4.set_title('Debt-to-Equity Ratio', fontweight='bold')
                    ax4.grid(axis='y', alpha=0.3)
                    
                    # Add horizontal line at 1.0 for reference
                    ax4.axhline(y=1.0, color='red', linestyle='--')
        
        plt.tight_layout()
        plt.suptitle(f"{ticker}: Fundamental Analysis", fontsize=16, fontweight='bold')
        plt.subplots_adjust(top=0.92)
        
        chart_path = f'charts/{ticker}_fundamental_analysis.png'
        plt.savefig(chart_path, dpi=150)
        plt.close()
        
        console.print(f"[green]Fundamental charts saved to {chart_path}[/green]")
        
    except Exception as e:
        console.print(f"[yellow]Error generating fundamental charts: {e}[/yellow]")