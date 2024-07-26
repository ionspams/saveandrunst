import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from datetime import datetime, timedelta
import pandas as pd
import json
import uuid
import io
import logging
import random
from num2words import num2words

# Set page config and logging
st.set_page_config(page_title="Document Management System", layout="wide")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load service account credentials and initialize gspread client
SERVICE_ACCOUNT_FILE = 'C:\apptests\1\docstreamerAPI.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# Open required spreadsheets
SPREADSHEET_ID = '1dCGuJDk4sYZcqxZ-7nvg3R09IjecoEV_1nMRuehDfwo'
SPREADSHEET_ID_2 = '1GzYxPHNLV3Hn0HYF6irSk5jvT3jyzIdAtHjNGC0bIgc'
spreadsheet_id_3 = '1iSlsgQrc0-RQ1gFSmyhmXE6x2TKrHgiKRDSDuoX3mEY'

# Open specific worksheets
employees_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Employees')
shifts_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Shifts')
guests_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Guests')
tender_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Tenders')
bidders_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Bidders')
review_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Review')

def main():
    st.sidebar.title("Document Management System")
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None

    if st.session_state.user_info:
        st.write(f"Welcome, {st.session_state.user_info['name']}!")
        if st.sidebar.button("Logout"):
            st.session_state.user_info = None
            st.experimental_rerun()
    else:
        st.write("Please log in to access the system.")
        if st.sidebar.button("Login"):
            # Implement your login logic here
            st.session_state.user_info = {"name": "Test User"}
            st.experimental_rerun()
    
    if st.session_state.user_info:
        menu = ["Document Generation", "Input Data", "Purchases", "People Management"]
        choice = st.sidebar.selectbox("Main Menu", menu)
        
        if choice == "Document Generation":
            document_generation()
        elif choice == "Input Data":
            input_data()
        elif choice == "Purchases":
            purchases()
        elif choice == "People Management":
            people_management()

def document_generation():
    st.title("Document Generation")
    
    uploaded_file = st.file_uploader("Upload your service account JSON file", type="json")
    
    if uploaded_file is not None:
        service_account_info = json.load(uploaded_file)
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        
        sheets_service = build('sheets', 'v4', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        department = st.selectbox("Select Department", get_departments(sheets_service))
        
        if department:
            templates = get_templates(sheets_service, department)
            selected_template = st.selectbox("Select Template", templates)
            
            if selected_template:
                template_data = get_template_data(sheets_service, department, selected_template)
                
                if template_data:
                    st.write("Template Data:")
                    st.write(template_data)
                    
                    selected_rows = st.multiselect("Select rows to generate documents", range(1, len(template_data) + 1))
                    
                    if st.button("Generate Documents"):
                        generated_docs = generate_documents(docs_service, drive_service, department, selected_template, template_data, selected_rows)
                        
                        if generated_docs:
                            st.success("Documents generated successfully!")
                            for doc in generated_docs:
                                st.markdown(f"[{doc['name']}]({doc['url']})")
                        else:
                            st.error("Failed to generate documents. Please try again.")

def get_departments(sheets_service):
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='doc_mappings!A2:B').execute()
    values = result.get('values', [])
    return [row[0] for row in values if len(row) > 0]

def get_templates(sheets_service, department):
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='doc_mappings!A2:B').execute()
    values = result.get('values', [])
    department_mapping = {row[0]: row[1] for row in values if len(row) > 1}
    
    if department in department_mapping:
        spreadsheet_id = department_mapping[department]
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]
    return []

def get_template_data(sheets_service, department, sheet_name):
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='doc_mappings!A2:B').execute()
    values = result.get('values', [])
    department_mapping = {row[0]: row[1] for row in values if len(row) > 1}
    
    if department in department_mapping:
        spreadsheet_id = department_mapping[department]
        result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
        values = result.get('values', [])
        if len(values) > 1:
            headers = values[0]
            return [dict(zip(headers, row)) for row in values[1:]]
    return []

