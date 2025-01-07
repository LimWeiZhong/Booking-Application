import streamlit as st
import pandas as pd
from datetime import datetime

ADMIN_PASSWORD = "admin123"
BLOCKED_DATES_PASSWORD = "admin123"  # New password for managing blocked dates

# Load the transaction log
try:
    transaction_log = pd.read_csv("transaction_log.csv")
except FileNotFoundError:
    transaction_log = pd.DataFrame(columns=[
        "Action", "Room", "Date", "Start Time", "End Time", "User", "Meeting Title", "Contact Number", "Password", "Timestamp"
    ])

# Load blocked dates from blocked_dates.csv
def load_blocked_dates():
    try:
        blocked_dates = pd.read_csv("blocked_dates.csv")
        # Ensure the Blocked Date column is parsed as datetime with the correct format
        blocked_dates['Blocked Date'] = pd.to_datetime(blocked_dates['Blocked Date'], format='%d/%m/%Y')
        return blocked_dates
    except FileNotFoundError:
        return pd.DataFrame(columns=["Blocked Date"])

# Save blocked dates back to blocked_dates.csv
def save_blocked_dates(blocked_dates):
    # Ensure the 'Blocked Date' column is in the correct format
    blocked_dates['Blocked Date'] = blocked_dates['Blocked Date'].dt.strftime('%d/%m/%Y')
    blocked_dates.to_csv("blocked_dates.csv", index=False)

# Admin page
st.title("Admin Page")

st.subheader("Download Transaction History")

# Password input for admin access (for transaction history only)
admin_password = st.text_input("Enter Admin Password", type="password")

if st.button("Login"):
    if admin_password == ADMIN_PASSWORD:
        st.success("Access granted. Welcome to the Admin Dashboard!")

        # Display transaction history
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

# Blocked Dates Section
st.subheader("Manage Blocked Dates")

# Password input for blocked dates management
blocked_dates_password = st.text_input("Enter Password to Manage Blocked Dates", type="password")

if blocked_dates_password == BLOCKED_DATES_PASSWORD:
    # Load blocked dates into session state if not already loaded
    if 'blocked_dates' not in st.session_state:
        blocked_dates = load_blocked_dates()
        st.session_state['blocked_dates'] = blocked_dates

    # Show current blocked dates
    blocked_dates = st.session_state['blocked_dates']
    if not blocked_dates.empty:
        st.write("Current Blocked Dates:")
        st.dataframe(blocked_dates, hide_index=True)

        # Allow the admin to select blocked dates for removal
        dates_to_remove = st.multiselect("Select Blocked Dates to Remove", options=blocked_dates['Blocked Date'].dt.strftime('%d/%m/%Y').tolist())

        if st.button("Remove Selected Blocked Dates"):
            # Remove the selected dates from the DataFrame
            blocked_dates = blocked_dates[~blocked_dates['Blocked Date'].dt.strftime('%d/%m/%Y').isin(dates_to_remove)]
            # Update session state with modified blocked dates
            st.session_state['blocked_dates'] = blocked_dates
            # Save the updated blocked dates back to CSV
            save_blocked_dates(blocked_dates)
            st.success("Selected blocked dates have been removed.")

    else:
        st.info("No blocked dates found.")

    # Add new blocked date
    st.write("Add a New Blocked Date:")

    new_blocked_date = st.text_input("Enter a blocked date (DD/MM/YYYY)", "")

    if st.button("Add Blocked Date"):
        try:
            # Parse the new blocked date
            new_date = datetime.strptime(new_blocked_date, "%d/%m/%Y")
            # Append the new date to the blocked dates dataframe
            new_blocked_row = pd.DataFrame({"Blocked Date": [new_date]})
            blocked_dates = pd.concat([blocked_dates, new_blocked_row], ignore_index=True)
            # Update session state with new blocked dates
            st.session_state['blocked_dates'] = blocked_dates
            # Save the updated blocked dates back to CSV
            save_blocked_dates(blocked_dates)
            st.success(f"The date {new_date.strftime('%d/%m/%Y')} has been blocked.")

        except ValueError:
            st.error("Invalid date format. Please enter the date in DD/MM/YYYY format.")
else:
    st.info("Enter the correct password to manage blocked dates.")
