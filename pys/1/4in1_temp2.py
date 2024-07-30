import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title='Dataset Cleaning and Unification Tool', layout='wide')

# Sidebar for navigation
st.sidebar.header('Navigation')
workflow = st.sidebar.selectbox('Choose workflow', ['Concatenate Datasets', 'Arrange & Clean Data', 'Analyze & Normalize', 'Correct Data'])

# Load datasets function with encoding and parsing error handling
def load_datasets(uploaded_files):
    datasets = []
    for file in uploaded_files:
        try:
            datasets.append(pd.read_csv(file, on_bad_lines='skip'))
        except UnicodeDecodeError:
            try:
                datasets.append(pd.read_csv(file, encoding='latin1', on_bad_lines='skip'))
            except Exception as e:
                st.error(f"Failed to read {file.name}: {e}")
    return datasets

# Concatenate datasets function
def concatenate_datasets(datasets):
    if not datasets:
        return None
    concatenated_df = pd.concat(datasets, ignore_index=True)
    return concatenated_df

# Remove characters from columns function
def remove_characters_from_columns(df, columns, chars, replacements):
    for col in columns:
        for char, replacement in zip(chars.split('|'), replacements.split('|')):
            df[col] = df[col].astype(str).str.replace(char, replacement)
    return df

# Normalize phone numbers function
def normalize_phone_numbers(df, columns, country_code):
    for col in columns:
        df[col] = df[col].astype(str).str.replace(r'\D', '', regex=True)
        df[col] = df[col].apply(lambda x: f"{country_code}{x[-8:]}" if len(x) >= 8 else x)
    return df

# Normalize dates function
def normalize_dates(df, columns, date_format):
    for col in columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime(date_format)
    return df

# Function to check for consecutive matching numeric characters
def has_consecutive_numeric_match(s1, s2, min_match_length):
    s1, s2 = ''.join(filter(str.isdigit, str(s1))), ''.join(filter(str.isdigit, str(s2)))
    for i in range(len(s1) - min_match_length + 1):
        substr = s1[i:i + min_match_length]
        if substr in s2:
            return True
    return False

# Refined function to merge datasets based on common fields and transpose additional fields
def merge_datasets(base_df, target_df, common_fields, additional_fields):
    # Convert common fields to string type in both dataframes
    for field in common_fields:
        base_df[field] = base_df[field].astype(str)
        target_df[field] = target_df[field].astype(str)

    # Initialize counters for summary
    exact_match_count = 0
    successful_transpose_count = 0
    total_values_transposed = 0

    # Initialize merged dataframe
    merged_df = target_df.copy()

    for index, target_row in target_df.iterrows():
        # Identify matching base rows
        matching_base_rows = base_df.copy()
        for field in common_fields:
            if field.lower() == 'contactphone':
                matching_base_rows = matching_base_rows[matching_base_rows[field].apply(
                    lambda x: x[:3] == target_row[field][:3] and has_consecutive_numeric_match(x[3:], target_row[field][3:], 4))]
            elif field.lower() == 'executed':
                matching_base_rows = matching_base_rows[matching_base_rows[field].apply(
                    lambda x: has_consecutive_numeric_match(x, target_row[field], 2))]
            else:
                matching_base_rows = matching_base_rows[matching_base_rows[field] == target_row[field]]

        if len(matching_base_rows) == 1:
            exact_match_count += 1
            matching_base_row = matching_base_rows.iloc[0]  # Select the first matching base row
            for field in additional_fields:
                merged_df.at[index, field] = matching_base_row[field]
                successful_transpose_count += 1
                total_values_transposed += 1

    summary = {
        "Exact Matches": exact_match_count,
        "Successful Row Transposes": successful_transpose_count,
        "Values Transposed": total_values_transposed
    }

    return merged_df, summary

