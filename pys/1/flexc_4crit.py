import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from collections import Counter
import gspread
from gspread_dataframe import set_with_dataframe
import json

st.set_page_config(page_title='Dashboard Portal', layout='wide')

# Set the maximum number of elements to be styled to a large number
pd.set_option('styler.render.max_elements', 10500000)  # Adjust this value as needed

st.title('Dashboard Portal')

# Sidebar for Google Spreadsheet ID
st.sidebar.header('Google Sheets')
spreadsheet_id = st.sidebar.text_input('Google Spreadsheet ID')

# Sidebar for GCP Credentials
use_gcp = st.sidebar.checkbox('Use GCP credentials')
gcp_credentials = None
if use_gcp:
    gcp_credentials = st.sidebar.file_uploader("Upload GCP Credentials JSON", type=["json"])

# Sidebar for data input method
st.sidebar.header('Data Input Method')
data_input_method = st.sidebar.selectbox('Choose data input method', ['Google Sheets', 'File Upload', 'API Fetch'])

# Sidebar for Google Sheets input
if data_input_method == 'Google Sheets':
    google_sheet_url_1 = st.sidebar.text_input('Google Sheet URL for first dataset')
    google_sheet_url_2 = st.sidebar.text_input('Google Sheet URL for second dataset')

# Sidebar for API token input if API Fetch is chosen
if data_input_method == 'API Fetch':
    api_token = st.sidebar.text_input('Enter API token')
    api_url_1 = st.sidebar.text_input('API URL for first dataset')
    api_url_2 = st.sidebar.text_input('API URL for second dataset')

# Sidebar for file uploads if File Upload is chosen
if data_input_method == 'File Upload':
    file1 = st.sidebar.file_uploader("Upload first spreadsheet", type=["csv", "xlsx"])
    file2 = st.sidebar.file_uploader("Upload second spreadsheet", type=["csv", "xlsx"])

# Sidebar for Flexcompare criteria
st.sidebar.header('Comparison Criteria')
criteria1 = st.sidebar.checkbox('7+ characters matching 100% consecutively')
criteria2 = st.sidebar.checkbox('5 or 6 characters matching 100% consecutively')
criteria3 = st.sidebar.checkbox('4 characters matching 100% consecutively + another 2, 3, or 4 characters matching 100% consecutively and simultaneously')
criteria4 = st.sidebar.checkbox('4+ characters matching 100% consecutively')

