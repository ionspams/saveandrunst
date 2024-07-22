import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib
import base64

# Function to initialize Google Sheets client
def authenticate_gsheets(json_keyfile_name):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(json_keyfile_name, scopes=scope)
    client = gspread.authorize(creds)
    return client

# Function to open a specific Google Sheet
def open_sheet(client, spreadsheet_url, sheet_name):
    spreadsheet = client.open_by_url(spreadsheet_url)
    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="20")
    return sheet

# Function to append a row to the Google Sheet
def append_row(sheet, row):
    sheet.append_row(row)

# Function to generate a unique public form URL
def generate_form_url(base_url, form_id):
    hash_object = hashlib.sha256(form_id.encode())
    form_hash = base64.urlsafe_b64encode(hash_object.digest()[:15]).decode('utf-8')
    return f"{base_url}?form_id={form_hash}"

# Function to flatten the data for Google Sheets
def flatten_data(data):
    flat_data = []
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    flat_data.extend(item.values())
                else:
                    flat_data.append(item)
        else:
            flat_data.append(value)
    return flat_data

# Function to list tenders
def list_tenders(sheet):
    records = sheet.get_all_records()
    tenders = []
    for record in records:
        tenders.append({
            "id": record["form_id"],
            "category": record["purchase_category"],
            "num_items": record["num_items"],
            "public_url": record["public_url"]
        })
    return tenders

# Function to view offers for a tender
def view_offers(sheet, form_id):
    offers = []
    records = sheet.get_all_records()
    for record in records:
        if record["form_id"] == form_id:
            offers.append(record)
    return offers

