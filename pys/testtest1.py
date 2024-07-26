import streamlit as st
from datetime import datetime, timedelta
from twilio.rest import Client
import requests
from num2words import num2words
import json
import pandas as pd
import io
import os
import logging
import random
import traceback
from uuid import uuid4
from gspread_formatting import *
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import gspread

# Set page config
st.set_page_config(page_title="Document Management System", layout="wide")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load service account credentials
SERVICE_ACCOUNT_FILE = 'C:\\apptests\\1\\docstreamerAPI.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# Open required spreadsheets
SPREADSHEET_ID = '1dCGuJDk4sYZcqxZ-7nvg3R09IjecoEV_1nMRuehDfwo'
SPREADSHEET_ID_2 = '1GzYxPHNLV3Hn0HYF6irSk5jvT3jyzIdAtHjNGC0bIgc'
spreadsheet_id_3 = '1iSlsgQrc0-RQ1gFSmyhmXE6x2TKrHgiKRDSDuoX3mEY'

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
    
    date = st.date_input("Select Date")
    employee = st.selectbox("Select Employee", get_employees())
    shift = st.selectbox("Select Shift", ["Morning", "Afternoon", "Night"])
    
    if st.button("Add Shift"):
        add_shift(date, employee, shift)
        st.success(f"Shift added for {employee} on {date} ({shift})")
    
    st.subheader("Current Roster")
    roster = get_shift_roster(date)
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
                    st.experimental_rerun()
            with col5:
                if st.button("Reject", key=f"reject_{shift['id']}"):
                    reject_shift(shift['id'])
                    st.success("Shift rejected!")
                    st.experimental_rerun()

def employee_hours():
    st.subheader("Employee Hours")
    
    employee = st.selectbox("Select Employee", get_employees())
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    
    if st.button("Log Hours"):
        hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
        log_employee_hours(employee, start_date, hours)
        st.success(f"Logged {hours} hours for {employee} on {start_date}")
    
    if st.button("View Hours"):
        total_hours = get_employee_hours(employee, start_date, end_date)
        st.write(f"Total hours worked: {total_hours}")

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

# Helper functions
def get_employees():
    employees_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Employees')
    return employees_sheet.col_values(1)[1:]  # Assuming first column is employee names, skipping header

def add_shift(date, employee, shift):
    shifts_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Shifts')
    shifts_sheet.append_row([str(date), employee, shift, "Pending"])

def get_shift_roster(date):
    shifts_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Shifts')
    all_shifts = shifts_sheet.get_all_records()
    return [shift for shift in all_shifts if shift['Date'] == str(date) and shift['Status'] == 'Approved']

def get_pending_shifts():
    shifts_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Shifts')
    all_shifts = shifts_sheet.get_all_records()
    return [shift for shift in all_shifts if shift['Status'] == 'Pending']

def approve_shift(shift_id):
    shifts_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Shifts')
    shifts_sheet.update_cell(shift_id + 2, 4, 'Approved')  # +2 because sheet is 1-indexed and we have a header row

def reject_shift(shift_id):
    shifts_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Shifts')
    shifts_sheet.update_cell(shift_id + 2, 4, 'Rejected')

def log_employee_hours(employee, date, hours):
    hours_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Employee Hours')
    hours_sheet.append_row([str(date), employee, hours])

def get_employee_hours(employee, start_date, end_date):
    hours_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Employee Hours')
    all_hours = hours_sheet.get_all_records()
    employee_hours = [float(record['Hours']) for record in all_hours 
                      if record['Employee'] == employee 
                      and start_date <= datetime.strptime(record['Date'], '%Y-%m-%d').date() <= end_date]
    return sum(employee_hours)

def add_new_guest(name, email, phone, check_in_date):
    guests_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Guests')
    guest_id = str(uuid4())
    guests_sheet.append_row([guest_id, name, email, phone, str(check_in_date)])
    return guest_id

def get_guest_info(guest_id):
    guests_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Guests')
    all_guests = guests_sheet.get_all_records()
    guest = next((g for g in all_guests if g['Guest ID'] == guest_id), None)
    return guest

def update_guest_check_in(guest_id, check_in_date):
    guests_sheet = gc.open_by_key(SPREADSHEET_ID_2).worksheet('Guests')
    all_guests = guests_sheet.get_all_records()
    guest_row = next((index for index, g in enumerate(all_guests) if g['Guest ID'] == guest_id), None)
    if guest_row is not None:
        guests_sheet.update_cell(guest_row + 2, 5, str(check_in_date))  # +2 because sheet is 1-indexed and we have a header row

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

