import streamlit as st
import requests
import tempfile
import subprocess
import os

def install_dependencies(requirements_url):
    try:
        response = requests.get(requirements_url)
        response.raise_for_status()
        
        requirements = response.text.splitlines()
        
        # Remove built-in modules from the requirements
        filtered_requirements = [req for req in requirements if req != 'subprocess']
        
        if filtered_requirements:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
                tmp_file.write("\n".join(filtered_requirements).encode())
                tmp_file_path = tmp_file.name
            
            subprocess.run(["pip", "install", "-r", tmp_file_path])
            os.remove(tmp_file_path)
    except Exception as e:
        st.error(f"Failed to install dependencies: {e}")

def fetch_and_run_script(github_url):
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
        
        # Read the content of the temporary file
        with open(tmp_file_path, 'r') as file:
            script_content = file.read()
        
        # Clean up the temporary file
        os.remove(tmp_file_path)
        
        # Execute the script content
        exec(script_content, globals())
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
        fetch_and_run_script(github_url)
    else:
        st.error("Please enter a valid GitHub URL.")
