import json, ast
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def extract_cart_data(df_sales):
    """
    Extracts and standardizes cart data, bypassing Pandas schema alignment bugs.
    """
    mask = df_sales.get('Payment Status', pd.Series(dtype=str)).astype(str).str.contains('paid', case=False, na=False)
    df_paid = df_sales[mask].copy()
    
    if df_paid.empty or 'Line_Items_JSON' not in df_paid.columns:
        return pd.DataFrame()

    all_items = []
    for idx, row_val in df_paid['Line_Items_JSON'].items():
        if pd.isna(row_val): continue
        val_str = str(row_val).strip()
        if not val_str: continue

        # 1. Robust Parsing
        try:
            parsed = json.loads(val_str)
        except Exception:
            try:
                parsed = ast.literal_eval(val_str)
            except Exception:
                continue

        if isinstance(parsed, dict):
            parsed = [parsed]
            
        # 2. Strict Pre-Processing (The Fix)
        if isinstance(parsed, list):
            for item in parsed:

                cat = str(item.get('Category', 'Unknown')).strip().title()
                det = str(item.get('Custom Details', '')).strip().title()
                
                disp_cat = cat
                if cat == 'Other' and det and det.lower() != 'nan':
                    disp_cat = f"Other: {det[:15]}"
                    
                # Force float math on extraction
                raw_qty = item.get('Quantity', item.get('Qty', 1))
                try:
                    qty = float(raw_qty)
                except ValueError:
                    qty = 1.0
                    
                # append the clean data
                all_items.append({
                    'Display_Category': disp_cat,
                    'Quantity': qty
                })

    if not all_items: 
        return pd.DataFrame()

    # 3. Return uniform dataframe ready for math
    return pd.DataFrame(all_items)

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

    # DONUT CHART GENERATION
    fig_donut = None
    items_df = extract_cart_data(df_sales)
    
    if not items_df.empty:
        category_sales = items_df.groupby('Display_Category')['Quantity'].sum().reset_index()            
        fig_donut = px.pie(category_sales, values='Quantity', names='Display_Category', hole=0.45)
        fig_donut.update_layout(title="Sales Distribution by Category", margin=dict(t=40, b=10, l=10, r=10))

    return fig_trend, fig_donut