def input_data():
    st.title("Input Data")
    st.write("This feature is not yet implemented.")
    # Implement your data input logic here

# Helper functions for document generation
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

def purchases():
    st.title("Purchases")
    
    purchase_options = ["Tender Creator", "View Tenders", "Submit Bid", "Evaluate Bids", "Currency Converter"]
    selected_option = st.selectbox("Select an option", purchase_options)
    
    if selected_option == "Tender Creator":
        tender_creator()
    elif selected_option == "View Tenders":
        view_tenders()
    elif selected_option == "Submit Bid":
        submit_bid()
    elif selected_option == "Evaluate Bids":
        evaluate_bids()
    elif selected_option == "Currency Converter":
        currency_converter()

def currency_converter():
    st.subheader("Currency Converter")
    amount = st.text_input("Enter Amount")
    currency = st.selectbox("Choose Currency", ["USD", "MDL", "EUR", "UAH", "RON"])
    
    if st.button("Convert"):
        amount = amount.replace(',', '.')
        amount_in_words_en = convert_amount(amount, currency, 'en')
        amount_in_words_ro = convert_amount(amount, currency, 'ro')
        
        st.write(f"English: {amount_in_words_en}")
        st.write(f"Romanian: {amount_in_words_ro}")

def tender_creator():
    st.subheader("Tender Creator")
    
    if 'step' not in st.session_state:
        st.session_state.step = 1
    
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    
    try:
        if st.session_state.step == 1:
            step1()
        elif st.session_state.step == 2:
            step2()
        elif st.session_state.step == 3:
            step3()
        elif st.session_state.step == 4:
            step4()
        elif st.session_state.step == 5:
            step5()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        if st.button("Reset Form"):
            st.session_state.step = 1
            st.session_state.form_data = {}
            st.experimental_rerun()

def step1():
    st.write("Step 1 of 5")
    with st.form("step1_form"):
        num_lots = st.number_input("How many lots do you need?", min_value=1, value=1)
        tender_description = st.text_area("Enter Tender Description")
        tender_deadline = st.date_input("Tender Deadline")
        bidder_contact = st.text_input("Enter Bidder Contact Details")
        
        if st.form_submit_button("Next"):
            st.session_state.form_data.update({
                'num_lots': num_lots,
                'tender_description': tender_description,
                'tender_deadline': tender_deadline.strftime('%Y-%m-%d'),
                'bidder_contact': bidder_contact
            })
            st.session_state.step = 2
            st.experimental_rerun()

def step2():
    st.write("Step 2 of 5")
    with st.form("step2_form"):
        for i in range(st.session_state.form_data['num_lots']):
            st.text_input(f"Name for Lot {i+1}", key=f"lot_{i}_name")
            st.number_input(f"Number of Products/Services in Lot {i+1}", min_value=1, max_value=30, key=f"products_{i}")
        
        if st.form_submit_button("Next"):
            for i in range(st.session_state.form_data['num_lots']):
                st.session_state.form_data[f'lot_{i}_name'] = st.session_state[f"lot_{i}_name"]
                st.session_state.form_data[f'products_{i}'] = st.session_state[f"products_{i}"]
            st.session_state.step = 3
            st.experimental_rerun()

def step3():
    st.write("Step 3 of 5")
    with st.form("step3_form"):
        for i in range(st.session_state.form_data['num_lots']):
            st.subheader(st.session_state.form_data[f'lot_{i}_name'])
            for j in range(st.session_state.form_data[f'products_{i}']):
                st.text_input(f"Name for Product/Service {j+1}", key=f"product_name_{i}_{j}")
                st.text_area(f"Description for Product/Service {j+1}", key=f"product_description_{i}_{j}")
                st.text_area(f"Requirements for Product/Service {j+1}", key=f"product_requirements_{i}_{j}")
                st.number_input(f"Quantity Needed for Product/Service {j+1}", min_value=1, key=f"product_quantity_{i}_{j}")
                st.number_input(f"Price per Item for Product/Service {j+1} (MDL)", min_value=0.0, key=f"product_price_{i}_{j}")
        
        if st.form_submit_button("Next"):
            lots = []
            for i in range(st.session_state.form_data['num_lots']):
                products = []
                for j in range(st.session_state.form_data[f'products_{i}']):
                    product = {
                        'name': st.session_state[f"product_name_{i}_{j}"],
                        'description': st.session_state[f"product_description_{i}_{j}"],
                        'requirements': st.session_state[f"product_requirements_{i}_{j}"],
                        'quantity': st.session_state[f"product_quantity_{i}_{j}"],
                        'price': st.session_state[f"product_price_{i}_{j}"],
                        'total': st.session_state[f"product_quantity_{i}_{j}"] * st.session_state[f"product_price_{i}_{j}"]
                    }
                    products.append(product)
                lots.append({
                    'name': st.session_state.form_data[f'lot_{i}_name'],
                    'products': products
                })
            st.session_state.form_data['lots'] = lots
            st.session_state.step = 4
            st.experimental_rerun()

