import streamlit as st
import pandas as pd
from helper_functions import llm

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


# Streamlit UI
st.title("Meeting Room Booking Analysis")

# Date pickers for selecting a date range
start_date = st.date_input("Select Start Date", min_value= (2024,1,1))
end_date = st.date_input("Select End Date", min_value= (2024,1,1))

# Validate selected dates
if start_date > end_date:
    st.error("Start Date must be earlier than or equal to End Date.")
else:
    st.success(f"Selected Date Range: {start_date} to {end_date}")

# Generate Report Button
if st.button("Generate Report"):
    with st.spinner("Generating report..."):
        try:
            # Call the generate_report function
            report = llm.generate_report(start_date, end_date,transaction_log,user_input = "Generate Report")
            st.success("Report generated successfully!")
            st.text_area("Generated Report", report, height=300)
        except Exception as e:
            st.error(f"An error occurred: {e}")