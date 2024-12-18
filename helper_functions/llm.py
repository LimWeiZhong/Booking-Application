import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken


if load_dotenv('.env'):
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Pass the API Key to the OpenAI Client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_embedding(input, model='text-embedding-3-small'):
    response = client.embeddings.create(
        input=input,
        model=model
    )
    return [x.embedding for x in response.data]


# This is the "Updated" helper function for calling LLM
def get_completion(prompt, model="gpt-4o-mini", temperature=0, top_p=1.0, max_tokens=1024, n=1, json_output=False):
    if json_output == True:
      output_json_structure = {"type": "json_object"}
    else:
      output_json_structure = None

    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create( #originally was openai.chat.completions
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        n=1,
        response_format=output_json_structure,
    )
    return response.choices[0].message.content


# Note that this function directly take in "messages" as the parameter.
def get_completion_by_messages(messages, model="gpt-4o-mini", temperature=0, top_p=1.0, max_tokens=1024, n=1):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        n=1
    )
    return response.choices[0].message.content


# This function is for calculating the tokens given the "message"
# ⚠️ This is simplified implementation that is good enough for a rough estimation
def count_tokens(text):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    return len(encoding.encode(text))


def count_tokens_from_message(messages):
    encoding = tiktoken.encoding_for_model('gpt-4o-mini')
    value = ' '.join([x.get('content') for x in messages])
    return len(encoding.encode(value))


