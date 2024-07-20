import streamlit as st
import subprocess
import sys
import io
import contextlib
import uuid

def generate_unique_key(prefix):
    return f"{prefix}_{uuid.uuid4()}"

def execute_code_in_memory(code_input):
    try:
        with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(code_input, {'__name__': '__main__'})
            output = buf.getvalue()
        st.text_area("Output", output, height=400, key=generate_unique_key("output"))
    except Exception as e:
        st.error(f"Error while executing the code: {e}")

def main():
    st.title("Streamlit App Code Runner")

    # Navigation
    option = st.sidebar.selectbox(
        "Choose an option",
        ["Run Streamlit Code", "Edit Local Files", "Run Existing Script with Dependencies"],
        key="main_option"
    )

    if option == "Run Streamlit Code":
        run_code_workflow()
    elif option == "Edit Local Files":
        edit_files_workflow()
    elif option == "Run Existing Script with Dependencies":
        run_script_workflow()

def run_code_workflow():
    st.header("Run Streamlit Code")
    st.markdown("**Enter your Streamlit Python code below.** The code will be executed in-memory and the output will be displayed.")
    
    code_input = st.text_area("Enter your Streamlit Python code here", height=200, key="code_input")

    def run_code():
        if code_input:
            execute_code_in_memory(code_input)
        else:
            st.error("Please enter the code.")

    st.button("Run Code", on_click=run_code, key="run_code_button")

def edit_files_workflow():
    st.header("Edit Local Files")
    st.markdown("**Edit the content of any local Python file.** Upload the file to edit.")

    uploaded_file = st.file_uploader("Choose a file", key=generate_unique_key("file_uploader"))
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode('utf-8')
        edited_content = st.text_area("File Content", file_content, height=400, key=generate_unique_key("file_content"))
        
        if st.button("Save File", key=generate_unique_key("save_file_button")):
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(edited_content)
            st.success(f"File saved: {file_path}")

def run_script_workflow():
    st.header("Run Existing Script with Dependencies")
    st.markdown("**Upload and run an existing Python script.** The script will be run with all its dependencies.")
    
    uploaded_file = st.file_uploader("Choose a .py file", key=generate_unique_key("script_uploader"))
    if uploaded_file is not None:
        file_content = uploaded_file.read().decode('utf-8')
        temp_dir = tempfile.mkdtemp()
        script_path = os.path.join(temp_dir, uploaded_file.name)

        with open(script_path, 'w', encoding='utf-8') as file:
            file.write(file_content)

        def run_script():
            try:
                with io.StringIO() as buf, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    exec(file_content, {'__name__': '__main__'})
                    output = buf.getvalue()
                st.text_area("Script Output", output, height=400, key=generate_unique_key("output"))
            except Exception as e:
                st.error(f"Error while executing the script: {e}")

        st.button("Run Script", on_click=run_script, key=generate_unique_key("run_script_button"))

if __name__ == "__main__":
    main()
