import streamlit as st
import pandas as pd

ADMIN_PASSWORD = "admin123"

# Load transaction log
try:
    transaction_log = pd.read_csv("transaction_log.csv")
except FileNotFoundError:
    transaction_log = pd.DataFrame(columns=[
        "Action", "Room", "Date", "Start Time", "End Time", "User", "Meeting Title", "Contact Number", "Password", "Timestamp"
    ])

st.title("Admin Page")
st.subheader("Transaction History")

# Password input for admin access
admin_password = st.text_input("Enter Admin Password", type="password")

if st.button("Login"):
    if admin_password == ADMIN_PASSWORD:
        st.success("Access granted. Welcome to the Admin Dashboard!")

        # Display booking transaction history
        try:
            # Reload the transaction log to ensure it reflects the most recent updates
            transaction_log = pd.read_csv("transaction_log.csv")
            
            if not transaction_log.empty:
                # Ensure the Contact Number column is displayed without commas
                if "Contact Number" in transaction_log.columns:
                    transaction_log["Contact Number"] = transaction_log["Contact Number"].astype(str)

                st.write("Below is the transaction history:")
                st.dataframe(transaction_log, hide_index=True)

                # Enable CSV download
                csv = transaction_log.to_csv(index=False)
                st.download_button(
                    label="Download Transaction History",
                    data=csv,
                    file_name="transaction_log.csv",
                    mime="text/csv"
                )
            else:
                st.info("The transaction history is currently empty.")

        except FileNotFoundError:
            st.error("No transaction history file found.")
    else:
        st.error("Invalid password. Access denied.")
