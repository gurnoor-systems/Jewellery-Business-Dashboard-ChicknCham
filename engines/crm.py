import pandas as pd

def engine_vip_loyalty(df_sales):
    if df_sales.empty or 'handle' not in df_sales.columns: return pd.DataFrame()
    paid_mask = df_sales['payment_status'].astype(str).str.contains('Paid', na=False)
    paid_sales = df_sales[paid_mask].copy() if 'payment_status' in df_sales.columns else df_sales.copy()
    if paid_sales.empty: return pd.DataFrame()

    paid_sales['amount_paid'] = pd.to_numeric(paid_sales['amount_paid'], errors='coerce').fillna(0)
    paid_sales['total_cost'] = pd.to_numeric(paid_sales['total_cost'], errors='coerce').fillna(0)
    paid_sales['Calculated_Profit'] = paid_sales['amount_paid'] - paid_sales['total_cost']

    vip_df = paid_sales.groupby('handle').agg(
        Total_Orders=('created_at', 'count'), Lifetime_Spend=('amount_paid', 'sum'), Total_Profit=('Calculated_Profit', 'sum')
    ).reset_index().sort_values(by='Lifetime_Spend', ascending=False)

    def assign_status(row):
        if row['Lifetime_Spend'] > 15000: return '💎 Diamond VIP'
        elif row['Lifetime_Spend'] > 5000: return '🥇 Gold Tier'
        elif row['Total_Orders'] > 1: return '⭐ Repeat Buyer'
        else: return '🆕 New Client'

    vip_df['Client Status'] = vip_df.apply(assign_status, axis=1)
    return vip_df