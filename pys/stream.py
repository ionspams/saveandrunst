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

def execute_code(code_input):
    tempdir = tempfile.mkdtemp()
    try:
        # Extract import statements and install missing packages
        import_lines = [line for line in code_input.split('\n') if line.startswith('import ') or line.startswith('from ')]
        for line in import_lines:
            package_name = line.split()[1]
            if "." in package_name:
                package_name = package_name.split(".")[0]
            if not pkgutil.find_loader(package_name):
                install_package(package_name)

        os.chdir(tempdir)
        # Execute the code
        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                exec(code_input, {'__name__': '__main__'})
            except Exception as e:
                return f"Error: {e}", tempdir
            output = buf.getvalue()

        return output, tempdir
    except Exception as e:
        return f"Error while installing packages: {e}", tempdir

def main():
    st.title("Enhanced Python Code Runner  and File Editor")

    # Navigation
    option = st.sidebar.selectbox(
        "Choose an option",
        ["Run Python Code", "Edit Local Files", "Run Script with Dependencies"]
    )

    if option == "Run Python Code":
        run_code_workflow()
    elif option == "Edit Local Files":
        edit_files_workflow()
    elif option == "Run Script with Dependencies":
        run_script_with_dependencies()

def run_code_workflow():
    st.header("Run Python Code")
    code_input = st.text_area("Enter Python Code Here", height=200)

    if st.button("Run Code"):
        if code_input:
            output, tempdir = execute_code(code_input)
            if tempdir:
                st.text_area("Output", value=output, height=200)
                st.write(f"Files generated in temporary directory: {tempdir}")
                st.write(f"Temporary directory content: {os.listdir(tempdir)}")
            else:
                st.error(output)
        else:
            st.error("Please enter some code to run.")

def edit_files_workflow():
    st.header("Edit Local Files")
    
    # Directory selector
    directory = st.text_input("Enter the directory path")
    
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
    st.header("Run Script with Dependencies")
    
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
