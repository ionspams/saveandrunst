import os
import streamlit as st
import matplotlib.pyplot as plt
import random
import string
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Dictionary for multilingual text
texts = {
    "welcome": {
        "en": "Welcome to the Moldova for Peace Hub Entry-Stand",
        "ro": "Bun venit la Standul de Intrare Moldova pentru Pace",
        "uk": "Ласкаво просимо до стенду входу Молдова за мир",
        "ru": "Добро пожаловать на стенд входа Молдова за мир"
    },
    "select_language": {
        "en": "Please select your language to continue:",
    },
    # ... (rest of the text dictionary)
}

# Define service locations on the map
service_locations = {
    "Assistance Desk": (50, 50),
    "Reception": (10, 10),
    "Event Hall": (30, 30),
    "Workshop Room": (70, 70),
    "Service Office": (90, 90),
    "Service Desk": (80, 80),
    "Assistance Office": (60, 60)
}

# Mapping visit purposes to service locations
purpose_to_location = {
    "Receive Assistance": "Assistance Desk",
    "Just Visit": "Reception",
    "Attend an Event": "Event Hall",
    "Attend a Workshop or Focus Group": "Workshop Room",
    "Offer a Regular Service": "Service Office",
    "Offer a Single Occurrence Service": "Service Desk",
    "Provide Assistance": "Assistance Office"
}

# Short descriptions for each type of service
service_descriptions = {
    "Assistance Desk": "Provides general assistance and guidance for various needs.",
    "Reception": "General information and directions for visitors.",
    "Event Hall": "Location for attending events and large gatherings.",
    "Workshop Room": "Space for attending workshops and focus group meetings.",
    "Service Office": "Office for regular service offerings and consultations.",
    "Service Desk": "Desk for one-time service offerings.",
    "Assistance Office": "Office for providing specialized assistance."
}

# Define session state for inactivity
if 'last_interaction' not in st.session_state:
    st.session_state['last_interaction'] = time.time()

# Initialize Google Sheets
def initialize_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scope)
    client = gspread.authorize(creds)
    sheet_id = os.getenv('GOOGLE_SHEETS_ID')
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

def save_to_google_sheet(data):
    sheet = initialize_google_sheet()
    sheet.append_row(data)

def main():
    st.set_page_config(page_title="Moldova for Peace Entry-Stand", layout="centered")
    
    # Reset session state if inactive for 30 seconds
    if time.time() - st.session_state['last_interaction'] > 30:
        st.session_state.clear()
        st.session_state['last_interaction'] = time.time()

    # Update last interaction time
    st.session_state['last_interaction'] = time.time()

    # Language selection page
    st.title("Moldova for Peace Hub Entry-Stand")
    st.markdown(f"<b>{texts['select_language']['en']}</b>", unsafe_allow_html=True)
    
    # Language selection as a single radio button group
    language = st.radio(
        "",
        ["English", "Română", "Українська", "Русский"],
        horizontal=True,
        index=0
    )
    
    lang_code = get_language_code(language)
    st.session_state['lang_code'] = lang_code

    # Display welcome message
    st.header(texts["welcome"][lang_code])

    # Select visitor type
    visitor_type = st.radio(
        texts["visitor_type"][lang_code],
        [texts["individual"][lang_code], texts["organization"][lang_code]],
        horizontal=True,
        index=0
    )

    if visitor_type == texts["individual"][lang_code]:
        visit_purposes = handle_individual_workflow(lang_code)
    else:
        visit_purposes = handle_organization_workflow(lang_code)

    # Display map and short description as soon as a purpose is selected
    if visit_purposes:
        destinations = [purpose_to_location[purpose] for purpose in visit_purposes]
        for purpose in visit_purposes:
            destination = purpose_to_location[purpose]
            st.write(f"**{destination}**: {service_descriptions[destination]}")
        display_map(destinations)

        # Options to generate and print ticket or generate digital ticket
        col1, col2 = st.columns(2)
        if col1.button(texts["generate_print_ticket"][lang_code]):
            ticket = generate_ticket(visitor_type, visit_purposes, lang_code)
            st.markdown(f"<h1 style='font-size:72px;'>{ticket['ticket_id']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2>{ticket['details']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h2>{texts['thank_you'][lang_code]}</h2>", unsafe_allow_html=True)
            # Save ticket to Google Sheets
            save_to_google_sheet([ticket['ticket_id'], visitor_type, ticket['destination'], time.strftime("%Y-%m-%d %H:%M:%S")])

        if col2.button(texts["generate_digital_ticket"][lang_code]):
            ticket = generate_ticket(visitor_type, visit_purposes, lang_code)
            st.markdown(f"<h1 style='font-size:72px;'>{ticket['ticket_id']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2>{ticket['details']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h2>{texts['thank_you'][lang_code]}</h2>", unsafe_allow_html=True)
            # Save ticket to Google Sheets
            save_to_google_sheet([ticket['ticket_id'], visitor_type, ticket['destination'], time.strftime("%Y-%m-%d %H:%M:%S")])
            # Logic to send ticket to Dopamoha (not implemented in this example)

