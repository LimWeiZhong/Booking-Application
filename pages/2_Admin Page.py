import streamlit as st
import pandas as pd

ADMIN_PASSWORD = "admin123"


# Load transaction log
try:
    transaction_log = pd.read_csv("transaction_log.csv")
except FileNotFoundError:
    transaction_log = pd.DataFrame(columns=["Action", "Room", "Date", "Start Time", "End Time", "User", "Timestamp"])

st.title("Admin Page")
st.subheader("Transaction History")

    # Password input for admin access
admin_password = st.text_input("Enter Admin Password", type="password")
if st.button("Login"):
        if admin_password == ADMIN_PASSWORD:
            st.success("Access granted. Welcome to the Admin Dashboard!")
            
            # Display booking transaction history
            try:
                 transaction_log = pd.read_csv("transaction_log.csv")
                 st.dataframe(transaction_log, hide_index=True)
                 csv = transaction_log.to_csv(index=False)
                 st.download_button(label="Download Transaction History", data=csv, file_name="transaction_log.csv", mime="text/csv")
    
            except FileNotFoundError:
                 st.error("No transaction history found.")
        else:
            st.error("Invalid password. Access denied.")

