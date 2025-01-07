import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Define available meeting rooms
meeting_rooms = ["DFO Conference Room (Max 15 Pax)", "I-Room (Max 5 Pax)"]

# Load bookings data
try:
    bookings = pd.read_csv("bookings.csv")
    bookings['Start Time'] = pd.to_datetime(bookings['Start Time'])
    bookings['End Time'] = pd.to_datetime(bookings['End Time'])
    bookings['Contact Number'] = bookings['Contact Number'].astype(str)  # Ensure contact number is treated as string
except FileNotFoundError:
    bookings = pd.DataFrame(columns=["Room", "Date", "Start Time", "End Time", "Booked By", "Meeting Title", "Contact Number", "Password"])

# Load blocked dates
try:
    blocked_dates_df = pd.read_csv("blocked_dates.csv")
    blocked_dates = set(pd.to_datetime(blocked_dates_df['Blocked Date']).dt.date)
except FileNotFoundError:
    blocked_dates = set()

# Load transaction log
try:
    transaction_log = pd.read_csv("transaction_log.csv")
    transaction_log['Contact Number'] = transaction_log['Contact Number'].astype(str)  # Ensure contact number is treated as string
except FileNotFoundError:
    transaction_log = pd.DataFrame(columns=["Action", "Room", "Date", "Start Time", "End Time", "User", "Meeting Title", "Contact Number", "Password", "Timestamp"])

# Generate time options in 30-minute intervals between 8 AM and 6 PM
def generate_time_options():
    base_time = datetime(2000, 1, 1, 8, 0)
    return [(base_time + timedelta(minutes=30 * i)).time() for i in range(21)]

time_options = generate_time_options()

# Function to convert time to a readable format
def convert_to_readable_time(time_obj):
    return time_obj.strftime('%I:%M %p')

# Function to check if a date is a weekend or a blocked date
def is_blocked_or_weekend(date):
    if date.weekday() >= 5:  # Check if it's a weekend (Saturday=5, Sunday=6)
        return True
    if date in blocked_dates:  # Check if it's a blocked date
        return True
    return False

# Function to log transactions
def log_transaction(action, room, date, start_time, end_time, user, meeting_title, contact_number, password):
    global transaction_log
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame({
        "Action": [action],
        "Room": [room],
        "Date": [date],
        "Start Time": [start_time],
        "End Time": [end_time],
        "User": [user],
        "Meeting Title": [meeting_title],
        "Contact Number": [str(contact_number)],  # Ensure contact number is logged as string
        "Password": [password],
        "Timestamp": [timestamp]
    })
    transaction_log = pd.concat([transaction_log, new_log], ignore_index=True)
    transaction_log.to_csv("transaction_log.csv", index=False)

# Streamlit Interface
image_path = "images/background.jpg"
st.set_page_config(
    initial_sidebar_state="collapsed"  # Collapse the sidebar
)
st.image(image_path, use_column_width=True)

tabs = st.tabs(["Book a Room", "Edit or Cancel Booking"])

