import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import ast

def get_clean_items_df(df_sales):
    """
    Helper function: Extracts, parses, and cleans all cart items from Paid transactions.
    """
    import streamlit as st # Injected for the X-Ray debugger

    # 1. Catch ALL paid statuses (Paid, Paid Online, Paid (UPI), etc.)
    paid_mask = df_sales['Payment Status'].astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[paid_mask]
    
    if df_paid.empty or 'Line_Items_JSON' not in df_paid.columns:
        return pd.DataFrame()

    all_items = []
    
    # 2. Bulletproof Parsing Engine
    for idx, val in df_paid['Line_Items_JSON'].items():
        if pd.isna(val) or val == "":
            continue

        parsed_items = None

        # Scenario A: The API already converted it to a list/dict in the background
        if isinstance(val, list):
            parsed_items = val
        elif isinstance(val, dict):
            parsed_items = [val]
            
        # Scenario B: It is a raw text string
        elif isinstance(val, str):
            val_str = val.strip()
            if not val_str:
                continue
            try:
                # Attempt 1: Standard JSON parsing
                parsed = json.loads(val_str)
                parsed_items = parsed if isinstance(parsed, list) else [parsed]
            except Exception as e1:
                try:
                    # Attempt 2: Python string fallback
                    parsed = ast.literal_eval(val_str)
                    parsed_items = parsed if isinstance(parsed, list) else [parsed]
                except Exception as e2:
                    # THE X-RAY: Expose exactly what is crashing
                    st.error(f"⚠️ Parsing Crash on Row {idx}! Value: `{val_str}` | Error: {e1}")
                    continue

        # Append the successful extractions
        if parsed_items and isinstance(parsed_items, list):
            all_items.extend(parsed_items)

    if not all_items:
        return pd.DataFrame()

    items_df = pd.DataFrame(all_items)

    # 3. Force Math-Ready Quantities
    if 'Quantity' not in items_df.columns:
        items_df['Quantity'] = items_df.get('Qty', items_df.get('quantity', 1))
    items_df['Quantity'] = pd.to_numeric(items_df['Quantity'], errors='coerce').fillna(1)

    # 4. Standardize Categories
    items_df['Category'] = items_df.get('Category', 'Unknown').astype(str).str.strip().str.title()

    # 5. Clean up "Other" display details
    def format_cat(row):
        cat = str(row.get('Category', '')).strip()
        details = str(row.get('Custom Details', '')).strip().title()
        if cat == 'Other' and details and details.lower() != 'nan':
            return f"Other: {details[:15]}..." if len(details) > 15 else f"Other: {details}"
        return cat

    items_df['Display_Category'] = items_df.apply(format_cat, axis=1)
    
    return items_df


def engine_cost_profitability(df_sales, df_sourcing):
    """Calculates True Profit, top performers, and Dead Stock alerts."""
    total_sales = 0.0
    true_profit = 0.0
    top_performer = "N/A"
    dead_stock_capital = 0.0
    
    # 1. Core Financial KPIs
    if not df_sales.empty and 'Payment Status' in df_sales.columns:
        paid_mask = df_sales['Payment Status'].astype(str).str.contains('paid', case=False, na=False)
        paid_df = df_sales[paid_mask]
        
        if 'Total Amount Client Paid You' in df_sales.columns and 'Total Cost of These Items' in df_sales.columns:
            revenue = pd.to_numeric(paid_df['Total Amount Client Paid You'], errors='coerce').fillna(0)
            cost = pd.to_numeric(paid_df['Total Cost of These Items'], errors='coerce').fillna(0)
            courier = pd.to_numeric(paid_df.get('Courier Charge You Paid', 0), errors='coerce').fillna(0)
            
            total_sales = revenue.sum()
            true_profit = (revenue - cost - courier).sum()
            
    # 2. Top Performer (Powered by the Helper Function)
    items_df = get_clean_items_df(df_sales)
    if not items_df.empty:
        category_totals = items_df.groupby('Category')['Quantity'].sum()
        if not category_totals.empty:
            top_performer = str(category_totals.idxmax())

    # 3. Dead Stock Alert
    if not df_sourcing.empty and 'Date of Purchase' in df_sourcing.columns and 'Total Amount' in df_sourcing.columns:
        try:
            df_sourcing['Date of Purchase'] = pd.to_datetime(df_sourcing['Date of Purchase'], errors='coerce')
            cutoff_date = pd.Timestamp.today() - pd.Timedelta(days=45)
            dead_stock_trips = df_sourcing[df_sourcing['Date of Purchase'] < cutoff_date]
            dead_stock_capital = pd.to_numeric(dead_stock_trips['Total Amount'], errors='coerce').fillna(0).sum()
        except Exception:
            dead_stock_capital = 0.0
            
    return total_sales, true_profit, top_performer, dead_stock_capital


