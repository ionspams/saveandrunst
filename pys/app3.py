import streamlit as st
import pandas as pd
import json
import re

def is_phone_number(text):
    # Adjust regex for the specific formats of phone numbers you expect
    pattern = re.compile(r'(\+?373|380)?[067]\d{7,9}')
    return pattern.match(text)

def extract_date(words):
    # Match dates, including partial dates and varied formatting within the specified range
    date_pattern = re.compile(r'\b(0?[1-9]|[12][0-9]|3[01])\.(0?[1-9]|1[0-2])\.((2023|2024)|(23|24)?)\b')
    for word in words:
        if date_pattern.match(word['content']):
            return word['content']
    return None

def extract_kits(words):
    # Capture specific kit information based on key terms and proximity within the text
    kit_data = {'Family Food Kit': None, 'Baby Food Kit': None}
    for i, word in enumerate(words):
        lower_content = word['content'].lower()
        if 'family' in lower_content or 'семейный' in lower_content:
            # Assuming quantity or identifier follows directly after the kit description
            if i + 1 < len(words) and words[i + 1]['content'].isdigit():
                kit_data['Family Food Kit'] = words[i + 1]['content']
        if 'baby' in lower_content or 'детского' in lower_content:
            if i + 1 < len(words) and words[i + 1]['content'].isdigit():
                kit_data['Baby Food Kit'] = words[i + 1]['content']
    return kit_data

def extract_data(json_files):
    data_list = []
    for file in json_files:
        json_data = json.load(file)
        pages = json_data.get("analyzeResult", {}).get("pages", [])
        for page in pages:
            words = page.get("words", [])
            for i in range(0, len(words), 20):  # Assuming 20 entries per page, adjust as necessary
                subset_words = words[i:i+20]  # Adjust indexing as necessary based on actual data structure
                date = extract_date(subset_words)
                kits = extract_kits(subset_words)
                phone = None
                for word in subset_words:
                    if is_phone_number(word['content']):
                        phone = word['content']
                        break
                data_list.append({
                    'Row Index': i // 20 + 1,
                    'Date': date,
                    'Family Food Kit': kits['Family Food Kit'],
                    'Baby Food Kit': kits['Baby Food Kit'],
                    'Telephone Number': phone
                })
    return pd.DataFrame(data_list)

st.title('Data Extraction Tool')
uploaded_files = st.file_uploader("Choose JSON files", type="json", accept_multiple_files=True)
if uploaded_files:
    result_df = extract_data(uploaded_files)
    st.write(result_df)
    if not result_df.empty:
        st.download_button("Download Data as CSV", result_df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv", key='download-csv')
    else:
        st.write("No data to display.")
