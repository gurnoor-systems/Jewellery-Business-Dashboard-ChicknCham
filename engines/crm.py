import pandas as pd

def engine_vip_loyalty(df_sales):
    """
    Parses client IDs, calculates lifetime value, and flags repeat buyers.
    """
    # 1. Screen for valid, completed transactions only
    df_cleared = df_sales[df_sales['Payment Status'] == 'Paid (UPI/Bank)'].copy()
    
    # 2. Group by Client ID to calculate fundamental LTV metrics
    vip_df = df_cleared.groupby('Instagram/Facebook Handle').agg(
        Total_Orders=('Instagram/Facebook Handle', 'count'),
        Lifetime_Spend=('Total Amount Client Paid You', 'sum'),
        Total_Profit=('True Profit', 'sum')
    ).reset_index()
    
    # 3. Sort by highest Lifetime Spend to generate the 80/20 list
    vip_df = vip_df.sort_values(by='Lifetime_Spend', ascending=False)
    
    # 4. Flag repeat buyers programmatically
    vip_df['Client Status'] = vip_df['Total_Orders'].apply(
        lambda x: '⭐ VIP Repeat' if x > 1 else 'New'
    )
    
    return vip_df