def engine_cac_mom_growth(df_sales, weekly_marketing_spend):
    """Calculates Customer Acquisition Cost and MoM Growth."""
    paid_mask = df_sales.get('Payment Status', pd.Series()).astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[paid_mask].copy()
    
    if df_paid.empty:
        return 0.0, 0, 0.0

    # 1. CAC
    if 'Date of Sale' in df_paid.columns:
        df_paid['Date of Sale'] = pd.to_datetime(df_paid['Date of Sale'], format='mixed', errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=7)
        recent_sales = df_paid[df_paid['Date of Sale'] >= cutoff]
    else:
        recent_sales = pd.DataFrame()
        
    new_clients = recent_sales['Instagram/Facebook Handle'].nunique() if not recent_sales.empty else 0
    cac = (weekly_marketing_spend / new_clients) if new_clients > 0 else weekly_marketing_spend
    
    # 2. MoM Growth
    mom_growth = 0.0
    if 'Date of Sale' in df_paid.columns and pd.api.types.is_datetime64_any_dtype(df_paid['Date of Sale']):
        df_paid['Month'] = df_paid['Date of Sale'].dt.to_period('M')
        monthly_rev = pd.to_numeric(df_paid['Total Amount Client Paid You'], errors='coerce').groupby(df_paid['Month']).sum()
        if len(monthly_rev) >= 2:
            mom_growth = monthly_rev.pct_change().iloc[-1] * 100.0
            
    return cac, new_clients, mom_growth


def generate_financial_charts(df_sales):
    """Generates Trend Line and Donut Chart."""
    if df_sales.empty or 'Payment Status' not in df_sales.columns:
        return None, None
        
    paid_mask = df_sales['Payment Status'].astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[paid_mask].copy()
    
    if df_paid.empty:
        return None, None

    # --- CHART 1: Trend Line ---
    if 'Date of Sale' in df_paid.columns:
        df_paid['Date of Sale'] = pd.to_datetime(df_paid['Date of Sale'], format='mixed', errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=90)
        df_trend = df_paid[df_paid['Date of Sale'] >= cutoff].copy()
    else:
        df_trend = df_paid.copy()

    df_trend['Rev'] = pd.to_numeric(df_trend['Total Amount Client Paid You'], errors='coerce').fillna(0)
    df_trend['Cost'] = pd.to_numeric(df_trend['Total Cost of These Items'], errors='coerce').fillna(0)
    df_trend['Cour'] = pd.to_numeric(df_trend.get('Courier Charge You Paid', 0), errors='coerce').fillna(0)
    df_trend['True Profit'] = df_trend['Rev'] - (df_trend['Cost'] + df_trend['Cour'])

    df_grouped = df_trend.groupby(df_trend['Date of Sale'].dt.date).agg(
        Gross_Revenue=('Rev', 'sum'),
        True_Profit=('True Profit', 'sum')
    ).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=df_grouped['Date of Sale'], y=df_grouped['Gross_Revenue'], mode='lines+markers', name='Gross Revenue', line=dict(color='#800000', width=3)))
    fig_trend.add_trace(go.Scatter(x=df_grouped['Date of Sale'], y=df_grouped['True_Profit'], mode='lines+markers', name='True Net Profit', line=dict(color='#2E7D32', width=3)))
    fig_trend.update_layout(title="📈 Revenue vs. Net Profit Trends", hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # --- CHART 2: Donut Chart (Powered by the Helper Function) ---
    fig_donut = None
    items_df = get_clean_items_df(df_sales)
    
    if not items_df.empty:
        category_sales = items_df.groupby('Display_Category')['Quantity'].sum().reset_index()            
        fig_donut = px.pie(category_sales, values='Quantity', names='Display_Category', hole=0.45)
        fig_donut.update_layout(title="Sales Distribution by Category", margin=dict(t=40, b=10, l=10, r=10))

    return fig_trend, fig_donut