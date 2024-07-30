import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Set page configuration
st.set_page_config(layout="wide")
st.title("Link Collector")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(r'C:\apptests\docstreamerAPI.json', scope)
client = gspread.authorize(creds)

# Use the correct Google Sheets ID
sheet = client.open_by_key('1hkc5RA6sUC5f_pKMrpyc_uRKJz1VHNNSBXxUyd2NkOg').sheet1

# Load data from Google Sheets
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Print the DataFrame structure to check for column names and contents
st.write("DataFrame structure:")
st.write(df)

# Ensure columns are correctly named and parsed
expected_columns = ['Category', 'Title', 'Link']
if not all(column in df.columns for column in expected_columns):
    st.error("The expected columns 'Category', 'Title', and 'Link' are not found in the Google Sheet. "
             "Please ensure the Google Sheet has these columns.")

# Function to add a new link
def add_link(link, title, category):
    sheet.append_row([link, title, category])
    st.experimental_rerun()

# Display the form to add a new link in the center column
with st.form(key='add_link_form', clear_on_submit=True):
    link_input = st.text_input("Enter link or content")
    title_input = st.text_input("Enter title or short description")
    category_input = st.selectbox("Select category", ["For Development", "Useful Information", "Tools", "Tasks", "Ideas & Proposals", "Courses", "News Reel", "Any Other"])
    submit_button = st.form_submit_button(label='Add Link')

    if submit_button and link_input and title_input:
        add_link(link_input, title_input, category_input)

# Create a dictionary of categories and their respective containers
categories = {
    "For Development": [],
    "Useful Information": [],
    "Tools": [],
    "Tasks": [],
    "Ideas & Proposals": [],
    "Courses": [],
    "News Reel": [],
    "Any Other": []
}

# Populate categories with the data from Google Sheets
for index, row in df.iterrows():
    if 'Category' in row and 'Title' in row and 'Link' in row:
        category = row['Category']
        title = row['Title']
        link = row['Link']
        if category in categories:
            categories[category].append((title, link))
        else:
            st.error(f"Invalid category '{category}' found in the data.")
    else:
        st.error(f"Row {index} is missing one of the required fields: {row}")

# Function to create an expandable container
def create_expandable_container(category, items):
    with st.expander(category):
        for title, link in items:
            st.write(f"**{title}**")
            st.write(link)

# Create the layout with 5 columns and the input form in the center
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    create_expandable_container("For Development", categories["For Development"])
    create_expandable_container("Courses", categories["Courses"])

with col2:
    create_expandable_container("Useful Information", categories["Useful Information"])
    create_expandable_container("News Reel", categories["News Reel"])

with col3:
    create_expandable_container("Tools", categories["Tools"])

with col4:
    create_expandable_container("Tasks", categories["Tasks"])
    create_expandable_container("Any Other", categories["Any Other"])

with col5:
    create_expandable_container("Ideas & Proposals", categories["Ideas & Proposals"])