def step4():
    st.write("Step 4 of 5")
    st.subheader("Form Preview")
    
    for lot in st.session_state.form_data['lots']:
        st.write(f"### {lot['name']}")
        for product in lot['products']:
            st.write(f"Product: {product['name']}")
    
    st.write(f"Tender Description: {st.session_state.form_data['tender_description']}")
    st.write(f"Tender Deadline: {st.session_state.form_data['tender_deadline']}")
    st.write(f"Bidder Contact Details: {st.session_state.form_data['bidder_contact']}")
    
    if st.button("Submit Form"):
        st.session_state.step = 5
        st.experimental_rerun()

def step5():
    st.write("Step 5 of 5")
    st.subheader("Final Review and Submission")
    
    for lot_index, lot in enumerate(st.session_state.form_data['lots']):
        st.write(f"### {lot['name']}")
        for product_index, product in enumerate(lot['products']):
            with st.expander(f"Product: {product['name']}"):
                product['name'] = st.text_input(f"Product Name", product['name'], key=f"final_product_name_{lot_index}_{product_index}")
                product['description'] = st.text_area(f"Description", product['description'], key=f"final_description_{lot_index}_{product_index}")
                product['requirements'] = st.text_area(f"Requirements", product['requirements'], key=f"final_requirements_{lot_index}_{product_index}")
                product['quantity'] = st.number_input(f"Quantity", min_value=1, value=int(product['quantity']), key=f"final_quantity_{lot_index}_{product_index}")
                product['price'] = st.number_input(f"Price per Item (MDL)", min_value=0.0, value=float(product['price']), key=f"final_price_{lot_index}_{product_index}")
                product['total'] = product['quantity'] * product['price']
                st.write(f"Total Sum (MDL): {product['total']:.2f}")
    
    st.session_state.form_data['tender_description'] = st.text_area("Tender Description", st.session_state.form_data['tender_description'])
    
    current_deadline = st.session_state.form_data['tender_deadline']
    if isinstance(current_deadline, str):
        current_deadline = datetime.strptime(current_deadline, '%Y-%m-%d').date()
    st.session_state.form_data['tender_deadline'] = st.date_input("Tender Deadline", current_deadline)
    
    st.session_state.form_data['bidder_contact'] = st.text_input("Bidder Contact Details", st.session_state.form_data['bidder_contact'])
    
    if st.button("Confirm & Submit"):
        success, tender_id, result = submit_tender()
        if success:
            st.success("Tender submitted successfully!")
            st.write(f"Your tender ID is: {tender_id}")
            st.write(f"Public tender page: [View Tender]({result})")
            st.write("You can share this link with potential bidders.")
            st.write("Guidance for using this tender:")
            st.write("1. Share the public tender page link with potential bidders.")
            st.write("2. Bidders can view the tender details and requirements on the public page.")
            st.write("3. Set up a system to receive and evaluate bids (e.g., dedicated email or submission form).")
            st.write("4. After the deadline, review received bids and select the winning bid(s).")
            
            st.session_state.step = 1  # Reset to first step for new tender
            st.session_state.form_data = {}  # Clear form data
        else:
            st.error(f"Failed to submit tender. Error: {result}")
            logger.error(f"Tender submission failed. Error: {result}")
    
    if st.button("Go Back"):
        st.session_state.step = 4
        st.experimental_rerun()

