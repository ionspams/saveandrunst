import streamlit as st
import pandas as pd
from io import StringIO

def merge_datasets(source_df, target_df, common_cols, transpose_cols):
    """Merges two datasets based on matching logic and transposes data.

    Args:
        source_df (pd.DataFrame): Source dataset containing data to transpose.
        target_df (pd.DataFrame): Target dataset to merge with.
        common_cols (list): List of common column names for matching.
        transpose_cols (list): List of columns to transpose from source to target.

    Returns:
        pd.DataFrame: Merged dataset with transposed data.
    """

    merged_df = target_df.copy()  # Start with a copy of the target DataFrame

    for index, row in target_df.iterrows():
        matches = []
        for src_index, src_row in source_df.iterrows():
            match = True
            for col in common_cols:
                if col in transpose_cols:
                    if len(str(src_row[col])) >= 10:
                        if not (str(src_row[col])[:3] == str(row[col])[:3] and any([
                            str(src_row[col])[i:i + 4] == str(row[col])[j:j + 4] 
                            for i in range(len(str(src_row[col]))) 
                            for j in range(len(str(row[col])))
                        ])):
                            match = False
                            break
                    else:
                        if not (str(src_row[col])[:3] == str(row[col])[:3] and any([
                            str(src_row[col])[i:i + 2] == str(row[col])[j:j + 2]
                            for i in range(len(str(src_row[col]))) 
                            for j in range(len(str(row[col])))
                        ])):
                            match = False
                            break
                else:
                    if src_row[col] != row[col]:
                        match = False
                        break
            if match:
                matches.append(src_row)

        if matches:
            for col in transpose_cols:
                if col in matches[0].keys():
                    merged_df.loc[index, col] = matches[0][col]  # Assign transposed values to the target row

    return merged_df

def main():
    """Streamlit app to merge datasets."""
    st.title("Dataset Merging and Transposition")

    # Upload source and target datasets
    source_file = st.file_uploader("Upload Source Dataset", type=["csv", "xlsx"])
    target_file = st.file_uploader("Upload Target Dataset", type=["csv", "xlsx"])

    if source_file and target_file:
        # Read datasets
        try:
            source_df = pd.read_csv(source_file)
        except:
            source_df = pd.read_excel(source_file)
        try:
            target_df = pd.read_csv(target_file)
        except:
            target_df = pd.read_excel(target_file)

        # Select common columns
        st.subheader("Select Common Columns:")
        common_cols = st.multiselect("Common Columns", source_df.columns, default=None)

        # Select columns to transpose
        st.subheader("Select Columns to Transpose:")
        transpose_cols = st.multiselect("Transpose Columns", source_df.columns, default=None)

        # Merge datasets and transpose data
        merged_df = merge_datasets(source_df, target_df, common_cols, transpose_cols)

        # Display merged dataset
        st.subheader("Merged Dataset:")
        st.dataframe(merged_df)

        # Download merged dataset
        csv = merged_df.to_csv(index=False)
        st.download_button(
            label="Download Merged Dataset as CSV",
            data=csv,
            file_name="merged_dataset.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()