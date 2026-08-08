import pandas as pd

def engine_cost_profitability(df_sales, df_sourcing):
    """
    Calculates True Profit, top performers, and Dead Stock alerts.
    """
    # 1. Core Financial KPIs
    total_sales = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)']['Total Amount Client Paid You'].sum()
    true_profit = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)']['True Profit'].sum()
    
    # 2. Identify Top Performer
    top_performer = "N/A"
    if not df_sales.empty:
        top_performer = df_sales.groupby('Items Sold Summary')['Total Amount Client Paid You'].sum().idxmax()
        
    # 3. Dead Stock Alert (Capital tied up in trips > 45 days ago)
    cutoff_date = pd.Timestamp.today() - pd.Timedelta(days=45)
    dead_stock_trips = df_sourcing[df_sourcing['Date of Purchase'] < cutoff_date]
    dead_stock_capital = dead_stock_trips['Total Amount'].sum()
    
    return total_sales, true_profit, top_performer, dead_stock_capital