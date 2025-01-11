import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar
from streamlit.components.v1 import html

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

# Function to convert string time to datetime.time object
def string_to_time(time_str):
    return datetime.strptime(time_str, "%I:%M %p").time()

# Streamlit Interface
image_path = "images/background.jpg"
st.set_page_config(
    initial_sidebar_state="collapsed"  # Collapse the sidebar
)
st.image(image_path, use_column_width=True)


# Inject JavaScript to capture screen width
js_code = """
<script>
    const width = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
    if (!window.initialized) {
        window.initialized = true;
        const streamlitPython = window.streamlitPyRuntime || window.streamlitRuntime;
        streamlitPython.sendMessage("clientWidth", {width: width});
    }
</script>
"""
html(js_code, height=0, width=0)

# Handle client width
if "clientWidth" not in st.session_state:
    st.session_state["clientWidth"] = 1200  # Default to a desktop screen width
else:
    st.session_state["clientWidth"] = st.session_state.get("clientWidth", 1200)

# Set default view based on screen width
default_view = "listMonth" if st.session_state["clientWidth"] < 768 else "dayGridMonth"

# Tabs setup
tabs = st.tabs(["Calendar Overview", "Book a Room", "Edit or Cancel Booking"])


# Function to create calendar events
def create_calendar_events(bookings, room_colors, view_type):
    calendar_events = []
    for index, booking in bookings.iterrows():
        title = booking.get('Meeting Title', 'Untitled Meeting')
        booked_by = booking.get('Booked By', 'Unknown')
        room = booking.get('Room', 'Unspecified Room')
        contact_number = booking.get('Contact Number', 'N/A')  # Optional field for contact
        start_time = booking.get('Start Time')
        end_time = booking.get('End Time')

        if start_time and end_time:
            formatted_start_time = start_time.strftime('%I:%M %p').lstrip("0").lower()
            formatted_end_time = end_time.strftime('%I:%M %p').lstrip("0").lower()

            if view_type == "dayGridMonth":  # Grid view
                event_title = f"m-{formatted_end_time}"
                event_description = ""
            elif view_type == "listMonth":  # List view
                event_title = f"{booked_by} ({contact_number}) - {title}"
                event_description = (
                    f"Room: {room}\n"
                    f"Booked by: {booked_by}\n"
                    f"Contact: {contact_number}\n"
                    f"Meeting Title: {title}\n"
                    f"Start: {formatted_start_time}\n"
                    f"End: {formatted_end_time}"
                )
            else:
                event_title = f"{title}"
                event_description = ""

            event = {
                "title": event_title,
                "start": start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                "end": end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                "resourceId": room,
                "backgroundColor": "#FFFFFF",
                "borderColor": room_colors.get(room, "#3788d8"),
                "description": event_description,
            }
            calendar_events.append(event)
    return calendar_events

# First Tab: Calendar Overview
with tabs[0]:
    st.title("DFO Meeting Room Overview")
    st.subheader("View meeting room bookings at a glance")

    # Allow user to override default view
    calendar_views = {
        "Month View (Desktop)": "dayGridMonth",
        "List View (Mobile)": "listMonth",
    }
    selected_view_label = st.selectbox(
        "Select Calendar View",
        list(calendar_views.keys()),
        index=0 if default_view == "dayGridMonth" else 1,
        help="Switch between a detailed month overview for desktops or a list view for mobile devices.",
    )
    selected_view = calendar_views[selected_view_label]

    # Dropdown for selecting a room filter
    selected_room = st.radio(
        "Filter by Room",
        options=["All Rooms"] + meeting_rooms,
        index=0
    )

    # Define room-specific colors
    room_colors = {
        "DFO Conference Room (Max 15 Pax)": "#4CAF50",
        "I-Room (Max 5 Pax)": "#2196F3",
    }

    # Create calendar events
    calendar_events = create_calendar_events(bookings, room_colors, selected_view)

    # Filter events based on the selected room
    if selected_room != "All Rooms":
        filtered_events = [
            event for event in calendar_events if event["resourceId"] == selected_room
        ]
    else:
        filtered_events = calendar_events

    # Default calendar options
    calendar_options = {
        "initialView": selected_view,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "",
        },
        "editable": False,
        "selectable": False,
        "eventColor": "#FFFFFF",
        "slotMinTime": "06:00:00",
        "slotMaxTime": "18:00:00",
    }

    # Custom CSS for mobile
    custom_css = """
        .fc-event {
            font-size: 10px;
            font-weight: bold;
            padding: 2px;
            margin: 1px;
            border-radius: 5px;
            text-overflow: ellipsis;
            overflow: hidden;
            border-style: groove;
            white-space: nowrap;
        }
        .fc-toolbar-title {
            font-size: 1.5rem;
            font-weight: bold;
            color: #333;
        }
        .fc-event:hover {
            background-color: #e8e8e8;
        }
        .fc {
            font-size: 12px;
        }
    """

    # Display the calendar with filtered events and optimized view
    calendar_widget = calendar(events=filtered_events, options=calendar_options, custom_css=custom_css)
    st.write(calendar_widget)