def process_user_message(start_date,end_date, data,user_input, debug=True):
    delimiter = "####"
    input = data

    # Step 1: Check input to see if it flags the Moderation API
    response = OpenAI().moderations.create(input=user_input)
    moderation_output = response.results

    if moderation_output[0].flagged:
        print("Step 1: Input flagged by Moderation API.")
        return "Sorry, we cannot process this request."

    if debug: print("Step 1: Input passed moderation check.")

    # Step 2: Answer the user question
    system_message = f"""You will be provided with data from a meeting room booking application in the form of a transaction log. 
The input data is {input}

The report must be generated dynamically based on the user-specified {start_date} and {end_date}. Additionally, compare metrics from this period with the **previous equivalent date range** (e.g., same duration immediately preceding the start date).

Follow these internal steps to generate a summary report analyzing meeting room booking trends, usage, and relevant metrics. Use steps 1, 2, 3, and 4 internally to formulate the final report in step 5, which will include visualizations and actionable insights.

Do not show steps 1 to 4 in the final output. Only display the finalized report from step 5 to the user.

---

**Step 1:** {delimiter} Preprocess and clean the input data.

- Parse the provided data (transaction_log DataFrame) and ensure proper formatting for the following columns:
  - **Action:** Categorize into key actions such as "Book," "Cancel," or "Update."
  - **Room:** Identify unique rooms and categorize them by type (e.g., Small, Medium, Large).
  - **Date, Start Time, End Time:** Ensure valid datetime formats for precise calculations.
  - **User:** Group data by users or departments if applicable.
  - **Timestamp:** Ensure accurate ordering of actions.

- Filter the data based on the user-specified **start date** and **end date**, and create a **comparison period** immediately preceding this date range of the same duration.

- Handle missing values or invalid entries (e.g., overlapping bookings, invalid timestamps).

---

**Step 2:** {delimiter} Analyze the data for trends and metrics.

- For the selected date range:
  - **Key Metrics:**
    1. Total bookings (count of "Book" actions).
    2. Average daily bookings.
    3. Booking utilization by time of day (e.g., peak hours vs. off-peak).
    4. Popular rooms (e.g., most booked by total hours).
    5. Average booking duration (calculated as `End Time - Start Time`).
    6. Cancellations (count of "Cancel" actions) and cancellation rate (cancellations as a percentage of total bookings).

  - **Trend Analysis:**
    - Identify peak booking periods (e.g., specific days, times, or weeks).
    - Analyze room usage by category (Small, Medium, Large) or specific rooms.
    - Examine user behavior (e.g., frequent users, departments with the highest bookings).

  - Compare these metrics with the **previous equivalent period** to highlight:
    1. Growth or decline in total bookings.
    2. Changes in peak booking times or popular rooms.
    3. Variations in average booking durations or cancellations.

---

**Step 3:** {delimiter} Generate visualizations and summaries.

- Create charts to visualize the data, such as:
  - A time-series line chart comparing total bookings for the current and previous periods.
  - A heatmap of room usage by hour and day of the week.
  - A bar chart showing the distribution of bookings by room type or specific rooms.
  - A pie chart or bar graph illustrating cancellation reasons (if available).
  - A histogram of booking durations.

- Highlight key comparisons and patterns (e.g., “20% increase in bookings compared to the previous period,” or “Higher room utilization observed during afternoons in this period”).

---

**Step 4:** {delimiter} Formulate actionable recommendations.

- Based on trends and insights, suggest data-driven actions, such as:
  - Adjusting room availability or scheduling during peak times.
  - Addressing underutilization of specific rooms through promotions or repurposing.
  - Implementing stricter booking rules or reminders to minimize cancellations.
  - Encouraging off-peak bookings with discounts or incentives.
  - Analyzing user-specific patterns (e.g., frequent bookers or departments) to tailor policies or offerings.

---

**Step 5:** {delimiter} Present the final report.

- Provide a concise summary of the key findings and trends for the selected date range.
- Include a comparison with the previous period, highlighting significant changes or trends.
- Visualize data through charts and tables for clarity.
- Offer actionable recommendations to optimize room usage and improve efficiency.

Example final report output:
---

**Meeting Room Booking Usage Report**

**Summary for {start_date} to {end_date}:**
- Total bookings: 820 (10% increase compared to the previous period).
- Average daily bookings: 27 (compared to 24 in the previous period).
- Peak booking times: 9:00 AM–11:00 AM on Tuesdays and Thursdays.
- Most popular room: "Room A" (32 total bookings, 20% of total).
- Average booking duration: 1.5 hours (unchanged from previous period).
- Cancellation rate: 7% (improved from 9% in the previous period).

**Key Comparisons with Previous Period:**
1. **Total Bookings:** +10% increase compared to the previous period (750 bookings).
2. **Utilization Rates:** Higher usage during late afternoons (2:00 PM–4:00 PM) in the current period.
3. **Cancellations:** Decreased by 22% (from 68 to 53 cancellations).

**Visualizations:**
- Line chart comparing total bookings over time for both periods.
- Heatmap showing room utilization by hour and day of the week.
- Bar chart of booking distribution by room type.
- Pie chart of cancellation reasons.

**Recommendations:**
1. Add more availability for Room A during peak hours to meet demand.
2. Promote off-peak bookings for underutilized rooms through targeted incentives.
3. Maintain stricter booking reminders to reduce last-minute cancellations.
4. Expand afternoon availability for meeting rooms based on increased demand.

---

Only display the final output from step 5 to the user.
    """
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': f"{delimiter}{user_input}{delimiter}"}
    ]

    final_response = get_completion_by_messages(messages)
    if debug:print("Step 2: Generated response to user question.")

    # Step 3: Put the answer through the Moderation API
    response = OpenAI().moderations.create(input=final_response)
    moderation_output = response.results

    if moderation_output[0].flagged:
        if debug: print("Step 3: Response flagged by Moderation API.")
        return "Sorry, we cannot provide this information."

    if debug: print("Step 3: Response passed moderation check.")

    # Step 4: Ask the model if the response answers the initial user query well
    user_message = f"""
    Customer message: {delimiter}{user_input}{delimiter}
    Agent response: {delimiter}{final_response}{delimiter}

    Does the response sufficiently answer the question?
    """
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    evaluation_response = get_completion_by_messages(messages)
    if debug: print("Step 4: Model evaluated the response.")

    # Step 5: If yes, use this answer; if not, say that you will need more information to answer the question
    if "Y" in evaluation_response:
        if debug: print("Step 5: Model approved the response.")
        return final_response
    else:
        if debug: print("Step 5: Model disapproved the response.")
        neg_str = "I'm unable to provide the information you're looking for. Please provide more information on your query"
        return neg_str
