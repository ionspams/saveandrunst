import streamlit as st
import matplotlib.pyplot as plt
import random
import string
import datetime
import time
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import json

# Set page config as the first Streamlit command
st.set_page_config(page_title="Moldova for Peace Entry-Stand", layout="centered")

# Load environment variables
load_dotenv('C:\\apptests\\docstreamerAPI\\.env')

# Set up Google Sheets API
scopes = ['https://www.googleapis.com/auth/spreadsheets']
json_creds = os.getenv("GOOGLE_SHEETS_CREDS")
sheet_name = os.getenv("GOOGLE_SHEET_NAME")
sheet = None  # Initialize sheet as None

if json_creds:
    try:
        creds = Credentials.from_service_account_info(json.loads(json_creds), scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = '1GzYxPHNLV3Hn0HYF6irSk5jvT3jyzIdAtHjNGC0bIgc'
        if sheet_name:
            sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
        else:
            sheet = client.open_by_key(sheet_id).sheet1
    except json.JSONDecodeError:
        st.error("Failed to decode JSON credentials. Please check the format of the JSON string.")
else:
    st.error("Google Sheets credentials not found in environment variables.")

# Dictionary for multilingual text
texts = {
    "welcome": {
        "en": "Welcome to the Moldova for Peace Hub",
        "ro": "Bun venit la Moldova pentru Pace",
        "uk": "Ласкаво просимо до Молдова за мир",
        "ru": "Добро пожаловать y Молдова за мир"
    },
    "select_language": {
        "en": "Please select your language to continue:",
    },
    "visitor_type": {
        "en": "Are you an individual or representing an organization?",
        "ro": "Sunteți o persoană fizică sau reprezentați o organizație?",
        "uk": "Ви фізична особа чи представляєте організацію?",
        "ru": "Вы физическое лицо или представляете организацию?"
    },
    "individual": {
        "en": "Individual",
        "ro": "Persoană fizică",
        "uk": "Фізична особа",
        "ru": "Физическое лицо"
    },
    "organization": {
        "en": "Organization",
        "ro": "Organizație",
        "uk": "Організація",
        "ru": "Организация"
    },
    "do_you_have_account": {
        "en": "Do you or your family members have an account with Dopomoha?",
        "ro": "Aveți dvs. sau membrii familiei dvs. un cont pe Dopomoha?",
        "uk": "Чи є у вас або членів вашої родини обліковий запис на Dopomoha?",
        "ru": "Есть ли у вас или членов вашей семьи учетная запись на Dopomoha?"
    },
    "yes": {
        "en": "Yes",
        "ro": "Da",
        "uk": "Так",
        "ru": "Да"
    },
    "no": {
        "en": "No",
        "ro": "Nu",
        "uk": "Ні",
        "ru": "Нет"
    },
    "phone_number": {
        "en": "Enter your phone number:",
        "ro": "Introduceți numărul dvs. de telefon:",
        "uk": "Введіть свій номер телефону:",
        "ru": "Введите свой номер телефона:"
    },
    "choose_names": {
        "en": "Select the names of the visitors:",
        "ro": "Selectați numele vizitatorilor:",
        "uk": "Виберіть імена відвідувачів:",
        "ru": "Выберите имена посетителей:"
    },
    "number_of_visitors": {
        "en": "Number of visitors:",
        "ro": "Numărul de vizitatori:",
        "uk": "Кількість відвідувачів:",
        "ru": "Количество посетителей:"
    },
    "provide_name": {
        "en": "Enter your name:",
        "ro": "Introduceți numele dvs.:",
        "uk": "Введіть своє ім'я:",
        "ru": "Введите свое имя:"
    },
    "select_organization": {
        "en": "Select your organization:",
        "ro": "Selectați organizația dvs.:",
        "uk": "Виберіть свою організацію:",
        "ru": "Выберите вашу организацию:"
    },
    "select_position": {
        "en": "Select your position:",
        "ro": "Selectați poziția dvs.:",
        "uk": "Виберіть свою позицію:",
        "ru": "Выберите свою позицию:"
    },
    "project_manager": {
        "en": "Project Manager",
        "ro": "Manager de Proiect",
        "uk": "Менеджер проекту",
        "ru": "Менеджер проекта"
    },
    "country_director": {
        "en": "Country Director",
        "ro": "Director de Țară",
        "uk": "Директор країни",
        "ru": "Директор страны"
    },
    "monitoring_officer": {
        "en": "Monitoring Officer",
        "ro": "Ofițer de Monitorizare",
        "uk": "Офіцер моніторингу",
        "ru": "Офицер мониторинга"
    },
    "audit_officer": {
        "en": "Audit Officer",
        "ro": "Ofițer de Audit",
        "uk": "Аудитор",
        "ru": "Аудитор"
    },
    "data_enumerator": {
        "en": "Data Enumerator",
        "ro": "Enumărător de Date",
        "uk": "Оператор даних",
        "ru": "Оператор данных"
    },
    "visit_purpose": {
        "en": "Please select your purpose(s) of visit:",
        "ro": "Vă rugăm să selectați scopul/scopurile vizitei dvs.:",
        "uk": "Будь ласка, виберіть мету/мети вашого візиту:",
        "ru": "Пожалуйста, выберите цель/цели вашего визита:"
    },
    "receive_assistance": {
        "en": "Receive Assistance",
        "ro": "Primirea Asistenței",
        "uk": "Отримання допомоги",
        "ru": "Получить помощь"
    },
    "just_visit": {
        "en": "Just Visit",
        "ro": "Doar Vizita",
        "uk": "Просто відвідати",
        "ru": "Просто посетить"
    },
    "attend_event": {
        "en": "Attend an Event",
        "ro": "Participați la un Eveniment",
        "uk": "Відвідати захід",
        "ru": "Посетить мероприятие"
    },
    "attend_workshop": {
        "en": "Attend a Workshop or Focus Group",
        "ro": "Participați la un Atelier sau Grup de Lucru",
        "uk": "Відвідати семінар або фокус-групу",
        "ru": "Посетить мастер-класс или фокус-группу"
    },
    "offer_regular_service": {
        "en": "Offer a Regular Service",
        "ro": "Oferiți un Serviciu Regular",
        "uk": "Пропонувати регулярну послугу",
        "ru": "Предложить регулярную услугу"
    },
    "offer_single_service": {
        "en": "Offer a Single Occurrence Service",
        "ro": "Oferiți un Serviciu Unic",
        "uk": "Пропонувати одноразову послугу",
        "ru": "Предложить разовую услугу"
    },
    "provide_assistance": {
        "en": "Provide Assistance",
        "ro": "Oferiți Asistență",
        "uk": "Надати допомогу",
        "ru": "Оказать помощь"
    },
    "generate_ticket": {
        "en": "Generate Ticket",
        "ro": "Generați Bilet",
        "uk": "Згенерувати квиток",
        "ru": "Создать билет"
    },
    "generate_digital_ticket": {
        "en": "Generate Digital Ticket",
        "ro": "Generați Bilet Digital",
        "uk": "Згенерувати цифровий квиток",
        "ru": "Создать цифровой билет"
    },
    "generate_print_ticket": {
        "en": "Generate and Print Ticket",
        "ro": "Generați și Imprimați Bilet",
        "uk": "Згенерувати і роздрукувати квиток",
        "ru": "Создать и распечатать билет"
    },
    "ticket": {
        "en": "Ticket",
        "ro": "Bilet",
        "uk": "Квиток",
        "ru": "Билет"
    },
    "visitor_type_label": {
        "en": "Visitor Type:",
        "ro": "Tip de Vizitator:",
        "uk": "Тип відвідувача:",
        "ru": "Тип посетителя:"
    },
    "visit_type_label": {
        "en": "Visit Type:",
        "ro": "Tip de Vizită:",
        "uk": "Тип візиту:",
        "ru": "Тип визита:"
    },
    "destination_label": {
        "en": "Destination:",
        "ro": "Destinație:",
        "uk": "Призначення:",
        "ru": "Назначение:"
    },
    "thank_you": {
        "en": "Thank you! Have a splendid time at the Hub!",
        "ro": "Mulțumim! Să aveți un timp splendid la Hub!",
        "uk": "Дякуємо! Бажаємо вам чудового часу в Хабі!",
        "ru": "Спасибо! Желаем вам замечательного времени в Хабе!"
    }
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

def main():
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
        translated_purposes = translate_purposes(visit_purposes, lang_code)
        destinations = [purpose_to_location[purpose] for purpose in translated_purposes]
        for purpose in translated_purposes:
            destination = purpose_to_location[purpose]
            st.write(f"**{destination}**: {service_descriptions[destination]}")
        display_map(destinations)

        # Options to generate and print ticket or generate digital ticket
        col1, col2 = st.columns(2)
        if col1.button(texts["generate_print_ticket"][lang_code]):
            ticket = generate_ticket(visitor_type, translated_purposes, lang_code)
            st.markdown(f"<h1 style='font-size:72px;'>{ticket['ticket_id']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2>{ticket['details']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h2>{texts['thank_you'][lang_code]}</h2>", unsafe_allow_html=True)
            save_to_google_sheets(ticket)

        if col2.button(texts["generate_digital_ticket"][lang_code]):
            ticket = generate_ticket(visitor_type, translated_purposes, lang_code)
            st.markdown(f"<h1 style='font-size:72px;'>{ticket['ticket_id']}</h1>", unsafe_allow_html=True)
            st.markdown(f"<h2>{ticket['details']}</h2>", unsafe_allow_html=True)
            st.markdown(f"<h2>{texts['thank_you'][lang_code]}</h2>", unsafe_allow_html=True)
            save_to_google_sheets(ticket)

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

def translate_purposes(purposes, lang_code):
    # Translate visit purposes to English for lookup in purpose_to_location
    translation_map = {
        "Receive Assistance": texts["receive_assistance"],
        "Just Visit": texts["just_visit"],
        "Attend an Event": texts["attend_event"],
        "Attend a Workshop or Focus Group": texts["attend_workshop"],
        "Offer a Regular Service": texts["offer_regular_service"],
        "Offer a Single Occurrence Service": texts["offer_single_service"],
        "Provide Assistance": texts["provide_assistance"]
    }
    return [key for key, value in translation_map.items() if value[lang_code] in purposes]

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

def save_to_google_sheets(ticket):
    global sheet
    if sheet:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, ticket['ticket_id'], ticket['destination'], ticket['details']])

if __name__ == "__main__":
    main()
