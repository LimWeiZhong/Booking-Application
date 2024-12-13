import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# Email Configuration
EMAIL_ADDRESS = "lim_wei_zhong@hotmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "d81c655b0deadtitan"   # Replace with your Gmail app password

# Define available meeting rooms
meeting_rooms = ["Room A", "Room B", "Room C"]

# Load bookings data
try:
    bookings = pd.read_csv("bookings.csv")
    bookings['Start Time'] = pd.to_datetime(bookings['Start Time'])
    bookings['End Time'] = pd.to_datetime(bookings['End Time'])
except FileNotFoundError:
    bookings = pd.DataFrame(columns=["Room", "Date", "Start Time", "End Time", "Booked By"])

# Load blocked dates
try:
    blocked_dates_df = pd.read_csv("blocked_dates.csv")
    blocked_dates = set(pd.to_datetime(blocked_dates_df['Blocked Date']).dt.date)
except FileNotFoundError:
    blocked_dates = set()

# Load transaction log
try:
    transaction_log = pd.read_csv("transaction_log.csv")
except FileNotFoundError:
    transaction_log = pd.DataFrame(columns=["Action", "Room", "Date", "Start Time", "End Time", "User", "Timestamp"])

# Generate time options in 30-minute intervals between 8 AM and 6 PM
def generate_time_options():
    base_time = datetime(2000, 1, 1, 8, 0)
    return [(base_time + timedelta(minutes=30 * i)).time() for i in range(20)]

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

def send_email_notification(action, room, date, start_time, end_time, user, recipient_email):
    subject = "New Booking System Notification"
    body = f"""
    A new transaction has been made in the booking system:

    Action: {action}
    Room: {room}
    Date: {date}
    Start Time: {start_time}
    End Time: {end_time}
    User: {user}

    Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """

    # Construct email
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the Outlook/Hotmail SMTP server
        with smtplib.SMTP('smtp-mail.outlook.com', 587) as server:
            server.starttls()  # Secure the connection using TLS
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Login with your Hotmail/Outlook email and app password
            server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())  # Send the email
        print(f"Email sent successfully to {recipient_email}")  # Debug message for success
    except Exception as e:
        print(f"Failed to send email notification: {e}")  # Debug message for failure
        print(traceback.format_exc())  # Print detailed traceback for debugging

# Function to log transactions
def log_transaction(action, room, date, start_time, end_time, user, recipient_email):
    global transaction_log
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame({
        "Action": [action],
        "Room": [room],
        "Date": [date],
        "Start Time": [start_time],
        "End Time": [end_time],
        "User": [user],
        "Timestamp": [timestamp]
    })
    transaction_log = pd.concat([transaction_log, new_log], ignore_index=True)
    transaction_log.to_csv("transaction_log.csv", index=False)

    # Send email notification
    send_email_notification(action, room, date, start_time, end_time, user, recipient_email)

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
            date_bookings['Start Time'] = date_bookings['Start Time'].apply(lambda x: convert_to_readable_time(x))
            date_bookings['End Time'] = date_bookings['End Time'].apply(lambda x: convert_to_readable_time(x))
            st.dataframe(date_bookings.drop(columns=['Date']), hide_index=True)

        room = st.selectbox("Select a Room", meeting_rooms)
        start_time = st.selectbox("Start Time", [None] + time_options, format_func=lambda x: convert_to_readable_time(x) if x else "")
        end_time = st.selectbox("End Time", [None] + time_options, format_func=lambda x: convert_to_readable_time(x) if x else "")
        booked_by = st.text_input("Your Name")
        recipient_email = st.text_input("Recipient Email Address")

        if st.button("Book Room"):
            if not start_time or not end_time:
                st.error("Please select both start and end times.")
            elif start_time >= end_time:
                st.error("End time must be after start time.")
            elif not booked_by.strip():
                st.error("Please enter your name.")
            elif not recipient_email.strip():
                st.error("Please enter a valid recipient email address.")
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
                        "Booked By": [booked_by]
                    })
                    bookings = pd.concat([bookings, new_booking], ignore_index=True)
                    bookings.to_csv("bookings.csv", index=False)
                    log_transaction("Booking", room, date.strftime('%Y-%m-%d'), start_datetime, end_datetime, booked_by, recipient_email)
                    st.success("Room booked successfully!")

# Second Tab: Edit or Cancel Booking
with tabs[1]:
    st.title("Manage Your Bookings")
    date = st.date_input("Select a Date for Editing or Cancelling", min_value=datetime.today())
    date_bookings = bookings[bookings['Date'] == date.strftime('%Y-%m-%d')]

    if date_bookings.empty:
        st.write("No bookings for the selected date.")
    else:
        date_bookings['Start Time'] = date_bookings['Start Time'].apply(lambda x: convert_to_readable_time(x))
        date_bookings['End Time'] = date_bookings['End Time'].apply(lambda x: convert_to_readable_time(x))
        st.dataframe(date_bookings.drop(columns=['Date']), hide_index=True)

        booking_to_edit = st.selectbox("Select a booking to edit or cancel", ["Select a booking"] + date_bookings['Booked By'].tolist())

        if booking_to_edit != "Select a booking":
            selected_booking = date_bookings[date_bookings['Booked By'] == booking_to_edit].iloc[0]
            edit_or_cancel = st.radio("What would you like to do?", ("Edit Booking", "Cancel Booking"))

            if edit_or_cancel == "Edit Booking":
                new_start_time = st.selectbox("New Start Time", time_options, 
                                              index=time_options.index(datetime.strptime(selected_booking['Start Time'], '%I:%M %p').time()) if selected_booking['Start Time'] else 0,
                                              format_func=lambda x: convert_to_readable_time(x))
                new_end_time = st.selectbox("New End Time", time_options, 
                                            index=time_options.index(datetime.strptime(selected_booking['End Time'], '%I:%M %p').time()) if selected_booking['End Time'] else 0,
                                            format_func=lambda x: convert_to_readable_time(x))
                new_booked_by = st.text_input("New Booked By", value=selected_booking['Booked By'])
                recipient_email = st.text_input("Recipient Email Address")

                if st.button("Save Changes"):
                    start_datetime = datetime.combine(date, new_start_time)
                    end_datetime = datetime.combine(date, new_end_time)
                    conflict = bookings[(bookings['Room'] == selected_booking['Room']) &
                                        (bookings['Date'] == date.strftime('%Y-%m-%d')) & 
                                        ((bookings['Start Time'] < end_datetime) & (bookings['End Time'] > start_datetime))]

                    if conflict.empty:
                        bookings.loc[bookings['Booked By'] == booking_to_edit, ['Start Time', 'End Time', 'Booked By']] = [start_datetime, end_datetime, new_booked_by]
                        bookings.to_csv("bookings.csv", index=False)
                        log_transaction("Edit", selected_booking['Room'], date.strftime('%Y-%m-%d'), start_datetime, end_datetime, new_booked_by, recipient_email)
                        st.success("Booking updated successfully!")
                    else:
                        st.error(f"New time conflicts with another booking during the selected time.")

            elif edit_or_cancel == "Cancel Booking":
                recipient_email = st.text_input("Recipient Email Address")
                if st.button("Cancel Booking"):
                    bookings = bookings[bookings['Booked By'] != booking_to_edit]
                    bookings.to_csv("bookings.csv", index=False)
                    log_transaction("Cancellation", selected_booking['Room'], date.strftime('%Y-%m-%d'), selected_booking['Start Time'], selected_booking['End Time'], booking_to_edit, recipient_email)
                    st.success(f"Booking for {booking_to_edit} has been canceled.")