def fetch_data(api_url, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Assuming the API returns JSON data
    else:
        st.error(f"Failed to fetch data from {api_url}. Status code: {response.status_code}")
        return None

def load_google_sheet(url):
    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        return pd.read_csv(sheet_url)
    except Exception as e:
        st.error(f"Failed to load Google Sheet: {e}")
        return None

def update_google_sheet(spreadsheet_id, df, sheet_name, gcp_credentials=None):
    try:
        if gcp_credentials:
            gc = gspread.service_account(filename=gcp_credentials)
        else:
            gc = gspread.Client(auth=None)
        
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        set_with_dataframe(worksheet, df)
        st.success(f"Sheet {sheet_name} updated successfully.")
    except Exception as e:
        st.error(f"Failed to update Google Sheet: {e}")

data1 = None
data2 = None

if data_input_method == 'API Fetch' and api_token and api_url_1 and api_url_2:
    data1 = fetch_data(api_url_1, api_token)
    data2 = fetch_data(api_url_2, api_token)

elif data_input_method == 'File Upload' and file1 and file2:
    if file1.name.endswith('csv'):
        data1 = pd.read_csv(BytesIO(file1.getvalue()))
    else:
        data1 = pd.read_excel(BytesIO(file1.getvalue()), engine='openpyxl')

    if file2.name.endswith('csv'):
        data2 = pd.read_csv(BytesIO(file2.getvalue()))
    else:
        data2 = pd.read_excel(BytesIO(file2.getvalue()), engine='openpyxl')

elif data_input_method == 'Google Sheets' and google_sheet_url_1 and google_sheet_url_2:
    data1 = load_google_sheet(google_sheet_url_1)
    data2 = load_google_sheet(google_sheet_url_2)

if data1 is not None and data2 is not None:
    if data_input_method == 'API Fetch':
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
    else:
        df1 = data1
        df2 = data2

    st.subheader("First dataset")
    st.dataframe(df1.head())
    
    st.subheader("Second dataset")
    st.dataframe(df2.head())

    st.subheader("Data Comparison")
    
    base_column = st.selectbox("Select the base column for matching", df1.columns)

    columns1 = st.multiselect("Select columns from the first dataset to compare", df1.columns, key='columns1')
    columns2 = st.multiselect("Select columns from the second dataset to compare", df2.columns, key='columns2')

    # Additional selectboxes for up to 6 common columns
    additional_columns = []
    for i in range(1, 7):
        col1 = st.selectbox(f"Select additional column {i} from the first dataset", ['None'] + list(df1.columns), key=f'additional_col1_{i}')
        col2 = st.selectbox(f"Select additional column {i} from the second dataset", ['None'] + list(df2.columns), key=f'additional_col2_{i}')
        if col1 != 'None' and col2 != 'None':
            additional_columns.append((col1, col2))

    def match_criteria(value1, value2, criteria):
        value1 = str(value1)
        value2 = str(value2)
        if criteria == 1:
            return len(value1) >= 7 and value1 == value2
        elif criteria == 2:
            return 5 <= len(value1) <= 6 and value1 == value2
        elif criteria == 3:
            return len(value1) >= 4 and any(value1[:i] == value2[:i] for i in range(4, min(len(value1), len(value2)) + 1))
        elif criteria == 4:
            return len(value1) >= 4 and value1 == value2
        return False

    if st.button("Compare"):
        if base_column and columns1 and columns2:
            if len(columns1) != len(columns2):
                st.error("The number of columns selected for comparison must be equal in both datasets!")
            else:
                df1[base_column] = df1[base_column].astype(str)
                df2[base_column] = df2[base_column].astype(str)
                result_df = pd.merge(df1, df2, on=base_column, suffixes=('_df1', '_df2'))

                class DifferenceCounter:
                    def __init__(self, columns):
                        self.diff_count = 0
                        self.diff_summary = {col: 0 for col in columns}
                        self.value_change_counter = Counter()
                        self.criteria_counters = {1: 0, 2: 0, 3: 0, 4: 0}
                    
                    def highlight_diff(self, row):
                        styles = []
                        changes = False
                        for col1, col2 in zip(columns1, columns2) + additional_columns:
                            df1_col = f'{col1}_df1'
                            df2_col = f'{col2}_df2'
                            matched = False
                            if criteria1 and match_criteria(row[df1_col], row[df2_col], 1):
                                matched = True
                                self.criteria_counters[1] += 1
                            elif criteria2 and match_criteria(row[df1_col], row[df2_col], 2):
                                matched = True
                                self.criteria_counters[2] += 1
                            elif criteria3 and match_criteria(row[df1_col], row[df2_col], 3):
                                matched = True
                                self.criteria_counters[3] += 1
                            elif criteria4 and match_criteria(row[df1_col], row[df2_col], 4):
                                matched = True
                                self.criteria_counters[4] += 1

                            if matched:
                                styles.extend(['background-color: lightgreen', 'background-color: lightgreen'])
                                self.diff_count += 1
                                self.diff_summary[col1] += 1
                                changes = True
                                change_pattern = (row[df1_col], row[df2_col])
                                self.value_change_counter[change_pattern] += 1
                            else:
                                styles.extend(['', ''])
                        return styles, changes

                diff_counter = DifferenceCounter(columns1 + [col1 for col1, col2 in additional_columns])
                
                def apply_highlight_and_changes(row):
                    styles, changes = diff_counter.highlight_diff(row)
                    row['Changes'] = 'Yes' if changes else 'No'
                    return styles

                result_df['Changes'] = result_df.apply(lambda row: 'Yes' if any(
                    match_criteria(row[f'{col}_df1'], row[f'{col}_df2'], 1) or
                    match_criteria(row[f'{col}_df1'], row[f'{col}_df2'], 2) or
                    match_criteria(row[f'{col}_df1'], row[f'{col}_df2'], 3) or
                    match_criteria(row[f'{col}_df1'], row[f'{col}_df2'], 4)
                    for col in columns1) else 'No', axis=1)

                styled_df = result_df.style.apply(lambda row: diff_counter.highlight_diff(row)[0], axis=1, subset=[f'{col}_df1' for col in columns1] + [f'{col}_df2' for col in columns2])
                
                st.write("Comparison result:")
                st.dataframe(styled_df)

                st.subheader("Summary")
                st.write(f"Total number of differing values: {diff_counter.diff_count}")
                for col, count in diff_counter.diff_summary.items():
                    st.write(f"Number of differing values in column '{col}': {count}")

                st.subheader("Criteria Match Counts")
                st.write(f"7+ characters matching 100% consecutively: {diff_counter.criteria_counters[1]}")
                st.write(f"5 or 6 characters matching 100% consecutively: {diff_counter.criteria_counters[2]}")
                st.write(f"4 characters matching 100% consecutively + another 2, 3, or 4 characters matching 100% consecutively and simultaneously: {diff_counter.criteria_counters[3]}")
                st.write(f"4+ characters matching 100% consecutively: {diff_counter.criteria_counters[4]}")
                
                st.subheader("Most changed value patterns")
                for pattern, count in diff_counter.value_change_counter.most_common():
                    st.write(f"Value change from {pattern[0]} to {pattern[1]}: {count} changes")
                
                if spreadsheet_id:
                    sheet_names = st.sidebar.text_area('Sheet Names (comma-separated)', value='Sheet1,Sheet2').split(',')
                    for sheet_name in sheet_names:
                        update_google_sheet(spreadsheet_id, result_df, sheet_name, gcp_credentials=gcp_credentials)
                else:
                    st.error("Please enter a valid Google Spreadsheet ID!")
        else:
            st.error("Please select a base column and columns for comparison from both datasets!")
else:
    st.write("Please enter the required inputs to fetch data.")
