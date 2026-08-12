import pandas as pd

def engine_vip_loyalty(df_sales):
    """
    Calculates Client Lifetime Value (CLV), total orders, and assigns VIP tiers.
    """
    if df_sales.empty or 'Instagram/Facebook Handle' not in df_sales.columns:
        return pd.DataFrame()

    # Safely filter for paid transactions only
    if 'Payment Status' in df_sales.columns:
        paid_mask = df_sales['Payment Status'].astype(str).str.contains('Paid', na=False)
        paid_sales = df_sales[paid_mask].copy()
    else:
        paid_sales = df_sales.copy()

    if paid_sales.empty:
        return pd.DataFrame()

    # Calculate True Profit dynamically
    paid_sales['Total Amount Client Paid You'] = pd.to_numeric(paid_sales['Total Amount Client Paid You'], errors='coerce').fillna(0)
    paid_sales['Total Cost of These Items'] = pd.to_numeric(paid_sales['Total Cost of These Items'], errors='coerce').fillna(0)
    paid_sales['Calculated_Profit'] = paid_sales['Total Amount Client Paid You'] - paid_sales['Total Cost of These Items']

    # Group by Social Handle
    vip_df = paid_sales.groupby('Instagram/Facebook Handle').agg(
        Total_Orders=('Timestamp', 'count'),
        Lifetime_Spend=('Total Amount Client Paid You', 'sum'),
        Total_Profit=('Calculated_Profit', 'sum')
    ).reset_index()

    # Sort by highest spenders
    vip_df = vip_df.sort_values(by='Lifetime_Spend', ascending=False)

    # Assign Status Tiers dynamically
    def assign_status(row):
        if row['Lifetime_Spend'] > 15000: 
            return '💎 Diamond VIP'
        elif row['Lifetime_Spend'] > 5000: 
            return '🥇 Gold Tier'
        elif row['Total_Orders'] > 1: 
            return '⭐ Repeat Buyer'
        else: 
            return '🆕 New Client'

    vip_df['Client Status'] = vip_df.apply(assign_status, axis=1)
    
    return vip_df