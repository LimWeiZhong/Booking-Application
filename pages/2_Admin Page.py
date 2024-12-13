import streamlit as st
import pandas as pd

# Load transaction log
try:
    transaction_log = pd.read_csv("transaction_log.csv")
except FileNotFoundError:
    transaction_log = pd.DataFrame(columns=["Action", "Room", "Date", "Start Time", "End Time", "User", "Timestamp"])

st.title("Admin Page")
st.subheader("Transaction History")
st.dataframe(transaction_log, hide_index=True)

csv = transaction_log.to_csv(index=False)
st.download_button(label="Download Transaction History", data=csv, file_name="transaction_log.csv", mime="text/csv")