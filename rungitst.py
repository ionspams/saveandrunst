import streamlit as st
import requests
import tempfile
import importlib.util
import os
import subprocess

def install_dependencies(requirements_url):
    try:
        response = requests.get(requirements_url)
        response.raise_for_status()
        
        requirements = response.text.splitlines()
        
        for requirement in requirements:
            subprocess.run(["pip", "install", requirement])
    except Exception as e:
        st.error(f"Failed to install dependencies: {e}")

def fetch_and_import_script(github_url):
    try:
        # Extract the base URL and file path
        base_url = github_url.rsplit('/', 1)[0]
        raw_base_url = base_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        raw_url = github_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        # Fetch the raw content of the script
        response = requests.get(raw_url)
        response.raise_for_status()
        
        # Check for a requirements.txt file in the same directory
        requirements_url = os.path.join(raw_base_url, 'requirements.txt')
        requirements_response = requests.get(requirements_url)
        if requirements_response.status_code == 200:
            install_dependencies(requirements_url)
        
        # Create a temporary Python file with the fetched script
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        
        # Import the script as a module
        spec = importlib.util.spec_from_file_location("dynamic_module", tmp_file_path)
        dynamic_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dynamic_module)
        
        # Clean up the temporary file
        os.remove(tmp_file_path)
    except Exception as e:
        st.error(f"Failed to fetch or run the script: {e}")

st.title("Dynamic Streamlit App Runner")
st.markdown("""
### Instructions
1. Enter the GitHub URL of the Streamlit app you want to run.
2. Click "Run App" to execute the app.
""")
github_url = st.text_input("Enter GitHub URL to Streamlit App:")
if st.button("Run App"):
    if github_url:
        fetch_and_import_script(github_url)
    else:
        st.error("Please enter a valid GitHub URL.")