import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

# Initialize the Streamlit app
st.title("Moldova for Peace Data Collection")

# Sidebar for navigation
st.sidebar.title("Navigation")
options = ["Trust Levels", "Participation Rates", "Diversity Indices", "Health and Safety", "Data Analysis", "Download Data"]
choice = st.sidebar.radio("Go to", options)

# Google Sheets credentials and initialization
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('C:\\apptests\\docstreamerAPI.json', scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1hkc5RA6sUC5f_pKMrpyc_uRKJz1VHNNSBXxUyd2NkOg/")

# Function to get or create a worksheet
def get_or_create_worksheet(spreadsheet, title):
    try:
        worksheet = spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=title, rows="1000", cols="20")
    return worksheet

# Get or create worksheets for each section
trust_levels_sheet = get_or_create_worksheet(spreadsheet, "Trust Levels")
participation_rates_sheet = get_or_create_worksheet(spreadsheet, "Participation Rates")
diversity_indices_sheet = get_or_create_worksheet(spreadsheet, "Diversity Indices")
health_and_safety_sheet = get_or_create_worksheet(spreadsheet, "Health and Safety")

# Function to save data to Google Sheets
def save_to_google_sheets(sheet, responses):
    headers = sheet.row_values(1)
    if not headers:
        headers = ["Section"] + list(responses.keys())
        sheet.append_row(headers)
    row = [responses.get(header, "") for header in headers[1:]]
    sheet.append_row(row)
    st.success("Data saved successfully!")

