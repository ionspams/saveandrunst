import streamlit as st
import subprocess
import sys
import io
import contextlib
import os
import tempfile
import pkgutil

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        st.error(f"Error installing package {package}: {e}")
        raise

def execute_code_in_memory(code_input):
    try:
        import_lines = [line for line in code_input.split('\n') if line.startswith('import ') or line.startswith('from ')]
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

        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(code_input, {'__name__': '__main__'})
            output = buf.getvalue()
        st.text_area("Output", output, height=400)
    except Exception as e:
        st.error(f"Error while executing the code: {e}")

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
    st.markdown("**Enter your Streamlit Python code below.** The code will be executed in-memory and the output will be displayed.")
    
    code_input = st.text_area("Enter your Streamlit Python code here", height=200)

    if st.button("Run Code"):
        if code_input:
            execute_code_in_memory(code_input)
        else:
            st.error("Please enter the code.")

def edit_files_workflow():
    st.header("Edit Local Files")
    st.markdown("**Edit the content of any local Python file.** Upload the file to edit.")

    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode('utf-8')
        edited_content = st.text_area("File Content", file_content, height=400)
        
        if st.button("Save File"):
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(edited_content)
            st.success(f"File saved: {file_path}")

def run_script_with_dependencies():
    st.header("Run Existing Script with Dependencies")
    st.markdown("**Upload and run an existing Python script.** The script will be run with all its dependencies.")
    
    uploaded_file = st.file_uploader("Choose a .py file")
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode('utf-8')
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, uploaded_file.name)

        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(file_content)
        
        venv_path = os.path.join(temp_dir, "venv")
        if not os.path.exists(venv_path):
            subprocess.check_call([sys.executable, "-m", "venv", "venv"], cwd=temp_dir)
        
        activate_script = os.path.join(venv_path, "Scripts", "activate") if os.name == 'nt' else os.path.join(venv_path, "bin", "activate")

        import_lines = [line for line in file_content.split('\n') if line.startswith('import ') or line.startswith('from ')]
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
            command = f'{activate_script} & python {script_path}'
        else:
            command = f'bash -c ". {activate_script} && python {script_path}"'

        st.write(f"Running command: {command}")

        process = subprocess.Popen(command, shell=True, cwd=temp_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        if out:
            st.text_area("Command Output", out.decode('utf-8'))
        if err:
            st.text_area("Command Error", err.decode('utf-8'))

        st.success(f"Running script: {script_path}")

if __name__ == "__main__":
    main()