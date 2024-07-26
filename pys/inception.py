import streamlit as st
import requests
import tempfile
import subprocess

def fetch_and_run_script(github_url):
    try:
        # Extract raw URL from GitHub URL
        raw_url = github_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        
        # Fetch the raw content
        response = requests.get(raw_url)
        response.raise_for_status()
        
        # Create a temporary Python file with the fetched script
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        
        # Run the script using streamlit run in a subprocess
        subprocess.run(["streamlit", "run", tmp_file_path])
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