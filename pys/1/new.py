import streamlit as st
import pandas as pd

# Function to find matches
def find_matches(base, target, common_fields):
    def match_criteria(row1, row2):
        # Extract relevant fields for comparison
        phone1, phone2 = str(row1['base_ContactPhone']), str(row2['target_ContactPhone'])
        exec1, exec2 = row1['base_Executed'], row2['target_Executed']
        
        if len(phone1) < 9 and len(phone2) < 9:
            phone_match = phone1[:3].isdigit() and phone2[:3].isdigit() and phone1[:3] == phone2[:3]
        elif len(phone1) >= 10 and len(phone2) >= 10:
            phone_match = (phone1[:3].isdigit() and phone2[:3].isdigit() and phone1[:3] == phone2[:3]) and any(
                subpart1.isdigit() and subpart2.isdigit() and len(subpart1) >= 4 and len(subpart2) >= 4 and subpart1 == subpart2
                for subpart1 in phone1.split(phone1[:3])[1:] for subpart2 in phone2.split(phone2[:3])[1:]
            )
        else:
            phone_match = False
        
        exec_match = exec1 == exec2
        return phone_match and exec_match

    # Ensure ContactPhone is treated as string
    base['ContactPhone'] = base['ContactPhone'].astype(str)
    target['ContactPhone'] = target['ContactPhone'].astype(str)

    # Create match_key in both datasets
    base['match_key'] = base[common_fields].astype(str).agg('-'.join, axis=1)
    target['match_key'] = target[common_fields].astype(str).agg('-'.join, axis=1)

    st.write("Base dataset with match_key:")
    st.write(base[['match_key'] + common_fields])

    st.write("Target dataset with match_key:")
    st.write(target[['match_key'] + common_fields])

    # Rename columns to ensure uniqueness
    base = base.rename(columns={col: 'base_' + col for col in base.columns})
    target = target.rename(columns={col: 'target_' + col for col in target.columns})

    # Create an empty dataframe for matches
    all_cols = list(base.columns) + list(target.columns) + ['match_key']
    matches = pd.DataFrame(columns=all_cols)

    total_iterations = len(base) * len(target)
    iteration = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    for _, base_row in base.iterrows():
        for _, target_row in target.iterrows():
            if match_criteria(base_row, target_row):
                match = pd.concat([base_row, target_row]).to_frame().T
                match['match_key'] = base_row['base_match_key']
                matches = pd.concat([matches, match], ignore_index=True)

            iteration += 1
            progress_bar.progress(iteration / total_iterations)
            status_text.text(f'Processing: {iteration}/{total_iterations}')

    matches['match'] = matches.apply(lambda row: match_criteria(row, row), axis=1)
    matched_rows = matches[matches['match']]
    
    return matched_rows, matches

# Streamlit app
st.title('Data Analysis and Processing App')

# Step 1: Upload datasets
uploaded_file1 = st.file_uploader("Choose the first dataset (base)", type=["csv", "xlsx"])
uploaded_file2 = st.file_uploader("Choose the second dataset (target)", type=["csv", "xlsx"])

if uploaded_file1 and uploaded_file2:
    if uploaded_file1.name.endswith('.csv'):
        base = pd.read_csv(uploaded_file1)
    else:
        base = pd.read_excel(uploaded_file1)

    if uploaded_file2.name.endswith('.csv'):
        target = pd.read_csv(uploaded_file2)
    else:
        target = pd.read_excel(uploaded_file2)

    st.write("Datasets uploaded successfully!")

    # Preview option
    preview_option = st.checkbox("Use preview mode (random 500 rows from each dataset)")

    if preview_option:
        base = base.sample(n=min(50, len(base)), random_state=1)
        target = target.sample(n=min(50, len(target)), random_state=1)

    common_fields = st.multiselect("Select up to 6 common fields for matching", base.columns, max_selections=6)
    
    if len(common_fields) > 0:
        # Step 3: Perform matching
        matched_rows, matches = find_matches(base, target, common_fields)

        # Step 4: Generate summary and annotated dataset
        st.write("Matched Rows Summary")
        st.write(matched_rows)

        st.download_button(
            label="Download matched dataset",
            data=matches.to_csv(index=False).encode('utf-8'),
            file_name='matched_dataset.csv',
            mime='text/csv',
        )

        # Step 5: Propose merging additional fields
        additional_fields = st.multiselect("Select fields to merge from base to target", base.columns.difference(target.columns))
        
        if st.button("Merge fields"):
            merged = target.merge(matched_rows[additional_fields + ['base_match_key']], on='match_key', how='left')
            st.write("Merged Dataset")
            st.write(merged)
            
            st.download_button(
                label="Download merged dataset",
                data=merged.to_csv(index=False).encode('utf-8'),
                file_name='merged_dataset.csv',
                mime='text/csv',
            )
