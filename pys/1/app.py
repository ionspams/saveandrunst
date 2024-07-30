import streamlit as st
import pandas as pd
import plotly.express as px
import json
import openpyxl
import requests
import os
from datetime import datetime

# Set the page configuration as the first Streamlit command
st.set_page_config(layout="wide")

# GitHub repository and branch details
REPO_OWNER = 'ionspams'
REPO_NAME = 'saveandrunst'
BRANCH_NAME = 'tendtest'
FOLDER_PATH = 'pys/1/existing_gantt_files'

def main():
    st.title("Project Management Interactive Dashboard")
    st.sidebar.title("Navigation")
    
    option = st.sidebar.selectbox("Choose an option", ["Upload Documents", "Use Existing Gantt File", "Manage Tasks", "Manage Resources", "View and Download Gantt Files"])

    if option == "Upload Documents":
        upload_documents()
    elif option == "Use Existing Gantt File":
        use_existing_gantt_file()
    elif option == "Manage Tasks":
        manage_tasks()
    elif option == "Manage Resources":
        manage_resources()
    elif option == "View and Download Gantt Files":
        view_and_download_files()

def list_files():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FOLDER_PATH}?ref={BRANCH_NAME}"
    response = requests.get(url)
    if response.status_code == 200:
        files = response.json()
        return [file['name'] for file in files if file['type'] == 'file']
    else:
        st.error(f"Failed to fetch files from GitHub: {response.status_code}")
        st.write(response.json())
        return []

def download_file(file_name):
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH_NAME}/{FOLDER_PATH}/{file_name}"
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(FOLDER_PATH, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        st.success(f"Downloaded {file_name}")
    else:
        st.error(f"Failed to download file: {response.status_code}")
        st.write(response.text)

def display_gantt_file(file_name):
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH_NAME}/{FOLDER_PATH}/{file_name}"
    response = requests.get(url)
    if response.status_code == 200:
        file_content = response.content.decode('utf-8')
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(file_content)
        elif file_name.endswith('.csv'):
            df = pd.read_csv(file_content)
        elif file_name.endswith('.gantt'):
            df = process_gantt_file_content(file_content)
        else:
            st.error("Unsupported file type.")
            return
        st.write(df)
    else:
        st.error(f"Failed to load file: {response.status_code}")

def view_and_download_files():
    st.sidebar.subheader("View and Download Gantt Files")
    files = list_files()
    if files:
        selected_file = st.sidebar.selectbox("Select a file to view/download", files)
        if st.sidebar.button("View"):
            display_gantt_file(selected_file)
        if st.sidebar.button("Download"):
            download_file(selected_file)

def process_gantt_file_content(file_content):
    try:
        gantt_data_json = json.loads(file_content)
    except json.JSONDecodeError:
        st.error("Error parsing the Gantt file. Please ensure it is in valid JSON format.")
        return pd.DataFrame()

    if 'data' not in gantt_data_json:
        st.error("The Gantt file does not contain the expected structure. Please check the file.")
        st.json(gantt_data_json)  # Display the JSON structure for debugging
        return pd.DataFrame()
    
    gantt_data = {
        'Task': [],
        'Start': [],
        'Finish': [],
        'Resource': [],
        'Progress': [],
        'Predecessor': [],
        'Info': []
    }
    
    for item in gantt_data_json['data']:
        gantt_data['Task'].append(item['TaskName'])
        gantt_data['Start'].append(item['StartDate'])
        gantt_data['Finish'].append(item['EndDate'])
        gantt_data['Resource'].append(", ".join([res['resourceName'] for res in item['resources']]))
        gantt_data['Progress'].append(item['Progress'])
        gantt_data['Predecessor'].append(item['Predecessor'])
        gantt_data['Info'].append(item['info'])
    
    gantt_df = pd.DataFrame(gantt_data)
    return gantt_df

def upload_documents():
    st.sidebar.subheader("Upload New Documents")
    budget_file = st.sidebar.file_uploader("Upload Activity Based Budget", type=["xlsx"])
    project_file = st.sidebar.file_uploader("Upload Project Document", type=["pdf", "docx"])

    if budget_file and project_file:
        budget_data = process_budget(budget_file)
        project_data = process_project_doc(project_file)

        gantt_data = generate_gantt_data(budget_data, project_data)
        gantt_chart = create_gantt_chart(gantt_data)

        st.plotly_chart(gantt_chart)
        show_dashboard(gantt_data)
        add_edit_tasks(gantt_data)

