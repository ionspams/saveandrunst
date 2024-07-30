import streamlit as st
import pandas as pd
import re

# Streamlit app setup
st.title("Dataset Matching App")

# File upload
base_file = st.file_uploader("Upload the base dataset", type=["csv"])
target_file = st.file_uploader("Upload the target dataset", type=["csv"])

if base_file and target_file:
    # Load the datasets
    base_df = pd.read_csv(base_file, encoding='latin-1')
    target_df = pd.read_csv(target_file)

    # Ensure that ContactPhone and Executed columns are strings and handle NaNs
    base_df['ContactPhone'] = base_df['ContactPhone'].astype(str).fillna('')
    base_df['Executed'] = base_df['Executed'].astype(str).fillna('')
    target_df['ContactPhone'] = target_df['ContactPhone'].astype(str).fillna('')
    target_df['Executed'] = target_df['Executed'].astype(str).fillna('')

    # Define a function to match phone numbers
    def match_phone(phone1, phone2):
        """
        Matches two phone numbers based on the provided logic:
        - The first three numeric characters must match.
        - Another set of minimum four numeric consecutive characters must match, elsewhere in the string.
        """
        if len(phone1) >= 10 and len(phone2) >= 10:
            # Extract first three numeric characters
            numbers_1 = re.findall(r'\d+', phone1)
            numbers_2 = re.findall(r'\d+', phone2)
            if numbers_1 and numbers_2:
                first_three_1 = numbers_1[0][:3]
                first_three_2 = numbers_2[0][:3]
                if first_three_1 == first_three_2:
                    # Find other consecutive numeric characters
                    for i in range(len(phone1) - 4):
                        if phone1[i:i+4] in phone2:
                            return True
        return False

    # Define a function to match dates
    def match_date(date1, date2):
        """
        Matches two dates based on the provided logic:
        - The first three numeric characters must match.
        - At least two other consecutive numeric characters must match.
        """
        if len(date1) < 10 and len(date2) < 10:
            # Extract first three numeric characters
            numbers_1 = re.findall(r'\d+', date1)
            numbers_2 = re.findall(r'\d+', date2)
            if numbers_1 and numbers_2:
                first_three_1 = numbers_1[0][:3]
                first_three_2 = numbers_2[0][:3]
                if first_three_1 == first_three_2:
                    # Find other consecutive numeric characters
                    for i in range(len(date1) - 2):
                        if date1[i:i+2] in date2:
                            return True
        return False

    # Create a dictionary to store the transposed TicketID values
    transposed_data = {}

    # Iterate over the base dataset
    for i in range(len(base_df)):
        phone_base = base_df.ContactPhone.iloc[i]
        executed_base = base_df.Executed.iloc[i]
        ticket_base = base_df.TicketID.iloc[i]

        # Iterate over the target dataset
        for j in range(len(target_df)):
            phone_target = target_df.ContactPhone.iloc[j]
            executed_target = target_df.Executed.iloc[j]
            
            # Match phone numbers and dates
            if (match_phone(phone_base, phone_target) or match_phone(phone_target, phone_base)) and (match_date(executed_base, executed_target) or match_date(executed_target, executed_base)):
                # Store the transposed TicketID value
                transposed_data[(phone_target, executed_target)] = ticket_base

    # Add the transposed TicketID values to the target dataset
    target_df['TicketID'] = target_df.apply(lambda row: transposed_data.get((row.ContactPhone, row.Executed)), axis=1)

    # Display the transposed dataset
    st.write("Transposed Dataset")
    st.dataframe(target_df)

    # Save the transposed dataset
    target_df.to_csv("transposed_dataset.csv", index=False)
    st.success("The transposed dataset has been saved as transposed_dataset.csv")

    # Provide a download link for the transposed dataset
    with open("transposed_dataset.csv", "rb") as file:
        btn = st.download_button(
            label="Download Transposed Dataset",
            data=file,
            file_name="transposed_dataset.csv",
            mime="text/csv"
        )
