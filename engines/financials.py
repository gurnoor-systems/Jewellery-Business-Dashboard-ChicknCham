import json, ast
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def get_col_safe(df, possible_names):
    """Case-insensitive column extraction. Returns None if not found to prevent type-checking crashes."""
    lower_targets = [n.lower() for n in possible_names]
    for col in df.columns:
        if str(col).lower() in lower_targets:
            return df[col].copy()
    return None

def extract_cart_data(df_sales):
    schema_columns = ['Category', 'Display_Category', 'Quantity']
    if df_sales.empty: return pd.DataFrame(columns=schema_columns)
    
    payment_col = get_col_safe(df_sales, ['payment_status', 'status'])
    if payment_col is None: return pd.DataFrame(columns=schema_columns)
    
    mask = payment_col.astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    
    line_items_col = get_col_safe(df_paid, ['line_items', 'cart'])
    # FIX: Safely check for None instead of using .sum() on a column of dictionaries
    if df_paid.empty or line_items_col is None:
        return pd.DataFrame(columns=schema_columns)

    all_items = []
    for _, row_val in line_items_col.items():
        if row_val is None or (isinstance(row_val, float) and pd.isna(row_val)):
            continue
            
        if isinstance(row_val, (list, dict)):
            parsed = row_val
        else:
            val_str = str(row_val).strip()
            if not val_str or val_str.lower() == 'nan':
                continue
            try:
                parsed = json.loads(val_str)
            except Exception:
                try:
                    parsed = ast.literal_eval(val_str)
                except Exception:
                    continue

        if isinstance(parsed, dict):
            parsed = [parsed]
            
        if isinstance(parsed, list):
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                    
                safe_item = {str(k).lower(): v for k, v in item.items()}
                
                cat = str(safe_item.get('category', 'Unknown')).strip().title()
                det = str(safe_item.get('custom details', safe_item.get('custom_details', ''))).strip().title()
                
                disp_cat = cat
                if cat == 'Other' and det and det.lower() != 'nan':
                    disp_cat = f"Other: {det[:15]}"
                    
                raw_qty = safe_item.get('quantity', safe_item.get('qty', 1))
                try:
                    qty = float(raw_qty)
                except ValueError:
                    qty = 1.0
                    
                all_items.append({
                    'Category': cat,
                    'Display_Category': disp_cat,
                    'Quantity': qty
                })

    if not all_items: 
        return pd.DataFrame(columns=schema_columns)

    return pd.DataFrame(all_items, columns=schema_columns)

def engine_cost_profitability(df_sales, df_sourcing):
    total_sales, true_profit, dead_stock_capital = 0.0, 0.0, 0.0
    top_performer = "N/A"
    
    if not df_sales.empty:
        payment_col = get_col_safe(df_sales, ['payment_status', 'status'])
        if payment_col is not None:
            mask = payment_col.astype(str).str.contains('paid', case=False, na=False)
            paid_df = df_sales[mask]
            
            rev_col = get_col_safe(paid_df, ['amount_paid', 'total_amount', 'amount'])
            cost_col = get_col_safe(paid_df, ['total_cost', 'cost'])
            cour_col = get_col_safe(paid_df, ['courier_charge', 'courier'])

            rev_clean = rev_col.astype(str).str.replace(r'[^\d.-]', '', regex=True) if rev_col is not None else pd.Series([0])
            cost_clean = cost_col.astype(str).str.replace(r'[^\d.-]', '', regex=True) if cost_col is not None else pd.Series([0])
            cour_clean = cour_col.astype(str).str.replace(r'[^\d.-]', '', regex=True) if cour_col is not None else pd.Series([0])

            revenue = pd.to_numeric(rev_clean, errors='coerce').fillna(0).astype(float)
            cost = pd.to_numeric(cost_clean, errors='coerce').fillna(0).astype(float)
            courier = pd.to_numeric(cour_clean, errors='coerce').fillna(0).astype(float)
            
            total_sales = revenue.sum()
            true_profit = (revenue - cost - courier).sum()
            
    items_df = extract_cart_data(df_sales)
    if not items_df.empty and 'Category' in items_df.columns:
        category_totals = items_df.groupby('Category')['Quantity'].sum()
        if not category_totals.empty:
            top_performer = str(category_totals.idxmax())

    if not df_sourcing.empty:
        date_col = get_col_safe(df_sourcing, ['date of purchase', 'created_at', 'date'])
        # FIX: Check if date_col is not None instead of trying to run .sum() on dates
        if date_col is not None:
            try:
                df_sourcing['Safe_Date'] = pd.to_datetime(date_col, errors='coerce', utc=True)
                cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=45)
                dead_stock = df_sourcing[df_sourcing['Safe_Date'] < cutoff]
                
                amt_col = get_col_safe(dead_stock, ['total amount', 'sourcing_price', 'cost'])
                if amt_col is not None:
                    amt_clean = amt_col.astype(str).str.replace(r'[^\d.-]', '', regex=True)
                    dead_stock_capital = pd.to_numeric(amt_clean, errors='coerce').fillna(0).sum()
            except Exception:
                pass
            
    return total_sales, true_profit, top_performer, dead_stock_capital