def use_existing_gantt_file():
    st.sidebar.subheader("Upload Existing Gantt File")
    gantt_file = st.sidebar.file_uploader("Upload Existing Gantt File", type=["xlsx", "csv", "gantt"])

    if gantt_file:
        if gantt_file.name.endswith('.xlsx'):
            gantt_data = pd.read_excel(gantt_file)
        elif gantt_file.name.endswith('.csv'):
            gantt_data = pd.read_csv(gantt_file)
        elif gantt_file.name.endswith('.gantt'):
            gantt_data = process_gantt_file(gantt_file)
        else:
            st.error("Unsupported file type. Please upload a CSV, XLSX, or Gantt file.")
            return

        if not gantt_data.empty:
            gantt_chart = create_gantt_chart(gantt_data)
            st.plotly_chart(gantt_chart)
            show_dashboard(gantt_data)
            add_edit_tasks(gantt_data)

def process_budget(file):
    df = pd.read_excel(file, sheet_name='Activity Based Budget')
    return df

def process_project_doc(file):
    pdf_reader = PyPDF2.PdfFileReader(file)
    project_text = ""
    for page in range(pdf_reader.getNumPages()):
        project_text += pdf_reader.getPage(page).extract_text()
    return project_text

def process_gantt_file(file):
    file_content = file.read().decode('utf-8')
    try:
        gantt_data_json = json.loads(file_content)
    except json.JSONDecodeError:
        st.error("Error parsing the Gantt file. Please ensure it is in valid JSON format.")
        return pd.DataFrame()

    if 'data' not in gantt_data_json:
        st.error("The Gantt file does not contain the expected structure. Please check the file.")
        st.json(gantt_data_json)  # Display the JSON structure for debugging
        return pd.DataFrame()
    
    gantt_data = {
        'Task': [],
        'Start': [],
        'Finish': [],
        'Resource': [],
        'Progress': [],
        'Predecessor': [],
        'Info': []
    }
    
    for item in gantt_data_json['data']:
        gantt_data['Task'].append(item['TaskName'])
        gantt_data['Start'].append(item['StartDate'])
        gantt_data['Finish'].append(item['EndDate'])
        gantt_data['Resource'].append(", ".join([res['resourceName'] for res in item['resources']]))
        gantt_data['Progress'].append(item['Progress'])
        gantt_data['Predecessor'].append(item['Predecessor'])
        gantt_data['Info'].append(item['info'])
    
    gantt_df = pd.DataFrame(gantt_data)
    return gantt_df

def generate_gantt_data(budget_data, project_data):
    gantt_data = {
        'Task': [],
        'Start': [],
        'Finish': [],
        'Resource': []
    }
    
    for index, row in budget_data.iterrows():
        gantt_data['Task'].append(row['Activity'])
        gantt_data['Start'].append(row['Start Date'])
        gantt_data['Finish'].append(row['End Date'])
        gantt_data['Resource'].append(row['Assigned To'])
    
    gantt_df = pd.DataFrame(gantt_data)
    return gantt_df

def create_gantt_chart(data):
    fig = px.timeline(data, x_start="Start", x_end="Finish", y="Task", color="Resource", title="Gantt Chart")
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(
        autosize=True, 
        margin=dict(l=20, r=20, t=40, b=20), 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        font=dict(size=14, color='white'), 
        yaxis=dict(tickfont=dict(size=16)),
        xaxis=dict(tickfont=dict(size=14))
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color='white')))
    return fig

def show_dashboard(data):
    st.header("Project Dashboard")
    
    st.subheader("Filter Tasks")
    resources = st.multiselect("Select Resources", options=data['Resource'].unique())
    filtered_data = data[data['Resource'].isin(resources)] if resources else data
    
    st.subheader("Filtered Gantt Chart")
    filtered_gantt_chart = create_gantt_chart(filtered_data)
    st.plotly_chart(filtered_gantt_chart)
    
    st.subheader("Progress Overview")
    progress_data = filtered_data[['Task', 'Progress']]
    st.table(progress_data)