def generate_documents(docs_service, drive_service, department, sheet_name, template_data, selected_rows):
    generated_docs = []
    
    result = docs_service.documents().get(documentId=SPREADSHEET_ID_2).execute()
    template_mappings = {item['key']: item['value'] for item in result.get('headers', []) if 'key' in item and 'value' in item}
    
    if sheet_name in template_mappings:
        template_id = template_mappings[sheet_name]
        
        for row_number in selected_rows:
            row_data = template_data[row_number - 1]
            new_document = copy_template(docs_service, drive_service, template_id, f"{row_number}_{sheet_name}")
            
            if new_document:
                replace_placeholders(docs_service, new_document['id'], row_data)
                generated_docs.append({
                    'name': new_document['name'],
                    'url': f"https://docs.google.com/document/d/{new_document['id']}/edit"
                })
    
    return generated_docs

def copy_template(docs_service, drive_service, template_id, document_name):
    try:
        copied_file = {'name': document_name}
        new_doc = drive_service.files().copy(fileId=template_id, body=copied_file).execute()
        return new_doc
    except Exception as e:
        st.error(f"Error copying template: {e}")
        return None

def replace_placeholders(docs_service, document_id, data):
    requests = []
    for key, value in data.items():
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': '{{' + key + '}}',
                    'matchCase': True,
                },
                'replaceText': str(value),
            }
        })
    
    if requests:
        try:
            docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        except Exception as e:
            st.error(f"Error replacing placeholders: {e}")

def input_data():
    st.title("Input Data")
    st.write("This feature is not yet implemented.")
    # Implement your data input logic heredef document_generation():
    st.title("Document Generation")
    
    uploaded_file = st.file_uploader("Upload your service account JSON file", type="json")
    
    if uploaded_file is not None:
        service_account_info = json.load(uploaded_file)
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        
        sheets_service = build('sheets', 'v4', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        department = st.selectbox("Select Department", get_departments(sheets_service))
        
        if department:
            templates = get_templates(sheets_service, department)
            selected_template = st.selectbox("Select Template", templates)
            
            if selected_template:
                template_data = get_template_data(sheets_service, department, selected_template)
                
                if template_data:
                    st.write("Template Data:")
                    st.write(template_data)
                    
                    selected_rows = st.multiselect("Select rows to generate documents", range(1, len(template_data) + 1))
                    
                    if st.button("Generate Documents"):
                        generated_docs = generate_documents(docs_service, drive_service, department, selected_template, template_data, selected_rows)
                        
                        if generated_docs:
                            st.success("Documents generated successfully!")
                            for doc in generated_docs:
                                st.markdown(f"[{doc['name']}]({doc['url']})")
                        else:
                            st.error("Failed to generate documents. Please try again.")

def get_departments(sheets_service):
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='doc_mappings!A2:B').execute()
    values = result.get('values', [])
    return [row[0] for row in values if len(row) > 0]

def get_templates(sheets_service, department):
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='doc_mappings!A2:B').execute()
    values = result.get('values', [])
    department_mapping = {row[0]: row[1] for row in values if len(row) > 1}
    
    if department in department_mapping:
        spreadsheet_id = department_mapping[department]
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]
    return []

def get_template_data(sheets_service, department, sheet_name):
    result = sheets_service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='doc_mappings!A2:B').execute()
    values = result.get('values', [])
    department_mapping = {row[0]: row[1] for row in values if len(row) > 1}
    
    if department in department_mapping:
        spreadsheet_id = department_mapping[department]
        result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
        values = result.get('values', [])
        if len(values) > 1:
            headers = values[0]
            return [dict(zip(headers, row)) for row in values[1:]]
    return []

def generate_documents(docs_service, drive_service, department, sheet_name, template_data, selected_rows):
    generated_docs = []
    
    result = docs_service.documents().get(documentId=SPREADSHEET_ID_2).execute()
    template_mappings = {item['key']: item['value'] for item in result.get('headers', []) if 'key' in item and 'value' in item}
    
    if sheet_name in template_mappings:
        template_id = template_mappings[sheet_name]
        
        for row_number in selected_rows:
            row_data = template_data[row_number - 1]
            new_document = copy_template(docs_service, drive_service, template_id, f"{row_number}_{sheet_name}")
            
            if new_document:
                replace_placeholders(docs_service, new_document['id'], row_data)
                generated_docs.append({
                    'name': new_document['name'],
                    'url': f"https://docs.google.com/document/d/{new_document['id']}/edit"
                })
    
    return generated_docs

