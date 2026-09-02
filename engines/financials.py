import json, ast
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def extract_cart_data(df_sales):
    """Extracts and standardizes cart data, enforcing strict column schemas (Data Contracts)."""
    mask = df_sales.get('Payment Status', pd.Series(dtype=str)).astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    
    # THE DATA CONTRACT: Define the exact schema guaranteed to be returned
    schema_columns = ['Category', 'Display_Category', 'Quantity']
    empty_df = pd.DataFrame(columns=schema_columns)
    
    if df_paid.empty or 'Line_Items_JSON' not in df_paid.columns:
        return empty_df

    all_items = []
    for idx, row_val in df_paid['Line_Items_JSON'].items():
        if pd.isna(row_val): continue
        val_str = str(row_val).strip()
        if not val_str: continue

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
                cat = str(item.get('Category', 'Unknown')).strip().title()
                det = str(item.get('Custom Details', '')).strip().title()
                
                disp_cat = cat
                if cat == 'Other' and det and det.lower() != 'nan':
                    disp_cat = f"Other: {det[:15]}"
                    
                raw_qty = item.get('Quantity', item.get('Qty', 1))
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
        return empty_df

    # FORCE PANDAS TO ACKNOWLEDGE THE EXACT COLUMNS
    return pd.DataFrame(all_items, columns=schema_columns)


def engine_cost_profitability(df_sales, df_sourcing):
    total_sales = 0.0
    true_profit = 0.0
    top_performer = "N/A"
    dead_stock_capital = 0.0
    
    if not df_sales.empty and 'Payment Status' in df_sales.columns:
        mask = df_sales['Payment Status'].astype(str).str.contains('paid', case=False, na=False)
        paid_df = df_sales[mask]
        
        rev_clean = paid_df.get('Total Amount Client Paid You', pd.Series(dtype=str)).astype(str).str.replace(',', '')
        cost_clean = paid_df.get('Total Cost of These Items', pd.Series(dtype=str)).astype(str).str.replace(',', '')
        cour_clean = paid_df.get('Courier Charge You Paid', pd.Series(dtype=str)).astype(str).str.replace(',', '')

        revenue = pd.to_numeric(rev_clean, errors='coerce').fillna(0)
        cost = pd.to_numeric(cost_clean, errors='coerce').fillna(0)
        courier = pd.to_numeric(cour_clean, errors='coerce').fillna(0)
        
        total_sales = revenue.sum()
        true_profit = (revenue - cost - courier).sum()
            
    items_df = extract_cart_data(df_sales)
    
    # CHECK: Verify column physically exists before grouping
    if not items_df.empty and 'Category' in items_df.columns:
        category_totals = items_df.groupby('Category')['Quantity'].sum()
        if not category_totals.empty:
            top_performer = str(category_totals.idxmax())

    if not df_sourcing.empty and 'Date of Purchase' in df_sourcing.columns:
        try:
            df_sourcing['Date of Purchase'] = pd.to_datetime(df_sourcing['Date of Purchase'], errors='coerce')
            cutoff = pd.Timestamp.today() - pd.Timedelta(days=45)
            dead_stock = df_sourcing[df_sourcing['Date of Purchase'] < cutoff]
            amt_clean = dead_stock.get('Total Amount', pd.Series(dtype=str)).astype(str).str.replace(',', '')
            dead_stock_capital = pd.to_numeric(amt_clean, errors='coerce').fillna(0).sum()
        except:
            pass
            
    return total_sales, true_profit, top_performer, dead_stock_capital


def engine_cac_mom_growth(df_sales, weekly_marketing_spend):
    mask = df_sales.get('Payment Status', pd.Series(dtype=str)).astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    
    if df_paid.empty: return 0.0, 0, 0.0

    if 'Date of Sale' in df_paid.columns:
        df_paid['Date of Sale'] = pd.to_datetime(df_paid['Date of Sale'], format='mixed', errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=7)
        recent_sales = df_paid[df_paid['Date of Sale'] >= cutoff]
    else:
        recent_sales = pd.DataFrame()
        
    new_clients = recent_sales['Instagram/Facebook Handle'].nunique() if not recent_sales.empty else 0
    cac = (weekly_marketing_spend / new_clients) if new_clients > 0 else weekly_marketing_spend
    
    mom_growth = 0.0
    if 'Date of Sale' in df_paid.columns and pd.api.types.is_datetime64_any_dtype(df_paid['Date of Sale']):
        df_paid['Month'] = df_paid['Date of Sale'].dt.to_period('M')
        rev_clean = df_paid.get('Total Amount Client Paid You', pd.Series(dtype=str)).astype(str).str.replace(',', '')
        monthly_rev = pd.to_numeric(rev_clean, errors='coerce').groupby(df_paid['Month']).sum()
        if len(monthly_rev) >= 2:
            mom_growth = monthly_rev.pct_change().iloc[-1] * 100.0
            
    return cac, new_clients, mom_growth


def generate_financial_charts(df_sales):
    if df_sales.empty or 'Payment Status' not in df_sales.columns: return None, None
        
    mask = df_sales['Payment Status'].astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    if df_paid.empty: return None, None

    if 'Date of Sale' in df_paid.columns:
        df_paid['Date of Sale'] = pd.to_datetime(df_paid['Date of Sale'], format='mixed', errors='coerce')
        cutoff = pd.Timestamp.today() - pd.Timedelta(days=90)
        df_trend = df_paid[df_paid['Date of Sale'] >= cutoff].copy()
    else:
        df_trend = df_paid.copy()

    rev_c = df_trend.get('Total Amount Client Paid You', pd.Series(dtype=str)).astype(str).str.replace(',', '')
    cost_c = df_trend.get('Total Cost of These Items', pd.Series(dtype=str)).astype(str).str.replace(',', '')
    cour_c = df_trend.get('Courier Charge You Paid', pd.Series(dtype=str)).astype(str).str.replace(',', '')

    df_trend['Rev'] = pd.to_numeric(rev_c, errors='coerce').fillna(0)
    df_trend['Cost'] = pd.to_numeric(cost_c, errors='coerce').fillna(0)
    df_trend['Cour'] = pd.to_numeric(cour_c, errors='coerce').fillna(0)
    df_trend['True Profit'] = df_trend['Rev'] - (df_trend['Cost'] + df_trend['Cour'])

    df_grouped = df_trend.groupby(df_trend['Date of Sale'].dt.date).agg(
        Gross_Revenue=('Rev', 'sum'),
        True_Profit=('True Profit', 'sum')
    ).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=df_grouped['Date of Sale'], y=df_grouped['Gross_Revenue'], mode='lines+markers', name='Gross Revenue', line=dict(color='#800000', width=3)))
    fig_trend.add_trace(go.Scatter(x=df_grouped['Date of Sale'], y=df_grouped['True_Profit'], mode='lines+markers', name='True Net Profit', line=dict(color='#2E7D32', width=3)))
    fig_trend.update_layout(title="📈 Revenue vs. Net Profit Trends", hovermode="x unified", margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    fig_donut = None
    items_df = extract_cart_data(df_sales)
    
    # CHECK: Verify column physically exists before grouping
    if not items_df.empty and 'Display_Category' in items_df.columns:
        category_sales = items_df.groupby('Display_Category')['Quantity'].sum().reset_index()            
        fig_donut = px.pie(category_sales, values='Quantity', names='Display_Category', hole=0.45)
        fig_donut.update_layout(title="Sales Distribution by Category", margin=dict(t=40, b=10, l=10, r=10))

    return fig_trend, fig_donut