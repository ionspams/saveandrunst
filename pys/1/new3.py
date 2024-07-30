import streamlit as st
import pandas as pd

# Function to generate match keys based on the criteria
def generate_match_key(df):
    def create_key(row):
        contact_phone = str(row['ContactPhone'])
        executed = str(row['Executed'])
        if len(contact_phone) < 9:
            phone_key = contact_phone[:3]
        else:
            phone_key = contact_phone[:3] + '-' + contact_phone[3:]
        return phone_key + '-' + executed

    df['match_key'] = df.apply(create_key, axis=1)
    return df

# Function to find matches
def find_matches(base, target, common_fields):
    def match_criteria(row1, row2):
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

    base['ContactPhone'] = base['ContactPhone'].astype(str)
    target['ContactPhone'] = target['ContactPhone'].astype(str)

    base = generate_match_key(base)
    target = generate_match_key(target)

    st.write("Base dataset with match_key:")
    st.write(base[['match_key'] + common_fields])

    st.write("Target dataset with match_key:")
    st.write(target[['match_key'] + common_fields])

    base = base.rename(columns={col: 'base_' + col for col in base.columns})
    target = target.rename(columns={col: 'target_' + col for col in target.columns})

    all_cols = list(base.columns) + list(target.columns)
    matches = pd.DataFrame(columns=all_cols)

    total_iterations = len(base) * len(target)
    iteration = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    for _, base_row in base.iterrows():
        for _, target_row in target.iterrows():
            if match_criteria(base_row, target_row):
                match = pd.concat([base_row, target_row]).to_frame().T
                matches = pd.concat([matches, match], ignore_index=True)

            iteration += 1
            progress_bar.progress(iteration / total_iterations)
            status_text.text(f'Processing: {iteration}/{total_iterations}')

    matches['is_exact_match'] = matches.apply(lambda row: match_criteria(row, row), axis=1)
    matched_rows = matches[matches['is_exact_match']]
    
    total_base_rows = len(base)
    total_target_rows = len(target)
    total_matches = len(matches)
    total_exact_matches = len(matched_rows)
    unmatched_base = base[~base['base_match_key'].isin(matches['base_match_key'].unique())]
    unmatched_target = target[~target['target_match_key'].isin(matches['target_match_key'].unique())]

    st.write(f"Total rows in base dataset: {total_base_rows}")
    st.write(f"Total rows in target dataset: {total_target_rows}")
    st.write(f"Total matched rows: {total_matches}")
    st.write(f"Total exact matched rows: {total_exact_matches}")
    st.write(f"Unmatched rows in base dataset: {len(unmatched_base)}")
    st.write(f"Unmatched rows in target dataset: {len(unmatched_target)}")

    return matched_rows, matches, unmatched_base, unmatched_target

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
    preview_option = st.checkbox("Use preview mode (random 50 rows from each dataset)")

    if preview_option:
        base = base.sample(n=min(50, len(base)), random_state=1)
        target = target.sample(n=min(50, len(target)), random_state=1)

    common_fields = st.multiselect("Select up to 6 common fields for matching", base.columns, max_selections=6)
    
    if len(common_fields) > 0:
        # Step 3: Perform matching
        matched_rows, matches, unmatched_base, unmatched_target = find_matches(base, target, common_fields)

        # Step 4: Generate summary and annotated dataset
        st.write("Matched Rows Summary")
        st.write(matched_rows)

        st.download_button(
            label="Download matched dataset",
            data=matches.to_csv(index=False).encode('utf-8'),
            file_name='matched_dataset.csv',
            mime='text/csv',
        )

        st.download_button(
            label="Download exact matched dataset",
            data=matched_rows.to_csv(index=False).encode('utf-8'),
            file_name='exact_matched_dataset.csv',
            mime='text/csv',
        )

        # Provide unmatched rows for validation
        st.write("Unmatched Rows in Base Dataset")
        st.write(unmatched_base)
        
        st.write("Unmatched Rows in Target Dataset")
        st.write(unmatched_target)

        st.download_button(
            label="Download unmatched rows from base dataset",
            data=unmatched_base.to_csv(index=False).encode('utf-8'),
            file_name='unmatched_base_dataset.csv',
            mime='text/csv',
        )
        
        st.download_button(
            label="Download unmatched rows from target dataset",
            data=unmatched_target.to_csv(index=False).encode('utf-8'),
            file_name='unmatched_target_dataset.csv',
            mime='text/csv',
        )

        # Step 5: Propose merging additional fields
        additional_fields = st.multiselect("Select fields to merge from base to target", [col for col in base.columns if col.startswith('base_')])
        
        if st.button("Merge fields"):
            merged = target.merge(matched_rows[[col for col in additional_fields + ['base_match_key'] if col in matched_rows.columns]], on='base_match_key', how='left')
            st.write("Merged Dataset")
            st.write(merged)
            
            st.download_button(
                label="Download merged dataset",
                data=merged.to_csv(index=False).encode('utf-8'),
                file_name='merged_dataset.csv',
                mime='text/csv',
            )
