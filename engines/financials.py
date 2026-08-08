import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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

def engine_cac_mom_growth(df_sales, weekly_marketing_spend):
    """
    Calculates Customer Acquisition Cost (CAC) for the last 7 days 
    and overall Month-over-Month (MoM) Revenue Growth.
    """
    df_paid = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)'].copy()
    
    if df_paid.empty:
        return 0.0, 0, 0.0

    # 1. Customer Acquisition Cost (CAC)
    if 'Date of Sale' in df_paid.columns and pd.api.types.is_datetime64_any_dtype(df_paid['Date of Sale']):
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=7)
        recent_sales = df_paid[df_paid['Date of Sale'] >= cutoff]
    else:
        recent_sales = pd.DataFrame()
        
    new_clients_acquired = recent_sales['Instagram/Facebook Handle'].nunique() if not recent_sales.empty else 0
    
    # Calculate CAC
    cac = (weekly_marketing_spend / new_clients_acquired) if new_clients_acquired > 0 else weekly_marketing_spend
    
    # 2. Month-over-Month (MoM) Growth
    mom_growth = 0.0
    if 'Date of Sale' in df_paid.columns and pd.api.types.is_datetime64_any_dtype(df_paid['Date of Sale']):
        df_paid['Month'] = df_paid['Date of Sale'].dt.to_period('M')
        monthly_rev = df_paid.groupby('Month')['Total Amount Client Paid You'].sum()
        
        if len(monthly_rev) >= 2:
            mom_growth = monthly_rev.pct_change().iloc[-1] * 100.0
            
    return cac, new_clients_acquired, mom_growth

def generate_financial_charts(df_sales):
    """
    Generates interactive Plotly charts for the Financial Command Center:
    1. Dual Line Trend Chart: Gross Revenue vs. True Profit (Last 90 Days)
    2. Donut Chart: Revenue Distribution by Item / Category
    """
    df_paid = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)'].copy()
    
    if df_paid.empty:
        return None, None

    # --- CHART 1: Gross Revenue vs. True Net Profit (Last 90 Days) ---
    if 'Date of Sale' in df_paid.columns and pd.api.types.is_datetime64_any_dtype(df_paid['Date of Sale']):
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=90)
        df_filtered = df_paid[df_paid['Date of Sale'] >= cutoff].copy()
        if df_filtered.empty:
            df_filtered = df_paid.copy()
    else:
        df_filtered = df_paid.copy()

    # Aggregate by sale date
    df_trend = df_filtered.groupby(df_filtered['Date of Sale'].dt.date).agg(
        Gross_Revenue=('Total Amount Client Paid You', 'sum'),
        True_Profit=('True Profit', 'sum')
    ).reset_index()

    fig_trend = go.Figure()
    
    # Gross Revenue Line (Maroon)
    fig_trend.add_trace(go.Scatter(
        x=df_trend['Date of Sale'],
        y=df_trend['Gross_Revenue'],
        mode='lines+markers',
        name='Gross Revenue',
        line=dict(color='#800000', width=3),
        hovertemplate="Date: %{x}<br>Revenue: ₹%{y:,.0f}<extra></extra>"
    ))
    
    # True Net Profit Line (Emerald Green)
    fig_trend.add_trace(go.Scatter(
        x=df_trend['Date of Sale'],
        y=df_trend['True_Profit'],
        mode='lines+markers',
        name='True Net Profit',
        line=dict(color='#2E7D32', width=3),
        hovertemplate="Date: %{x}<br>Profit: ₹%{y:,.0f}<extra></extra>"
    ))

    fig_trend.update_layout(
        title="📈 Revenue vs. Net Profit Trends",
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # --- CHART 2: Category / Item Revenue Donut Chart ---
    df_items = df_paid.groupby('Items Sold Summary')['Total Amount Client Paid You'].sum().reset_index()
    df_items = df_items.sort_values(by='Total Amount Client Paid You', ascending=False)

    fig_donut = px.pie(
        df_items,
        values='Total Amount Client Paid You',
        names='Items Sold Summary',
        title="🍩 Sales Breakdown by Category",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    
    fig_donut.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="Category: %{label}<br>Sales: ₹%{value:,.0f}<extra></extra>"
    )
    fig_donut.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False
    )
    return fig_trend, fig_donut