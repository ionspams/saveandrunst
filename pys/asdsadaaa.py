import streamlit as st
import subprocess
import sys
import io
import contextlib
import os
import tempfile
import pkgutil
from PIL import Image, ImageDraw

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        st.error(f"Error installing package {package}: {e}")
        raise

def save_code_and_run_with_dependencies(code_input, directory, file_name):
    try:
        # Ensure the file name has a .py extension
        if not file_name.endswith(".py"):
            file_name += ".py"

        # Save the code input to a .py file
        script_path = os.path.join(directory, file_name)
        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(code_input)
        
        # Run the script with dependencies
        venv_path = os.path.join(directory, "venv")
        if not os.path.exists(venv_path):
            subprocess.check_call([sys.executable, "-m", "venv", "venv"], cwd=directory)
        
        activate_script = os.path.join(venv_path, "Scripts", "activate") if os.name == 'nt' else os.path.join(venv_path, "bin", "activate")

        with open(script_path, 'r', encoding='utf-8') as file:
            code_content = file.read()

        import_lines = [line for line in code_content.split('\n') if line.startswith('import ') or line.startswith('from ')]
        required_packages = set()
        for line in import_lines:
            parts = line.split()
            if parts[0] == "import":
                package_name = parts[1]
            elif parts[0] == "from":
                package_name = parts[1]
            if "." in package_name:
                package_name = package_name.split(".")[0]
            if not pkgutil.find_loader(package_name):
                required_packages.add(package_name)

        installed_packages = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True).split('\n')
        installed_packages = {pkg.split('==')[0] for pkg in installed_packages}

        for package in required_packages:
            if package not in installed_packages:
                install_package(package)

        if os.name == 'nt':
            command = f'{activate_script} & streamlit run {script_path}'
        else:
            command = f'source {activate_script} && streamlit run {script_path}'

        st.write(f"Running command: {command}")

        result = subprocess.Popen(command, shell=True, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        if out:
            st.text_area("Command Output", out.decode('utf-8'))
        if err:
            st.text_area("Command Error", err.decode('utf-8'))

        st.success(f"Running Streamlit app: {script_path}")
    except Exception as e:
        st.error(f"Error while saving and running the script: {e}")

def main():
    st.title("Streamlit App Code Runner and File Editor")

    # Navigation
    option = st.sidebar.selectbox(
        "Choose an option",
        ["Save & Run Streamlit Code", "Edit Local Files", "Run Existing Script with Dependencies"]
    )

    if option == "Save & Run Streamlit Code":
        save_and_run_workflow()
    elif option == "Edit Local Files":
        edit_files_workflow()
    elif option == "Run Existing Script with Dependencies":
        run_script_with_dependencies()

def save_and_run_workflow():
    st.header("Save & Run Streamlit Code")
    st.markdown("**Enter your Streamlit Python code below.** The code will be saved as a `.py` file in the specified directory and run as a Streamlit app.")
    
    code_input = st.text_area("Enter your Streamlit Python code here", height=200)
    directory = st.text_input("Enter the directory path to save the .py file")
    file_name = st.text_input("Enter the file name (e.g., `app.py`)")

    if st.button("Save & Run"):
        if code_input and directory and file_name:
            if os.path.isdir(directory):
                save_code_and_run_with_dependencies(code_input, directory, file_name)
            else:
                st.error("Directory not found. Please enter a valid directory path.")
        else:
            st.error("Please enter the code, directory path, and file name.")

def edit_files_workflow():
    st.header("Edit Local Files")
    st.markdown("**Edit the content of any local Python file.** Enter the directory path and select the file to edit.")
    
    # Directory selector
    directory = st.text_input("Enter the directory path containing the files")

    if st.button("Load Directory"):
        if os.path.isdir(directory):
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            st.session_state['directory'] = directory
            st.session_state['files'] = files
        else:
            st.error("Directory not found. Please enter a valid directory path.")

    if 'files' in st.session_state:
        file_to_edit = st.selectbox("Select a file to edit", st.session_state['files'])
        file_path = os.path.join(st.session_state['directory'], file_to_edit)
        
        if st.button("Load File"):
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            st.session_state['file_content'] = file_content
            st.session_state['file_path'] = file_path

    if 'file_content' in st.session_state:
        file_content = st.text_area("File Content", st.session_state['file_content'], height=400)
        
        if st.button("Save File"):
            with open(st.session_state['file_path'], 'w', encoding='utf-8') as file:
                file.write(file_content)
            st.success(f"File saved: {st.session_state['file_path']}")
            del st.session_state['file_content']

def run_script_with_dependencies():
    st.header("Run Existing Script with Dependencies")
    st.markdown("**Select and run an existing Python script from a specified directory.** The script will be run with all its dependencies.")
    
    # Directory selector
    directory = st.text_input("Enter the directory path containing .py files")
    
    if st.button("Load Directory"):
        if os.path.isdir(directory):
            py_files = [f for f in os.listdir(directory) if f.endswith('.py')]
            st.session_state['py_directory'] = directory
            st.session_state['py_files'] = py_files
        else:
            st.error("Directory not found. Please enter a valid directory path.")
    
    if 'py_files' in st.session_state:
        script_to_run = st.selectbox("Select a script to run", st.session_state['py_files'])
        script_path = os.path.join(st.session_state['py_directory'], script_to_run)
        
        if st.button("Run Script"):
            venv_path = os.path.join(st.session_state['py_directory'], "venv")
            if not os.path.exists(venv_path):
                subprocess.check_call([sys.executable, "-m", "venv", "venv"], cwd=st.session_state['py_directory'])
            
            activate_script = os.path.join(venv_path, "Scripts", "activate") if os.name == 'nt' else os.path.join(venv_path, "bin", "activate")

            with open(script_path, 'r', encoding='utf-8') as file:
                code_content = file.read()

            import_lines = [line for line in code_content.split('\n') if line.startswith('import ') or line.startswith('from ')]
            required_packages = set()
            for line in import_lines:
                parts = line.split()
                if parts[0] == "import":
                    package_name = parts[1]
                elif parts[0] == "from":
                    package_name = parts[1]
                if "." in package_name:
                    package_name = package_name.split(".")[0]
                if not pkgutil.find_loader(package_name):
                    required_packages.add(package_name)
            
            installed_packages = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True).split('\n')
            installed_packages = {pkg.split('==')[0] for pkg in installed_packages}
            
            for package in required_packages:
                if package not in installed_packages:
                    install_package(package)
            
            command = f'cmd /k "{activate_script} & streamlit run {script_path}"' if os.name == 'nt' else f'bash -c "source {activate_script} && streamlit run {script_path}"'
            subprocess.Popen(command, shell=True, cwd=st.session_state['py_directory'])
            st.success(f"Running script: {script_path}")

if __name__ == "__main__":
    main()