# Add custom CSS to hide specific parts of the JSON output
st.markdown("""
    <style>
    /* Hide the collapsed icon (arrow) */
    .stJson .collapsed-icon {
        display: none !important;
    }
    
    /* Hide the opening '{' */
    .stJson .object-key-val span:nth-child(2) {
        display: none !important;
    }

    /* Hide the ellipsis '...' */
    .stJson .node-ellipsis {
        display: none !important;
    }

    /* Hide the closing '}' */
    .stJson .brace-row span {
        display: none !important;
    }
    
    /* Hide the opening '{' for object contents */
    .stJson .object-key-val > span:first-child {
        display: none !important;
    }

    /* Hide the entire variable-row element */
    .variable-row {
        display: none !important;
    }
    
    /* Hide the string-value span */
    .string-value {
        display: none !important;
    }

    /* Hide the copy-to-clipboard container */
    .copy-to-clipboard-container {
        display: none !important;
    }

    /* Hide the object-key-val element */
    .object-key-val {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)




# First Tab: Book a Room
with tabs[1]:
    st.title("Meeting Room Booking System")
    st.subheader("Book a Room")
    today = datetime.today()
    date = st.date_input("Select a Date", min_value=today,format="DD/MM/YYYY")

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


with tabs[2]:
    st.title("Edit or Cancel Booking")
    
    # User input for searching existing bookings by password
    password = st.text_input("Enter Meeting Password (Cap Sensitive)")

    if password:
        # Search for existing bookings matching the password
        matched_bookings = bookings[bookings['Password'] == password]

        if matched_bookings.empty:
            st.error("No matching bookings found. Please check the meeting password. If you forget your password, please contact Wei Zhong @ 90890631")
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

                    # Allow user to select a new date
                    new_date = st.date_input(
                        "Select a New Date", 
                        min_value=datetime.today(), 
                        value=selected_date, 
                        format="DD/MM/YYYY"
                    )

                    if is_blocked_or_weekend(new_date):
                        if new_date in blocked_dates:
                            st.error(f"The meeting room is unavailable on {new_date.strftime('%A, %B %d, %Y')} due to a blocked date.")
                        else:
                            st.error(f"The meeting room is closed on {new_date.strftime('%A, %B %d, %Y')} (weekend).")
                    else:
                        # Populate the form with the selected booking details
                        new_room = st.selectbox("New Room", meeting_rooms, index=meeting_rooms.index(selected_booking['Room']))

                        # Convert the string time to datetime.time objects for comparison
                        new_start_time = st.selectbox(
                            "New Start Time", 
                            time_options, 
                            format_func=lambda x: convert_to_readable_time(x) if x else "",
                            index=time_options.index(string_to_time(selected_booking['Start Time']))
                        )
                        new_end_time = st.selectbox(
                            "New End Time", 
                            time_options, 
                            format_func=lambda x: convert_to_readable_time(x) if x else "",
                            index=time_options.index(string_to_time(selected_booking['End Time']))
                        )

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
                                new_start_datetime = datetime.combine(new_date, new_start_time)
                                new_end_datetime = datetime.combine(new_date, new_end_time)

                                # Check for any conflicts with existing bookings (ignoring the current booking being edited)
                                conflict = bookings[
                                    (bookings['Room'] == new_room) & 
                                    (bookings['Date'] == new_date.strftime('%Y-%m-%d')) & 
                                    ((bookings['Start Time'] < new_end_datetime) & (bookings['End Time'] > new_start_datetime))
                                ]

                                # Exclude the current booking from conflict check
                                conflict = conflict[conflict.index != booking_to_edit]

                                if not conflict.empty:
                                    conflict_user = conflict['Booked By'].iloc[0]
                                    
                                    # If the conflicting booking is by a different user, show an error
                                    if conflict_user != selected_booking['Booked By']:
                                        st.error(f"This room is already booked during the selected time by {conflict_user}. Please choose a different time.")
                                    else:
                                        # If the conflict is by the same user, allow the edit
                                        bookings.loc[booking_to_edit, ['Date', 'Room', 'Start Time', 'End Time', 'Meeting Title']] = [
                                            new_date.strftime('%Y-%m-%d'), 
                                            new_room, 
                                            new_start_datetime, 
                                            new_end_datetime, 
                                            new_meeting_title
                                        ]
                                        bookings.to_csv("bookings.csv", index=False)

                                        # Log the transaction
                                        log_transaction(
                                            "Edit", new_room, new_date.strftime('%Y-%m-%d'), 
                                            new_start_datetime, new_end_datetime, 
                                            selected_booking['Booked By'], new_meeting_title, 
                                            selected_booking['Contact Number'], password
                                        )
                                        
                                        st.success("Booking updated successfully!")
                                else:
                                    # No conflict, proceed with the edit
                                    bookings.loc[booking_to_edit, ['Date', 'Room', 'Start Time', 'End Time', 'Meeting Title']] = [
                                        new_date.strftime('%Y-%m-%d'), 
                                        new_room, 
                                        new_start_datetime, 
                                        new_end_datetime, 
                                        new_meeting_title
                                    ]
                                    bookings.to_csv("bookings.csv", index=False)

                                    # Log the transaction
                                    log_transaction(
                                        "Edit", new_room, new_date.strftime('%Y-%m-%d'), 
                                        new_start_datetime, new_end_datetime, 
                                        selected_booking['Booked By'], new_meeting_title, 
                                        selected_booking['Contact Number'], password
                                    )
                                    
                                    st.success("Booking updated successfully!")
                
                elif action == "Cancel Booking":
                    if st.button("Confirm Cancellation"):
                        # Remove the booking from the dataframe
                        bookings = bookings.drop(booking_to_edit)
                        bookings.to_csv("bookings.csv", index=False)

                        # Log the cancellation transaction
                        log_transaction("Cancellation", selected_booking['Room'], selected_booking['Date'], selected_booking['Start Time'], selected_booking['End Time'], selected_booking['Booked By'], selected_booking['Meeting Title'], selected_booking['Contact Number'], password)
                        
                        st.success("Booking cancelled successfully!")