# Function to create a dataframe from Google Sheets data
def create_dataframe(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Main content based on the selected section
if choice == "Trust Levels":
    st.header("Trust Levels Survey")
    neighbors_trust = st.slider("How much do you trust your neighbors?", 1, 5, 3)
    leaders_trust = st.slider("How much do you trust local community leaders?", 1, 5, 3)
    institutions_trust = st.slider("How much do you trust local institutions?", 1, 5, 3)
    help_willingness = st.slider("How often do you feel people in your community are willing to help each other?", 1, 5, 3)
    people_trustworthy = st.radio("Do you believe that most people in your community are trustworthy?", ["Yes", "No"])
    government_confidence = st.slider("How confident are you in the local government’s ability to handle crises?", 1, 5, 3)
    government_transparency = st.slider("How transparent do you believe the local government is?", 1, 5, 3)

    if st.button("Submit"):
        responses = {
            "Neighbors Trust": neighbors_trust,
            "Leaders Trust": leaders_trust,
            "Institutions Trust": institutions_trust,
            "Help Willingness": help_willingness,
            "People Trustworthy": people_trustworthy,
            "Government Confidence": government_confidence,
            "Government Transparency": government_transparency
        }
        save_to_google_sheets(trust_levels_sheet, responses)

elif choice == "Participation Rates":
    st.header("Participation Rates Survey")
    community_events = st.selectbox("How often do you participate in community events?", ["Never", "Rarely", "Sometimes", "Often", "Always"])
    local_organizations = st.radio("Are you a member of any local organizations or groups?", ["Yes", "No"])
    volunteer_frequency = st.selectbox("How often do you volunteer in your community?", ["Never", "Rarely", "Sometimes", "Often", "Always"])
    voted_last_election = st.radio("Did you vote in the last local election?", ["Yes", "No"])
    town_hall_meetings = st.selectbox("How often do you attend town hall meetings?", ["Never", "Rarely", "Sometimes", "Often", "Always"])

    if st.button("Submit"):
        responses = {
            "Community Events Participation": community_events,
            "Local Organizations Membership": local_organizations,
            "Volunteer Frequency": volunteer_frequency,
            "Voted Last Election": voted_last_election,
            "Town Hall Meetings Attendance": town_hall_meetings
        }
        save_to_google_sheets(participation_rates_sheet, responses)

elif choice == "Diversity Indices":
    st.header("Diversity Indices Survey")
    ethnic_diversity = st.selectbox("How would you describe the ethnic diversity in your community?", ["Very Diverse", "Somewhat Diverse", "Not Very Diverse", "Not Diverse"])
    cultural_interactions = st.selectbox("How frequently do you interact with people from different cultural backgrounds?", ["Never", "Rarely", "Sometimes", "Often", "Always"])
    socio_economic_diversity = st.selectbox("How would you describe the socio-economic diversity in your community?", ["Very Diverse", "Somewhat Diverse", "Not Very Diverse", "Not Diverse"])

    if st.button("Submit"):
        responses = {
            "Ethnic Diversity": ethnic_diversity,
            "Cultural Interactions": cultural_interactions,
            "Socio-Economic Diversity": socio_economic_diversity
        }
        save_to_google_sheets(diversity_indices_sheet, responses)

elif choice == "Health and Safety":
    st.header("Health and Safety Survey")
    day_safety = st.selectbox("How safe do you feel in your neighborhood during the day?", ["Very Safe", "Safe", "Neutral", "Unsafe", "Very Unsafe"])
    night_safety = st.selectbox("How safe do you feel in your neighborhood at night?", ["Very Safe", "Safe", "Neutral", "Unsafe", "Very Unsafe"])
    healthcare_access = st.selectbox("How easy is it for you to access healthcare services?", ["Very Easy", "Easy", "Neutral", "Difficult", "Very Difficult"])
    community_health = st.selectbox("How would you rate the overall health and well-being of your community?", ["Very Good", "Good", "Neutral", "Poor", "Very Poor"])

    if st.button("Submit"):
        responses = {
            "Day Safety": day_safety,
            "Night Safety": night_safety,
            "Healthcare Access": healthcare_access,
            "Community Health": community_health
        }
        save_to_google_sheets(health_and_safety_sheet, responses)

elif choice == "Data Analysis":
    st.header("Data Analysis")
    trust_levels_df = create_dataframe(trust_levels_sheet)
    participation_rates_df = create_dataframe(participation_rates_sheet)
    diversity_indices_df = create_dataframe(diversity_indices_sheet)
    health_and_safety_df = create_dataframe(health_and_safety_sheet)

    # Display data and analysis for each section
    if not trust_levels_df.empty:
        st.subheader("Trust Levels Data")
        st.write(trust_levels_df)
        st.subheader("Trust Levels Analysis")
        trust_levels_mean = trust_levels_df.mean()
        st.bar_chart(trust_levels_mean)
        fig, ax = plt.subplots()
        trust_levels_mean.plot(kind='bar', ax=ax)
        st.pyplot(fig)
        
    if not participation_rates_df.empty:
        st.subheader("Participation Rates Data")
        st.write(participation_rates_df)
        st.subheader("Participation Rates Analysis")
        participation_counts = participation_rates_df.apply(pd.value_counts).fillna(0)
        st.bar_chart(participation_counts)
        fig, ax = plt.subplots()
        participation_counts.plot(kind='bar', ax=ax)
        st.pyplot(fig)
        
    if not diversity_indices_df.empty:
        st.subheader("Diversity Indices Data")
        st.write(diversity_indices_df)
        st.subheader("Diversity Indices Analysis")
        diversity_counts = diversity_indices_df.apply(pd.value_counts).fillna(0)
        st.bar_chart(diversity_counts)
        fig, ax = plt.subplots()
        diversity_counts.plot(kind='bar', ax=ax)
        st.pyplot(fig)
        
    if not health_and_safety_df.empty:
        st.subheader("Health and Safety Data")
        st.write(health_and_safety_df)
        st.subheader("Health and Safety Analysis")
        health_safety_counts = health_and_safety_df.apply(pd.value_counts).fillna(0)
        st.bar_chart(health_safety_counts)
        fig, ax = plt.subplots()
        health_safety_counts.plot(kind='bar', ax=ax)
        st.pyplot(fig)

elif choice == "Download Data":
    st.header("Download Collected Data")
    trust_levels_df = create_dataframe(trust_levels_sheet)
    participation_rates_df = create_dataframe(participation_rates_sheet)
    diversity_indices_df = create_dataframe(diversity_indices_sheet)
    health_and_safety_df = create_dataframe(health_and_safety_sheet)
    
    all_data_df = pd.concat([trust_levels_df, participation_rates_df, diversity_indices_df, health_and_safety_df], keys=["Trust Levels", "Participation Rates", "Diversity Indices", "Health and Safety"])
    st.write(all_data_df)
    csv = all_data_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='moldova_for_peace_data.csv',
        mime='text/csv',
    )