def copy_template(docs_service, drive_service, template_id, document_name):
    try:
        copied_file = {'name': document_name}
        new_doc = drive_service.files().copy(fileId=template_id, body=copied_file).execute()
        return new_doc
    except Exception as e:
        st.error(f"Error copying template: {e}")
        return None

def replace_placeholders(docs_service, document_id, data):
    requests = []
    for key, value in data.items():
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': '{{' + key + '}}',
                    'matchCase': True,
                },
                'replaceText': str(value),
            }
        })
    
    if requests:
        try:
            docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        except Exception as e:
            st.error(f"Error replacing placeholders: {e}")

def input_data():
    st.title("Input Data")
    st.write("This feature is not yet implemented.")
    # Implement your data input logic here

def purchases():
    st.title("Purchases")
    
    options = ["Create Tender", "View Tenders", "Submit Bid", "Evaluate Bids"]
    selection = st.selectbox("Select a task", options)

    if selection == "Create Tender":
        create_tender()
    elif selection == "View Tenders":
        view_tenders()
    elif selection == "Submit Bid":
        submit_bid()
    elif selection == "Evaluate Bids":
        evaluate_bids()

def create_tender():
    st.subheader("Create Tender")
    
    with st.form("tender_form"):
        tender_description = st.text_area("Tender Description")
        tender_deadline = st.date_input("Tender Deadline")
        tpo_contact = st.text_input("TPO Contact Details")
        
        num_lots = st.number_input("Number of Lots", min_value=1, value=1)
        
        lots = []
        for i in range(num_lots):
            st.subheader(f"Lot {i+1}")
            lot_name = st.text_input(f"Lot {i+1} Name")
            num_products = st.number_input(f"Number of Products in Lot {i+1}", min_value=1, value=1)
            
            products = []
            for j in range(num_products):
                st.subheader(f"Product {j+1}")
                product_name = st.text_input(f"Product {j+1} Name")
                product_description = st.text_area(f"Product {j+1} Description")
                product_requirements = st.text_area(f"Product {j+1} Requirements")
                product_quantity = st.number_input(f"Product {j+1} Quantity", min_value=1, value=1)
                product_price = st.number_input(f"Product {j+1} Price (MDL)", min_value=0.0, value=0.0)
                
                products.append({
                    'name': product_name,
                    'description': product_description,
                    'requirements': product_requirements,
                    'quantity': product_quantity,
                    'price': product_price,
                    'total': product_quantity * product_price
                })
            
            lots.append({
                'name': lot_name,
                'products': products
            })
        
        if st.form_submit_button("Create Tender"):
            tender_id = str(uuid.uuid4())
            tender_data = {
                'tender_id': tender_id,
                'tender_description': tender_description,
                'tender_deadline': tender_deadline.strftime('%Y-%m-%d'),
                'tpo_contact': tpo_contact,
                'lots': lots
            }
            save_tender(tender_data)
            st.success(f"Tender created successfully. Tender ID: {tender_id}")

def save_tender(tender_data):
    flat_data = flatten_tender_data(tender_data)
    tender_sheet.append_row(flat_data)

def flatten_tender_data(data):
    flat_data = [
        data['tender_id'],
        data['tender_description'],
        data['tender_deadline'],
        data['tpo_contact'],
        len(data['lots'])
    ]
    
    for lot in data['lots']:
        flat_data.extend([
            lot['name'],
            len(lot['products'])
        ])
        for product in lot['products']:
            flat_data.extend([
                product['name'],
                product['description'],
                product['requirements'],
                product['quantity'],
                product['price'],
                product['total']
            ])
    
    return flat_data

