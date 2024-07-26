import streamlit as st
import pandas as pd

# Path to the CSV file
csv_path = r"C:\apptests\distribution_list.csv"

# Read the CSV file
df = pd.read_csv(csv_path)

# Display the DataFrame
st.title("Distribution List Data")
st.write(df)