# First Tab: Book a Room
with tabs[0]:
    st.title("Meeting Room Booking System")
    st.subheader("Book a Room")
    today = datetime.today()
    date = st.date_input("Select a Date", min_value=today)

    if is_blocked_or_weekend(date):
        if date in blocked_dates:
            st.error(f"The meeting room is unavailable on {date.strftime('%A, %B %d, %Y')} due to a blocked date.")
        else:
            st.error(f"The meeting room is closed on {date.strftime('%A, %B %d, %Y')} (weekend).")
    else:
        date_bookings = bookings[bookings['Date'] == date.strftime('%Y-%m-%d')]
        if date_bookings.empty:
            st.write("No bookings for the selected date.")
        else:
            st.subheader("Existing Bookings")
            date_bookings['Start Time'] = date_bookings['Start Time'].dt.strftime('%I:%M %p')
            date_bookings['End Time'] = date_bookings['End Time'].dt.strftime('%I:%M %p')
            date_bookings['Contact Number'] = date_bookings['Contact Number'].astype(str)  # Ensure contact numbers are displayed without commas
            st.dataframe(date_bookings.drop(columns=['Date', "Password"]), hide_index=True)

        room = st.selectbox("Select a Room", meeting_rooms)
        start_time = st.selectbox("Start Time", time_options, format_func=lambda x: convert_to_readable_time(x) if x else "")
        end_time = st.selectbox("End Time", time_options, format_func=lambda x: convert_to_readable_time(x) if x else "")
        booked_by = st.text_input("Your Name")
        meeting_title = st.text_input("Meeting Title (Do not use words related to the organisation)")
        contact_number = st.text_input("Contact Number")
        password = st.text_input("Meeting Password (Cap Sensitive - Required when you want to edit/cancel your booking)")

        if st.button("Book Room"):
            if not start_time or not end_time:
                st.error("Please select both start and end times.")
            elif start_time >= end_time:
                st.error("End time must be after start time.")
            elif not booked_by.strip():
                st.error("Please enter your name.")
            elif not meeting_title.strip():
                st.error("Please enter a meeting title.")
            elif not contact_number.strip():
                st.error("Please enter a contact number.")
            elif not password.strip():
                st.error("Please enter a meeting password.")
            else:
                start_datetime = datetime.combine(date, start_time)
                end_datetime = datetime.combine(date, end_time)

                conflict = bookings[(bookings['Room'] == room) &
                                    (bookings['Date'] == date.strftime('%Y-%m-%d')) &
                                    ((bookings['Start Time'] < end_datetime) & (bookings['End Time'] > start_datetime))]

                if not conflict.empty:
                    st.error(f"This room is already booked during the selected time by: {conflict['Booked By'].iloc[0]}.")
                else:
                    new_booking = pd.DataFrame({
                        "Room": [room],
                        "Date": [date.strftime('%Y-%m-%d')],
                        "Start Time": [start_datetime],
                        "End Time": [end_datetime],
                        "Booked By": [booked_by],
                        "Meeting Title": [meeting_title],
                        "Contact Number": [str(contact_number)],  # Ensure contact number is stored as string
                        "Password": [password]
                    })
                    bookings = pd.concat([bookings, new_booking], ignore_index=True)
                    bookings.to_csv("bookings.csv", index=False)
                    log_transaction("Booking", room, date.strftime('%Y-%m-%d'), start_datetime, end_datetime, booked_by, meeting_title, contact_number, password)
                    st.success("Room booked successfully!")

# Second Tab: Edit or Cancel Booking
# Function to convert string time to datetime.time object
def string_to_time(time_str):
    return datetime.strptime(time_str, "%I:%M %p").time()