def view_tenders():
    st.subheader("View Tenders")
    
    tenders = tender_sheet.get_all_records()
    for tender in tenders:
        with st.expander(f"Tender {tender['tender_id']}"):
            st.write(f"Description: {tender['tender_description']}")
            st.write(f"Deadline: {tender['tender_deadline']}")
            st.write(f"TPO Contact: {tender['tpo_contact']}")
            
            lots = parse_lots(tender)
            for lot in lots:
                st.subheader(f"Lot: {lot['name']}")
                for product in lot['products']:
                    st.write(f"Product: {product['name']}")
                    st.write(f"Description: {product['description']}")
                    st.write(f"Requirements: {product['requirements']}")
                    st.write(f"Quantity: {product['quantity']}")
                    st.write(f"Price: {product['price']} MDL")
                    st.write(f"Total: {product['total']} MDL")

def parse_lots(tender):
    lots = []
    lot_count = tender['lot_count']
    index = 5  # Start index for lot data
    
    for _ in range(lot_count):
        lot_name = tender[f'lot_{index}_name']
        product_count = tender[f'lot_{index + 1}_product_count']
        products = []
        
        for j in range(product_count):
            product = {
                'name': tender[f'product_{index + 2 + j * 6}_name'],
                'description': tender[f'product_{index + 3 + j * 6}_description'],
                'requirements': tender[f'product_{index + 4 + j * 6}_requirements'],
                'quantity': tender[f'product_{index + 5 + j * 6}_quantity'],
                'price': tender[f'product_{index + 6 + j * 6}_price'],
                'total': tender[f'product_{index + 7 + j * 6}_total']
            }
            products.append(product)
        
        lots.append({
            'name': lot_name,
            'products': products
        })
        index += 2 + product_count * 6
    
    return lots

def submit_bid():
    st.subheader("Submit Bid")
    
    tender_id = st.text_input("Enter Tender ID")
    if tender_id:
        tender = get_tender(tender_id)
        if tender:
            st.write(f"Tender Description: {tender['tender_description']}")
            st.write(f"Deadline: {tender['tender_deadline']}")
            
            with st.form("bid_form"):
                bidder_name = st.text_input("Bidder Name")
                bidder_email = st.text_input("Bidder Email")
                bid_amount = st.number_input("Bid Amount (MDL)", min_value=0.0)
                bid_description = st.text_area("Bid Description")
                
                if st.form_submit_button("Submit Bid"):
                    save_bid(tender_id, bidder_name, bidder_email, bid_amount, bid_description)
                    st.success("Bid submitted successfully!")
        else:
            st.error("Tender not found")

def get_tender(tender_id):
    tenders = tender_sheet.get_all_records()
    return next((tender for tender in tenders if tender['tender_id'] == tender_id), None)

def save_bid(tender_id, bidder_name, bidder_email, bid_amount, bid_description):
    bidders_sheet.append_row([
        datetime.now().isoformat(),
        tender_id,
        bidder_name,
        bidder_email,
        bid_amount,
        bid_description,
        'Pending'  # Initial status
    ])

def evaluate_bids():
    st.subheader("Evaluate Bids")
    
    tenders = tender_sheet.get_all_records()
    selected_tender = st.selectbox("Select Tender", [f"{tender['tender_id']} - {tender['tender_description'][:50]}..." for tender in tenders])
    tender_id = selected_tender.split(' - ')[0]
    
    bids = get_bids_for_tender(tender_id)
    
    if bids:
        for bid in bids:
            with st.expander(f"Bid from {bid['bidder_name']} - {bid['bid_amount']} MDL"):
                st.write(f"Email: {bid['bidder_email']}")
                st.write(f"Description: {bid['bid_description']}")
                st.write(f"Status: {bid['status']}")
                
                if bid['status'] == 'Pending':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Accept", key=f"accept_{bid['id']}"):
                            update_bid_status(bid['id'], 'Accepted')
                            st.success("Bid accepted!")
                    with col2:
                        if st.button("Reject", key=f"reject_{bid['id']}"):
                            update_bid_status(bid['id'], 'Rejected')
                            st.success("Bid rejected!")
    else:
        st.write("No bids found for this tender.")

