import streamlit as st
import pandas as pd
import json
import re

def extract_structured_data(uploaded_files):
    all_data = []
    date_pattern = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")
    phone_pattern = re.compile(r"((373|380)?0?[67]\d{6,7})")
    
    for uploaded_file in uploaded_files:
        json_data = json.load(uploaded_file)
        pages = json_data.get("analyzeResult", {}).get("pages", [])

        for page in pages:
            words = page.get("words", [])
            entries = []
            for word in words:
                polygon = word.get('polygon', [])
                if len(polygon) % 2 == 0:  # Expecting even number of elements
                    # Assume it's a flat list: [x1, y1, x2, y2, ...]
                    x_vals = [polygon[i] for i in range(0, len(polygon), 2)]
                    y_vals = [polygon[i] for i in range(1, len(polygon), 2)]
                    centroid_x = sum(x_vals) / len(x_vals)
                    centroid_y = sum(y_vals) / len(y_vals)
                    entries.append({
                        'content': word['content'].strip(),
                        'centroid': (centroid_x, centroid_y)
                    })

            entries.sort(key=lambda e: (e['centroid'][1], e['centroid'][0]))

            current_row = {}
            last_y = 0

            for entry in entries:
                content = entry['content']
                x, y = entry['centroid']

                if y - last_y > 15:  # Detecting new lines
                    if current_row:
                        all_data.append(current_row)
                    current_row = {}
                    last_y = y

                if re.match(date_pattern, content):
                    current_row['Date'] = content
                elif re.match(phone_pattern, content):
                    current_row['Telephone Number'] = content
                elif "Family" in content or "Kit" in content:
                    kit_type = 'Family Food Kit' if 'Family' in content else 'Baby Food Kit'
                    quantity = re.search(r'\b\d+\b', content)
                    if quantity:
                        current_row[kit_type] = quantity.group()
                elif content.isalpha():  # Assume it's a name if all alphabetic
                    current_row['Name Surname'] = content

            if current_row:  # Ensure the last row is added
                all_data.append(current_row)

    return pd.DataFrame(all_data)

st.title('Enhanced Data Extraction Tool')
uploaded_files = st.file_uploader("Choose JSON files", type="json", accept_multiple_files=True)

if uploaded_files:
    data_frame = extract_structured_data(uploaded_files)
    st.write(data_frame)
    if not data_frame.empty:
        st.download_button("Download Data as CSV", data_frame.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv", key='download-csv')
    else:
        st.write("No data to display.")
