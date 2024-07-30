import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Set up Google Sheets API
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("docstreamerAPI.json", scope)
    client = gspread.authorize(creds)
    return client

# Function to make column names unique
def make_unique(column_names):
    seen = set()
    result = []
    for col in column_names:
        if col in seen:
            count = 1
            new_col = f"{col}_{count}"
            while new_col in seen:
                count += 1
                new_col = f"{col}_{count}"
            seen.add(new_col)
            result.append(new_col)
        else:
            seen.add(col)
            result.append(col)
    return result

# Main Streamlit app
def main():
    st.title("Expenditure Data Entry and Visualization")

    client = setup_google_sheets()
    spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1yBMRHY_DitVqrMIU73nRvUsMOqYtHmtEOuHXafSMMHc/")

    st.write("## Available Sheets")
    sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
    selected_sheet = st.selectbox("Select a sheet to visualize and edit", sheet_names)
    worksheet = spreadsheet.worksheet(selected_sheet)

    # Check if the selected sheet name contains "Reporting"
    if "Reporting" in selected_sheet:
        st.write(f"### Viewing Sheet: {selected_sheet}")
        data = worksheet.get_all_values()
        headers = make_unique(data[0])  # Ensure unique column names
        df = pd.DataFrame(data[1:], columns=headers)
        st.dataframe(df)

        st.write("### Select Cell and Enter Data")
        row = st.number_input("Row", min_value=1, step=1)
        col = st.text_input("Column (e.g., A, B, C, ...)")
        value = st.text_input("Value")

        if st.button("Submit"):
            cell = f'{col}{row}'
            worksheet.update(cell, value)
            st.success(f"Data written to cell {cell} successfully!")
    else:
        st.write("### This sheet is not editable.")

if __name__ == "__main__":
    main()