# Main workflow
if workflow == 'Concatenate Datasets':
    st.header("Concatenate and Merge Datasets")
    base_file = st.file_uploader("Upload Base Dataset CSV", type=["csv"])
    target_file = st.file_uploader("Upload Target Dataset CSV", type=["csv"])

    if base_file and target_file:
        try:
            base_df = pd.read_csv(base_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            base_df = pd.read_csv(base_file, encoding='latin1', on_bad_lines='skip')
        
        try:
            target_df = pd.read_csv(target_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            target_df = pd.read_csv(target_file, encoding='latin1', on_bad_lines='skip')
        
        st.write("Base dataset:")
        st.dataframe(base_df)
        
        st.write("Target dataset:")
        st.dataframe(target_df)
        
        common_fields = st.multiselect("Select common fields to merge on (up to 6)", base_df.columns.tolist(), max_selections=6)
        additional_fields = st.multiselect("Select additional fields to transpose (up to 20)", base_df.columns.tolist(), max_selections=20)

        if st.button("Merge Datasets"):
            if common_fields and additional_fields:
                merged_df, summary = merge_datasets(base_df, target_df, common_fields, additional_fields)
                st.write("Merged Dataset:")
                st.dataframe(merged_df)
                st.download_button(label="Download Merged Dataset", data=merged_df.to_csv(index=False), file_name='merged_dataset.csv', mime='text/csv')

                st.write("Summary:")
                st.write(f"Exact Matches: {summary['Exact Matches']}")
                st.write(f"Successful Row Transposes: {summary['Successful Row Transposes']}")
                st.write(f"Values Transposed: {summary['Values Transposed']}")
            else:
                st.error("Please select both common fields and additional fields to transpose.")

elif workflow == 'Arrange & Clean Data':
    st.header("Arrange & Clean Data by Removing or Replacing Specific Characters")
    uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='latin1', on_bad_lines='skip')

        columns = df.columns.tolist()

        # Stage 1: Rearrange Columns
        st.subheader("Rearrange Columns")
        col_order = st.multiselect("Reorder columns", columns, default=columns)
        
        if st.button("Rearrange Columns"):
            df = df[col_order]
            st.write("Reordered Dataset:")
            st.dataframe(df)
            st.download_button(label="Download Reordered Dataset", data=df.to_csv(index=False), file_name='reordered_dataset.csv', mime='text/csv')

        # Stage 2: Clean Data
        st.subheader("Clean Data")
        selected_columns = st.multiselect("Select columns to clean", columns)
        chars_to_remove = st.text_input("Characters to remove (e.g., , | .)")
        replacements = st.text_input("Replacements (e.g., | #)")

        if st.button("Clean Data"):
            cleaned_df = remove_characters_from_columns(df, selected_columns, chars_to_remove, replacements)
            st.write("Cleaned Dataset:")
            st.dataframe(cleaned_df)
            st.download_button(label="Download Cleaned Dataset", data=cleaned_df.to_csv(index=False), file_name='cleaned_dataset.csv', mime='text/csv')

        # Stage 3: Normalize Phone Numbers
        st.subheader("Normalize Phone Numbers")
        phone_columns = st.multiselect("Select phone number columns", columns)
        country_code = st.selectbox("Select country code", ['373', '380', '40'])  # Moldova, Ukraine, Romania

        if st.button("Normalize Phone Numbers"):
            normalized_df = normalize_phone_numbers(df, phone_columns, country_code)
            st.write("Normalized Phone Numbers:")
            st.dataframe(normalized_df)
            st.download_button(label="Download Normalized Dataset", data=normalized_df.to_csv(index=False), file_name='normalized_dataset.csv', mime='text/csv')

        # Stage 4: Normalize Dates
        st.subheader("Normalize Dates")
        date_columns = st.multiselect("Select date columns", columns)
        date_format = st.selectbox("Select date format", [
            '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%d/%m/%Y', '%m/%d/%Y',
            '%Y/%m/%d', '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d',
            '%d %b %Y', '%d %B %Y'
        ])

        if st.button("Normalize Dates"):
            normalized_dates_df = normalize_dates(df, date_columns, date_format)
            st.write("Normalized Dates:")
            st.dataframe(normalized_dates_df)
            st.download_button(label="Download Normalized Dates Dataset", data=normalized_dates_df.to_csv(index=False), file_name='normalized_dates_dataset.csv', mime='text/csv')

        # Stage 5: Format Dataset as Text
        st.subheader("Format Entire Dataset as Text")
        if st.button("Format Dataset as Text"):
            formatted_text_df = df.applymap(str)
            st.write("Formatted Dataset:")
            st.dataframe(formatted_text_df)
            st.download_button(label="Download Formatted Text Dataset", data=formatted_text_df.to_csv(index=False), file_name='formatted_text_dataset.csv', mime='text/csv')

elif workflow == 'Analyze & Normalize':
    st.header("Analyze & Normalize Data")
    base_file = st.file_uploader("Upload Base Truth CSV", type=["csv"])
    target_file = st.file_uploader("Upload Target CSV", type=["csv"])

    if base_file and target_file:
        try:
            base_df = pd.read_csv(base_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            base_df = pd.read_csv(base_file, encoding='latin1', on_bad_lines='skip')
        
        try:
            target_df = pd.read_csv(target_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            target_df = pd.read_csv(target_file, encoding='latin1', on_bad_lines='skip')
        
        # Display dataframes for verification
        st.write("Base dataset:")
        st.dataframe(base_df)
        
        st.write("Target dataset:")
        st.dataframe(target_df)
        
        # Select columns
        reference_col = st.selectbox("Select reference base column", base_df.columns.tolist())
        target_col = st.selectbox("Select target column for analysis", target_df.columns.tolist())
        base_cols = st.multiselect("Select base columns for matching", base_df.columns.tolist(), max_selections=3)

        if st.button("Analyze Data"):
            # Estimate time for analysis
            est_time = (len(base_df) * len(target_df) / 50000) * 2  # Estimate based on dataset size
            st.write(f"Estimated time for analysis: {est_time:.2f} seconds")

            progress_bar = st.progress(0)
            annotated_df, match_summary, deviation_summary = analyze_normalize(base_df, target_df, base_cols, reference_col, target_col, progress_bar)
            st.write("Match Summary:")
            st.write(match_summary)
            st.write("Deviation Summary:")
            st.dataframe(deviation_summary)
            st.write("Annotated Data:")
            st.dataframe(annotated_df)
            st.download_button(label="Download Annotated Data", data=annotated_df.to_csv(index=False), file_name='annotated_data.csv', mime='text/csv')

elif workflow == 'Correct Data':
    st.header("Correct Dataset Using Base Truth")
    base_file = st.file_uploader("Upload Base Truth CSV", type=["csv"])
    target_file = st.file_uploader("Upload Target CSV", type=["csv"])

    if base_file and target_file:
        try:
            base_df = pd.read_csv(base_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            base_df = pd.read_csv(base_file, encoding='latin1', on_bad_lines='skip')
        
        try:
            target_df = pd.read_csv(target_file, on_bad_lines='skip')
        except UnicodeDecodeError:
            target_df = pd.read_csv(target_file, encoding='latin1', on_bad_lines='skip')
        
        st.write("Base dataset columns:")
        st.dataframe(base_df)
        
        st.write("Target dataset columns:")
        st.write(target_df.columns.tolist())
        
        columns = target_df.columns.tolist()
        base_columns = st.multiselect("Select base columns for matching", columns, max_selections=3)
        check_columns = st.multiselect("Select columns to check for correction", columns)
        
        if base_columns and check_columns:
            if st.button("Correct Dataset"):
                try:
                    corrected_df, summary = correct_dataset(base_df, target_df, base_columns, check_columns)
                    st.write("Corrected Dataset:")
                    st.dataframe(corrected_df)
                    st.download_button(label="Download Corrected Dataset", data=corrected_df.to_csv(index=False), file_name='corrected_dataset.csv', mime='text/csv')
                    
                    st.write("Summary of Corrections:")
                    for key, value in summary.items():
                        st.write(f"{key}: {value}")
                except KeyError as e:
                    st.error(e)
        else:
            st.error("Please select base columns and columns to check for correction.")

