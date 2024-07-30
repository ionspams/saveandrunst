import streamlit as st
import os
import zipfile

# Function to concatenate files
def concatenate_files_in_folder(folder_path, output_filename):
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".cshtml") or file.endswith(".cs"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(f'// {file_path}\n')
                        outfile.write(infile.read())
                        outfile.write('\n\n')  # Add some space between files

st.title("Dopomoha Code File Concatenator")

# Uploading zip file
uploaded_file = st.file_uploader("Upload a Zip File of Code Folders", type="zip")

if uploaded_file:
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall('temp')
    st.write("Files extracted successfully")

    # Option to select the extracted folder
    extracted_folders = [f for f in os.listdir('temp') if os.path.isdir(os.path.join('temp', f))]
    selected_folder = st.selectbox("Select a Folder", extracted_folders)

    if st.button("Concatenate and Download"):
        folder_path = os.path.join('temp', selected_folder)
        output_filename = f'{selected_folder}_Concatenated.cs'
        concatenate_files_in_folder(folder_path, output_filename)

        # Provide download link
        with open(output_filename, 'rb') as f:
            st.download_button('Download Concatenated File', data=f, file_name=output_filename)
