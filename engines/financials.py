import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def engine_cost_profitability(df_sales, df_sourcing):
    """
    Calculates True Profit, top performers, and Dead Stock alerts.
    """
    # Default fallback values for when the database is empty
    total_sales = 0.0
    true_profit = 0.0
    top_performer = "N/A"
    dead_stock_capital = 0.0
    
    # 1. Core Financial KPIs (Fault-Tolerant Check)
    if not df_sales.empty and 'Payment Status' in df_sales.columns:
        # Safely mask only paid transactions
        paid_mask = df_sales['Payment Status'].astype(str).str.contains('Paid', na=False)
        paid_df = df_sales[paid_mask]
        
        # Calculate Total Sales
        if 'Total Amount Client Paid You' in df_sales.columns:
            total_sales = pd.to_numeric(paid_df['Total Amount Client Paid You'], errors='coerce').fillna(0).sum()
            
        # Calculate True Profit dynamically (Revenue - Cost) since we removed the Sheet formula
        if 'Total Amount Client Paid You' in df_sales.columns and 'Total Cost of These Items' in df_sales.columns:
            revenue = pd.to_numeric(paid_df['Total Amount Client Paid You'], errors='coerce').fillna(0)
            cost = pd.to_numeric(paid_df['Total Cost of These Items'], errors='coerce').fillna(0)
            true_profit = (revenue - cost).sum()
            
        # 2. Identify Top Performer
        if 'Line_Items_JSON' in df_sales.columns and not paid_df.empty:
            all_items = []
            for json_string in paid_df['Line_Items_JSON'].dropna():
                if isinstance(json_string, str) and json_string.strip():
                    try:
                        all_items.extend(json.loads(json_string))
                    except Exception:
                        pass
            
            if all_items:
                items_df = pd.DataFrame(all_items)
                # Finds the category that sold the highest quantity
                top_cat = items_df.groupby('Category')['Quantity'].sum().idxmax()
                top_performer = str(top_cat)
                
    # 3. Dead Stock Alert
    if not df_sourcing.empty and 'Date of Purchase' in df_sourcing.columns and 'Total Amount' in df_sourcing.columns:
        try:
            # Convert string dates to datetime objects for accurate math
            df_sourcing['Date of Purchase'] = pd.to_datetime(df_sourcing['Date of Purchase'], errors='coerce')
            cutoff_date = pd.Timestamp.today() - pd.Timedelta(days=45)
            
            dead_stock_trips = df_sourcing[df_sourcing['Date of Purchase'] < cutoff_date]
            dead_stock_capital = pd.to_numeric(dead_stock_trips['Total Amount'], errors='coerce').fillna(0).sum()
        except Exception:
            dead_stock_capital = 0.0
    
    return total_sales, true_profit, top_performer, dead_stock_capital

def engine_cac_mom_growth(df_sales, weekly_marketing_spend):
    """
    Calculates Customer Acquisition Cost (CAC) for the last 7 days 
    and overall Month-over-Month (MoM) Revenue Growth.
    """
    df_paid = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)'].copy()
    
    if df_paid.empty:
        return 0.0, 0, 0.0

    # 1. Customer Acquisition Cost (CAC)
    paid_mask = df_sales['Payment Status'].astype(str).str.contains('Paid', na=False)
    df_paid = df_sales[paid_mask].copy()
    
    if df_paid.empty:
        return 0.0, 0, 0.0

    if 'Date of Sale' in df_paid.columns:
        # Convert strings to datetime safely
        df_paid['Date of Sale'] = pd.to_datetime(df_paid['Date of Sale'], format='mixed', errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=7)
        recent_sales = df_paid[df_paid['Date of Sale'] >= cutoff]
    else:
        recent_sales = pd.DataFrame()
        
    new_clients_acquired = recent_sales['Instagram/Facebook Handle'].nunique() if not recent_sales.empty else 0
    cac = (weekly_marketing_spend / new_clients_acquired) if new_clients_acquired > 0 else weekly_marketing_spend
    
    # 2. Month-over-Month (MoM) Growth
    mom_growth = 0.0
    if 'Date of Sale' in df_paid.columns and pd.api.types.is_datetime64_any_dtype(df_paid['Date of Sale']):
        df_paid['Month'] = df_paid['Date of Sale'].dt.to_period('M')
        monthly_rev = pd.to_numeric(df_paid['Total Amount Client Paid You'], errors='coerce').groupby(df_paid['Month']).sum()
        
        if len(monthly_rev) >= 2:
            mom_growth = monthly_rev.pct_change().iloc[-1] * 100.0
            
    return cac, new_clients_acquired, mom_growth