# Second Tab: Edit or Cancel Booking
with tabs[1]:
    st.title("Edit or Cancel Booking")
    
    # User input for searching existing bookings by password
    password = st.text_input("Enter Meeting Password (Cap Sensitive)")

    if password:
        # Search for existing bookings matching the password
        matched_bookings = bookings[bookings['Password'] == password]

        if matched_bookings.empty:
            st.error("No matching bookings found. Please check the meeting password.")
        else:
            # Display the matched booking details
            st.subheader("Your Bookings")
            matched_bookings['Start Time'] = matched_bookings['Start Time'].dt.strftime('%I:%M %p')
            matched_bookings['End Time'] = matched_bookings['End Time'].dt.strftime('%I:%M %p')
            st.dataframe(matched_bookings.drop(columns=["Password"]), hide_index=True)

            # If multiple bookings exist, allow the user to select one
            booking_to_edit = st.selectbox("Select a Booking to Edit or Cancel", matched_bookings.index, format_func=lambda x: f"Room: {matched_bookings.loc[x, 'Room']} | Date: {matched_bookings.loc[x, 'Date']} | Start: {matched_bookings.loc[x, 'Start Time']} | End: {matched_bookings.loc[x, 'End Time']}")

            if booking_to_edit is not None:
                # Store the selected booking in session state
                st.session_state.selected_booking = matched_bookings.loc[booking_to_edit]

                # Retrieve the selected booking from session state
                selected_booking = st.session_state.selected_booking

                action = st.radio("Select Action", ["Edit Booking", "Cancel Booking"])

                if action == "Edit Booking":
                    # Convert the string date to a datetime.date object
                    selected_date = datetime.strptime(selected_booking['Date'], '%Y-%m-%d').date()

                    # Populate the form with the selected booking details
                    new_room = st.selectbox("New Room", meeting_rooms, index=meeting_rooms.index(selected_booking['Room']))
                    
                    # Convert the string time to datetime.time objects for comparison
                    new_start_time = st.selectbox("New Start Time", time_options, format_func=lambda x: convert_to_readable_time(x) if x else "", 
                                                  index=time_options.index(string_to_time(selected_booking['Start Time'])))
                    new_end_time = st.selectbox("New End Time", time_options, format_func=lambda x: convert_to_readable_time(x) if x else "", 
                                                index=time_options.index(string_to_time(selected_booking['End Time'])))

                    new_meeting_title = st.text_input("New Meeting Title", value=selected_booking['Meeting Title'])
                    
                    if st.button("Save Changes"):
                        if not new_start_time or not new_end_time:
                            st.error("Please select both start and end times.")
                        elif new_start_time >= new_end_time:
                            st.error("End time must be after start time.")
                        elif not new_meeting_title.strip():
                            st.error("Please enter a new meeting title.")
                        else:
                            # Convert selected times back to datetime objects using the selected date
                            new_start_datetime = datetime.combine(selected_date, new_start_time)
                            new_end_datetime = datetime.combine(selected_date, new_end_time)
                            
                            # Check for any conflicts with existing bookings (ignoring the current booking being edited)
                            conflict = bookings[(bookings['Room'] == new_room) & 
                                                (bookings['Date'] == selected_booking['Date']) & 
                                                ((bookings['Start Time'] < new_end_datetime) & (bookings['End Time'] > new_start_datetime))]

                            # Exclude the current booking from conflict check
                            conflict = conflict[conflict.index != booking_to_edit]

                            if not conflict.empty:
                                conflict_user = conflict['Booked By'].iloc[0]
                                
                                # If the conflicting booking is by a different user, show an error
                                if conflict_user != selected_booking['Booked By']:
                                    st.error(f"This room is already booked during the selected time by {conflict_user}. Please choose a different time.")
                                else:
                                    # If the conflict is by the same user, allow the edit
                                    bookings.loc[booking_to_edit, ['Room', 'Start Time', 'End Time', 'Meeting Title']] = [new_room, new_start_datetime, new_end_datetime, new_meeting_title]
                                    bookings.to_csv("bookings.csv", index=False)

                                    # Log the transaction
                                    log_transaction("Edit", new_room, selected_booking['Date'], new_start_datetime, new_end_datetime, selected_booking['Booked By'], new_meeting_title, selected_booking['Contact Number'], password)
                                    
                                    st.success("Booking updated successfully!")
                            else:
                                # No conflict, proceed with the edit
                                bookings.loc[booking_to_edit, ['Room', 'Start Time', 'End Time', 'Meeting Title']] = [new_room, new_start_datetime, new_end_datetime, new_meeting_title]
                                bookings.to_csv("bookings.csv", index=False)

                                # Log the transaction
                                log_transaction("Edit", new_room, selected_booking['Date'], new_start_datetime, new_end_datetime, selected_booking['Booked By'], new_meeting_title, selected_booking['Contact Number'], password)
                                
                                st.success("Booking updated successfully!")
                
                elif action == "Cancel Booking":
                    if st.button("Confirm Cancellation"):
                        # Remove the booking from the dataframe
                        bookings = bookings.drop(booking_to_edit)
                        bookings.to_csv("bookings.csv", index=False)

                        # Log the cancellation transaction
                        log_transaction("Cancellation", selected_booking['Room'], selected_booking['Date'], selected_booking['Start Time'], selected_booking['End Time'], selected_booking['Booked By'], selected_booking['Meeting Title'], selected_booking['Contact Number'], password)
                        
                        st.success("Booking cancelled successfully!")
