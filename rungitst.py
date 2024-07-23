import streamlit as st
import requests
import tempfile
import subprocess
import os
from github import Github

# Initialize GitHub API (you may need a token for private repos)
gh = Github()

def fetch_repo_structure(repo_url):
    try:
        # Extract user and repo name from the URL
        user_repo = repo_url.replace('https://github.com/', '').split('/')[0:2]
        repo_name = '/'.join(user_repo)
        
        # Get the repository
        repo = gh.get_repo(repo_name)
        
        # Fetch the directory structure
        contents = repo.get_contents("")
        return contents, repo_name
    except Exception as e:
        st.error(f"Failed to fetch repository structure: {e}")
        return None, None

def display_folder_contents(contents, repo_name):
    py_files = []
    folders = []
    
    for content_file in contents:
        if content_file.type == "dir":
            folders.append(content_file.path)
        elif content_file.name.endswith(".py"):
            py_files.append(content_file.path)
    
    selected_folder = st.selectbox("Select a folder:", [""] + folders)
    if selected_folder:
        sub_contents = repo.get_contents(selected_folder)
        for sub_content in sub_contents:
            if sub_content.name.endswith(".py"):
                py_files.append(sub_content.path)
    
    selected_file = st.selectbox("Select a .py file to run:", [""] + py_files)
    return selected_file

def install_dependencies(repo_name, file_path):
    try:
        # Fetch the raw content of the requirements.txt file
        base_url = f"https://raw.githubusercontent.com/{repo_name}/main/{os.path.dirname(file_path)}"
        requirements_url = f"{base_url}/requirements.txt"
        response = requests.get(requirements_url)
        
        if response.status_code == 200:
            requirements = response.text.splitlines()
            filtered_requirements = [req for req in requirements if req.strip() and 'subprocess' not in req.lower()]
            
            if filtered_requirements:
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
                    tmp_file.write("\n".join(filtered_requirements).encode())
                    tmp_file_path = tmp_file.name
                
                try:
                    subprocess.run(["pip", "install", "-r", tmp_file_path], check=True)
                except subprocess.CalledProcessError as e:
                    st.error(f"Failed to install dependencies from requirements.txt: {e}")
                    st.error("Ensure the system-level dependencies are installed.")
                
                os.remove(tmp_file_path)
    except Exception as e:
        st.error(f"Failed to install dependencies: {e}")

def fetch_and_run_script(repo_name, file_path):
    try:
        # Fetch the raw content of the script
        raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{file_path}"
        response = requests.get(raw_url)
        response.raise_for_status()
        
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
1. Enter the GitHub URL of the repository you want to run.
2. Select the folder and .py file you want to run.
3. Click "Run App" to execute the app.
""")
repo_url = st.text_input("Enter GitHub URL to repository:")

if repo_url:
    contents, repo_name = fetch_repo_structure(repo_url)
    if contents:
        selected_file = display_folder_contents(contents, repo_name)
        if selected_file and st.button("Run App"):
            install_dependencies(repo_name, selected_file)
            fetch_and_run_script(repo_name, selected_file)
