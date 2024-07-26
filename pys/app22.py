import json
import numpy as np
import pandas as pd
import streamlit as st

# Function to calculate centroid of a polygon
def calculate_centroid(polygon):
    x_coords = polygon[0::2]
    y_coords = polygon[1::2]
    centroid = [sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)]
    return centroid

# Function to parse JSON and extract data
def parse_json(json_data):
    words = json_data['analyzeResult']['pages'][0]['words']
    extracted_data = {'Name': [], 'Date': [], 'City/Village': [], 'Family Food Kit': [], 'Baby Food Kit': [], 'Telephone Number': []}

    for word in words:
        content = word['content']
        if 'boundingRegions' in word:
            polygon = word['boundingRegions'][0]['polygon']
        elif 'polygon' in word:
            polygon = word['polygon']
        else:
            continue
        centroid = calculate_centroid(polygon)

        # Determine the column based on the X coordinate of the centroid
        if 0 <= centroid[0] <= 2:
            extracted_data['Name'].append(content)
        elif 2 < centroid[0] <= 4:
            extracted_data['Date'].append(content)
        elif 4 < centroid[0] <= 6:
            extracted_data['City/Village'].append(content)
        elif 6 < centroid[0] <= 8:
            extracted_data['Family Food Kit'].append(content)
        elif 8 < centroid[0] <= 10:
            extracted_data['Baby Food Kit'].append(content)
        elif 10 < centroid[0] <= 12:
            extracted_data['Telephone Number'].append(content)
    
    return extracted_data

# Function to format extracted data into a dataframe
def format_extracted_data(extracted_data):
    max_length = max([len(extracted_data[key]) for key in extracted_data.keys()])
    for key in extracted_data.keys():
        while len(extracted_data[key]) < max_length:
            extracted_data[key].append('')
    df = pd.DataFrame(extracted_data)
    return df

# Streamlit App
st.title('Distribution List Data Extraction')

uploaded_files = st.file_uploader("Upload JSON files", type="json", accept_multiple_files=True)

if uploaded_files:
    all_data = {'Name': [], 'Date': [], 'City/Village': [], 'Family Food Kit': [], 'Baby Food Kit': [], 'Telephone Number': []}

    for uploaded_file in uploaded_files:
        json_data = json.load(uploaded_file)
        extracted_data = parse_json(json_data)
        for key in all_data.keys():
            all_data[key].extend(extracted_data[key])
    
    if all_data:
        df = format_extracted_data(all_data)
        st.write("Extracted Data:")
        st.dataframe(df)

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='extracted_data.csv',
            mime='text/csv',
        )