def add_edit_tasks(data):
    st.header("Add/Edit Tasks")
    
    with st.form("task_form"):
        task_name = st.text_input("Task Name")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        existing_resources = list(set(", ".join(data['Resource']).split(", ")))
        resource_selection = st.multiselect("Resources", options=existing_resources, default=None)
        new_resource = st.text_input("Add New Resource")
        if new_resource:
            resource_selection.append(new_resource)
        progress = st.slider("Progress", 0, 100, 0)
        info = st.text_area("Task Info")
        
        if st.form_submit_button("Add Task"):
            new_task = pd.DataFrame({
                'Task': [task_name],
                'Start': [start_date.strftime('%Y-%m-%d')],
                'Finish': [end_date.strftime('%Y-%m-%d')],
                'Resource': [", ".join(resource_selection)],
                'Progress': [progress],
                'Predecessor': [""],
                'Info': [info]
            })
            data = pd.concat([data, new_task], ignore_index=True)
            st.success("Task added successfully!")
            save_gantt_file(data)
            st.experimental_rerun()
    
    task_to_edit = st.selectbox("Select Task to Edit", options=data['Task'].unique())
    task_data = data[data['Task'] == task_to_edit]

    edit_start_date = st.date_input("Start Date", pd.to_datetime(task_data['Start'].values[0]))
    edit_end_date = st.date_input("End Date", pd.to_datetime(task_data['Finish'].values[0]))
    edit_resources = st.multiselect("Resources", options=existing_resources, default=task_data['Resource'].values[0].split(", "))
    edit_new_resource = st.text_input("Add New Resource")
    if edit_new_resource:
        edit_resources.append(edit_new_resource)
    edit_progress = st.slider("Progress", 0, 100, int(task_data['Progress'].values[0]))
    edit_info = st.text_area("Task Info", task_data['Info'].values[0])

    if st.button("Save Changes"):
        data.loc[data['Task'] == task_to_edit, 'Start'] = edit_start_date.strftime('%Y-%m-%d')
        data.loc[data['Task'] == task_to_edit, 'Finish'] = edit_end_date.strftime('%Y-%m-%d')
        data.loc[data['Task'] == task_to_edit, 'Resource'] = ", ".join(edit_resources)
        data.loc[data['Task'] == task_to_edit, 'Progress'] = edit_progress
        data.loc[data['Task'] == task_to_edit, 'Info'] = edit_info
        st.success("Task updated successfully!")
        
        # Save the updated data
        save_gantt_file(data)
        st.experimental_rerun()

def manage_tasks():
    gantt_file = st.sidebar.file_uploader("Upload Existing Gantt File", type=["xlsx", "csv", "gantt"])

    if gantt_file:
        if gantt_file.name.endswith('.xlsx'):
            gantt_data = pd.read_excel(gantt_file)
        elif gantt_file.name.endswith('.csv'):
            gantt_data = pd.read_csv(gantt_file)
        elif gantt_file.name.endswith('.gantt'):
            gantt_data = process_gantt_file(gantt_file)
        else:
            st.error("Unsupported file type. Please upload a CSV, XLSX, or Gantt file.")
            return

        if not gantt_data.empty:
            add_edit_tasks(gantt_data)

def manage_resources():
    gantt_file = st.sidebar.file_uploader("Upload Existing Gantt File", type=["xlsx", "csv", "gantt"])

    if gantt_file:
        if gantt_file.name.endswith('.xlsx'):
            gantt_data = pd.read_excel(gantt_file)
        elif gantt_file.name.endswith('.csv'):
            gantt_data = pd.read_csv(gantt_file)
        elif gantt_file.name.endswith('.gantt'):
            gantt_data = process_gantt_file(gantt_file)
        else:
            st.error("Unsupported file type. Please upload a CSV, XLSX, or Gantt file.")
            return

        if not gantt_data.empty:
            edit_resources(gantt_data)

def edit_resources(data):
    st.header("Edit Resources")
    
    resources = st.multiselect("Select Resources to Edit", options=data['Resource'].unique())
    if not resources:
        st.warning("Please select at least one resource to edit.")
        return

    resource_name = st.text_input("Edit Resource Name")
    if st.button("Save Resource Changes"):
        for resource in resources:
            data.loc[data['Resource'] == resource, 'Resource'] = resource_name
        st.success("Resources updated successfully!")
        
        # Save the updated data
        save_gantt_file(data)
        st.experimental_rerun()

def save_gantt_file(data):
    gantt_data_json = {
        'data': []
    }
    for i, row in data.iterrows():
        start_date = row['Start']
        finish_date = row['Finish']

        # Convert to datetime if they are strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(finish_date, str):
            finish_date = datetime.strptime(finish_date, '%Y-%m-%d')

        task_data = {
            "TaskName": row['Task'],
            "StartDate": start_date.strftime('%Y-%m-%d'),  # Convert date to string
            "EndDate": finish_date.strftime('%Y-%m-%d'),  # Convert date to string
            "Progress": row['Progress'],
            "Predecessor": row['Predecessor'],
            "info": row['Info'],
            "resources": [{"resourceName": res.strip()} for res in row['Resource'].split(",")]
        }
        gantt_data_json['data'].append(task_data)

    with open('updated_gantt_file.gantt', 'w') as f:
        json.dump(gantt_data_json, f)
        st.info("Updated Gantt file saved as 'updated_gantt_file.gantt'")

if __name__ == "__main__":
    main()
