import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Define the scope
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Use a raw string literal or double backslashes for the file path
creds_path = r"C:\apptests\docstreamerAPI.json"

# Add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)

# Authorize the client
client = gspread.authorize(creds)

# Option 1: Open the Google Sheet by name (ensure this name matches exactly with your Google Sheet name)
sheet_name = "Your Google Sheet Name"  # Replace with your actual Google Sheet name

# Option 2: Open the Google Sheet by URL (extract the spreadsheet ID from the URL)
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1hkc5RA6sUC5f_pKMrpyc_uRKJz1VHNNSBXxUyd2NkOg/edit"  # Replace with your actual Google Sheet URL
spreadsheet_id = spreadsheet_url.split('/')[5]

try:
    # Try opening by name first
    sheet = client.open(sheet_name)
except gspread.SpreadsheetNotFound:
    try:
        # If not found by name, try by URL ID
        sheet = client.open_by_key(spreadsheet_id)
    except gspread.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' or ID '{spreadsheet_id}' not found. Please check the name or URL and ensure it is shared with the service account.")
        st.stop()

# Get the first sheet of the Spreadsheet
worksheet = sheet.get_worksheet(0)

def main():
    st.title("Circles of Influence Generator")

    st.write("""
    ## Instructions:
    Fill out the form below to generate your customized Circles of Influence. 
    Your inputs will help classify different aspects into Control, Influence, and Concern.
    """)

    # User Profile Section
    st.header("User Profile")
    org_type = st.selectbox("Select your organization type:", ["NGO", "Community Group", "Government Agency", "Business", "Individual"])
    location = st.text_input("Enter your location:")
    role = st.selectbox("Select your role within the organization:", ["Leader", "Member", "Advocate", "Volunteer"])

    # Issues and Goals Section
    st.header("Issues and Goals")
    primary_issue = st.text_input("What are the main issues you are addressing?")
    specific_challenges = st.text_area("Describe the specific challenges you are facing in your advocacy efforts.")
    goals = st.text_input("What are your primary goals for using this tool?")

    # Current Influence and Control Section
    st.header("Current Influence and Control")
    existing_influence = st.text_area("Who do you currently influence?")
    areas_of_control = st.text_area("What areas do you have direct control over?")

    # Stakeholders Section
    st.header("Stakeholders")
    key_stakeholders = st.text_area("Identify the key stakeholders involved in your issue.")
    stakeholder_influence = st.select_slider("How much influence do these stakeholders have on your issue?", options=["Low", "Medium", "High"])

    # Submit Button
    if st.button("Generate Circles of Influence"):
        user_data = {
            'org_type': org_type,
            'location': location,
            'role': role,
            'primary_issue': primary_issue,
            'specific_challenges': specific_challenges,
            'goals': goals,
            'existing_influence': existing_influence,
            'areas_of_control': areas_of_control,
            'key_stakeholders': key_stakeholders,
            'stakeholder_influence': stakeholder_influence
        }
        st.write("User Data Submitted:", user_data)
        
        # Save data to Google Sheets
        worksheet.append_row([
            org_type, location, role, primary_issue, specific_challenges, goals,
            existing_influence, areas_of_control, key_stakeholders, stakeholder_influence
        ])
        st.success("Data saved to Google Sheets successfully!")
        
        # Generate Circles of Influence
        circles = generate_circles_of_influence(user_data)
        st.subheader("Generated Circles of Influence")
        st.write("**Circle of Control:**", ", ".join(circles["Circle of Control"]))
        st.write("**Circle of Influence:**", ", ".join(circles["Circle of Influence"]))
        st.write("**Circle of Concern:**", ", ".join(circles["Circle of Concern"]))
        
        # Visualize Circles of Influence
        visualize_circles(circles)

def generate_circles_of_influence(user_data):
    # Define the logic to classify data into circles
    circle_of_control = []
    circle_of_influence = []
    circle_of_concern = []

    # Classify user data
    if user_data['areas_of_control']:
        circle_of_control.extend(user_data['areas_of_control'].split(', '))
    if user_data['existing_influence']:
        circle_of_influence.extend(user_data['existing_influence'].split(', '))
    if user_data['key_stakeholders']:
        if user_data['stakeholder_influence'] in ["Medium", "High"]:
            circle_of_influence.extend(user_data['key_stakeholders'].split(', '))
        else:
            circle_of_concern.extend(user_data['key_stakeholders'].split(', '))
    if user_data['primary_issue']:
        circle_of_concern.append(user_data['primary_issue'])
    if user_data['specific_challenges']:
        circle_of_concern.extend(user_data['specific_challenges'].split(', '))

    return {
        "Circle of Control": circle_of_control,
        "Circle of Influence": circle_of_influence,
        "Circle of Concern": circle_of_concern
    }

def visualize_circles(circles):
    fig, ax = plt.subplots()

    # Create a circle for each category
    control_circle = plt.Circle((0.5, 0.5), 0.1, color='green', alpha=0.5, label='Control')
    influence_circle = plt.Circle((0.5, 0.5), 0.3, color='yellow', alpha=0.5, label='Influence')
    concern_circle = plt.Circle((0.5, 0.5), 0.5, color='red', alpha=0.5, label='Concern')

    # Add circles to the plot
    ax.add_patch(control_circle)
    ax.add_patch(influence_circle)
    ax.add_patch(concern_circle)

    # Add text annotations
    ax.text(0.5, 0.5, '\n'.join(circles["Circle of Control"]), fontsize=12, ha='center', va='center', color='black')
    ax.text(0.5, 0.8, '\n'.join(circles["Circle of Influence"]), fontsize=10, ha='center', va='center', color='black')
    ax.text(0.5, 1.1, '\n'.join(circles["Circle of Concern"]), fontsize=8, ha='center', va='center', color='black')

    # Set limits and remove axes
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Add legend
    legend_handles = [
        mpatches.Patch(color='green', label='Circle of Control', alpha=0.5),
        mpatches.Patch(color='yellow', label='Circle of Influence', alpha=0.5),
        mpatches.Patch(color='red', label='Circle of Concern', alpha=0.5)
    ]
    ax.legend(handles=legend_handles, loc='upper right')

    st.pyplot(fig)

if __name__ == "__main__":
    main()