def get_bids_for_tender(tender_id):
    all_bids = bidders_sheet.get_all_records()
    return [{'id': index, **bid} for index, bid in enumerate(all_bids, start=2) if bid['tender_id'] == tender_id]

def update_bid_status(bid_id, new_status):
    bidders_sheet.update_cell(bid_id, 7, new_status)  # Assuming status is in the 7th column

# Currency conversion function
def convert_amount(amount, currency_code, language):
    try:
        amount_float = float(amount)
        try:
            return num2words(amount_float, lang=language, to='currency', currency=currency_code)
        except (NotImplementedError, IndexError):
            amount_in_words = num2words(amount_float, lang=language)
            return f"{amount_in_words} {currency_code}"
    except ValueError:
        return "Invalid input. Please enter a valid number."

# Route for currency conversion
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    message = ''
    if request.method == 'POST':
        amount = request.form.get('amount')
        currency = request.form.get('currency')
        amount = amount.replace(',', '.')

        amount_in_words_en = convert_amount(amount, currency, 'en')
        amount_in_words_ro = convert_amount(amount, currency, 'ro')

        message = f"English: {amount_in_words_en}<br>Romanian: {amount_in_words_ro}"

    return '''
        <form method="post">
            Enter Amount: <input type="text" name="amount"><br>
            Choose Currency:
            <select name="currency">
                <option value="USD">USD</option>
                <option value="MDL">MDL</option>
                <option value="EUR">EUR</option>
                <option value="UAH">UAH</option>
                <option value="RON">RON</option>
            </select><br>
            <input type="submit" value="Convert"><br>
        </form>
        <p>{}</p>
    '''.format(message)
                'name': tender[f'product_{index + 2 + j * 6}_name'],
                'description': tender[f'product_{index + 3 + j * 6}_description'],
                'requirements': tender[f'product_{index + 4 + j * 6}_requirements'],
                'quantity

def people_management():
    st.title("People Management")
    options = ["Shift Roster", "Shift Approval", "Employee Hours", "Guest Check-In"]
    selection = st.selectbox("Select a task", options)

    if selection == "Shift Roster":
        shift_roster()
    elif selection == "Shift Approval":
        shift_approval()
    elif selection == "Employee Hours":
        employee_hours()
    elif selection == "Guest Check-In":
        guest_check_in()

def shift_roster():
    st.subheader("Shift Roster")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input("Select date for shift roster")
        employees = get_employees()
        selected_employee = st.selectbox("Select employee", employees)
        shifts = ["Morning", "Afternoon", "Night"]
        selected_shift = st.selectbox("Select shift", shifts)
        
        if st.button("Add Shift"):
            add_shift(selected_date, selected_employee, selected_shift)
            st.success(f"Shift added for {selected_employee} on {selected_date} ({selected_shift})")
    
    with col2:
        st.subheader("Current Roster")
        roster = get_shift_roster(selected_date)
        st.table(roster)

def shift_approval():
    st.subheader("Shift Approval")
    
    pending_shifts = get_pending_shifts()
    
    if not pending_shifts:
        st.write("No pending shifts to approve.")
    else:
        for shift in pending_shifts:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.write(shift['employee'])
            with col2:
                st.write(shift['date'])
            with col3:
                st.write(shift['shift'])
            with col4:
                if st.button("Approve", key=f"approve_{shift['id']}"):
                    approve_shift(shift['id'])
                    st.success("Shift approved!")
            with col5:
                if st.button("Reject", key=f"reject_{shift['id']}"):
                    reject_shift(shift['id'])
                    st.success("Shift rejected!")

def employee_hours():
    st.subheader("Employee Hours")
    
    employees = get_employees()
    selected_employee = st.selectbox("Select employee", employees)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date")
    with col2:
        end_date = st.date_input("End date")
    
    if st.button("Fetch Hours"):
        hours = get_employee_hours(selected_employee, start_date, end_date)
        st.write(f"Total hours worked: {hours}")
        
        # Display detailed breakdown
        st.subheader("Hours Breakdown")
        breakdown = get_hours_breakdown(selected_employee, start_date, end_date)
        st.table(breakdown)