def generate_financial_charts(df_sales):

    """
    Generate interactive Plotly charts for the Financial Command Center:
    1. Dual Line Trend Chart: Gross Revenue vs. True Profit (Last 90 Days)
    2. Donut Chart: Revenue Distribution by Item / Category
    """
    if df_sales.empty or 'Payment Status' not in df_sales.columns:
        return None, None
    paid_mask = df_sales['Payment Status'].astype(str).str.contains('Paid', na=False)
    df_paid = df_sales[paid_mask].copy()
    
    if df_paid.empty:
        return None, None

    # --- CHART 1: Gross Revenue vs. True Net Profit (Last 90 Days) ---
    if 'Date of Sale' in df_paid.columns:
        df_paid['Date of Sale'] = pd.to_datetime(df_paid['Date of Sale'], format='mixed', errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=90)
        df_filtered = df_paid[df_paid['Date of Sale'] >= cutoff].copy()
    else:
        df_filtered = df_paid.copy()

    df_filtered['Total Amount Client Paid You'] = pd.to_numeric(df_filtered['Total Amount Client Paid You'], errors='coerce').fillna(0)
    df_filtered['Total Cost of These Items'] = pd.to_numeric(df_filtered['Total Cost of These Items'], errors='coerce').fillna(0)
    df_filtered['Courier Charge You Paid'] = pd.to_numeric(df_filtered['Courier Charge You Paid'], errors='coerce').fillna(0)   #added this line to ensure courier charges are numeric and fill NaN with 0
    df_filtered['True Profit'] = df_filtered['Total Amount Client Paid You'] - df_filtered['Total Cost of These Items'] - df_filtered['Courier Charge You Paid'].fillna(0) # added this line to calculate True Profit by subtracting courier charges from the profit calculation

    df_trend = df_filtered.groupby(df_filtered['Date of Sale'].dt.date).agg(
        Gross_Revenue=('Total Amount Client Paid You', 'sum'),
        True_Profit=('True Profit', 'sum')
    ).reset_index()

    fig_trend = go.Figure()
    
    fig_trend.add_trace(go.Scatter(
        x=df_trend['Date of Sale'], y=df_trend['Gross_Revenue'],
        mode='lines+markers', name='Gross Revenue',
        line=dict(color='#800000', width=3),
        hovertemplate="Date: %{x}<br>Revenue: ₹%{y:,.0f}<extra></extra>"
    ))
    
    fig_trend.add_trace(go.Scatter(
        x=df_trend['Date of Sale'], y=df_trend['True_Profit'],
        mode='lines+markers', name='True Net Profit',
        line=dict(color='#2E7D32', width=3),
        hovertemplate="Date: %{x}<br>Profit: ₹%{y:,.0f}<extra></extra>"
    ))

    fig_trend.update_layout(
        title="📈 Revenue vs. Net Profit Trends",
        xaxis_title="Date", yaxis_title="Amount (₹)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # --- CHART 2: Category / Item Revenue Donut Chart ---

    fig_donut = None
    if 'Line_Items_JSON' in df_paid.columns:
        all_items = []
        for json_string in df_paid['Line_Items_JSON'].dropna():
            if isinstance(json_string, str) and json_string.strip():
                try:
                    items = json.loads(json_string)
                    all_items.extend(items)
                except Exception:
                    pass

        if all_items:
            items_df = pd.DataFrame(all_items)
            category_grouped = items_df.groupby('Category')['Quantity'].sum().reset_index()
            
            fig_donut = px.pie(
                category_grouped, names='Category', values='Quantity', hole=0.4,
                title="Sales by Category", color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_donut.update_layout(margin=dict(t=30, b=10, l=10, r=10))

    return fig_trend, fig_donut