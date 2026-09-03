import streamlit as st
from engines.invoicing import generate_invoice_pdf

def render_invoice(df_sales):
    st.subheader("🧾 Invoice")
    st.caption("Select the transaction to fetch its Invoice.")
    
    # instead of fetching it from the database again via load_sales_data()
    sales_df = df_sales
    
    if not sales_df.empty and 'Client Formal Name' in sales_df.columns:
        # Filter out blank rows safely
        valid_sales = sales_df[sales_df['Client Formal Name'].astype(str).str.strip() != ""]
        
        if not valid_sales.empty:
            # Sort by most recent first (using the index since newest rows are appended at the bottom)
            # Added .copy() to prevent Pandas SettingWithCopyWarnings
            recent_sales = valid_sales.iloc[::-1].head(10).copy() 
            
            # Create a clean display string for the dropdown
            recent_sales['Display'] = recent_sales['Date of Sale'].astype(str) + " - " + recent_sales['Client Formal Name'].astype(str) + " (₹" + recent_sales['Total Amount Client Paid You'].astype(str) + ")"
            
            selected_display = st.selectbox("Select Transaction", options=recent_sales['Display'].tolist())
            
            if selected_display:
                # Extract the exact row based on the selection
                selected_row = recent_sales[recent_sales['Display'] == selected_display].iloc[0]
                
                st.divider()
                st.markdown(f"**Generating Invoice for:** {selected_row['Client Formal Name']}")
                
                # Generate the PDF
                pdf_bytes = generate_invoice_pdf(selected_row)
                
                if isinstance(pdf_bytes, bytes):
                    # Create a dynamic filename
                    safe_name = str(selected_row['Client Formal Name']).replace(" ", "_")
                    file_name = f"Invoice_chikncham_{safe_name}.pdf"
                    
                    st.download_button(
                        label="📥 Download PDF Invoice",
                        data=pdf_bytes,
                        file_name=file_name,
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True
                    )
                else:
                    st.error(pdf_bytes) # Displays the error string if PDF generation fails
        else:
            st.info("No valid transactions found with a formal client name.")
    else:
        st.warning("Database empty or missing structured columns. Log a sale first.")