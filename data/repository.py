import pandas as pd
from data.ingestion import load_data, init_connection

class BusinessRepository:
    """Abstracts database operations so the underlying store can change later."""
    
    @staticmethod
    def get_sales_data() -> pd.DataFrame:
        df_sales, _ = load_data()
        return df_sales

    @staticmethod
    def get_sourcing_data() -> pd.DataFrame:
        _, df_sourcing = load_data()
        return df_sourcing

    @staticmethod
    def update_transaction(order_id: str, new_amount: float, new_status: str, new_client_name: str):
        """Safely updates a sales transaction row in Google Sheets by Order_ID."""
        try:
            db = init_connection()
            worksheet = db.worksheet("Sales_Engine")
            
            # Find the cell matching the Order_ID in Column A
            cell = worksheet.find(order_id)
            if cell:
                row_idx = cell.row
                # Based on your exact Sales_Engine headers:
                # Column D (4) = Client Formal Name
                # Column J (10) = Total Amount Client Paid You
                # Column K (11) = Payment Status
                worksheet.update_cell(row_idx, 4, new_client_name)
                worksheet.update_cell(row_idx, 10, new_amount)
                worksheet.update_cell(row_idx, 11, new_status)
                return True
            return "Order ID not found in database."
        except Exception as e:
            return str(e)