def submit_tender():
    try:
        logger.info("Starting tender submission process")
        
        tender_id = str(uuid4())
        logger.info(f"Generated tender ID: {tender_id}")
        
        form_data = st.session_state.form_data.copy()
        form_data['tender_deadline'] = form_data['tender_deadline'].strftime('%Y-%m-%d')
        form_data['tender_id'] = tender_id
        logger.info("Prepared form data for submission")
        
        tender_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Tenders')
        flat_data = flatten_tender_data(form_data)
        tender_sheet.append_row(flat_data)
        logger.info("Tender data saved to Google Sheets")
        
        html_content = generate_tender_html(form_data)
        logger.info("Generated HTML content for tender page")
        
        file_metadata = {
            'name': f'Tender_{tender_id}.html',
            'mimeType': 'text/html',
            'parents': ['1JnnPQPpcsGb4xBmPDr6cGbEBbWN5VAFx']  # Specify the folder ID
        }
        media = MediaIoBaseUpload(io.BytesIO(html_content.encode()), mimetype='text/html', resumable=True)
        drive_service = build('drive', 'v3', credentials=creds)
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        drive_service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'},
            fields='id'
        ).execute()
        
        public_link = file.get('webViewLink')
        logger.info(f"Tender HTML file uploaded to Google Drive. Public link: {public_link}")
        
        return True, tender_id, public_link
    except Exception as e:
        logger.error(f"Error in submit_tender: {str(e)}", exc_info=True)
        return False, None, str(e)

