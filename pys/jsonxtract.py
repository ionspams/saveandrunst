import streamlit as st
import pandas as pd
import json

def extract_data_from_json(json_data):
    data = []
    for entry in json_data.get("analyzeResult", {}).get("pages", []):
        for line in entry.get("lines", []):
            if len(line.get("words", [])) >= 5:
                row = {
                    "Row": line["words"][0]["text"],
                    "Date": line["words"][1]["text"],
                    "Family Food Kit": line["words"][2]["text"],
                    "Baby Food Kit": line["words"][3]["text"],
                    "Telephone Number": line["words"][4]["text"]
                }
                data.append(row)
    return pd.DataFrame(data)

st.title('Data Extraction Tool')

uploaded_file = st.file_uploader("Choose a JSON file", type="json")
if uploaded_file is not None:
    json_data = json.load(uploaded_file)
    df = extract_data_from_json(json_data)
    st.write(df)
    st.download_button("Download Data as CSV", df.to_csv(index=False).encode('utf-8'), "data.csv", "text/csv", key='download-csv')