# Streamlit multi-step form
def main():
    st.title("Procurement Wizard Form")

    # Authenticate Google Sheets
    json_keyfile_name = r'docstreamerAPI.json'  # Hardcoded path for the JSON keyfile
    client = authenticate_gsheets(json_keyfile_name)
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1iSlsgQrc0-RQ1gFSmyhmXE6x2TKrHgiKRDSDuoX3mEY'
    sheet_name = 'Procurement Data'
    sheet = open_sheet(client, spreadsheet_url, sheet_name)

    # Get current port
    port = st.query_params.get('port', ['8501'])[0]
    base_url = f"http://localhost:{port}"

    # Sidebar navigation
    st.sidebar.title("Navigation")
    options = ["Create Tender", "View Tenders", "Review Offers"]
    choice = st.sidebar.radio("Go to", options)

    if choice == "Create Tender":
        # Initialize session state
        if 'step' not in st.session_state:
            st.session_state['step'] = 1

        def reset_form():
            for key in list(st.session_state.keys()):
                if key != 'step':
                    del st.session_state[key]

        # Step 1: Determine Purchase Category
        if st.session_state['step'] == 1:
            st.header("Start Procurement Process")
            purchase_category = st.radio("Determine Purchase Category", ["Category A <= $500", "Category B $500 - $5000", "Category C > $5000"])
            st.session_state['purchase_category'] = purchase_category
            if st.button("Next"):
                st.session_state['step'] = 2

        # Step 2: Category-specific Form
        elif st.session_state['step'] == 2:
            st.header("Purchase Details")
            if st.session_state['purchase_category'] == "Category A <= $500":
                num_items = st.number_input("Number of items to be purchased", min_value=1)
                st.session_state['num_items'] = num_items
                items = []
                for i in range(int(num_items)):
                    st.subheader(f"Item {i+1}")
                    product_name = st.text_input(f"Product name {i+1}")
                    product_description = st.text_area(f"Product description {i+1}")
                    product_requirements = st.text_area(f"Product requirements {i+1}")
                    product_quantity = st.number_input(f"Product quantity {i+1}", min_value=1)
                    desired_price = st.number_input(f"Desired price {i+1} (not more than the maximum price)", min_value=0.01, step=0.01)
                    items.append({
                        "product_name": product_name,
                        "product_description": product_description,
                        "product_requirements": product_requirements,
                        "product_quantity": product_quantity,
                        "desired_price": desired_price
                    })
                st.session_state['items'] = items
                if st.button("Create Public Form"):
                    st.session_state['step'] = 3

            elif st.session_state['purchase_category'] == "Category B $500 - $5000":
                projected_price = st.number_input("Projected price", min_value=500.01, max_value=5000.00, step=0.01)
                st.session_state['projected_price'] = projected_price
                num_items = st.number_input("Number of items to be purchased", min_value=1)
                st.session_state['num_items'] = num_items
                items = []
                for i in range(int(num_items)):
                    st.subheader(f"Item {i+1}")
                    product_name = st.text_input(f"Product name {i+1}")
                    product_description = st.text_area(f"Product description {i+1}")
                    product_requirements = st.text_area(f"Product requirements {i+1}")
                    product_quantity = st.number_input(f"Product quantity {i+1}", min_value=1)
                    desired_price = st.number_input(f"Desired price {i+1} (not more than the maximum price)", min_value=0.01, step=0.01)
                    items.append({
                        "product_name": product_name,
                        "product_description": product_description,
                        "product_requirements": product_requirements,
                        "product_quantity": product_quantity,
                        "desired_price": desired_price
                    })
                st.session_state['items'] = items
                if st.button("Create Public Form"):
                    st.session_state['step'] = 3

            elif st.session_state['purchase_category'] == "Category C > $5000":
                projected_amount = st.number_input("Projected amount", min_value=5000.01, step=0.01)
                st.session_state['projected_amount'] = projected_amount
                num_lots = st.number_input("Number of lots in the tender", min_value=1)
                st.session_state['num_lots'] = num_lots
                tender_description = st.text_area("Tender description")
                tender_deadline = st.date_input("Tender deadline")
                tender_process_owner = st.text_input("Tender process owner contact details")
                st.session_state['tender_description'] = tender_description
                st.session_state['tender_deadline'] = tender_deadline
                st.session_state['tender_process_owner'] = tender_process_owner
                lots = []
                for i in range(int(num_lots)):
                    st.subheader(f"Lot {i+1}")
                    lot_name = st.text_input(f"Lot name {i+1}")
                    num_products = st.number_input(f"Number of products/services in Lot {i+1}", min_value=1)
                    products = []
                    for j in range(int(num_products)):
                        st.subheader(f"Product/Service {j+1} in Lot {i+1}")
                        product_name = st.text_input(f"Product name {i+1}.{j+1}")
                        product_description = st.text_area(f"Product description {i+1}.{j+1}")
                        product_requirements = st.text_area(f"Product requirements {i+1}.{j+1}")
                        product_quantity = st.number_input(f"Product quantity {i+1}.{j+1}", min_value=1)
                        desired_price = st.number_input(f"Desired price {i+1}.{j+1}", min_value=0.01, step=0.01)
                        products.append({
                            "product_name": product_name,
                            "product_description": product_description,
                            "product_requirements": product_requirements,
                            "product_quantity": product_quantity,
                            "desired_price": desired_price
                        })
                    lots.append({
                        "lot_name": lot_name,
                        "products": products
                    })
                st.session_state['lots'] = lots
                if st.button("Create Public Form"):
                    st.session_state['step'] = 3

        # Step 3: Finalize and Store Data
        elif st.session_state['step'] == 3:
            st.header("Finalize Procurement")
            st.write("Review the details and submit the form.")
            
            # Display a summary of the data
            st.subheader("Summary")
            st.write(f"Category: {st.session_state['purchase_category']}")
            
            if 'num_items' in st.session_state:
                st.write(f"Number of Items: {st.session_state['num_items']}")
                for item in st.session_state['items']:
                    st.write(item)
            
            if 'projected_price' in st.session_state:
                st.write(f"Projected Price: {st.session_state['projected_price']}")
            
            if 'projected_amount' in st.session_state:
                st.write(f"Projected Amount: {st.session_state['projected_amount']}")
                st.write(f"Tender Description: {st.session_state['tender_description']}")
                st.write(f"Tender Deadline: {st.session_state['tender_deadline']}")
                st.write(f"Tender Process Owner: {st.session_state['tender_process_owner']}")
                for lot in st.session_state['lots']:
                    st.write(f"Lot Name: {lot['lot_name']}")
                    for product in lot['products']:
                        st.write(product)
            
            if st.button("Submit"):
                data = {
                    'form_id': hashlib.sha256(str(st.session_state).encode()).hexdigest(),
                    'purchase_category': st.session_state.get('purchase_category'),
                    'num_items': st.session_state.get('num_items'),
                    'items': st.session_state.get('items'),
                    'projected_price': st.session_state.get('projected_price'),
                    'projected_amount': st.session_state.get('projected_amount'),
                    'num_lots': st.session_state.get('num_lots'),
                    'tender_description': st.session_state.get('tender_description'),
                    'tender_deadline': st.session_state.get('tender_deadline').strftime('%Y-%m-%d') if st.session_state.get('tender_deadline') else None,
                    'tender_process_owner': st.session_state.get('tender_process_owner'),
                    'lots': st.session_state.get('lots')
                }
                flat_data = flatten_data(data)
                append_row(sheet, flat_data)
                
                form_id = hashlib.sha256(str(data).encode()).hexdigest()
                form_url = generate_form_url(base_url, form_id)
                st.success("Procurement data submitted successfully!")
                st.write(f"Public form URL: {form_url}")
                reset_form()

    # Handling public form submission
    elif 'form_id' in st.query_params:
        form_id = st.query_params.get('form_id')[0]
        st.header(f"Tender ID: {form_id}")
        st.write("Submit your offer below:")
        
        offer_name = st.text_input("Offer Name")
        offer_description = st.text_area("Offer Description")
        offer_price = st.number_input("Offer Price", min_value=0.01, step=0.01)
        
        if st.button("Submit Offer"):
            offer_data = {
                'form_id': form_id,
                'offer_name': offer_name,
                'offer_description': offer_description,
                'offer_price': offer_price
            }
            flat_offer_data = flatten_data(offer_data)
            append_row(sheet, flat_offer_data)
            st.success("Offer submitted successfully!")

    elif choice == "View Tenders":
        # View tenders
        st.header("View Tenders")
        tenders = list_tenders(sheet)
        for tender in tenders:
            st.subheader(f"Tender ID: {tender['id']}")
            st.write(f"Category: {tender['category']}")
            st.write(f"Number of Items: {tender['num_items']}")
            st.write(f"Public URL: {tender['public_url']}")

    elif choice == "Review Offers":
        # Review offers
        st.header("Review Offers")
        form_id = st.text_input("Enter the Tender ID to review offers:")
        if st.button("Review Offers"):
            offers = view_offers(sheet, form_id)
            if offers:
                st.write(f"Offers for Tender ID: {form_id}")
                for offer in offers:
                    st.write(offer)
            else:
                st.write(f"No offers found for Tender ID: {form_id}")

if __name__ == "__main__":
    main()