def guest_check_in():
    st.subheader("Guest Check-In")
    
    check_in_type = st.radio("Check-in Type", ["New Guest", "Returning Guest"])
    
    if check_in_type == "New Guest":
        with st.form("new_guest_form"):
            name = st.text_input("Guest Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone Number")
            check_in_date = st.date_input("Check-in Date")
            
            if st.form_submit_button("Check In"):
                guest_id = add_new_guest(name, email, phone, check_in_date)
                st.success(f"New guest checked in successfully. Guest ID: {guest_id}")
    else:
        guest_id = st.text_input("Enter Guest ID")
        if st.button("Fetch Guest Info"):
            guest_info = get_guest_info(guest_id)
            if guest_info:
                st.write(f"Name: {guest_info['name']}")
                st.write(f"Email: {guest_info['email']}")
                st.write(f"Phone: {guest_info['phone']}")
                check_in_date = st.date_input("Check-in Date")
                if st.button("Check In"):
                    update_guest_check_in(guest_id, check_in_date)
                    st.success("Guest checked in successfully")
            else:
                st.error("Guest not found")

# Helper functions for People Management
def get_employees():
    return [row[0] for row in employees_sheet.get_all_values()[1:]]  # Exclude header row

def add_shift(date, employee, shift):
    shifts_sheet.append_row([str(date), employee, shift, "Pending"])
    logger.info(f"Shift added: {employee} on {date} ({shift})")

def get_shift_roster(date):
    all_shifts = shifts_sheet.get_all_records()
    return [shift for shift in all_shifts if shift['Date'] == str(date) and shift['Status'] == 'Approved']

def get_pending_shifts():
    all_shifts = shifts_sheet.get_all_records()
    return [{'id': index, **shift} for index, shift in enumerate(all_shifts) if shift['Status'] == 'Pending']

def approve_shift(shift_id):
    shifts_sheet.update_cell(shift_id + 2, 4, 'Approved')  # +2 because sheet is 1-indexed and we have a header row
    logger.info(f"Shift {shift_id} approved")

def reject_shift(shift_id):
    shifts_sheet.update_cell(shift_id + 2, 4, 'Rejected')
    logger.info(f"Shift {shift_id} rejected")

def get_employee_hours(employee, start_date, end_date):
    all_shifts = shifts_sheet.get_all_records()
    employee_shifts = [shift for shift in all_shifts if shift['Employee'] == employee and 
                       start_date <= datetime.strptime(shift['Date'], '%Y-%m-%d').date() <= end_date and
                       shift['Status'] == 'Approved']
    return len(employee_shifts) * 8  # Assuming each shift is 8 hours

def get_hours_breakdown(employee, start_date, end_date):
    all_shifts = shifts_sheet.get_all_records()
    employee_shifts = [shift for shift in all_shifts if shift['Employee'] == employee and 
                       start_date <= datetime.strptime(shift['Date'], '%Y-%m-%d').date() <= end_date and
                       shift['Status'] == 'Approved']
    return pd.DataFrame(employee_shifts)

def add_new_guest(name, email, phone, check_in_date):
    guest_id = str(uuid.uuid4())
    guests_sheet.append_row([guest_id, name, email, phone, str(check_in_date)])
    logger.info(f"New guest added: {name} (ID: {guest_id})")
    return guest_id

def get_guest_info(guest_id):
    all_guests = guests_sheet.get_all_records()
    guest = next((g for g in all_guests if g['Guest ID'] == guest_id), None)
    return guest if guest else None

def update_guest_check_in(guest_id, check_in_date):
    all_guests = guests_sheet.get_all_records()
    guest_row = next((index for index, g in enumerate(all_guests) if g['Guest ID'] == guest_id), None)
    if guest_row is not None:
        guests_sheet.update_cell(guest_row + 2, 5, str(check_in_date))  # +2 because sheet is 1-indexed and we have a header row
        logger.info(f"Guest {guest_id} checked in on {check_in_date}")

# Main app execution
if __name__ == "__main__":
    main()