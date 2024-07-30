import streamlit as st
import pandas as pd

# URL to the public Google Sheet CSV export
csv_url = 'https://docs.google.com/spreadsheets/d/1HyfnLpZHn07WjKqxqp1jbPFJxj-UV-KLF93WO0xIlx4/export?format=csv'

# Function to save data to Google Sheets
def save_to_gsheet(data):
    # Append data to the public Google Sheet using pandas
    df = pd.read_csv(csv_url)
    new_df = pd.DataFrame([data], columns=df.columns)
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv('google_sheet.csv', index=False)  # Save locally (for demo purposes, normally you would upload this)

# Page configuration
st.set_page_config(page_title="Vulnerability Assessment Framework - Moldova", layout="wide")

# Title
st.title("Vulnerability Assessment Framework (VAF) - Moldova")

# Description
st.write("""
This application replicates the Vulnerability Assessment Framework (VAF) used in Jordan, 
adapted for the refugee situation in Moldova caused by the Russian aggression in Ukraine. 
The tool aims to facilitate better targeting of humanitarian assistance.
""")

# General Information Section
st.header("General Information")
interviewer_name = st.text_input("Name of Interviewer/Organization")
interview_date = st.date_input("Interview Date")
questionnaire_code = st.text_input("Questionnaire Code")
governorate_code = st.text_input("Governorate/Code")
district_code = st.text_input("District/Code")
town_village_code = st.text_input("Town/Village/Code")
gps_code = st.text_input("GPS Code")
assessment_type = st.selectbox("Type of Assessment", ["New Assessment", "Reassessment"])

# Household Information Section
st.header("Household Information")
unhcr_file_number = st.text_input("UNHCR File Number")
related_unhcr_file_number = st.text_input("Related UNHCR File Number within the same residence")
respondent_name = st.text_input("Name of Respondent")
identification_document_number = st.text_input("Identification Document Number & Type")
respondent_gender = st.selectbox("Gender of Respondent", ["Male", "Female"])
respondent_dob = st.date_input("Date of Birth of Respondent")
head_of_household_gender = st.selectbox("Gender of the Registered Head of Household", ["Male", "Female"])

# Household Demographics
st.header("Household Demographics")
household_size = st.number_input("Number of Household Members", min_value=1, step=1)
household_data = []

for i in range(household_size):
    st.subheader(f"Member {i+1}")
    name = st.text_input(f"Name of Member {i+1}", key=f"name_{i}")
    age = st.number_input(f"Age of Member {i+1}", min_value=0, key=f"age_{i}")
    gender = st.selectbox(f"Gender of Member {i+1}", ["Male", "Female", "Other"], key=f"gender_{i}")
    relation = st.text_input(f"Relation to Head of Household for Member {i+1}", key=f"relation_{i}")
    household_data.append([name, age, gender, relation])

# Protection Indicators Section
st.header("Protection Indicators")
legal_status = st.selectbox("Legal Status", ["Registered", "Unregistered"])
protection_concerns = st.text_area("Describe any protection concerns")

# Health Indicators Section
st.header("Health Indicators")
health_issues = st.text_area("List any health issues in the household")
access_to_health_services = st.selectbox("Access to Health Services", ["Yes", "No"])

# Education Indicators Section
st.header("Education Indicators")
education_status = st.text_area("Describe the education status of household members")

# Livelihood Indicators Section
st.header("Livelihood Indicators")
employment_status = st.selectbox("Employment Status", ["Employed", "Unemployed", "Informally Employed"])
sources_of_income = st.text_area("List sources of income")

# Shelter Indicators Section
st.header("Shelter Indicators")
housing_conditions = st.text_area("Describe housing conditions")
access_to_utilities = st.multiselect("Access to Utilities", ["Water", "Electricity", "Sanitation"])

# Food Security Indicators Section
st.header("Food Security Indicators")
food_access = st.text_area("Describe access to food")
nutrition_status = st.text_area("Describe nutritional status")

# Collect all data
all_data = [
    interviewer_name,
    interview_date,
    questionnaire_code,
    governorate_code,
    district_code,
    town_village_code,
    gps_code,
    assessment_type,
    unhcr_file_number,
    related_unhcr_file_number,
    respondent_name,
    identification_document_number,
    respondent_gender,
    respondent_dob,
    head_of_household_gender,
    household_size,
    legal_status,
    protection_concerns,
    health_issues,
    access_to_health_services,
    education_status,
    employment_status,
    sources_of_income,
    housing_conditions,
    access_to_utilities,
    food_access,
    nutrition_status
] + [item for sublist in household_data for item in sublist]

# Submit button
if st.button("Submit"):
    save_to_gsheet(all_data)
    st.success("Data submitted successfully!")

# Data Analysis and Reporting
st.header("Data Analysis and Reporting")
data = pd.read_csv(csv_url)
df = pd.DataFrame(data)
st.write(df)

# Basic statistics
st.subheader("Basic Statistics")
st.write(df.describe())

# Data Visualization
st.subheader("Data Visualization")
st.bar_chart(df['Age'])