def flatten_tender_data(data):
    flat_data = [
        data['tender_description'],
        data['tender_deadline'],
        data['bidder_contact'],
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

def generate_tender_html(tender_data):
    html_content = f"""
    <html>
    <head>
        <title>Tender: {tender_data['tender_description'][:50]}...</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            h1 {{ color: #333; }}
            .lot {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; }}
            .product {{ margin-left: 20px; }}
        </style>
    </head>
    <body>
        <h1>Tender Details</h1>
        <p><strong>Description:</strong> {tender_data['tender_description']}</p>
        <p><strong>Deadline:</strong> {tender_data['tender_deadline']}</p>
        <p><strong>Contact:</strong> {tender_data['bidder_contact']}</p>
        
        <h2>Lots and Products</h2>
    """
    
    for lot in tender_data['lots']:
        html_content += f"""
        <div class="lot">
            <h3>{lot['name']}</h3>
        """
        for product in lot['products']:
            html_content += f"""
            <div class="product">
                <p><strong>{product['name']}</strong></p>
                <p>Description: {product['description']}</p>
                <p>Requirements: {product['requirements']}</p>
                <p>Quantity: {product['quantity']}</p>
                <p>Price per Item: {product['price']} MDL</p>
                <p>Total: {product['total']} MDL</p>
            </div>
            """
        html_content += "</div>"
    
    html_content += """
    </body>
    </html>
    """
    
    return html_content

def view_tenders():
    st.subheader("View Tenders")
    tender_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Tenders')
    tenders = tender_sheet.get_all_records()
    
    for tender in tenders:
        with st.expander(f"Tender ID: {tender['tender_id']}"):
            st.write(f"Description: {tender['tender_description']}")
            st.write(f"Deadline: {tender['tender_deadline']}")
            st.write(f"Contact: {tender['bidder_contact']}")
            if st.button(f"View Details for Tender {tender['tender_id']}"):
                view_tender_details(tender['tender_id'])

def view_tender_details(tender_id):
    tender_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Tenders')
    tender_data = tender_sheet.find(tender_id)
    if not tender_data:
        st.error("Tender not found")
        return
    
    row = tender_sheet.row_values(tender_data.row)
    
    st.title(f"Tender Details: {tender_id}")
    st.write(f"Description: {row[1]}")
    st.write(f"Deadline: {row[2]}")
    st.write(f"Contact: {row[3]}")
    
    lot_count = int(row[4])
    index = 5
    for i in range(lot_count):
        st.subheader(f"Lot {i+1}: {row[index]}")
        index += 1
        product_count = int(row[index])
        index += 1
        for j in range(product_count):
            st.write(f"Product: {row[index]}")
            st.write(f"Description: {row[index+1]}")
            st.write(f"Requirements: {row[index+2]}")
            st.write(f"Quantity: {row[index+3]}")
            st.write(f"Price per Item: {row[index+4]} MDL")
            st.write(f"Total: {row[index+5]} MDL")
            index += 6

def submit_bid():
    st.subheader("Submit a Bid")
    tender_id = st.text_input("Enter Tender ID")
    if tender_id:
        view_tender_details(tender_id)
        
        st.subheader("Submit Your Bid")
        with st.form("bid_submission"):
            bidder_name = st.text_input("Bidder Name")
            bidder_email = st.text_input("Bidder Email")
            bid_amount = st.number_input("Bid Amount (MDL)", min_value=0.0, step=0.01)
            bid_description = st.text_area("Bid Description")
            submitted = st.form_submit_button("Submit Bid")
            
            if submitted:
                save_bid(tender_id, bidder_name, bidder_email, bid_amount, bid_description)
                st.success("Your bid has been submitted successfully!")

def save_bid(tender_id, bidder_name, bidder_email, bid_amount, bid_description):
    bids_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Bids')
    bids_sheet.append_row([
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
    
    tender_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Tenders')
    tenders = tender_sheet.get_all_records()
    
    selected_tender = st.selectbox("Select a tender to evaluate", 
                                   [f"{tender['tender_id']} - {tender['tender_description']}" for tender in tenders])
    tender_id = selected_tender.split(' - ')[0]
    
    bids_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Bids')
    all_bids = bids_sheet.get_all_records()
    tender_bids = [bid for bid in all_bids if bid['tender_id'] == tender_id]
    
    if not tender_bids:
        st.write("No bids received for this tender yet.")
        return
    
    st.subheader("Received Bids")
    for bid in tender_bids:
        with st.expander(f"Bid from {bid['bidder_name']} - {bid['bid_amount']} MDL"):
            st.write(f"Email: {bid['bidder_email']}")
            st.write(f"Description: {bid['bid_description']}")
            st.write(f"Status: {bid['status']}")
            
            if bid['status'] == 'Pending':
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Accept Bid {bid['bidder_name']}"):
                        update_bid_status(bid['timestamp'], 'Accepted')
                        st.success("Bid accepted!")
                        st.experimental_rerun()
                with col2:
                    if st.button(f"Reject Bid {bid['bidder_name']}"):
                        update_bid_status(bid['timestamp'], 'Rejected')
                        st.success("Bid rejected!")
                        st.experimental_rerun()
    
    st.subheader("Bid Summary")
    accepted_bids = [bid for bid in tender_bids if bid['status'] == 'Accepted']
    rejected_bids = [bid for bid in tender_bids if bid['status'] == 'Rejected']
    pending_bids = [bid for bid in tender_bids if bid['status'] == 'Pending']
    
    st.write(f"Total Bids: {len(tender_bids)}")
    st.write(f"Accepted Bids: {len(accepted_bids)}")
    st.write(f"Rejected Bids: {len(rejected_bids)}")
    st.write(f"Pending Bids: {len(pending_bids)}")
    
    if accepted_bids:
        st.subheader("Winning Bid")
        winning_bid = min(accepted_bids, key=lambda x: float(x['bid_amount']))
        st.write(f"Winner: {winning_bid['bidder_name']}")
        st.write(f"Winning Bid Amount: {winning_bid['bid_amount']} MDL")
        
        if st.button("Finalize Tender"):
            finalize_tender(tender_id, winning_bid)
            st.success("Tender finalized successfully!")

def update_bid_status(timestamp, new_status):
    bids_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Bids')
    cell = bids_sheet.find(timestamp)
    status_col = 7  # Assuming status is in the 7th column
    bids_sheet.update_cell(cell.row, status_col, new_status)

def finalize_tender(tender_id, winning_bid):
    tender_sheet = gc.open_by_key(spreadsheet_id_3).worksheet('Tenders')
    cell = tender_sheet.find(tender_id)
    row = cell.row
    
    # Update tender status
    status_col = tender_sheet.find("Status").col
    tender_sheet.update_cell(row, status_col, "Finalized")
    
    # Update winning bid information
    winner_col = tender_sheet.find("Winning Bidder").col
    amount_col = tender_sheet.find("Winning Bid Amount").col
    tender_sheet.update_cell(row, winner_col, winning_bid['bidder_name'])
    tender_sheet.update_cell(row, amount_col, winning_bid['bid_amount'])
    
    # Notify the winning bidder
    notify_winning_bidder(winning_bid, tender_id)

def notify_winning_bidder(winning_bid, tender_id):
    # This function would typically send an email or SMS to the winning bidder
    # For this example, we'll just print a message
    print(f"Notifying {winning_bid['bidder_name']} that they've won tender {tender_id}")
    # In a real-world scenario, you might use an email service or Twilio for SMS here

# Helper function to convert currency amounts to words
def convert_amount(amount, currency_code, language):
    try:
        amount_float = float(amount)
        # Attempt currency conversion
        try:
            return num2words(amount_float, lang=language, to='currency', currency=currency_code)
        except (NotImplementedError, IndexError):
            # Fallback to number-to-words conversion without specifying currency
            amount_in_words = num2words(amount_float, lang=language)
            return f"{amount_in_words} {currency_code}"
    except ValueError:
        return "Invalid input. Please enter a valid number."

# Add this route to your Flask app if you're using Flask alongside Streamlit
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    message = ''
    if request.method == 'POST':
        amount = request.form.get('amount')
        currency = request.form.get('currency')
        # Replace comma with dot for decimal
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

# Main app execution
if __name__ == "__main__":
    main()