def engine_cac_mom_growth(df_sales, weekly_marketing_spend):
    if df_sales.empty: return 0.0, 0, 0.0
    
    payment_col = get_col_safe(df_sales, ['payment_status', 'status'])
    if payment_col is None: return 0.0, 0, 0.0
    
    mask = payment_col.astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    
    if df_paid.empty: return 0.0, 0, 0.0

    created_col = get_col_safe(df_paid, ['created_at', 'date_logged', 'date'])
    if created_col is None: return 0.0, 0, 0.0
    
    df_paid['Safe_Date'] = pd.to_datetime(created_col, format='mixed', errors='coerce', utc=True)
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)
    recent_sales = df_paid[df_paid['Safe_Date'] >= cutoff]
        
    handle_col = get_col_safe(recent_sales, ['handle', 'instagram', 'client'])
    new_clients = handle_col.nunique() if handle_col is not None and not recent_sales.empty else 0
    cac = (weekly_marketing_spend / new_clients) if new_clients > 0 else weekly_marketing_spend
    
    mom_growth = 0.0
    if pd.api.types.is_datetime64_any_dtype(df_paid['Safe_Date']):
        df_paid['Month'] = df_paid['Safe_Date'].dt.tz_localize(None).dt.to_period('M')
        rev_col = get_col_safe(df_paid, ['amount_paid', 'total_amount', 'amount'])
        if rev_col is not None:
            rev_clean = rev_col.astype(str).str.replace(r'[^\d.-]', '', regex=True)
            monthly_rev = pd.to_numeric(rev_clean, errors='coerce').groupby(df_paid['Month']).sum()
            if len(monthly_rev) >= 2:
                mom_growth = monthly_rev.pct_change().iloc[-1] * 100.0
            
    return cac, new_clients, mom_growth

def generate_financial_charts(df_sales):
    empty_fig = go.Figure()
    empty_fig.update_layout(title="No Data Available")
    
    if df_sales.empty: return empty_fig, empty_fig
        
    payment_col = get_col_safe(df_sales, ['payment_status', 'status'])
    if payment_col is None: return empty_fig, empty_fig
    
    mask = payment_col.astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    
    if df_paid.empty: return empty_fig, empty_fig

    created_col = get_col_safe(df_paid, ['created_at', 'date_logged', 'date'])
    if created_col is None: return empty_fig, empty_fig
    
    df_paid['Safe_Date'] = pd.to_datetime(created_col, format='mixed', errors='coerce', utc=True)
    # FIX: Drop NaT (Not a Time) values so they don't break Plotly axes
    df_paid = df_paid.dropna(subset=['Safe_Date'])
    if df_paid.empty: return empty_fig, empty_fig
    
    cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=90)
    df_trend = df_paid[df_paid['Safe_Date'] >= cutoff].copy()
    if df_trend.empty: return empty_fig, empty_fig

    rev_col = get_col_safe(df_trend, ['amount_paid', 'total_amount', 'amount'])
    cost_col = get_col_safe(df_trend, ['total_cost', 'cost'])
    cour_col = get_col_safe(df_trend, ['courier_charge', 'courier'])

    rev_c = rev_col.astype(str).str.replace(r'[^\d.-]', '', regex=True) if rev_col is not None else pd.Series([0]*len(df_trend))
    cost_c = cost_col.astype(str).str.replace(r'[^\d.-]', '', regex=True) if cost_col is not None else pd.Series([0]*len(df_trend))
    cour_c = cour_col.astype(str).str.replace(r'[^\d.-]', '', regex=True) if cour_col is not None else pd.Series([0]*len(df_trend))

    df_trend['Rev'] = pd.to_numeric(rev_c, errors='coerce').fillna(0).astype(float)
    df_trend['Cost'] = pd.to_numeric(cost_c, errors='coerce').fillna(0).astype(float)
    df_trend['Cour'] = pd.to_numeric(cour_c, errors='coerce').fillna(0).astype(float)
    df_trend['True Profit'] = df_trend['Rev'] - (df_trend['Cost'] + df_trend['Cour'])

    df_grouped = df_trend.groupby(df_trend['Safe_Date'].dt.date)[['Rev', 'True Profit']].sum().reset_index()

    x_dates = df_grouped['Safe_Date'].tolist()
    y_rev = df_grouped['Rev'].tolist()
    y_prof = df_grouped['True Profit'].tolist()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=x_dates, y=y_rev, mode='lines+markers', name='Gross Revenue', line=dict(color='#800000', width=3)))
    fig_trend.add_trace(go.Scatter(x=x_dates, y=y_prof, mode='lines+markers', name='True Net Profit', line=dict(color='#2E7D32', width=3)))
    fig_trend.update_layout(title="📈 Revenue vs. Net Profit Trends", hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    fig_donut = empty_fig
    items_df = extract_cart_data(df_sales)
    
    if not items_df.empty and 'Display_Category' in items_df.columns:
        category_sales = items_df.groupby('Display_Category')['Quantity'].sum().reset_index()   
        category_sales['Quantity'] = category_sales['Quantity'].astype(float)
        
        fig_donut = px.pie(category_sales, values='Quantity', names='Display_Category', hole=0.45)
        fig_donut.update_layout(title="Sales Distribution by Category", margin=dict(t=40, b=10, l=10, r=10))

    return fig_trend, fig_donut