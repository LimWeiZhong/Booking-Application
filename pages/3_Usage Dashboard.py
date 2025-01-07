import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Function to load and preprocess transaction log
def load_transaction_log():
    transaction_log = pd.read_csv('./transaction_log.csv')
    # Filter the transaction log to include only 'Booking' actions
    transaction_log = transaction_log[transaction_log['Action'] == 'Booking']
    transaction_log['Date'] = pd.to_datetime(transaction_log['Date'])
    transaction_log['Year'] = transaction_log['Date'].dt.year
    transaction_log['Month'] = transaction_log['Date'].dt.month
    transaction_log['Day'] = transaction_log['Date'].dt.day
    transaction_log['Start Time'] = pd.to_datetime(transaction_log['Start Time'])
    transaction_log['End Time'] = pd.to_datetime(transaction_log['End Time'])
    return transaction_log

# Function to load and preprocess blocked dates
def load_blocked_dates():
    blocked_dates = pd.read_csv('./blocked_dates.csv')
    blocked_dates['Blocked Date'] = pd.to_datetime(blocked_dates['Blocked Date'], format='%d/%m/%Y')
    return blocked_dates


st.set_page_config(
    page_title="Booking Usage Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Reload transaction log and blocked dates each time the page is refreshed
transaction_log = load_transaction_log()
blocked_dates = load_blocked_dates()

# Store the reloaded transaction log and blocked dates in session state
if 'transaction_log' not in st.session_state:
    st.session_state.transaction_log = transaction_log
if 'blocked_dates' not in st.session_state:
    st.session_state.blocked_dates = blocked_dates

# Sidebar for filtering dashboard
with st.sidebar:
    st.header("Filter options")
    
    # Year selection with 'All Years' option
    selected_year = st.selectbox("Select Year", options=['All Years'] + [str(year) for year in sorted(st.session_state.transaction_log['Year'].unique(), reverse=True)])
    
    # Filter data for selected year (if not 'All Years' selected)
    if selected_year != 'All Years':
        filtered_by_year = st.session_state.transaction_log[st.session_state.transaction_log['Year'] == int(selected_year)]
    else:
        filtered_by_year = st.session_state.transaction_log  # Use all data if 'All Years' is selected

    # Room selection with an option for 'All Rooms'
    selected_room = st.selectbox("Select Room", options=['All Rooms'] + sorted(filtered_by_year['Room'].unique().tolist()))
    
    # Month options for the selected year (defaults to 'All Months' when a year is selected)
    month_names = [datetime(1900, month, 1).strftime('%b') for month in range(1, 13)]
    selected_month_name = st.selectbox("Select Month", options=['All Months'] + month_names)
    
    # Convert month name back to month number when not 'All Months'
    if selected_month_name != 'All Months':
        selected_month = datetime.strptime(selected_month_name, '%b').month
    else:
        selected_month = None  # Show all months if 'All Months' is selected
    
    # Day of the month filter (1, 2, 3, etc.)
    day_of_month = st.multiselect("Select Day(s) of the Month", options=list(range(1, 32)))

# Filter the transaction log for the selected room, year, month, and day
if selected_room == 'All Rooms':
    filtered_transactions = filtered_by_year[filtered_by_year['Action'] == 'Booking']  # Only include bookings
else:
    filtered_transactions = filtered_by_year[(filtered_by_year['Room'] == selected_room) & 
                                              (filtered_by_year['Action'] == 'Booking')]  # Only include bookings

if selected_month:
    filtered_transactions = filtered_transactions[filtered_transactions['Month'] == selected_month]

if day_of_month:
    filtered_transactions = filtered_transactions[filtered_transactions['Day'].isin(day_of_month)]

# Check if there are no transactions after filtering
if filtered_transactions.empty:
    st.warning("No transactions found for the selected filters.")
else:
    # Define available time slots (8 AM to 6 PM, 30-minute intervals)
    def available_time_slots(year, month, day_of_month=None):
        # Get the first and last date of the selected month
        first_day = datetime(year, month, 1)
        last_day = datetime(year, month, 1) + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        # Generate a list of all dates in the month
        all_dates = pd.date_range(start=first_day, end=last_day, freq='D')

        # Filter by the selected days of the month (if any)
        if day_of_month:
            available_dates = all_dates[all_dates.day.isin(day_of_month)]
        else:
            available_dates = all_dates

        # Blocked dates filtering
        blocked_dates = st.session_state.blocked_dates['Blocked Date'].dt.date
        available_dates = [d for d in available_dates if d.date() not in blocked_dates.values]

        # Number of available dates
        num_available_dates = len(available_dates)

        # Multiply by slots per day (20 slots per day from 8 AM to 6 PM)
        return num_available_dates * 20  # 20 slots per day (8 AM - 6 PM)

    # Calculate booked time slots (number of time slots booked)
    def booked_time_slots(bookings):
        total_booked_slots = 0
        for _, row in bookings.iterrows():
            if row['Action'] == 'Booking':  # Only count bookings
                start_time = row['Start Time']
                end_time = row['End Time']
                # Calculate the difference in minutes and divide by 30 for slots
                booked_slots = (end_time - start_time).total_seconds() / 1800  # 1800 seconds = 30 minutes
                total_booked_slots += booked_slots
        return total_booked_slots

    # Get available time slots based on filtered data
    if selected_month and selected_year:
        available_slots = available_time_slots(int(selected_year), selected_month, day_of_month)
    else:
        available_slots = 0

    # Get booked time slots from the filtered transactions
    booked_slots = booked_time_slots(filtered_transactions)

    # Calculate the utilization rate (booked slots / available slots)
    utilization_rate = (booked_slots / available_slots) * 100 if available_slots > 0 else 0

    # Display key metrics
    with st.container():
        if selected_room == 'All Rooms':
            st.title(f"Booking Usage Dashboard")
        else:
            st.title(f"Booking Dashboard for {selected_room}")
        
        st.info("Use the Filter Options in the sidebar.")

        st.markdown(f"### Key Metrics for {selected_room}")
        met1, met2, met3 = st.columns(3)
        met1.metric(
            label="Utilization Rate",
            value=f"{utilization_rate:.2f}%",
            help="The percentage of time slots booked compared to the total available time slots"
        )
        met2.metric(
            label="Total Bookings",
            value=filtered_transactions.shape[0],
            help="Total number of bookings for the selected period"
        )
        met3.metric(
            label="Unique Users",
            value=filtered_transactions['User'].nunique(),
            help="Number of unique users who made bookings"
        )

    # Tabs for each metric
    tab_utilization_rate, tab_total_bookings, tab_unique_users = st.tabs(["Utilization Rate", "Total Bookings", "Unique Users"])

    # Utilization Rate Tab
    with tab_utilization_rate:
        st.header("Utilization Rate")
        subtab_monthly, subtab_daily = st.tabs(["Monthly Trend", "Daily Trend"])

        with subtab_monthly:
            st.subheader("Monthly Utilization Rate")
            # Create a complete list of months
            all_months = pd.MultiIndex.from_product(
                [filtered_transactions['Year'].unique(), range(1, 13)], names=['Year', 'Month']
            ).to_frame(index=False)

            # Group data and merge with all months
            monthly_utilization = (
                filtered_transactions.groupby(['Year', 'Month'])
                .apply(lambda df: booked_time_slots(df) / available_time_slots(df['Year'].iloc[0], df['Month'].iloc[0]) * 100)
                .reset_index(name="Utilization Rate")
            )
            monthly_utilization = all_months.merge(monthly_utilization, on=['Year', 'Month'], how='left').fillna(0)

            # Add month labels (Jan, Feb, etc.)
            monthly_utilization['Month Name'] = monthly_utilization['Month'].apply(lambda x: datetime(1900, x, 1).strftime('%b'))

            # Plot
            fig = px.bar(
                monthly_utilization,
                x="Month Name", y="Utilization Rate",
                title="Monthly Utilization Rate", labels={'Utilization Rate': 'Utilization Rate (%)'}
            )
            fig.update_layout(showlegend=False)  # Remove legend
            st.plotly_chart(fig, use_container_width=True)

        with subtab_daily:
            st.subheader("Daily Utilization Rate")
            # Create a complete list of dates
            all_dates = pd.date_range(
                start=filtered_transactions['Date'].min(), end=filtered_transactions['Date'].max(), freq='D'
            )
            all_dates_df = pd.DataFrame(all_dates, columns=['Date'])

            # Group data and merge with all dates
            daily_utilization = (
                filtered_transactions.groupby(filtered_transactions['Date'])
                .apply(lambda df: booked_time_slots(df) / available_time_slots(df['Year'].iloc[0], df['Month'].iloc[0], [df['Day'].iloc[0]]) * 100)
                .reset_index(name="Utilization Rate")
            )
            daily_utilization = all_dates_df.merge(daily_utilization, on='Date', how='left').fillna(0)

            # Plot
            fig = px.line(
                daily_utilization,
                x="Date", y="Utilization Rate",
                title="Daily Utilization Rate", labels={'Utilization Rate': 'Utilization Rate (%)'}
            )
            fig.update_layout(showlegend=False)  # Remove legend
            st.plotly_chart(fig, use_container_width=True)

    # Total Bookings Tab
    with tab_total_bookings:
        st.header("Total Bookings")
        subtab_monthly, subtab_daily = st.tabs(["Monthly Trend", "Daily Trend"])

        with subtab_monthly:
            st.subheader("Monthly Total Bookings")
            # Create a complete list of months
            monthly_bookings = filtered_transactions.groupby(['Year', 'Month'])['Action'].count().reset_index(name="Total Bookings")
            monthly_bookings = all_months.merge(monthly_bookings, on=['Year', 'Month'], how='left').fillna(0)

            # Add month labels (Jan, Feb, etc.)
            monthly_bookings['Month Name'] = monthly_bookings['Month'].apply(lambda x: datetime(1900, x, 1).strftime('%b'))

            # Plot
            fig = px.bar(
                monthly_bookings,
                x="Month Name", y="Total Bookings",
                title="Monthly Total Bookings", labels={'Total Bookings': 'Total Bookings'}
            )
            fig.update_layout(showlegend=False)  # Remove legend
            st.plotly_chart(fig, use_container_width=True)

        with subtab_daily:
            st.subheader("Daily Total Bookings")
            # Create a complete list of dates
            daily_bookings = filtered_transactions.groupby('Date')['Action'].count().reset_index(name="Total Bookings")
            daily_bookings = all_dates_df.merge(daily_bookings, on='Date', how='left').fillna(0)

            # Plot as a line chart
            fig = px.line(
                daily_bookings,
                x="Date", y="Total Bookings",
                title="Daily Total Bookings", labels={'Total Bookings': 'Total Bookings'}
            )
            fig.update_layout(showlegend=False)  # Remove legend
            st.plotly_chart(fig, use_container_width=True)

    # Unique Users Tab
    with tab_unique_users:
        st.header("Unique Users")
        subtab_monthly, subtab_daily = st.tabs(["Monthly Trend", "Daily Trend"])

        with subtab_monthly:
            st.subheader("Monthly Unique Users")
            # Create a complete list of months
            monthly_users = filtered_transactions.groupby(['Year', 'Month'])['User'].nunique().reset_index(name="Unique Users")
            monthly_users = all_months.merge(monthly_users, on=['Year', 'Month'], how='left').fillna(0)

            # Add month labels (Jan, Feb, etc.)
            monthly_users['Month Name'] = monthly_users['Month'].apply(lambda x: datetime(1900, x, 1).strftime('%b'))

            # Plot
            fig = px.bar(
                monthly_users,
                x="Month Name", y="Unique Users",
                title="Monthly Unique Users", labels={'Unique Users': 'Unique Users'}
            )
            fig.update_layout(showlegend=False)  # Remove legend
            st.plotly_chart(fig, use_container_width=True)

        with subtab_daily:
            st.subheader("Daily Unique Users")
            # Create a complete list of dates
            daily_users = filtered_transactions.groupby('Date')['User'].nunique().reset_index(name="Unique Users")
            daily_users = all_dates_df.merge(daily_users, on='Date', how='left').fillna(0)

            # Plot
            fig = px.line(
                daily_users,
                x="Date", y="Unique Users",
                title="Daily Unique Users", labels={'Unique Users': 'Unique Users'}
            )
            fig.update_layout(showlegend=False)  # Remove legend
            st.plotly_chart(fig, use_container_width=True)
