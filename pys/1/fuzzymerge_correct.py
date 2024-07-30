import streamlit as st
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz, process
import re
import time
from datetime import datetime

# Function to clean and preprocess the columns
def clean_column(col):
    return col.astype(str).str.replace(r'\W', '', regex=True)

# Function to extract numeric patterns and calculate match confidence
def calculate_match_confidence(value, threshold):
    numeric_patterns = re.findall(r'\d+', value)
    confidence = 0
    
    for pattern in numeric_patterns:
        if len(pattern) >= 7:
            confidence = max(confidence, 1.0)
        elif len(pattern) >= 5:
            confidence = max(confidence, 0.9)
        elif len(pattern) >= 4:
            additional_patterns = re.findall(r'\d{2,}', value.replace(pattern, ''))
            if additional_patterns:
                confidence = max(confidence, 0.8)
            else:
                confidence = max(confidence, 0.7)
    
    return confidence >= threshold, confidence

# Function to perform fuzzy matching
def fuzzy_match(row, df, keys, thresholds):
    for _, target_row in df.iterrows():
        confidences = []
        for key, threshold in zip(keys, thresholds):
            is_match, confidence = calculate_match_confidence(target_row[key], threshold)
            if is_match:
                confidences.append(confidence)
            else:
                confidences.append(0)
        
        if all(conf >= threshold for conf, threshold in zip(confidences, thresholds)):
            aggregate_confidence = np.mean(confidences)
            return target_row, aggregate_confidence
    return None, None

st.title("Dataset Merger with Fuzzy Matching")
st.write("Upload the base dataset and the target dataset, select the matching keys and target columns for value transposition.")

# Upload datasets
base_file = st.file_uploader("Upload Base Dataset", type=["csv", "xlsx"])
target_file = st.file_uploader("Upload Target Dataset", type=["csv", "xlsx"])

if base_file and target_file:
    # Read datasets
    base_df = pd.read_csv(base_file) if base_file.name.endswith('.csv') else pd.read_excel(base_file)
    target_df = pd.read_csv(target_file) if target_file.name.endswith('.csv') else pd.read_excel(target_file)

    # Display a random sample of the datasets
    st.write("Preview of Base Dataset (max 500 rows):")
    base_preview = base_df.sample(min(500, len(base_df)))
    st.dataframe(base_preview)

    st.write("Preview of Target Dataset (max 500 rows):")
    target_preview = target_df.sample(min(500, len(target_df)))
    st.dataframe(target_preview)

    # Display columns for selection
    st.write("Select up to three common columns for matching:")
    common_cols = base_df.columns.intersection(target_df.columns).tolist()
    match_cols = st.multiselect("Select Matching Columns", common_cols, default=common_cols[:3])

    # Individual fuzzy matching thresholds
    thresholds = []
    for col in match_cols:
        thresholds.append(st.slider(f"Fuzzy Matching Threshold for {col}", 0.0, 1.0, 0.7))

    # Aggregate confidence threshold
    aggregate_threshold = st.slider("Aggregate Confidence Threshold", 0.0, 1.0, 0.8)

    # Checkbox to work with preview data
    use_preview = st.checkbox("Use preview data for matching and transposition")

    if match_cols:
        # Clean and preprocess columns
        base_df[match_cols] = base_df[match_cols].apply(clean_column)
        target_df[match_cols] = target_df[match_cols].apply(clean_column)
        base_preview[match_cols] = base_preview[match_cols].apply(clean_column)
        target_preview[match_cols] = target_preview[match_cols].apply(clean_column)

        # Select target columns for value transposition
        st.write("Select the target column for value transposition:")
        trans_col_base = st.selectbox("Select Base Dataset Column", base_df.columns)
        trans_col_target = st.selectbox("Select Target Dataset Column", target_df.columns)

        # Perform matching and transposition
        if st.button("Match and Transpose"):
            start_time = datetime.now()

            if use_preview:
                base_data = base_preview
                target_data = target_preview
            else:
                base_data = base_df
                target_data = target_df

            total_base_rows = len(base_data)
            total_target_rows = len(target_data)
            matched_rows = []
            transposed_count = 0
            matched_info = []

            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, base_row in base_data.iterrows():
                matched_row, confidence = fuzzy_match(base_row, target_data, match_cols, thresholds)
                if matched_row is not None and confidence >= aggregate_threshold:
                    target_data.at[matched_row.name, trans_col_target] = base_row[trans_col_base]
                    matched_rows.append(matched_row.name)
                    transposed_count += 1
                    matched_info.append({f"Base_{col}": base_row[col], f"Target_{col}": matched_row[col]} for col in match_cols)

                # Update progress bar and status
                progress_bar.progress(min((i + 1) / total_base_rows, 1.0))
                status_text.text(f"Processed {i + 1} of {total_base_rows} rows")

            end_time = datetime.now()
            elapsed_time = end_time - start_time

            # Create a DataFrame for matched info
            matched_info_df = pd.DataFrame(matched_info)

            # Add matched info columns to the beginning of the target DataFrame
            target_data_with_matches = pd.concat([matched_info_df, target_data.reset_index(drop=True)], axis=1)

            # Summary of matches and transpositions
            match_percentage = (len(matched_rows) / total_target_rows) * 100 if total_target_rows > 0 else 0

            st.write(f"Total base rows: {total_base_rows}")
            st.write(f"Total target rows: {total_target_rows}")
            st.write(f"Total matched rows: {len(matched_rows)}")
            st.write(f"Match percentage: {match_percentage:.2f}%")
            st.write(f"Total values transposed: {transposed_count}")
            st.write(f"Start time: {start_time}")
            st.write(f"End time: {end_time}")
            st.write(f"Elapsed time: {elapsed_time}")

            st.write("Matched rows in target dataset:")
            st.dataframe(target_data.loc[matched_rows])
            st.write("Full Target Dataset after transposition:")
            st.dataframe(target_data_with_matches)

            # Option to download the updated target dataset
            csv = target_data_with_matches.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Updated Target Dataset",
                csv,
                "updated_target_dataset.csv",
                "text/csv",
                key='download-csv'
            )