def handle_individual_workflow(lang_code):
    st.subheader(texts["do_you_have_account"][lang_code])
    has_account = st.radio("", [texts["yes"][lang_code], texts["no"][lang_code]], index=0)

    if has_account == texts["yes"][lang_code]:
        phone_number = st.text_input(texts["phone_number"][lang_code])
        if len(phone_number) >= 9:
            visitor_names = st.multiselect(
                texts["choose_names"][lang_code],
                ["Андрій", "Марія", "Олександр", "Іван", "Катерина"]  # Example names in Russian
            )
    else:
        visitor_name = st.text_input(texts["provide_name"][lang_code])
        num_visitors = st.number_input(texts["number_of_visitors"][lang_code], min_value=1, max_value=10)
    
    # Select visit purpose(s)
    visit_purposes = st.multiselect(
        texts["visit_purpose"][lang_code],
        [
            texts["receive_assistance"][lang_code],
            texts["just_visit"][lang_code],
            texts["attend_event"][lang_code],
            texts["attend_workshop"][lang_code]
        ]
    )
    return visit_purposes

def handle_organization_workflow(lang_code):
    org_name = st.selectbox(
        texts["select_organization"][lang_code],
        ["Select your organization", "Org1", "Org2", "Org3", "Org4", "Org5"],
        index=0
    )
    position = st.selectbox(
        texts["select_position"][lang_code],
        [
            "Select your position",
            texts["project_manager"][lang_code],
            texts["country_director"][lang_code],
            texts["monitoring_officer"][lang_code],
            texts["audit_officer"][lang_code],
            texts["data_enumerator"][lang_code]
        ],
        index=0
    )
    contact_name = st.text_input(texts["provide_name"][lang_code])

    # Select visit purpose(s)
    visit_purposes = st.multiselect(
        texts["visit_purpose"][lang_code],
        [
            texts["offer_regular_service"][lang_code],
            texts["offer_single_service"][lang_code],
            texts["provide_assistance"][lang_code],
            texts["just_visit"][lang_code]
        ]
    )
    return visit_purposes

def generate_ticket(visitor_type, visit_purposes, lang_code):
    # Generate ticket ID
    ticket_id = generate_ticket_id(visitor_type[0].upper())
    destination = random.choice(visit_purposes) if visit_purposes else "Reception"  # Select one of the purposes as destination
    destination_location = purpose_to_location[destination]
    ticket_details = (
        f"{texts['visitor_type_label'][lang_code]} {visitor_type}\n"
        f"{texts['visit_type_label'][lang_code]} {ticket_id}\n"
        f"{texts['destination_label'][lang_code]} {destination_location}"
    )
    return {
        "ticket_id": ticket_id,
        "destination": destination_location,
        "details": ticket_details
    }

def generate_ticket_id(prefix):
    random_digits = ''.join(random.choices(string.digits, k=3))
    ticket_id = f"{prefix}{random_digits}"
    return ticket_id

def get_language_code(language):
    language_codes = {
        "English": "en",
        "Română": "ro",
        "Українська": "uk",
        "Русский": "ru"
    }
    return language_codes.get(language, "en")

def display_map(destinations):
    fig, ax = plt.subplots()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_title('Service Locations')
    for destination in destinations:
        if destination in service_locations:
            ax.plot(*service_locations[destination], 'ro')  # Mark the destination with a red dot
            ax.text(*service_locations[destination], destination, fontsize=12, ha='right')
    st.pyplot(fig)

if __name__ == "__main__":
    main()
