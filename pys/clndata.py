import pandas as pd
import re
import streamlit as st

# Load the extracted data
file_path = 'extracted_data.csv'  # Adjust the path if needed
df = pd.read_csv(file_path)

# Ensure all phone numbers are strings
df['Telephone Number'] = df['Telephone Number'].astype(str)

# Clean phone numbers
def clean_phone_number(phone):
    phone = re.sub(r'\D', '', phone)  # Remove all non-numeric characters
    if len(phone) == 9:
        phone = '0' + phone  # Assuming missing leading 0 for local numbers
    return phone

df['Telephone Number'] = df['Telephone Number'].apply(clean_phone_number)

# Clean dates
def clean_date(date):
    date_formats = ['%d.%m.%Y', '%d.%m.%y', '%d.%m']
    for date_format in date_formats:
        try:
            return pd.to_datetime(date, format=date_format).strftime('%d.%m.%Y')
        except:
            continue
    return date  # Return the original if no format matched

df['Date'] = df['Date'].apply(clean_date)

# Count kit occurrences
family_food_kit_count = df['Family Food Kit'].count()
baby_food_kit_count = df['Baby Food Kit'].count()

# Analysis summary
phone_number_count = df['Telephone Number'].nunique()
date_count = df['Date'].nunique()

# Streamlit App
st.title('Cleaned Distribution List Data')

st.write("### Data Preview")
st.dataframe(df)

st.write("### Analysis Summary")
st.write(f"Total unique phone numbers: {phone_number_count}")
st.write(f"Total unique dates: {date_count}")
st.write(f"Total Family Food Kits: {family_food_kit_count}")
st.write(f"Total Baby Food Kits: {baby_food_kit_count}")

# Upload original scans for comparison
uploaded_files = st.file_uploader("Upload Original Scan Images for Comparison", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)

st.write("### Download Cleaned Data")
csv = df.to_csv(index=False)
st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='cleaned_extracted_data.csv',
    mime='text/csv',
)

if __name__ == "__main__":
    st.write("Running data cleaning and analysis...")
