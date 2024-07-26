import streamlit as st
import pandas as pd
import requests
from io import StringIO
import base64

# URLs of the public Google Sheets as CSVs
sheet_urls = {
    "Sheet1": "https://docs.google.com/spreadsheets/d/1yBMRHY_DitVqrMIU73nRvUsMOqYtHmtEOuHXafSMMHc/export?format=csv&gid=0",
    "Sheet2": "https://docs.google.com/spreadsheets/d/1yBMRHY_DitVqrMIU73nRvUsMOqYtHmtEOuHXafSMMHc/export?format=csv&gid=123456789",
    "Sheet3": "https://docs.google.com/spreadsheets/d/1yBMRHY_DitVqrMIU73nRvUsMOqYtHmtEOuHXafSMMHc/export?format=csv&gid=987654321",
    "Sheet4": "https://docs.google.com/spreadsheets/d/1yBMRHY_DitVqrMIU73nRvUsMOqYtHmtEOuHXafSMMHc/export?format=csv&gid=1122334455"
}

# Function to read a Google Sheet
def load_data(sheet_url):
    response = requests.get(sheet_url)
    data = StringIO(response.text)
    df = pd.read_csv(data)
    return df

# Function to update the Google Sheet (here we'll just simulate the update)
def update_sheet(df, new_row):
    df = df.append(new_row, ignore_index=True)
    return df

# Function to upload file and return the URL
def upload_file(file):
    file_details = {"filename": file.name, "filetype": file.type, "filesize": file.size}
    file_data = file.getvalue()
    encoded = base64.b64encode(file_data).decode()
    url = f"data:{file.type};base64,{encoded}"
    return url

# Main Streamlit app
def main():
    st.title("Expenditure Data Entry and Visualization")

    st.write("## Available Sheets")
    selected_sheet = st.selectbox("Select a sheet to visualize and edit", list(sheet_urls.keys()))
    sheet_url = sheet_urls[selected_sheet]
    df = load_data(sheet_url)
    
    st.write(f"### Viewing Sheet: {selected_sheet}")
    st.dataframe(df)

    st.write("### Enter Expenditure Data")
    date = st.date_input("Date")
    category = st.selectbox("Category", ["Travel", "Food", "Supplies", "Miscellaneous"])
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    description = st.text_area("Description")
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "jpg", "jpeg", "png"])

    if st.button("Submit"):
        if uploaded_file is not None:
            file_url = upload_file(uploaded_file)
            new_row = {"Date": str(date), "Category": category, "Amount": amount, "Description": description, "Document URL": file_url}
            updated_df = update_sheet(df, new_row)
            st.success("Data submitted successfully!")
            st.write("Updated Data")
            st.dataframe(updated_df)
            csv = updated_df.to_csv(index=False).encode()
            b64 = base64.b64encode(csv).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="updated_{selected_sheet}.csv">Download updated CSV file</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("Please upload a document")

if __name__ == "__main__":
    main()
